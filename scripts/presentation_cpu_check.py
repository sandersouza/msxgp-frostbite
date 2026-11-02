"""Fresh presentation-cartridge native CPU replay; no paced/graphics verdict."""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

from environment import ROOT
from native_contract import compare
from presentation_build import FILES,validate_rom
from progression_play import source_helpers,input_records,assess_receipt
from progression_routes import validate_policy
from reference_provenance import audit_manifest
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile
from stella_floe import digest
from trace_compare import validate_trace

HELPERS=tuple(dict.fromkeys((*FILES,'scripts/presentation_cpu_check.py','scripts/progression_play.py','scripts/progression_routes.py',
    'scripts/progression_native.tcl','scripts/hazard_native.tcl','scripts/native_contract.py','scripts/render_build.py','scripts/smoke.py')))


def verify_capture(actual,expected,log):
    if 'FLOE_NATIVE_FAIL' in log or len(actual)!=len(expected)*137:raise ValueError('fatal or incomplete native CPU capture')
    points=[];cycles=[]
    for index,want in enumerate(expected):
        row=actual[index*137:(index+1)*137]
        got={'registers':dict(zip(('a','x','y','p','sp'),row[:5])),'ram':list(row[5:133])}
        try:compare(want,got)
        except ValueError as error:raise ValueError(f'presentation native CPU/RAM case{index}: {error}') from error
        points.append({**got,'index':index});cycles.append(struct.unpack('<I',row[133:137])[0])
    return points,cycles


def check(source,out,build_dir):
    source=Path(source).resolve();build_dir=Path(build_dir).resolve();receipt=json.loads((source/'route.json').read_text())
    helpers=source_helpers(receipt);audit_manifest(receipt,helpers)
    if receipt.get('clean_start')is not True or any(digest(source/name)!=value for name,value in receipt['files'].items()):raise ValueError('clean immutable original route required')
    consumed={str(source/name):value for name,value in receipt['files'].items()};consumed[str(source/'route.json')]=digest(source/'route.json')
    trace=json.loads((source/'trace.json').read_text());validate_trace(trace);validate_policy(trace['policy'])
    inputs=json.loads((source/'inputs.json').read_text());records=input_records(inputs,trace['steps'])
    expected=[{'ram':point['ram'],'registers':{k:point['cpu'][k] for k in ('a','x','y','p','sp')}} for point in trace['steps']]
    if not expected:raise ValueError('nonempty complete original route required')
    metadata=json.loads((build_dir/'build.json').read_text());artifact=build_dir/metadata['rom']['filename'];rom=artifact.read_bytes()
    if validate_rom(rom) or digest(artifact)!=metadata['rom']['sha256']:raise ValueError('presentation native replay ROM identity mismatch')
    if any(digest(ROOT/name)!=value for name,value in metadata['source_files'].items()):raise ValueError('presentation build producers changed')
    files=tuple(dict.fromkeys((*HELPERS,*helpers)));producer={name:digest(ROOT/name) for name in files}
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(records)
    (out/'expected.json').write_text(json.dumps(expected,indent=2)+'\n')
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_CpuReplay.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    syms=symbols(build_dir/'presentation.sym');launcher=out/'launch.tcl'
    launcher.write_text(f'set floe_dir {{{out}}}\nset natural 1\nset step_fixture 0\nset inject none\n'
        +'array set symbols {'+' '.join(f'{name} {syms[name]}' for name in ('native_reset_done','native_step','visible_step','sample_native_return','native_call','native_return'))+'}\n'
        +f'source {{{ROOT/"scripts/progression_native.tcl"}}}\n')
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_CpuReplay','-cart',str(artifact),'-romtype','ASCII16','-script',str(launcher)],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'FLOE_NATIVE_FAIL' in log or not (out/'complete.json').is_file():raise ValueError('presentation CPU replay capture failed: '+log[-1400:])
    complete=json.loads((out/'complete.json').read_text())
    if (complete.get('complete')is not True or complete['cases']!=len(expected) or complete['clock_hz']!=3579545 or complete['ram_bytes']!=65536
        or complete['stack_min']<0xF340 or complete['canonical_ram_injections']!=0):raise ValueError('incomplete or unsafe presentation CPU receipt')
    points,cycles=verify_capture((out/'actual.bin').read_bytes(),expected,log);assessment=assess_receipt(points,receipt)
    if assessment!=receipt['assessment']:raise ValueError('original/native replay milestones differ')
    if (any(digest(ROOT/name)!=value for name,value in producer.items()) or any(digest(name)!=value for name,value in consumed.items())
        or artifact.read_bytes()!=rom or (out/'cases.bin').read_bytes()!=records):raise ValueError('CPU replay producers/source/ROM/input changed')
    report={**complete,'producer_files':producer,'source_files':consumed,'original_route_sha256':digest(source/'route.json'),'assessment':assessment,
        'rom_sha256':metadata['rom']['sha256'],'max_native_cycles':max(cycles),'emulator_sha256':digest(emulator),
        'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,'graphics_accepted':False,'audio_accepted':False,
        'scope':'Fresh exact presentation-cartridge CPU/all128RAM and native contact-bank replay against immutable independent original input-only route, with real controller/console sampling and zero state injections. This CPU-only RPC does not execute/promise paced rendering or PSG.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_native_cycles')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','out','build-dir'):p.add_argument('--'+name,type=Path,required=True)
    check(**vars(p.parse_args()))
