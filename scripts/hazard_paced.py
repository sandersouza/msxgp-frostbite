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
from hazard_build import OUT,FILES,expected_pixels,presentation
from floe_bench import decode_scene
from hazard_check import HELPERS as NATIVE_HELPERS
from hazard_routes import HELPERS as SOURCE_HELPERS,assess,validate_policy
from hazard_play import input_records
from native_contract import compare
from reference_provenance import snapshot_paths,audit_manifest
from reference_traces import private_output
from render_bench import validate_source_files,visible_signature
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile
from stella_floe import digest
from trace_compare import validate_trace
import render_model as model

FRAME_BYTES=49364
HELPERS=tuple(dict.fromkeys((*NATIVE_HELPERS,*SOURCE_HELPERS,'scripts/hazard_play.py','scripts/hazard_paced.py',
                           'scripts/hazard_paced.tcl','scripts/floe_bench.py','scripts/render_model.py')))


def validate_report(report,steps,family):
    period={'ntsc':59736,'pal':71364}[family];frames=report.get('frames',0)
    if (report.get('complete') is not True or report.get('source_steps')!=steps or type(frames) is not int or frames<1
            or not 1+sum(model.schedule(frames,period))<=steps<=1+sum(model.schedule(frames+1,period))
            or report.get('canonical_ram_injections')!=0 or report.get('clock_hz')!=3579545 or report.get('ram_bytes')!=65536
            or report.get('min_spacing',0)<29 or not 1<=report.get('max_sprites_per_line',0)<=4
            or report.get('stack_min',0)<0xF340 or report.get('pal_flag')!=int(family=='pal')
            or any(type(report.get(k)) is not int or report[k] not in (0,1) for k in ('layout','width'))):
        raise ValueError('incomplete/unsafe paced named-route evidence')


def assess_receipt(points,receipt):
    return assess(points,receipt['kind'],receipt['preparation_intervals'],receipt['assessment'].get('approach_end'))


def verify_saved(out,source,family,report,*,assessor=assess_receipt,pixels=expected_pixels,scene_builder=presentation):
    out=Path(out);source=Path(source)
    source_receipt=json.loads((source/'route.json').read_text())
    trace=json.loads((source/'trace.json').read_text());inputs=json.loads((source/'inputs.json').read_text())
    states=(out/'states.bin').read_bytes();frames=(out/'frames.bin').read_bytes()
    validate_report(report,len(inputs),family)
    if len(states)!=137*len(inputs) or len(frames)!=FRAME_BYTES*report['frames']:raise ValueError('truncated paced state/frame observations')
    points=[];source_cycles=[]
    for index,want in enumerate(trace['steps']):
        row=states[index*137:(index+1)*137];got={'registers':dict(zip(('a','x','y','p','sp'),row[:5])),'ram':list(row[5:133])}
        expected={'registers':{key:want['cpu'][key] for key in ('a','x','y','p','sp')},'ram':want['ram']}
        try:compare(expected,got)
        except ValueError as error:raise ValueError(f'paced native state{index}: {error}; {out}') from error
        points.append({**got,'index':index});source_cycles.append(struct.unpack('<I',row[133:137])[0])
    if assessor(points,source_receipt)!=source_receipt['assessment']:
        raise ValueError('paced named-route interaction milestones differ')
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
        if (decoded['layout'],decoded['width'])!=(report['layout'],report['width']):raise ValueError('paced named presentation mode differs')
        if model.encode_scene(scene_builder(canonical,decoded['layout'],decoded['width']))!=scene:raise ValueError('natural presentation adaptation differs')
        before=row[188:16572];before_regs=list(row[16572:16580]);prepared=row[16580:32964];prepared_regs=list(row[32964:32972])
        presented=row[32972:49356];presented_regs=list(row[49356:49364])
        if visible_signature(before,before_regs)!=visible_signature(prepared,prepared_regs):raise ValueError('natural preparation changed the visible frame')
        if bytes(model.decode_pixels(presented,presented_regs))!=bytes(pixels(decoded)):raise ValueError(f'natural pixel mismatch frame{index}')
        if presented[0x1B00:0x1B21]!=model.sprite_attributes(decoded) or presented[0x3800:0x4000]!=model.sprite_patterns():raise ValueError('natural SAT/pattern mismatch')
        peak=max(peak,max(model.occupancy(presented[0x1B00:0x1B21])));vdp_frames.append(frame);busy.append(work)
    if any(b-a!=1 for a,b in zip(vdp_frames,vdp_frames[1:])) or peak!=report['max_sprites_per_line']:raise ValueError('natural skipped frames or mismatched sprite receipt')
    return period,busy,source_cycles


