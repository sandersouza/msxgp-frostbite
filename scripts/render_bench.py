"""Independent original-free renderer validation and bounded openMSX capture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import struct
import zlib
import xml.etree.ElementTree as ET

from render_build import ROOT,OUT,ROM,validate_identity,symbols
import render_model as model
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

PACED_MODES=tuple((family if layout==width==0 else f'{family}_layout{layout}_width{width}',family,layout,width,False)
    for family in ('ntsc','pal') for layout in (0,1) for width in (0,1)) + (
    ('ntsc_transitions','ntsc',0,0,True),('pal_transitions','pal',0,0,True))

def validate_observations(result,expected_cases,rom_hash):
    if (result.get('complete') is not True or result.get('cases')!=expected_cases
        or result.get('min_spacing',0)<29 or result.get('pixel_errors')!=0
        or result.get('max_sprites_per_line',99)>4 or result.get('rom_sha256')!=rom_hash
        or not 0<result.get('max_busy_cycles',0)<result.get('frame_budget',0)):
        raise ValueError('incomplete/incorrect/unsafe renderer observation')


def validate_source_files(metadata,root=ROOT):
    if not isinstance(metadata.get('source_files'),dict) or not metadata['source_files']:
        raise ValueError('build source fingerprints required')
    for path,digest in metadata['source_files'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'build source changed since compilation: {path}')


def validate_paced(result,period,layout=0,width=0,transitions=False):
    if result.get('complete') is not True or result.get('cases')!=240:raise ValueError('240 paced frames required')
    frames=result['frames'];busy=result['busy_cycles'];commits=result['commit_cycles']
    if len(frames)!=240 or any(b-a!=1 for a,b in zip(frames,frames[1:])):raise ValueError('skipped/repeated VDP frames')
    if len(busy)!=240 or any(type(v) is not int or not 0<v<period for v in busy) or max(busy)!=result['max_busy_cycles']:
        raise ValueError('paced work exceeded presentation budget')
    if len(commits)!=240 or any(not 0<v<4000 for v in commits):raise ValueError('missing/oversized commit')
    for field in ('commit_start_y','commit_y'):
        if len(result[field])!=240 or any(0<=y<192 for y in result[field]):raise ValueError('commit outside VBlank')
    if len(result['period_cycles'])!=240 or any(abs(value-period)>40 for value in result['period_cycles']):
        raise ValueError('wrong presentation cadence')
    total=0;expected=[]
    for count in model.schedule(240,period):total+=count;expected.append(total)
    if result['step_counts']!=expected or result['pal_flag']!=int(period==71364):raise ValueError('lost/wrongly paced source reservations')
    if not total<=len(result['surrogate_cycles'])<=total+2 or any(value!=10018 for value in result['surrogate_cycles']):
        raise ValueError('unmeasured source-step reservation')
    if type(result.get('max_sprites_per_line')) is not int or not 0<result['max_sprites_per_line']<=4:
        raise ValueError('actual SAT occupancy missing/overloaded')
    expected_modes=[3 if (index//4)%2==0 else 0 for index in range(240)] if transitions else [2*layout+width]*240
    if result.get('mode_samples')!=expected_modes:raise ValueError('paced layout/width/transition was not exercised')


def validate_controls(result):
    expected=['right','left','space-edge','space-held','space-repress']
    if (result.get('complete') is not True or result.get('cases')!=1 or result.get('control_checks')!=expected
            or result.get('max_sprites_per_line',99)>4 or result.get('min_spacing',0)<29):
        raise ValueError('actual renderer controls incomplete/incorrect')


def write_preview(directory):
    pixels=model.decode_pixels((directory/'final-vram.bin').read_bytes(),list((directory/'final-regs.bin').read_bytes()))
    palette=((0,0,0),(0,0,0),(62,184,73),(116,208,125),(89,85,224),(128,118,241),
             (185,94,81),(101,219,239),(219,101,89),(255,137,125),(204,195,94),(222,208,135),
             (58,162,65),(183,102,181),(204,204,204),(255,255,255))
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    rows=b''.join(b'\0'+b''.join(bytes(palette[index]) for index in pixels[y*256:(y+1)*256]) for y in range(192))
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',256,192,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
    (directory/'preview.png').write_bytes(data)
    return {'path':str((directory/'preview.png').relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),
            'method':'Reconstructed from actual emulated VRAM/register dump; approximate RGB palette, not framebuffer capture'}


def cases():
    result=[]
    for layout in (0,1):
        for width in (0,1):
            for x in range(160):
                s=model.scene(x);s.update(layout=layout,width=width,
                    player_y=(48,80,95,119,127,158,175,191)[x%8])
                s['bear_y']=s['player_y'];result.append(s)
    for count in (0,1,2):
        s=model.scene(64);s['counts']=[count]*4;result.append(s)
    return result


def visible_signature(vram,regs):
    names=vram[(regs[2]&15)*1024:(regs[2]&15)*1024+768];data=bytearray(names)
    for index,tile in enumerate(names):
        start=(index//256)*2048+tile*8
        data+=vram[start:start+8]+vram[8192+start:8192+start+8]
    data+=vram[0x1B00:0x1B80]+vram[0x3800:0x4000]+bytes(regs)
    return hashlib.sha256(data).hexdigest()


def execute_capture(mode='rpc',family='ntsc',selected=None,screenshot=False,inject='none',layout=0,width=0,transitions=False):
    if type(layout) is not int or layout not in (0,1) or type(width) is not int or width not in (0,1) or type(transitions) is not bool:
        raise ValueError('explicit bounded paced mode required')
    data=ROM.read_bytes();metadata=json.loads((OUT/'build.json').read_text());validate_identity(data,metadata)
    validate_source_files(metadata)
    selected=cases() if selected is None else selected
    emulator=shutil.which('openmsx')
    if not emulator:raise ValueError('openMSX unavailable')
    emulator_hash=hashlib.sha256(Path(emulator).resolve().read_bytes()).hexdigest()
    profile=find_machine_profile(emulator);effective=ET.fromstring(isolated_profile(profile))
    effective.find('.//VDP/version').text='TMS9918A' if family=='ntsc' else 'TMS9929A'
    profile_data=b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">'+ET.tostring(effective)
    validate_machine_profile(profile_data)
    directory=Path(tempfile.mkdtemp(prefix=f'{mode}-{family}-',dir=OUT))
    user=directory/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/Frostbite_Renderer.xml').write_bytes(profile_data)
    settings=directory/'settings.xml'
    settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    (directory/'cases.bin').write_bytes(b''.join(model.encode_scene(scene) for scene in selected))
    syms=symbols(OUT/'render.sym')
    needed=('rpc_start','rpc_done','prepared_marker','paced_frame_start','paced_wait','paced_commit',
            'commit_begin','commit_end','status_sample','surrogate_call','surrogate_return')
    launcher=directory/'launch.tcl'
    launcher.write_text(f'set bench_dir {{{directory}}}\nset bench_mode {mode}\nset capture_image {int(screenshot)}\nset inject_fault {inject}\n'
        +f'set initial_layout {layout}\nset initial_width {width}\nset transition_mode {int(transitions)}\n'
        +'array set symbols {'+' '.join(f'{name} {syms[name]}' for name in needed)+'}\n'
        +f'source {{{ROOT/"scripts/render_bench.tcl"}}}\n')
    env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_AUDIODRIVER':'dummy'}
    if not screenshot:env['SDL_VIDEODRIVER']='dummy'
    else:env.pop('SDL_VIDEODRIVER',None)
    helper_paths=('scripts/render_bench.py','scripts/render_bench.tcl','scripts/render_controls.tcl',
                  'scripts/render_model.py','scripts/render_build.py','scripts/smoke.py','scripts/rom.py',
                  'scripts/environment.py','references/renderer-contract.json','references/tools-lock.json')
    tool_hashes={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in helper_paths}
    tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    tool_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    command=[emulator,'-setting',str(settings),'-machine','Frostbite_Renderer','-cart',str(ROM),'-romtype','Normal','-script',str(launcher)]
    try:result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=60 if screenshot else 120)
    except subprocess.TimeoutExpired as error:
        fragments=[value.decode(errors='replace') if isinstance(value,bytes) else (value or '') for value in (error.stdout,error.stderr)]
        (directory/'emulator.log').write_text('Host watchdog expired; no acceptance.\n'+''.join(fragments))
        raise ValueError(f'bounded renderer host watchdog expired; see {directory}/emulator.log') from error
    (directory/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode or not (directory/'complete.json').is_file():
        detail=(result.stdout+result.stderr).strip().splitlines()
        raise ValueError(f'fresh renderer capture failed: {detail[-1] if detail else "no result"}; see {directory}/emulator.log')
    if ROM.read_bytes()!=data:raise ValueError('ROM changed during capture')
    if hashlib.sha256(Path(emulator).resolve().read_bytes()).hexdigest()!=emulator_hash:
        raise ValueError('emulator binary changed during capture')
    validate_source_files(metadata)
    for name,digest in tool_hashes.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('harness changed during capture')
    observation=json.loads((directory/'complete.json').read_text())
    expected_cases=len(selected) if mode=='rpc' else 1 if mode=='controls' else 240
    if observation.get('complete') is not True or observation.get('cases')!=expected_cases:
        raise ValueError('incomplete fresh capture count')
    observation.update({'rom_sha256':metadata['rom']['sha256'],'directory':str(directory.relative_to(ROOT)),
        'build_source_commit':metadata['source_commit'],'build_source_dirty':metadata['source_dirty'],
        'harness_source_commit':tool_commit,'harness_source_dirty':tool_dirty,
        'harness_hashes':tool_hashes,'emulator':subprocess.check_output([emulator,'-v'],text=True).splitlines()[0],
        'emulator_sha256':emulator_hash,
        'profile_sha256':hashlib.sha256(profile_data).hexdigest(),'family':family})
    if mode=='rpc':
        dumps=(directory/'vram.bin').read_bytes();prepared=(directory/'prepared.bin').read_bytes()
        previous=(directory/'baseline.bin').read_bytes();regs_data=(directory/'regs.bin').read_bytes()
        before_regs=(directory/'prepared-regs.bin').read_bytes();cycles=[int(value) for value in (directory/'cycles.txt').read_text().splitlines()]
        if len(dumps)!=len(selected)*16384 or len(prepared)!=len(dumps) or len(cycles)!=len(selected):
            raise ValueError('missing/truncated renderer checkpoints')
        errors=0;peak=0
        for index,scene in enumerate(selected):
            vr=dumps[index*16384:(index+1)*16384];pre=prepared[index*16384:(index+1)*16384]
            regs=list(regs_data[index*8:(index+1)*8]);pre_regs=list(before_regs[index*8:(index+1)*8])
            if visible_signature(pre,pre_regs)!=visible_signature(previous,pre_regs):
                raise ValueError(f'visible preparation changed at case{index}')
            expected=model.expected_pixels(scene);actual=model.decode_pixels(vr,regs)
            if actual!=expected:
                mismatch=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
                raise ValueError(f'pixel mismatch case{index} at{mismatch%256},{mismatch//256}: actual{actual[mismatch]} expected{expected[mismatch]}; {directory}')
            if vr[0x1B00:0x1B21]!=model.sprite_attributes(scene):raise ValueError(f'SAT mismatch case{index}')
            if vr[0x3800:0x4000]!=model.sprite_patterns():raise ValueError('sprite pattern data changed')
            peak=max(peak,max(model.occupancy(vr[0x1B00:0x1B21])))
            previous=vr
        if observation['max_sprites_per_line']!=peak:raise ValueError('SAT occupancy evidence differs')
        if observation['data_writes']!=sum(929+64*scene['layout'] for scene in selected):raise ValueError('unexpected renderer write count')
        observation.update(pixel_errors=errors,max_busy_cycles=max(cycles),frame_budget=59736)
        validate_observations(observation,len(selected),metadata['rom']['sha256'])
        observation['worst_case']=cycles.index(max(cycles))
    elif mode=='pace':
        period=59736 if family=='ntsc' else 71364
        validate_paced(observation,period,layout,width,transitions)
        if observation['min_spacing']<29:raise ValueError('unsafe paced IO spacing')
        observation.update(frame_budget=period)
    else:validate_controls(observation)
    if inject!='none':raise ValueError('negative fault escaped detection')
    (directory/'verified.json').write_text(json.dumps(observation,indent=2)+'\n')
    return observation


def negative_controls():
    expectations={'pixel':('pixel mismatch',),'sprite':('pixel mismatch','SAT mismatch'),
                  'overflow':('SAT occupancy exceeds four',),'guard':('RAM guard changed',),
                  'spacing':('VRAM spacing','VDP rejected fast VRAM')}
    results={}
    for fault,reasons in expectations.items():
        try:execute_capture(selected=cases()[:1],inject=fault)
        except ValueError as error:
            if not any(reason in str(error) for reason in reasons):raise ValueError(f'negative {fault} failed for wrong reason: {error}') from error
            results[fault]=True
        else:raise ValueError(f'negative {fault} escaped')
    return results


def run_suite(screenshot=False,preview=False):
    result={'schema_version':1,'rpc':execute_capture()}
    for name,family,layout,width,transitions in PACED_MODES:
        result[name]=execute_capture('pace',family,layout=layout,width=width,transitions=transitions,
                                     screenshot=screenshot and name=='ntsc')
    result.update(controls=execute_capture('controls'),negative_controls=negative_controls())
    hashes={result[name]['rom_sha256'] for name in ('rpc','controls',*(mode[0] for mode in PACED_MODES))}
    if len(hashes)!=1:raise ValueError('suite ROM identity differs')
    if preview:result['preview']=write_preview(ROOT/result['ntsc']['directory'])
    (OUT/'suite.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--limit',type=int)
    parser.add_argument('--suite',action='store_true')
    parser.add_argument('--mode',choices=('rpc','pace','controls'),default='rpc');parser.add_argument('--family',choices=('ntsc','pal'),default='ntsc')
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--layout',type=int,choices=(0,1),default=0);parser.add_argument('--width',type=int,choices=(0,1),default=0)
    parser.add_argument('--transitions',action='store_true')
    parser.add_argument('--screenshot',action='store_true')
    parser.add_argument('--inject',choices=('none','pixel','sprite','overflow','guard','spacing'),default='none');args=parser.parse_args()
    try:
        if args.suite:
            result=run_suite(args.screenshot,args.preview)
            print('Full renderer suite passed:643pixel cases,10x240paced mode/transition frames, controls and five negative faults.')
            print(f'Exact ROM {result["rpc"]["rom_sha256"]}; evidence {OUT/"suite.json"}')
        else:
            selected=cases()[:args.limit] if args.limit else None
            result=execute_capture(args.mode,args.family,selected,args.screenshot,args.inject,args.layout,args.width,args.transitions)
            print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,KeyError,ET.ParseError,subprocess.SubprocessError) as error:
        print(f'Render benchmark failed: {error}',file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
