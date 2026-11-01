"""Capture, audit and package exact native diagnostic bytes without relabeling."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import re

import movement_build as build_api
from movement_build import ROOT,OUT,ROM,VERSION,FILES,validate_rom
from movement_bench import capture,negative_controls,validate_receipt
from native_contract import HELPERS,run_contract
from native_input_check import run as input_check
from reference_provenance import audit_manifest,snapshot_paths
from render_bench import PACED_MODES
from native_build import OUT as CPU_OUT,BUILD_FILES as CPU_BUILD_FILES
from movement_evidence import (VISUAL_ROOT,VISUAL_PROFILE,CPU_PROFILE,PORT2_DECLARED,FAILURES,
    cpu_files,visual_files,digest_files,audit_files,validate_failure_identity,verify_failure_data)

POSITIVES=tuple(n for n,*_ in PACED_MODES)+('counts',)
CPU_COUNTS={'generic':4497,'phase':1793,'devices_generic':1354,'devices_phase':1354}


def producer_paths(kind):
    inputs=('scripts/device_replay.py','scripts/native_input_check.py','src/native_input.asm')
    if kind=='generic':return HELPERS
    if kind=='devices':return HELPERS+inputs
    if kind=='movement':return tuple(dict.fromkeys((*HELPERS,*FILES,'scripts/movement_bench.py','scripts/movement_bench.tcl','scripts/render_bench.py','references/native-contract.json')))
    if kind=='mutant_build':return CPU_BUILD_FILES+('scripts/native_fast.py','scripts/native_analysis.py','src/native_input.asm')
    raise ValueError('unknown producer scope')


def audit_producer(part,kind):audit_manifest(part,producer_paths(kind))


def encoded(value):return (json.dumps(value,indent=2)+'\n').encode()


def sha(data):return hashlib.sha256(data).hexdigest()


def require(value,message):
    if not value:raise ValueError(message)


def write_immutable(destination,files):
    destination=Path(destination)
    require(not destination.is_symlink(),'package destination is a symlink')
    require(all(Path(n).name==n and n not in ('.','..') for n in files),'flat package names required')
    if destination.exists():
        require(destination.is_dir() and {p.name for p in destination.iterdir()}==set(files),'existing version package differs')
        require(all(not (destination/n).is_symlink() and (destination/n).read_bytes()==v for n,v in files.items()),'never replace existing version bytes')
        return
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='movement-package-',dir=destination.parent) as temporary:
        staged=Path(temporary)/'complete';staged.mkdir()
        for name,data in files.items():(staged/name).write_bytes(data)
        staged.rename(destination)


def with_sums(files):
    return {**files,'SHA256SUMS':''.join(f'{sha(data)}  {name}\n' for name,data in sorted(files.items())).encode()}


def read_frozen(path):
    path=Path(path);require(path.is_dir() and not path.is_symlink(),'frozen package directory required')
    sums={name:digest for digest,name in (line.split('  ',1) for line in (path/'SHA256SUMS').read_text().splitlines())}
    require({p.name for p in path.iterdir()}==set(sums)|{'SHA256SUMS'},'frozen file set differs')
    for name,digest in sums.items():
        require(Path(name).name==name and not (path/name).is_symlink() and sha((path/name).read_bytes())==digest,'frozen file hash differs')
    return {name:(path/name).read_bytes() for name in sums}


def _audit_primary(build,suite,cpu,port2,rom):
    require(not validate_rom(rom) and build['rom']['sha256']==sha(rom) and build['version']==VERSION and build['source_dirty'] is False,'clean exact movement build required')
    audit_manifest({'tool_source_commit':build['source_commit'],'utility_fingerprints':build['source_files']},FILES)
    require(set(suite)==set(POSITIVES)|{'negative_controls'},'complete11-mode movement suite required')
    modes={name:(family,layout,width,transitions) for name,family,layout,width,transitions in PACED_MODES}
    modes['counts']=('ntsc',0,0,False)
    for name in POSITIVES:
        part=suite[name];family,layout,width,transitions=modes[name]
        require(part['rom_sha256']==build['rom']['sha256'] and part['build_source_commit']==build['source_commit']
            and part['build_dirty'] is False and part['harness_dirty'] is False and part['pixel_errors']==0,'capture differs from clean tested build')
        validate_receipt(part,59736 if family=='ntsc' else 71364,layout,width,transitions)
        audit_producer(part,'movement')
        directory=(ROOT/part['directory']).resolve();require(directory.is_relative_to(OUT.resolve()),'movement capture outside owned outputs')
        require(json.loads((directory/'verified.json').read_text())==part,'suite differs from verified capture')
        audit_files(directory,part['artifacts'],VISUAL_ROOT|{ROM.name})
        require(sha((directory/VISUAL_PROFILE).read_bytes())==part['profile_sha256'],'movement machine profile differs')
    require(set(cpu)==set(CPU_COUNTS),'complete generic/phase/device CPU proofs required')
    for name,count in CPU_COUNTS.items():
        part=cpu[name]
        require(part['cases']==count and part['build_dirty'] is False and part['harness_dirty'] is False
            and part['build_source_commit']==build['source_commit'],'CPU proof coverage/producer differs')
        require(part['fast_phase']==(name in ('phase','devices_phase')) and part['input_adapter']==name.startswith('devices_'),'CPU proof kind differs')
        if name.startswith('devices_'):require(part['receipt']['input_samples']==2*count,'missing per-phase genuine input reads')
        audit_producer(part,'devices' if name.startswith('devices_') else 'generic')
        directory=(ROOT/part['directory']).resolve();require(directory.is_relative_to((ROOT/'outputs/native').resolve()),'CPU capture outside owned outputs')
        digest_files(directory,cpu_files(name.startswith('devices_')))
        require(json.loads((directory/'verified.json').read_text())==part and sha((directory/'native-contract.rom').read_bytes())==part['rom_sha256'],'CPU receipt/binary differs')
        require(json.loads((directory/'complete.json').read_text())==part['receipt'],'CPU completion receipt differs')
        require(sha((directory/CPU_PROFILE).read_bytes())==part['backend']['profile_sha256'],'CPU machine profile differs')
        native_build=json.loads((directory/'build.json').read_text())
        require(native_build['source_commit']==part['build_source_commit'] and native_build['source_dirty'] is False
            and native_build['rom_sha256']==part['rom_sha256'] and native_build['source']==build['original']
            and native_build['fast_phase']==part['fast_phase'] and native_build['input_adapter']==part['input_adapter']
            and native_build['corrupt_port2'] is False,'CPU build metadata differs')
        audit_manifest({'tool_source_commit':native_build['source_commit'],'utility_fingerprints':native_build['source_files']},
            CPU_BUILD_FILES+('scripts/native_fast.py','scripts/native_analysis.py')+(('src/native_input.asm',) if name.startswith('devices_') else ()))
        for filename,key in (('cases.bin','input_sha256'),('expected.json','expected_sha256'),('actual.bin','actual_sha256')):
            require(sha((directory/filename).read_bytes())==part[key],'CPU artifact differs')
        if name.startswith('devices_'):
            require(sha((directory/'devices.omr').read_bytes())==part['device_replay_sha256']
                and sha((directory/'mirrors.bin').read_bytes())==part['mirrors_sha256'],'device replay/mirror hash differs')
    faults=suite['negative_controls'];require(set(faults)=={'pixel','state','sprite','guard','spacing'},'five actual injected faults required')
    for fault,part in faults.items():
        require(part['detected'] is True and part['harness_dirty'] is False and part['rom_sha256']==sha(rom)
            and part['build_source_commit']==build['source_commit'],'negative-control binary/producer differs')
        audit_producer(part['producer'],'movement')
        require(FAILURES[fault][1] in part['detail'],'negative detail lacks expected cause')
    require(port2['detected'] is True and 'RAM AF' in port2['detail'],'actual port2 fire inversion must fail source comparison')
    mutant=port2['build'];require(mutant['source_dirty'] is False and mutant['source_commit']==build['source_commit']
        and mutant['corrupt_port2'] is True and mutant['input_adapter'] is True and mutant['fast_phase'] is True,'port2 mutant producer differs')
    audit_producer({'tool_source_commit':mutant['source_commit'],'utility_fingerprints':mutant['source_files']},'mutant_build')
    directory=(ROOT/port2['directory']).resolve();require(directory.is_relative_to(CPU_OUT.resolve()),'port2 capture outside owned outputs')
    digest_files(directory,cpu_files(True,verified=False))
    require(json.loads((directory/'build.json').read_text())==mutant and sha((directory/'native-contract.rom').read_bytes())==mutant['rom_sha256'],'port2 mutant binary differs')
    audit_files(directory,port2['artifacts'],PORT2_DECLARED)
    require(sha((directory/CPU_PROFILE).read_bytes())==cpu['devices_phase']['backend']['profile_sha256'],'port2 machine profile differs')


def integrity_evidence(build,suite,cpu,port2):
    artifacts={};failures={};baseline=ROOT/suite['ntsc']['directory']
    for name in POSITIVES:
        directory=ROOT/suite[name]['directory']
        artifacts['visual:'+name]={'directory':suite[name]['directory'],'hashes':digest_files(directory,visual_files(ROM.name))}
    for name in CPU_COUNTS:
        directory=ROOT/cpu[name]['directory']
        artifacts['cpu:'+name]={'directory':cpu[name]['directory'],'hashes':digest_files(directory,cpu_files(name.startswith('devices_')))}
    artifacts['cpu:port2']={'directory':port2['directory'],'hashes':digest_files(ROOT/port2['directory'],cpu_files(True,verified=False))}
    for fault,part in {**suite['negative_controls'],'port2_fire':port2}.items():
        stage,cause=FAILURES[fault]
        if fault=='port2_fire':directory=(ROOT/part['directory']).resolve();required=cpu_files(True,verified=False)
        else:
            match=re.search(re.escape(str(OUT.resolve()))+r'/pace-[^\s:;]+',part['detail'])
            require(match is not None,'negative capture directory absent');directory=Path(match[0]).resolve()
            require(directory.is_relative_to(OUT.resolve()),'negative capture outside owned outputs')
            required=visual_files(ROM.name,verified=False,complete=stage=='comparison')
            require(not (directory/'verified.json').exists(),'negative capture incorrectly marked verified')
            require(f'set inject_fault {fault}\n' in (directory/'launch.tcl').read_text(),'negative injection selector differs')
            require(json.loads((directory/'build.json').read_text())==build and sha((directory/ROM.name).read_bytes())==build['rom']['sha256'],'negative target differs')
            require(sha((directory/VISUAL_PROFILE).read_bytes())==suite['ntsc']['profile_sha256'],'negative machine profile differs')
        record={'injection':fault,'stage':stage,'cause':cause,'detected':part['detected'],'detail':part['detail'],
            'directory':str(directory.relative_to(ROOT)),'artifacts':digest_files(directory,required)}
        verify_failure_data(record,directory,baseline)
        failures[fault]=record
    return {'artifacts':artifacts,'failures':failures}


def integrity_summary(manifest):
    return {'schema':1,'scope':'Separate post-review integrity audit of unchanged original captures; no runtime or producer relabeling',
        'runtime_source_commit':manifest['runtime_source_commit'],'rom_sha256':manifest['rom_sha256'],
        'auditor_source_commit':manifest['auditor_producer']['tool_source_commit'],'integrity_sha256':sha(encoded(manifest)),
        'primary_sums_sha256':manifest['primary_sums_sha256'],
        'failures':{n:{'stage':v['stage'],'cause':v['cause'],'receipt_sha256':sha(encoded(v))} for n,v in manifest['evidence']['failures'].items()}}


def seal_integrity(frozen,destination):
    files=read_frozen(frozen);build,suite,cpu,port2=[json.loads(files[n]) for n in ('build.json','suite.json','native.json','port2-negative.json')]
    _audit_primary(build,suite,cpu,port2,files[ROM.name])
    producer=snapshot_paths(('scripts/movement_delivery.py','scripts/movement_evidence.py'))
    manifest={'schema':1,'runtime_source_commit':build['source_commit'],'rom_sha256':sha(files[ROM.name]),
        'primary_sums_sha256':sha((Path(frozen)/'SHA256SUMS').read_bytes()),'auditor_producer':producer,
        'evidence':integrity_evidence(build,suite,cpu,port2)}
    require(snapshot_paths(('scripts/movement_delivery.py','scripts/movement_evidence.py'))==producer,'integrity auditor changed')
    result={'integrity.json':encoded(manifest),'movement-integrity.json':encoded(integrity_summary(manifest))}
    result.update({f'failure-{n}.json':encoded(record) for n,record in manifest['evidence']['failures'].items()})
    write_immutable(destination,with_sums(result));return integrity_summary(manifest)


def audit(build,suite,cpu,port2,rom,integrity=None,primary=None):
    _audit_primary(build,suite,cpu,port2,rom)
    require(integrity is not None and primary is not None,'separate frozen integrity supplement required')
    files=read_frozen(integrity);manifest=json.loads(files['integrity.json'])
    require(manifest['schema']==1 and manifest['runtime_source_commit']==build['source_commit'] and manifest['rom_sha256']==sha(rom)
        and manifest['primary_sums_sha256']==sha((Path(primary)/'SHA256SUMS').read_bytes()),'integrity supplement targets different evidence')
    audit_manifest(manifest['auditor_producer'],('scripts/movement_delivery.py','scripts/movement_evidence.py'))
    require(manifest['evidence']==integrity_evidence(build,suite,cpu,port2),'sealed raw evidence differs')
    require(encoded(integrity_summary(manifest))==files['movement-integrity.json'],'integrity summary differs')
    for name,record in manifest['evidence']['failures'].items():require(files[f'failure-{name}.json']==encoded(record),'failure receipt differs')


def compact(build,suite,cpu,port2):
    timings={name:{'frames':part['cases'],'source_steps':part['step_counts'][-1],'max_busy_cycles':part['max_busy_cycles'],
        'frame_budget':part['frame_budget'],'margin_cycles':part['frame_budget']-part['max_busy_cycles'],'min_spacing':part['min_spacing'],
        'max_sprites_per_line':part['max_sprites_per_line'],'stack_min':part['stack_min'],'max_commit_cycles':max(part['commit_cycles']),
        'capture_directory':part['directory'],'verified_sha256':sha(encoded(part))} for name,part in suite.items() if name in POSITIVES}
    return {'schema':1,'version':VERSION,'source_commit':build['source_commit'],'rom':build['rom'],
        'scope':'Native post-visible F476 to F019 diagnostic; synthetic graphics and scripted contacts, not natural/full-game acceptance',
        'target':{'ram_kib':64,'vram_kib':16,'cpu_hz':3579545,'mapper':'ASCII16','extra_expansions':False},
        'original_sha256':build['original']['sha256'],'cpu':{name:{'cases':part['cases'],'max_cycles':part['max_cycles'],
            'rom_sha256':part['rom_sha256'],'verified_sha256':sha(encoded(part)),'capture_directory':part['directory']} for name,part in cpu.items()},
        'timings':timings,'negative_controls':{**{n:v['detected'] for n,v in suite['negative_controls'].items()},'port2_fire':port2['detected']},
        'build_source_files':build['source_files'],'assembler_sha256':build['assembler_sha256'],
        'atlas':{'colored_tiles':build['atlas']['tiles'],'ordinary_tiles':build['atlas']['ordinary_tiles'],'row_bytes':build['atlas']['rows_bytes'],
            'row_variants':build['atlas']['variants'],'bottom_static_tiles':248,'bottom_dynamic_slots_per_page':4},
        'limitations':['No natural collision acquisition or whole-frame/game proof; issues11/12 reconcile the missing visible/contact phase',
            'Original graphics prepared in9 remain offline; this runtime uses synthetic masks and a diagnostic HUD',
            'No audio engine; source writes terminate at explicit shadows, not an ordered PSG/audio proof',
            'Fast whole-phase entry requires D=0/SP=FF; generic CPU slices keep their separate bounded ABI',
            'Automated emulated evidence only; manual viewing/listening, expanded slots and physical hardware remain pending']}


def notes(build,report):
    rom=build['rom'];ntsc=min(v['margin_cycles'] for k,v in report['timings'].items() if not k.startswith('pal'))
    pal=min(v['margin_cycles'] for k,v in report['timings'].items() if k.startswith('pal'))
    return f'''# Frostbite MSX1 {VERSION} — movement diagnostic

Exact source commit: `{build['source_commit']}`. ROM: `{rom['filename']}`,
{rom['size']} bytes, **ASCII16** mapper, SHA-256 `{rom['sha256']}`.
Standard-speed MSX1, 64 KiB RAM, 16 KiB TMS9918-family VRAM and built-in PSG.
The mapper is part of the cartridge; no RAM, sound, disk or turbo expansion is used.

## Current state

The original post-visible movement phase runs as native Z80. Raw cursor keys,
SPACE, both standard joystick ports and F1/F2 are sampled at the original fire
and direction/console boundaries. Original counter parity, jump tables, raw
opposing directions, fire edges, air steering and floe transport are retained
at this declared phase boundary. PAL presents 50 frames while scheduling the
same logical source cadence; no required source steps are skipped.

**This is a diagnostic with scripted contacts and synthetic graphics.** Ground
contacts are supplied at declared logical rows; visible X overlap does not decide
collisions. The HUD shows diagnostic position/palette, with coarse construction
preview. Original sprites/HUD, natural collision acquisition, whole-game routes
and sound remain pending. The ROM's normal display follows native state; the
crowded test scenes belong to the automated harness.

Automated checks: 4,497 generic CPU cases including all 101 published mechanics
fixtures; 1,793 specialized phase/cold/continuous cases; 1,354 genuine-device
cases for each CPU path. Eleven 240-frame captures compare every presented pixel,
native CPU / all 128 RAM bytes, uninterrupted source chains, adapter values, visible
preparation invariance, SAT, 29-cycle VRAM spacing, stack/heap, consecutive frames
and VBlank commits. Minimum measured margin: NTSC {ntsc}, PAL {pal} cycles.
Five injected pipeline faults and an inverted port2 fire input were rejected.
These are automated emulated results; manual and physical acceptance is pending.

## Next

[Issue11](https://github.com/sandersouza/msxgp-frostbite/issues/11) continues floes,
construction, entry and temperature, including the real floe contacts needed for
its natural route. [Issue12](https://github.com/sandersouza/msxgp-frostbite/issues/12)
continues RNG/hazards and full TIA-derived collision semantics. The missing visible
phase must be reconciled; subsequent issues integrate full progression,
original presentation/audio and complete-game/hardware acceptance. Legacy
Seaquest deletion remains issue17 after replacement acceptance.

## Human tests

1. Load the attached exact ROM on an unexpanded 64 KiB MSX1, or openMSX with an
   MSX1/16KiB-VRAM profile and mapper **ASCII16**. Example:
   `openmsx -machine C-BIOS_MSX1 -cart {rom['filename']} -romtype ASCII16`.
   Test a PAL MSX1 profile too if available. Record machine/VDP/video standard and
   cartridge/mapper. Host function keys may require Fn.
2. Wait for **FROSTBITE MOVEMENT DIAG**. Use F2 to select an original variation
   and F1 to reset/start. Cursors or the selected player's joystick control
   direction; SPACE or joystick primary fire is the original reversal action.
   Regular/advanced and one/two-player selections follow the source ROM.
3. Hold DOWN about 0.1s, then release. A started jump should complete its source
   arc to the next scripted row. Try LEFT/RIGHT in the air and near both edges.
   Try opposing directions: left and up retain the source priorities. Graphics
   are diagnostic; do not interpret apparent X overlaps as collision acceptance.
4. On a grounded scripted row press/release SPACE, hold it, then repress. Expect
   one reversal per press, with no repeat from holding; an airborne press must
   not create the grounded reversal. Check joystick1 and, when that player is
   active, joystick2. Keyboard joins the currently selected original port.
5. F3 changes diagnostic row layout; F4 changes floe width. Hold/release/repress
   each: one visual change per press, no repeated toggle while held. Source
   coordinates/mechanics continue. Sound effects are not implemented.
6. Run about 5 minutes. Report version/SHA, setup, controls and exact reproduction
   steps for hangs, flicker, sprite loss, wrong priorities, repeated edges or
   speed differences. A short video plus whether it was PAL/NTSC helps. Report
   emulator and physical results separately; no manual/physical pass is assumed.
'''


def capture_bundle(destination,integrity):
    require(not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'commit producers before canonical capture')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();driver=sha(Path(__file__).read_bytes())
    print('Canonical movement build',flush=True);build=build_api.build();artifact=ROM.read_bytes()
    cpu={}
    for name,call in (('generic',lambda:run_contract()),('phase',lambda:run_contract(fast_phase=True)),
        ('devices_generic',lambda:input_check()),('devices_phase',lambda:input_check(fast_phase=True))):
        print(f'Canonical {name}',flush=True);cpu[name]=call()
    try:input_check(negative=True,fast_phase=True)
    except ValueError as error:
        require('RAM AF' in str(error),'wrong port2 negative failure')
        directory=Path(str(error).rsplit('; ',1)[-1]).resolve();require(directory.is_relative_to(CPU_OUT.resolve()),'port2 error missing owned capture')
        port2={'detected':True,'detail':str(error),'build':json.loads((directory/'build.json').read_text()),'directory':str(directory.relative_to(ROOT)),
            'artifacts':{n:sha((directory/n).read_bytes()) for n in ('cases.bin','expected.json','actual.bin','complete.json','emulator.log')}}
    else:raise ValueError('port2 negative escaped')
    suite={}
    for name,family,layout,width,transitions in PACED_MODES:
        print(f'Canonical {name}',flush=True);suite[name]=capture(family,layout,width,transitions)
    suite['counts']=capture(catalog='counts');suite['negative_controls']=negative_controls()
    require(head==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() and driver==sha(Path(__file__).read_bytes())
        and not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'canonical orchestration/checkout changed')
    _audit_primary(build,suite,cpu,port2,artifact);report=compact(build,suite,cpu,port2)
    files={ROM.name:artifact,'build.json':encoded(build),'suite.json':encoded(suite),'native.json':encoded(cpu),
        'port2-negative.json':encoded(port2),'movement-result.json':encoded(report),'release-notes.md':notes(build,report).encode()}
    write_immutable(destination,with_sums(files));print(f'Frozen exact movement evidence: {destination}',flush=True)
    seal_integrity(destination,integrity)
    audit(build,suite,cpu,port2,artifact,integrity,destination)
    return report


def package(frozen,destination,integrity):
    files=read_frozen(frozen);build=json.loads(files['build.json']);suite=json.loads(files['suite.json']);cpu=json.loads(files['native.json']);port2=json.loads(files['port2-negative.json'])
    audit(build,suite,cpu,port2,files[ROM.name],integrity,frozen);report=compact(build,suite,cpu,port2)
    require(encoded(report)==files['movement-result.json'] and notes(build,report).encode()==files['release-notes.md'],'frozen summary/notes differs')
    public={name:files[name] for name in (ROM.name,'build.json','movement-result.json','release-notes.md')}
    public['movement-integrity.json']=read_frozen(integrity)['movement-integrity.json']
    write_immutable(destination,with_sums(public));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('capture','package','audit','integrity'))
    parser.add_argument('--frozen',type=Path,default=OUT/'issue10-final');parser.add_argument('--out',type=Path)
    parser.add_argument('--integrity',type=Path,default=OUT/'issue10-integrity')
    args=parser.parse_args()
    if args.command=='capture':capture_bundle(args.out or args.frozen,args.integrity)
    elif args.command=='integrity':seal_integrity(args.frozen,args.out or args.integrity)
    elif args.command=='package':package(args.frozen,args.out or ROOT/f'outputs/releases/v{VERSION}-verified',args.integrity)
    else:
        files=read_frozen(args.frozen);audit(json.loads(files['build.json']),json.loads(files['suite.json']),json.loads(files['native.json']),json.loads(files['port2-negative.json']),files[ROM.name],args.integrity,args.frozen);print('Frozen movement evidence audited')
