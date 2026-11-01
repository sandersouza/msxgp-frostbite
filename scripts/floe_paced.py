"""Replay natural controls through the actual paced ROM and verify every frame."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET

from environment import ROOT
from floe_build import OUT,FILES,expected_pixels,presentation
from floe_bench import decode_scene
from floe_check import HELPERS as NATIVE_HELPERS
from floe_routes import assess
from native_contract import compare
from reference_provenance import snapshot_paths,audit_manifest
from reference_traces import private_output
from render_bench import validate_source_files,visible_signature
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile
from stella_floe import digest
import render_model as model

FRAME_BYTES=49364
HELPERS=tuple(dict.fromkeys((*NATIVE_HELPERS,'scripts/floe_paced.py','scripts/floe_paced.tcl','scripts/floe_bench.py','scripts/floe_bench.tcl')))


def capture(out,build_dir,source,family='ntsc',explore=False):
    if family not in ('ntsc','pal'):raise ValueError('explicit NTSC/PAL family required')
    source=Path(source);out=private_output(out);out.mkdir(parents=True,exist_ok=False);build_dir=Path(build_dir)
    source_receipt=json.loads((source/'route.json').read_text())
    if any(digest(source/name)!=sha for name,sha in source_receipt['files'].items()):raise ValueError('natural original evidence changed')
    trace=json.loads((source/'trace.json').read_text());inputs=json.loads((source/'inputs.json').read_text())
    metadata=json.loads((build_dir/'build.json').read_text());rom=build_dir/metadata['rom']['filename'];artifact=rom.read_bytes()
    if digest(rom)!=metadata['rom']['sha256'] or artifact[16:20]!=b'FBF0':raise ValueError('paced ROM identity mismatch')
    validate_source_files(metadata)
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    if not explore and (dirty or metadata['source_dirty']):raise ValueError('clean committed paced producer required')
    producer=snapshot_paths(HELPERS) if not explore else {'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'utility_fingerprints':{name:digest(ROOT/name) for name in HELPERS}}
    if not explore:audit_manifest({'tool_source_commit':metadata['source_commit'],'utility_fingerprints':metadata['source_files']},FILES)
    raw_inputs=bytearray()
    for sample in inputs:
        if sample['swcha']&15!=15 or sample['fire'][1]:raise ValueError('natural keyboard replay requires neutral second controller')
        raw_inputs.extend((sample['swcha'],sample['swchb'],int(sample['fire'][0])))
    (out/'inputs.bin').write_bytes(raw_inputs);(out/rom.name).write_bytes(artifact)
    (out/'build.json').write_text(json.dumps(metadata,indent=2)+'\n')
    emulator=Path(shutil.which('openmsx')).resolve();emulator_sha=digest(emulator)
    effective=ET.fromstring(isolated_profile(find_machine_profile(str(emulator))))
    effective.find('.//VDP/version').text='TMS9918A' if family=='ntsc' else 'TMS9929A'
    profile=b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">'+ET.tostring(effective);validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Paced.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    syms=symbols(build_dir/'floes.sym');names=('native_reset_done','native_step','native_return','paced_frame_start','prepare','paced_wait','paced_commit','commit_end','status_sample')
    launcher=out/'launch.tcl';launcher.write_text(f'set paced_dir {{{out}}}\narray set symbols {{'+' '.join(f'{name} {syms[name]}' for name in names)+'}\n'+f'source {{{ROOT/"scripts/floe_paced.tcl"}}}\n')
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Paced','-cart',str(out/rom.name),'-romtype','ASCII16','-script',str(launcher)],
        cwd=ROOT,env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,errors='replace',timeout=120)
    (out/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode or not (out/'complete.json').is_file():raise ValueError(f'paced natural replay incomplete {out}: '+(result.stdout+result.stderr)[-1000:])
    report=json.loads((out/'complete.json').read_text());states=(out/'states.bin').read_bytes();frames=(out/'frames.bin').read_bytes()
    if (report.get('complete') is not True or report['source_steps']!=len(inputs) or len(states)!=137*len(inputs)
            or len(frames)!=FRAME_BYTES*report['frames'] or report['canonical_ram_injections']!=0 or report['frames']<1000
            or report['clock_hz']!=3579545 or report['ram_bytes']!=65536 or report['min_spacing']<29
            or not 1<=report['max_sprites_per_line']<=4 or report['stack_min']<0xF340 or report['pal_flag']!=int(family=='pal')):
        raise ValueError('incomplete/unsafe paced natural evidence')
    points=[];source_cycles=[]
    for index,want in enumerate(trace['steps']):
        row=states[index*137:(index+1)*137];got={'registers':dict(zip(('a','x','y','p','sp'),row[:5])),'ram':list(row[5:133])}
        expected={'registers':{key:want['cpu'][key] for key in ('a','x','y','p','sp')},'ram':want['ram']}
        try:compare(expected,got)
        except ValueError as error:raise ValueError(f'paced native state{index}: {error}; {out}') from error
        points.append(got);source_cycles.append(struct.unpack('<I',row[133:137])[0])
    if assess(points,trace['policy']['preparation_intervals']-1)!=source_receipt['assessment']:raise ValueError('paced natural milestones differ')
    period=59736 if family=='ntsc' else 71364;busy=[];vdp_frames=[];logical=1;peak=0
    for index,nsteps in enumerate(model.schedule(report['frames'],period)):
        row=frames[index*FRAME_BYTES:(index+1)*FRAME_BYTES];frame,steps,work,spacing,commit,y0,y1=struct.unpack('<7i',row[:28])
        logical+=nsteps
        if steps!=logical or not 0<=steps-1<len(points):raise ValueError('paced source count/cadence differs')
        if index and (not 0<work<period or abs(spacing-period)>40):raise ValueError(f'natural frame budget/cadence exceeded at{index}: {work}/{period}')
        if not 0<commit<4000 or 0<=y0<192 or 0<=y1<192:raise ValueError('natural commit outside VBlank')
        canonical=row[28:156];scene=row[156:188]
        if canonical!=bytes(points[steps-1]['ram']):raise ValueError('natural renderer did not use its own latest source state')
        decoded=decode_scene(scene)
        if model.encode_scene(presentation(canonical,decoded['layout'],decoded['width']))!=scene:raise ValueError('natural presentation adaptation differs')
        before=row[188:16572];before_regs=list(row[16572:16580]);prepared=row[16580:32964];prepared_regs=list(row[32964:32972])
        presented=row[32972:49356];presented_regs=list(row[49356:49364])
        if visible_signature(before,before_regs)!=visible_signature(prepared,prepared_regs):raise ValueError('natural preparation changed the visible frame')
        if bytes(model.decode_pixels(presented,presented_regs))!=bytes(expected_pixels(decoded)):raise ValueError(f'natural pixel mismatch frame{index}')
        if presented[0x1B00:0x1B21]!=model.sprite_attributes(decoded) or presented[0x3800:0x4000]!=model.sprite_patterns():raise ValueError('natural SAT/pattern mismatch')
        peak=max(peak,max(model.occupancy(presented[0x1B00:0x1B21])));vdp_frames.append(frame);busy.append(work)
    if any(b-a!=1 for a,b in zip(vdp_frames,vdp_frames[1:])) or peak!=report['max_sprites_per_line']:raise ValueError('natural skipped frames or mismatched sprite receipt')
    if digest(emulator)!=emulator_sha or rom.read_bytes()!=artifact:raise ValueError('paced emulator/ROM changed')
    validate_source_files(metadata)
    if any(digest(ROOT/name)!=sha for name,sha in producer['utility_fingerprints'].items()):raise ValueError('paced helper changed during capture')
    if not explore and snapshot_paths(HELPERS)!=producer:raise ValueError('paced producer revision changed')
    report.update(**producer,family=family,rom=metadata['rom'],build_source_commit=metadata['source_commit'],exploratory=explore,
        original_route_sha256=digest(source/'route.json'),assessment=source_receipt['assessment'],frame_budget=period,max_busy_cycles=max(busy),
        min_margin_cycles=period-max(busy),max_native_cycles=max(source_cycles),pixel_errors=0,emulator_sha256=emulator_sha,
        profile_sha256=hashlib.sha256(profile).hexdigest(),scope='Actual paced ROM cold boot and real keyboard inputs; every logical CPU/RAM state and completed visible frame checked. Trailing unfinished frame excluded; no source/contact injections. Manual/physical acceptance separate.',
        artifacts={str(path.relative_to(out)):digest(path) for path in out.rglob('*') if path.is_file()})
    (out/'verified.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--build-dir',type=Path,default=OUT)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--family',choices=('ntsc','pal'),default='ntsc');parser.add_argument('--explore',action='store_true')
    args=parser.parse_args();r=capture(args.out,args.build_dir,args.source,args.family,args.explore)
    print(json.dumps({key:r[key] for key in ('source_steps','frames','max_busy_cycles','frame_budget','min_margin_cycles','pixel_errors')}))
