"""Actual native/input/mapper/render workload, never a surrogate reservation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from functools import lru_cache

from floe_build import ROOT,OUT,ROM,FILES,VERSION,expected_pixels,presentation
from floe_query import RawContacts
from floe_reference import visible_reference
from floe_model import visible_state
from native_contract import HELPERS,reference,compare
from native_input_check import hardware as sign_hardware
from reference_provenance import snapshot_paths,audit_manifest
from reference_inventory import verified_input
from render_bench import visible_signature,PACED_MODES,validate_source_files
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile
import render_model as model


def digest_catalog(reader):
    return hashlib.sha256((reader.directory/'catalog.json').read_bytes()).hexdigest()


def hardware(keys,player):
    ports,console,f1,f2=sign_hardware(keys,player)
    return ports,console,f1|12,f2|12


def decode_scene(data):
    if len(data)!=32:raise ValueError('complete presentation ABI required')
    result={name:list(data[i*4:i*4+4]) for i,name in enumerate(('floes','threats','colors','kinds','counts','spacing'))}
    result.update(zip(('player_x','player_y','bear_x','bear_y','palette','igloo','width','layout'),data[24:]));model.encode_scene(result)
    return result


@lru_cache(maxsize=2048)
def expected_image(data):return bytes(expected_pixels(decode_scene(data)))


def validate_receipt(report,period,layout,width,transitions):
    if report.get('complete') is not True or report.get('cases')!=240:raise ValueError('240 completed movement frames required')
    frames=report['frames']
    if len(frames)!=240 or any(b-a!=1 for a,b in zip(frames,frames[1:])):raise ValueError('skipped/repeated VDP frames')
    if len(report['busy_cycles'])!=240 or any(type(c) is not int or not 0<c<period for c in report['busy_cycles']):raise ValueError('actual native workload exceeded frame budget')
    for key in ('commit_y','commit_end_y'):
        if len(report[key])!=240 or any(0<=y<192 for y in report[key]):raise ValueError('commit outside VBlank')
    if len(report['commit_cycles'])!=240 or any(not 0<c<4000 for c in report['commit_cycles']):raise ValueError('unsafe/missing commit')
    if len(report['period_cycles'])!=240 or any(abs(c-period)>40 for c in report['period_cycles']):raise ValueError('wrong presentation cadence')
    total=0;steps=[]
    for n in model.schedule(240,period):total+=n;steps.append(total)
    if report['step_counts']!=steps or report['source_steps']!=sum(model.schedule(241,period)) or report['pal_flag']!=int(period==71364):
        raise ValueError('missing/wrongly paced real source steps')
    if len(report['source_cycles'])!=report['source_steps'] or any(not 0<c<period for c in report['source_cycles']):raise ValueError('unmeasured native steps')
    initial_mode=layout*2+width
    modes=[initial_mode^3 if (i//4)%2==0 else initial_mode for i in range(240)] if transitions else [initial_mode]*240
    if report['mode_samples']!=modes:raise ValueError('requested layout/width/transitions not exercised')
    if report['min_spacing']<29 or not 0<report['max_sprites_per_line']<=4 or not 0xF340<=report['stack_min']<=0xF380:
        raise ValueError('unsafe VRAM/SAT/stack observation')


def verify_data(directory,report,reader,original):
    directory=Path(directory)
    records=(directory/'states.bin').read_bytes()
    if len(records)!=report['source_steps']*404:raise ValueError('truncated native source-step records')
    previous=None
    for index in range(report['source_steps']):
        row=records[index*404:(index+1)*404]
        def phase(offset):
            return {'registers':dict(zip(('a','x','y','p','sp'),row[offset:offset+5])),'ram':list(row[offset+5:offset+133])}
        initial=phase(0);before=phase(133);after=phase(266)
        contacts=reader.contacts(initial['ram'])
        expected_visible=visible_reference(original,initial['ram'],initial['registers'],contacts)
        compare(expected_visible,visible_state(original,initial['ram'],initial['registers'],contacts))
        try:compare(expected_visible,before)
        except ValueError as error:raise ValueError(f'visible step{index}: {error}; {directory}') from error
        ports,console,f1,f2=hardware((0,row[399],0,0),before['ram'][0xC7-128])
        if tuple(row[400:404])!=(ports,console,f1,f2):raise ValueError(f'stale input at native step{index}')
        case={'id':f'integrated-{index}','start':'F476','stops':['F019'],'registers':before['registers'],
            'ram':{f'{i+128:02X}':f'{v:02X}' for i,v in enumerate(before['ram'])},'limit':10000,
            'mmio':{'0280':f'{ports:02X}','0282':f'{console:02X}','0284':'00','000C':f'{f1:02X}','000D':f'{f2:02X}'}}
        try:compare(reference(original,case),after)
        except ValueError as error:raise ValueError(f'native step{index}: {error}; {directory}') from error
        if previous is not None:compare(previous,initial)
        previous=after
    adapters=(directory/'adapters.bin').read_bytes();scenes=(directory/'scene_actual.bin').read_bytes()
    if len(adapters)!=241*160 or len(scenes)!=241*32:raise ValueError('truncated scene/adapter evidence')
    for index in range(241):
        row=adapters[index*160:(index+1)*160];actual=row[128:]
        if model.encode_scene(presentation(row[:128],actual[31],actual[30]))!=actual:raise ValueError('source-to-presentation adapter changed coordinates')
    chunks={name:(directory/(name+'.bin')).read_bytes() for name in ('before_vram','before_regs','prepared','prepared_regs','presented','presented_regs')}
    for name,blob in chunks.items():
        count=240 if name.startswith('presented') else 241;size=8 if name.endswith('regs') else 16384
        if len(blob)!=count*size:raise ValueError(f'truncated visual observation {name}')
    peak=0
    for index in range(241):
        before=chunks['before_vram'][index*16384:(index+1)*16384];prepared=chunks['prepared'][index*16384:(index+1)*16384]
        before_regs=list(chunks['before_regs'][index*8:index*8+8]);prepared_regs=list(chunks['prepared_regs'][index*8:index*8+8])
        if visible_signature(before,before_regs)!=visible_signature(prepared,prepared_regs):raise ValueError(f'visible frame changed during preparation {index}')
        if index==240:continue
        vram=chunks['presented'][index*16384:(index+1)*16384];regs=list(chunks['presented_regs'][index*8:index*8+8]);scene=scenes[index*32:index*32+32]
        pixels=bytes(model.decode_pixels(vram,regs));wanted=expected_image(scene)
        if pixels!=wanted:
            at=next(i for i,(a,b) in enumerate(zip(pixels,wanted)) if a!=b)
            raise ValueError(f'pixel mismatch frame{index} at{at%256},{at//256}: actual{pixels[at]} expected{wanted[at]}; {directory}')
        decoded=decode_scene(scene)
        if vram[0x1B00:0x1B21]!=model.sprite_attributes(decoded) or vram[0x3800:0x4000]!=model.sprite_patterns():raise ValueError('SAT/sprite pattern mismatch')
        peak=max(peak,max(model.occupancy(vram[0x1B00:0x1B21])))
    if peak!=report['max_sprites_per_line']:raise ValueError('SAT occupancy receipt differs from dumps')


def capture(family='ntsc',layout=0,width=0,transitions=False,explore=False,inject='none',catalog='dense',source_catalog=None,
            source_reader=None,source_identity=None,initial_override=None,additional_helpers=()):
    if family not in ('ntsc','pal') or type(layout) is not int or layout not in (0,1) or type(width) is not int or width not in (0,1) or type(transitions) is not bool:
        raise ValueError('explicit bounded movement mode required')
    data=ROM.read_bytes();metadata=json.loads((OUT/'build.json').read_text())
    if data[16:20]!=b'FBF0' or hashlib.sha256(data).hexdigest()!=metadata['rom']['sha256']:raise ValueError('movement build identity mismatch')
    validate_source_files(metadata)
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    if not explore and (dirty or metadata['source_dirty']):raise ValueError('canonical movement capture requires clean committed producers; use --explore for WIP')
    helpers=tuple(dict.fromkeys((*HELPERS,*FILES,'scripts/floe_bench.py','scripts/floe_bench.tcl','scripts/floe_query.py','scripts/floe_reference.py','scripts/floe_model.py','scripts/floe_catalog.py','scripts/stella_floe.py','scripts/floe_truth.py','scripts/render_bench.py','references/native-contract.json',*additional_helpers)))
    producer=snapshot_paths(helpers) if not explore else {'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'utility_fingerprints':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in helpers}}
    if not explore:audit_manifest({'tool_source_commit':metadata['source_commit'],'utility_fingerprints':metadata['source_files']},FILES)
    if verified_input(ROOT/'references/roms/frostbite.bin')!=metadata['original']:raise ValueError('original identity changed since build')
    directory=Path(tempfile.mkdtemp(prefix=f'pace-{family}-',dir=OUT));syms=symbols(OUT/'floes.sym')
    (directory/ROM.name).write_bytes(data);(directory/'build.json').write_text(json.dumps(metadata,indent=2)+'\n')
    original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    initial=reference(original,{'id':'init','start':'FB3B','stops':['FB94'],'registers':{},'ram':{'80':'03','82':'01','81':'FC','C5':'00'}})
    if initial_override is not None:initial=initial_override(initial)
    regs=initial['registers'];p=regs['p'];af=regs['a']*256+(p&128)+(64 if p&2 else 0)
    (directory/'initial.bin').write_bytes(bytes(initial['ram'])+struct.pack('<HHBBBB',af,regs['x']*256+regs['y'],p&1,p&64,p&0x3C,regs['sp']))
    selected=[{**model.scene(i%160),'player_y':(48,80,95,119,127,158,175,191)[i%8],
        'bear_y':(48,80,95,119,127,158,175,191)[i%8]} for i in range(244)]
    if catalog=='counts':
        for i,count in enumerate((3,0,0,0,1,0,0,2,0,0,3,0)):
            selected[i]={**model.scene(64),'counts':[count]*4}
    elif catalog!='dense':raise ValueError('unknown scene catalog')
    (directory/'scenes.bin').write_bytes(b''.join(model.encode_scene(s) for s in selected))
    emulator=shutil.which('openmsx');effective=ET.fromstring(isolated_profile(find_machine_profile(emulator)))
    emulator_hash=hashlib.sha256(Path(emulator).resolve().read_bytes()).hexdigest()
    effective.find('.//VDP/version').text='TMS9918A' if family=='ntsc' else 'TMS9929A'
    profile=b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">'+ET.tostring(effective);validate_machine_profile(profile)
    user=directory/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Movement.xml').write_bytes(profile)
    settings=directory/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    names=('start','map_page2','detect_period','native_reset','adapt_scene','paced_frame_start','paced_wait','paced_commit','commit_end','status_sample','native_step','native_call','native_return','adapt_done','prepare','prepared_marker')
    launcher=directory/'launch.tcl';launcher.write_text(f'set bench_dir {{{directory}}}\nset initial_layout {layout}\nset initial_width {width}\nset transitions {int(transitions)}\nset inject_fault {inject}\n'
        +'array set symbols {'+' '.join(f'{name} {syms[name]}' for name in names)+'}\n'+f'source {{{ROOT/"scripts/floe_bench.tcl"}}}\n')
    result=subprocess.run([emulator,'-setting',str(settings),'-machine','Frostbite_Movement','-cart',str(ROM),'-romtype','ASCII16','-script',str(launcher)],
        cwd=ROOT,env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,errors='replace',timeout=120)
    (directory/'emulator.log').write_text(result.stdout+result.stderr)
    if result.returncode or not (directory/'complete.json').is_file():raise ValueError(f'movement capture incomplete {directory}: '+(result.stdout+result.stderr)[-500:])
    if ROM.read_bytes()!=data or verified_input(ROOT/'references/roms/frostbite.bin')!=metadata['original']:raise ValueError('source/binary changed during capture')
    validate_source_files(metadata)
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in producer['utility_fingerprints'].items()):raise ValueError('movement helper changed during capture')
    if not explore and snapshot_paths(helpers)!=producer:raise ValueError('movement producer changed during capture')
    if hashlib.sha256(Path(emulator).resolve().read_bytes()).hexdigest()!=emulator_hash:raise ValueError('emulator changed during capture')
    report=json.loads((directory/'complete.json').read_text());report['directory']=str(directory.relative_to(ROOT));report['rom_sha256']=metadata['rom']['sha256']
    reader=RawContacts(source_catalog) if source_reader is None else source_reader
    if source_reader is None:
        if digest_catalog(reader)!=metadata['tables']['catalog_sha256']:raise ValueError('timing source catalog differs from build')
    elif source_identity is None:raise ValueError('explicit source-reader build binding required')
    else:source_identity(reader,metadata)
    verify_data(directory,report,reader,original)
    period=59736 if family=='ntsc' else 71364
    print(json.dumps({'directory':report['directory'],'max_busy_cycles':max(report['busy_cycles']),'frame_budget':period,'frames':report['frames'][:4]},indent=2))
    validate_receipt(report,period,layout,width,transitions)
    if inject!='none':raise ValueError('negative fault escaped detection')
    report.update(**producer,build_source_commit=metadata['source_commit'],build_dirty=metadata['source_dirty'],harness_dirty=dirty,
        emulator_sha256=emulator_hash,profile_sha256=hashlib.sha256(profile).hexdigest(),family=family,layout=layout,width=width,transitions=transitions,catalog=catalog,
        max_busy_cycles=max(report['busy_cycles']),frame_budget=period,pixel_errors=0,
        artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()},
        scope='Automated complete native visible+post-visible/input/mapper/render proof with original-clock floes; seeded benchmark and synthetic presentation. Full hazard/shore acquisition, natural-route and manual/physical acceptance are separate.')
    if source_reader is not None:reader.verify_consumed()
    (directory/'verified.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def negative_controls(explore=False,source_catalog=None):
    expected={'spacing':'fast-io-spacing','sprite':'fifth-sprite-slot','guard':'heap-guard','state':'RAM','pixel':'pixel mismatch','contact':'visible step0: RAM B6','cache':'pixel mismatch'}
    artifact=ROM.read_bytes();digest=hashlib.sha256(artifact).hexdigest();result={}
    metadata=json.loads((OUT/'build.json').read_text())
    paths=tuple(dict.fromkeys((*HELPERS,*FILES,'scripts/floe_bench.py','scripts/floe_bench.tcl','scripts/floe_query.py','scripts/floe_reference.py','scripts/floe_model.py','scripts/floe_catalog.py','scripts/stella_floe.py','scripts/floe_truth.py','scripts/render_bench.py','references/native-contract.json')))
    snapshot=snapshot_paths(paths) if not explore else {'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'utility_fingerprints':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}}
    for fault,needle in expected.items():
        before=set(OUT.glob('pace-ntsc-*'))
        try:capture(explore=explore,inject=fault,source_catalog=source_catalog,catalog='counts' if fault=='cache' else 'dense')
        except ValueError as error:
            if needle not in str(error):raise ValueError(f'{fault}: wrong failure: {error}') from error
            created=set(OUT.glob('pace-ntsc-*'))-before
            if len(created)!=1:raise ValueError('negative capture directory is ambiguous')
            result[fault]={'detected':True,'detail':str(error),'rom_sha256':digest,'build_source_commit':metadata['source_commit'],
                'harness_dirty':explore,'producer':snapshot,'directory':str(created.pop().relative_to(ROOT))}
        else:raise ValueError(f'{fault}: negative fault escaped')
    if ROM.read_bytes()!=artifact or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in snapshot['utility_fingerprints'].items()):
        raise ValueError('negative-control binary/helper changed')
    if not explore and snapshot_paths(paths)!=snapshot:raise ValueError('negative-control producer changed')
    (OUT/'negative-controls.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--family',choices=('ntsc','pal'),default='ntsc')
    parser.add_argument('--layout',type=int,choices=(0,1),default=0);parser.add_argument('--width',type=int,choices=(0,1),default=0)
    parser.add_argument('--transitions',action='store_true');parser.add_argument('--explore',action='store_true');parser.add_argument('--suite',action='store_true')
    parser.add_argument('--negatives',action='store_true');parser.add_argument('--source-catalog',type=Path,required=True)
    parser.add_argument('--build-dir',type=Path,default=OUT)
    parser.add_argument('--inject',choices=('none','state','pixel','spacing','guard','sprite','contact','cache'),default='none');args=parser.parse_args()
    OUT=args.build_dir.resolve();ROM=OUT/f'frostbite-{VERSION}.rom'
    if args.suite:
        reports={name:capture(family,layout,width,transitions,args.explore,source_catalog=args.source_catalog) for name,family,layout,width,transitions in PACED_MODES}
        reports['ntsc_transitions_inverted']=capture('ntsc',1,1,True,args.explore,source_catalog=args.source_catalog)
        reports['pal_transitions_inverted']=capture('pal',1,1,True,args.explore,source_catalog=args.source_catalog)
        reports['counts']=capture(explore=args.explore,catalog='counts',source_catalog=args.source_catalog)
        reports['negative_controls']=negative_controls(args.explore,args.source_catalog)
        (OUT/'suite.json').write_text(json.dumps(reports,indent=2)+'\n')
    elif args.negatives:negative_controls(args.explore,args.source_catalog)
    else:capture(args.family,args.layout,args.width,args.transitions,args.explore,args.inject,source_catalog=args.source_catalog)
