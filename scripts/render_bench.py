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
import xml.etree.ElementTree as ET

from render_build import ROOT,OUT,ROM,validate_identity,symbols
import render_model as model
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

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


def validate_paced(result,period):
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


def execute_capture(mode='rpc',family='ntsc',selected=None,screenshot=False,inject='none'):
    data=ROM.read_bytes();metadata=json.loads((OUT/'build.json').read_text());validate_identity(data,metadata)
    validate_source_files(metadata)
    selected=cases() if selected is None else selected
    emulator=shutil.which('openmsx')
    if not emulator:raise ValueError('openMSX unavailable')
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
        +'array set symbols {'+' '.join(f'{name} {syms[name]}' for name in needed)+'}\n'
        +f'source {{{ROOT/"scripts/render_bench.tcl"}}}\n')
    env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_AUDIODRIVER':'dummy'}
    if not screenshot:env['SDL_VIDEODRIVER']='dummy'
    else:env.pop('SDL_VIDEODRIVER',None)
    tool_hashes={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__),ROOT/'scripts/render_bench.tcl',ROOT/'scripts/render_model.py')}
    command=[emulator,'-setting',str(settings),'-machine','Frostbite_Renderer','-cart',str(ROM),'-romtype','Normal','-script',str(launcher)]
    result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
    (directory/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode or not (directory/'complete.json').is_file():
        detail=(result.stdout+result.stderr).strip().splitlines()
        raise ValueError(f'fresh renderer capture failed: {detail[-1] if detail else "no result"}; see {directory}/emulator.log')
    if ROM.read_bytes()!=data:raise ValueError('ROM changed during capture')
    validate_source_files(metadata)
    for name,digest in tool_hashes.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('harness changed during capture')
    observation=json.loads((directory/'complete.json').read_text())
    if observation.get('complete') is not True or observation.get('cases')!=(len(selected) if mode=='rpc' else 240):
        raise ValueError('incomplete fresh capture count')
    observation.update({'rom_sha256':metadata['rom']['sha256'],'directory':str(directory.relative_to(ROOT)),
        'build_source_commit':metadata['source_commit'],'build_source_dirty':metadata['source_dirty'],
        'harness_hashes':tool_hashes,'emulator':subprocess.check_output([emulator,'-v'],text=True).splitlines()[0],
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
        if observation['data_writes']!=len(selected)*929:raise ValueError('unexpected renderer write count')
        observation.update(pixel_errors=errors,max_busy_cycles=max(cycles),frame_budget=59736)
        validate_observations(observation,len(selected),metadata['rom']['sha256'])
        observation['worst_case']=cycles.index(max(cycles))
    else:
        period=59736 if family=='ntsc' else 71364
        validate_paced(observation,period)
        if observation['min_spacing']<29:raise ValueError('unsafe paced IO spacing')
        observation.update(frame_budget=period)
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


def run_suite(screenshot=False):
    result={'schema_version':1,'rpc':execute_capture(),
            'ntsc':execute_capture('pace','ntsc',screenshot=screenshot),
            'pal':execute_capture('pace','pal'), 'negative_controls':negative_controls()}
    hashes={result[name]['rom_sha256'] for name in ('rpc','ntsc','pal')}
    if len(hashes)!=1:raise ValueError('suite ROM identity differs')
    (OUT/'suite.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--limit',type=int)
    parser.add_argument('--suite',action='store_true')
    parser.add_argument('--mode',choices=('rpc','pace'),default='rpc');parser.add_argument('--family',choices=('ntsc','pal'),default='ntsc')
    parser.add_argument('--screenshot',action='store_true')
    parser.add_argument('--inject',choices=('none','pixel','sprite','overflow','guard','spacing'),default='none');args=parser.parse_args()
    try:
        if args.suite:
            result=run_suite(args.screenshot)
            print('Full renderer suite passed:643pixel cases,240NTSC/240PAL frames and five negative controls.')
            print(f'Exact ROM {result["rpc"]["rom_sha256"]}; evidence {OUT/"suite.json"}')
        else:
            selected=cases()[:args.limit] if args.limit else None
            result=execute_capture(args.mode,args.family,selected,args.screenshot,args.inject)
            print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,KeyError,ET.ParseError,subprocess.SubprocessError) as error:
        print(f'Render benchmark failed: {error}',file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
