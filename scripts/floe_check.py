"""Actual MSX1 visible-adapter cases and uninterrupted original natural replay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET

from environment import ROOT
from floe_build import OUT,FILES
from floe_query import RawContacts
from floe_reference import visible_reference
from floe_model import visible_state
from floe_routes import assess
from floe_truth import full_record
from native_contract import compare,HELPERS as NATIVE_HELPERS
from reference_provenance import snapshot_paths,audit_manifest
from reference_state import decode_state
from reference_traces import private_output
from render_bench import validate_source_files
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile
from stella_floe import control_pairs,digest,fixture,observe,HELPERS as OBSERVER_HELPERS

HELPERS=tuple(dict.fromkeys((*FILES,*OBSERVER_HELPERS,*NATIVE_HELPERS,'scripts/floe_check.py','scripts/floe_native.tcl',
         'scripts/floe_query.py','scripts/floe_routes.py','references/floe-routes.json','scripts/floe_catalog.py',
         'scripts/floe_reference.py','scripts/floe_model.py','scripts/native_contract.py','scripts/reference_cpu_check.py',
         'scripts/mechanics_probe.py','scripts/reference_provenance.py','scripts/smoke.py','scripts/render_bench.py',
         'scripts/trace_compare.py','scripts/source_timing.py')))


def run_target(out,build_dir,records,expected,natural=False,explore=False,inject='none',step_fixture=False,extra_helpers=(),target_script='scripts/floe_native.tcl'):
    expected=[{'registers':row['registers'],'ram':list(row['ram'])} for row in expected]
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);build_dir=Path(build_dir)
    metadata=json.loads((build_dir/'build.json').read_text());rom=build_dir/metadata['rom']['filename'];artifact=rom.read_bytes()
    if digest(rom)!=metadata['rom']['sha256'] or artifact[16:20]!=b'FBF0':raise ValueError('native floe ROM identity mismatch')
    validate_source_files(metadata)
    if not explore:
        if metadata['source_dirty'] or subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('clean committed native capture required')
        audit_manifest({'tool_source_commit':metadata['source_commit'],'utility_fingerprints':metadata['source_files']},FILES)
    helpers=tuple(dict.fromkeys((*HELPERS,*extra_helpers)))
    if target_script not in helpers:raise ValueError('target script must be in the audited helper closure')
    producer=snapshot_paths(helpers) if not explore else {'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'utility_fingerprints':{name:digest(ROOT/name) for name in helpers}}
    (out/'cases.bin').write_bytes(records);(out/'expected.json').write_text(json.dumps(expected,indent=2)+'\n')
    (out/rom.name).write_bytes(artifact);(out/'build.json').write_text(json.dumps(metadata,indent=2)+'\n')
    emulator=Path(shutil.which('openmsx')).resolve();emulator_sha=digest(emulator)
    profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/Frostbite_Floes.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    syms=symbols(build_dir/'floes.sym');launcher=out/'launch.tcl'
    launcher.write_text(f'set floe_dir {{{out}}}\nset natural {int(natural)}\nset step_fixture {int(step_fixture)}\nset inject {{{inject}}}\n'
        +'array set symbols {'+' '.join(f'{name} {syms[name]}' for name in ('native_reset_done','native_step','visible_step','sample_native_return'))+'}\n'
        +f'source {{{ROOT/target_script}}}\n')
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Floes','-cart',str(out/rom.name),
        '-romtype','ASCII16','-script',str(launcher)],cwd=ROOT,env={**os.environ,'OPENMSX_USER_DATA':str(user),
        'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,errors='replace',timeout=120)
    (out/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode or not (out/'complete.json').is_file():raise ValueError(f'native floe capture failed {out}: '+(result.stdout+result.stderr)[-1000:])
    receipt=json.loads((out/'complete.json').read_text());actual=(out/'actual.bin').read_bytes()
    if (receipt.get('complete') is not True or receipt['cases']!=len(expected) or len(actual)!=len(expected)*137 or
            receipt['clock_hz']!=3579545 or receipt['ram_bytes']!=65536 or receipt['stack_min']<0xF340 or
            receipt['canonical_ram_injections']!=(0 if natural else len(expected))):raise ValueError('incomplete/unsafe native floe receipt')
    points=[];cycles=[]
    for index,want in enumerate(expected):
        row=actual[index*137:(index+1)*137];got={'registers':dict(zip(('a','x','y','p','sp'),row[:5])),'ram':list(row[5:133])}
        try:compare(want,got)
        except ValueError as error:raise ValueError(f'native floe case{index}: {error}; {out}') from error
        points.append(got);cycles.append(struct.unpack('<I',row[133:137])[0])
    if inject!='none':raise ValueError('intended native floe fault escaped detection')
    if digest(emulator)!=emulator_sha or rom.read_bytes()!=artifact:raise ValueError('emulator/ROM changed during capture')
    validate_source_files(metadata)
    if any(digest(ROOT/name)!=sha for name,sha in producer['utility_fingerprints'].items()):raise ValueError('native floe producer changed')
    if not explore and snapshot_paths(helpers)!=producer:raise ValueError('native floe producer revision changed')
    report={**receipt,**producer,'rom':metadata['rom'],'build_source_commit':metadata['source_commit'],
            'exploratory':explore,'emulator_sha256':emulator_sha,'profile_sha256':hashlib.sha256(profile).hexdigest(),
            'max_native_cycles':max(cycles),'natural':natural,
            'artifacts':{str(path.relative_to(out)):digest(path) for path in out.rglob('*') if path.is_file()}}
    (out/'verified.json').write_text(json.dumps(report,indent=2)+'\n');return report,points


def geometry(out,build_dir,binary,initial_path,explore=False,inject='none'):
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    initial=Path(initial_path).read_bytes();base=decode_state(initial);rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    controls=control_pairs(rom);rng=random.Random(1111);cases=[]
    for i in range(1368):
        view=i%228;px=(0,1,7,8,9,15,64,151,152,158,159)[i%11];row=i%4
        y=45+rng.randrange(33)+(3-row)*26;fx=(0,1,7,8,9,15,64,151,152,158,159)[(i//11)%11]
        ram=bytearray(fixture(base['ram'],px,y,fx,controls[i%len(controls)]))
        values={0xEE:view//38,0xEB:view%38//2,0xEC:(view%2)*8,0xC6:rng.randrange(256),0xF0:i%4,
                0xC5:128 if i%5==0 else 0,0xCB:i%8,0xCD:(255,0,14,15)[i%4],0xED:(0,7,128,199)[i%4],0xBF:128 if i%7==0 else 0}
        for address,value in values.items():ram[address-128]=value
        cases.append(bytes(ram))
    data,source=observe(ROOT/'references/roms/frostbite.bin',binary,initial,cases,out/'original')
    expected=[];full_original=0;neutralized=[]
    for index,ram in enumerate(cases):
        original=full_record(data[index*384:(index+1)*384])
        rows=bytearray(original['ram'][0x30:0x38]);rows[1::2]=bytes([7])*4
        contacts={'rows':bytes(rows),'shore':7}
        want=visible_reference(rom,ram,base['cpu'],contacts)
        compare(want,visible_state(rom,ram,base['cpu'],contacts))
        differences=[offset for offset,(a,b) in enumerate(zip(original['ram'],want['ram'])) if a!=b]
        if original['registers']!=want['registers'] or any(offset not in (0x31,0x33,0x35,0x37,0x6D) for offset in differences):
            raise ValueError('original visible differences exceed explicitly deferred hazard/shore acquisition')
        if differences:neutralized.append({'case':index,'source_fields':[f'{offset+128:02X}' for offset in differences]})
        else:full_original+=1
        expected.append(want)
    records=b''.join(ram+bytes(base['cpu'][key] for key in ('a','x','y','p','sp')) for ram in cases)
    report,_=run_target(out/'native',build_dir,records,expected,explore=explore,inject=inject)
    report.update(source_observation_sha256=digest(out/'original/observation.json'),actual_literal_views=228,
                  full_original_phase_cases=full_original,declared_neutral_hazard_cases=neutralized,
                  scope='Original actual even-row electrical contacts in every case, then complete CPU/RAM reduction against unchanged original instructions with explicit odd07/shore07 stimuli. Full actual-original phase equality when those deferred channels agree. Full hazard/shore acquisition belongs12; natural-route acceptance is separate.')
    (out/'geometry.json').write_text(json.dumps(report,indent=2)+'\n');return report


def natural(out,build_dir,source,explore=False):
    source=Path(source);receipt=json.loads((source/'route.json').read_text())
    if any(digest(source/name)!=sha for name,sha in receipt['files'].items()):raise ValueError('natural source evidence changed')
    trace=json.loads((source/'trace.json').read_text());inputs=json.loads((source/'inputs.json').read_text())
    if len(inputs)!=len(trace['steps']):raise ValueError('complete natural raw inputs required')
    records=b''
    for sample in inputs:
        if sample['fire'][1] or sample['swcha']&15!=15:raise ValueError('natural keyboard route requires neutral port2')
        records+=bytes((sample['swcha'],sample['swchb'],int(sample['fire'][0])))
    expected=[{'ram':point['ram'],'registers':{key:point['cpu'][key] for key in ('a','x','y','p','sp')}} for point in trace['steps']]
    report,points=run_target(out,build_dir,records,expected,natural=True,explore=explore)
    assessment=assess(points,trace['policy']['preparation_intervals']-1)
    if assessment!=receipt['assessment']:raise ValueError('native natural milestones differ from original')
    report.update(assessment=assessment,original_route_sha256=digest(source/'route.json'),
                  scope='Automated standard MSX1 uninterrupted native cold-reset/input route versus unmodified original full CPU/RAM; no source/contact injections. Manual/physical acceptance separate.')
    (Path(out)/'natural.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--build-dir',type=Path,default=OUT);parser.add_argument('--natural-source',type=Path)
    parser.add_argument('--binary',type=Path);parser.add_argument('--initial',type=Path);parser.add_argument('--explore',action='store_true')
    parser.add_argument('--inject',choices=('none','contact'),default='none');args=parser.parse_args()
    result=natural(args.out,args.build_dir,args.natural_source,args.explore) if args.natural_source else geometry(args.out,args.build_dir,args.binary,args.initial,args.explore,args.inject)
    print(json.dumps({'cases':result['cases'],'natural':result.get('natural'),'max_native_cycles':result['max_native_cycles']}))