def capture(out,build_dir,source,family='ntsc',explore=False,layout=0,width=0,*,
            source_helpers=SOURCE_HELPERS,build_files=FILES,assessor=assess_receipt,
            pixels=expected_pixels,scene_builder=presentation,input_encoder=input_records,additional_helpers=()):
    if family not in ('ntsc','pal') or any(type(v) is not int or v not in (0,1) for v in (layout,width)):
        raise ValueError('explicit NTSC/PAL family and presentation mode required')
    source=Path(source);out=private_output(out);out.mkdir(parents=True,exist_ok=False);build_dir=Path(build_dir)
    source_receipt=json.loads((source/'route.json').read_text())
    audit_manifest(source_receipt,source_helpers)
    if source_receipt.get('clean_start') is not True:raise ValueError('clean original source route required')
    if any(digest(source/name)!=sha for name,sha in source_receipt['files'].items()):raise ValueError('natural original evidence changed')
    trace=json.loads((source/'trace.json').read_text());inputs=json.loads((source/'inputs.json').read_text())
    validate_trace(trace);validate_policy(trace['policy'])
    metadata=json.loads((build_dir/'build.json').read_text());rom=build_dir/metadata['rom']['filename'];artifact=rom.read_bytes()
    if digest(rom)!=metadata['rom']['sha256'] or artifact[16:20]!=b'FBF0':raise ValueError('paced ROM identity mismatch')
    validate_source_files(metadata)
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    if not explore and (dirty or metadata['source_dirty']):raise ValueError('clean committed paced producer required')
    helpers=tuple(dict.fromkeys((*HELPERS,*source_helpers,*build_files,*additional_helpers)))
    producer=snapshot_paths(helpers) if not explore else {'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'utility_fingerprints':{name:digest(ROOT/name) for name in helpers}}
    if not explore:audit_manifest({'tool_source_commit':metadata['source_commit'],'utility_fingerprints':metadata['source_files']},build_files)
    raw_inputs=input_encoder(inputs,trace['steps'])
    (out/'inputs.bin').write_bytes(raw_inputs);(out/rom.name).write_bytes(artifact)
    (out/'build.json').write_text(json.dumps(metadata,indent=2)+'\n')
    emulator=Path(shutil.which('openmsx')).resolve();emulator_sha=digest(emulator)
    effective=ET.fromstring(isolated_profile(find_machine_profile(str(emulator))))
    effective.find('.//VDP/version').text='TMS9918A' if family=='ntsc' else 'TMS9929A'
    profile=b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">'+ET.tostring(effective);validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Paced.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    syms=symbols(build_dir/'floes.sym');names=('native_reset_done','native_step','native_return','paced_frame_start','prepare','paced_wait','paced_commit','commit_end','status_sample')
    launcher=out/'launch.tcl';launcher.write_text(f'set paced_dir {{{out}}}\nset initial_layout {layout}\nset initial_width {width}\narray set symbols {{'+' '.join(f'{name} {syms[name]}' for name in names)+'}\n'+f'source {{{ROOT/"scripts/hazard_paced.tcl"}}}\n')
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Paced','-cart',str(out/rom.name),'-romtype','ASCII16','-script',str(launcher)],
        cwd=ROOT,env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,errors='replace',timeout=120)
    (out/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode or not (out/'complete.json').is_file():raise ValueError(f'paced natural replay incomplete {out}: '+(result.stdout+result.stderr)[-1000:])
    report=json.loads((out/'complete.json').read_text())
    period,busy,source_cycles=verify_saved(out,source,family,report,assessor=assessor,pixels=pixels,scene_builder=scene_builder)
    if digest(emulator)!=emulator_sha or rom.read_bytes()!=artifact:raise ValueError('paced emulator/ROM changed')
    validate_source_files(metadata)
    if any(digest(ROOT/name)!=sha for name,sha in producer['utility_fingerprints'].items()):raise ValueError('paced helper changed during capture')
    if not explore and snapshot_paths(helpers)!=producer:raise ValueError('paced producer revision changed')
    report.update(**producer,family=family,rom=metadata['rom'],build_source_commit=metadata['source_commit'],exploratory=explore,
        original_route_sha256=digest(source/'route.json'),assessment=source_receipt['assessment'],frame_budget=period,max_busy_cycles=max(busy),
        min_margin_cycles=period-max(busy),max_native_cycles=max(source_cycles),pixel_errors=0,emulator_sha256=emulator_sha,
        profile_sha256=hashlib.sha256(profile).hexdigest(),scope='Actual paced ROM cold boot and real keyboard inputs; every logical CPU/RAM state and completed visible frame checked. Trailing unfinished frame excluded; no source/contact injections. Manual/physical acceptance separate.',
        artifacts={str(path.relative_to(out)):digest(path) for path in out.rglob('*') if path.is_file()})
    (out/'verified.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--build-dir',type=Path,default=OUT)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--family',choices=('ntsc','pal'),default='ntsc');parser.add_argument('--explore',action='store_true')
    parser.add_argument('--layout',type=int,choices=(0,1),default=0);parser.add_argument('--width',type=int,choices=(0,1),default=0)
    args=parser.parse_args();r=capture(args.out,args.build_dir,args.source,args.family,args.explore,args.layout,args.width)
    print(json.dumps({key:r[key] for key in ('source_steps','frames','max_busy_cycles','frame_budget','min_margin_cycles','pixel_errors')}))
