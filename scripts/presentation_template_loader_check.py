"""Actual Z80 finite-template lookup; no native game or frame acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=('scripts/presentation_template_loader_check.py','src/presentation_template_loader.asm','src/presentation_template_reader.asm',
    'scripts/presentation_template_assets.py','scripts/presentation_floe_templates.py','src/movement.asm','scripts/environment.py','scripts/smoke.py','scripts/render_build.py')
ROW_BYTES=61


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('complete template count/keys/program/error differs or truncates')


def fixtures(meta,raw):
    params=[(root,delta,88+phase) for phase in range(8) for delta in meta['deltas'] for root in range(160)]
    params.extend((159,meta['deltas'][-1],y) for y in (0,7,63,64,127,128,179,185))
    params.extend(((160,4,88),(255,4,88),(0,3,88),(0,7,88),(0,17,88),(0,255,88),(0,4,186),(0,4,255)))
    keys=bytearray([165])*28;names=bytes([165])*30;count=165;inputs=bytearray();expected=bytearray();s=meta['sections']
    for root,delta,y in params:
        inputs.extend(bytes((root,delta,y)));error=int(root>=160 or y>=186 or delta not in meta['deltas'])
        if not error:
            index=((y&7)*len(meta['deltas'])+meta['deltas'].index(delta))*16+(root&15)
            at=s['template_index']['offset']+index*2
            record=s['template_keys']['offset']+int.from_bytes(raw[at:at+2],'little')
            program,count=raw[record:record+2];keys[:count*2]=raw[record+2:record+2+count*2]
            at=s['template_names']['offset']+program*32;names=raw[at:at+30]
        expected.extend(bytes((count,))+keys+names+bytes((error,error)))
    return bytes(inputs),bytes(expected)


def check(out,assets):
    producer={name:digest(ROOT/name) for name in FILES};assets=Path(assets).resolve();meta=json.loads((assets/'assets.json').read_text())
    consumed={str(assets/'assets.json'):digest(assets/'assets.json'),str(assets/'presentation_template.inc'):digest(assets/'presentation_template.inc')}
    for name,value in meta['files'].items():
        if digest(assets/name)!=value:raise ValueError('template asset bank changed')
        consumed[str(assets/name)]=value
    raw=b''.join((assets/f'assets-{bank:03d}.bin').read_bytes() for bank in meta['physical_banks']);inputs,expected=fixtures(meta,raw);count=len(inputs)//3
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    movement=(ROOT/'src/movement.asm').read_text();mapper=movement[movement.index('map_page2:\n'):movement.index('set_address:\n')]
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
start:
    DI
    LD SP,$F380
    CALL map_page2
    DI
ready:
    JP ready
    INCLUDE "presentation_template_reader.asm"
    INCLUDE "presentation_template_loader.asm"
'''+mapper+'    DS $8000-$,$FF\n'
    for bank in range(1,256):
        entry+='    ORG $8000\n'
        entry+=f'    INCBIN "{assets/f"assets-{bank:03d}.bin"}"\n' if bank in meta['physical_banks'] else '    DS $4000,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={assets}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('template loader assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_TemplateLoader.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    guards=((0xC000,0xC2BC),(0xC2BD,0xC2D3),(0xC2D4,0xC2EC),(0xC2EF,0xC2F0),(0xC2F2,0xC760),(0xC768,0xE2A0),(0xE2BC,0xE2C0),(0xE2DE,0xF340))
    guard_list=' '.join(f'{a} {b-a}' for a,b in guards)
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_loader {{message}} {{puts stderr "TEMPLATE_LOADER_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_loader {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    binary scan [string range $::cases [expr {{$::index*3}}] [expr {{$::index*3+2}}]] cu* params
    lassign $params root delta y
    reg AF [expr {{$root*256}}];reg BC [expr {{$delta*256+$y}}];reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_loader target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['p_template_load']&255} {syms['p_template_load']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{{guard_list}}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_loader "guard $address"}}
        }}
        if {{[debug read_block VRAM 0 16384] ne $::vram}} {{fail_loader vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_loader abi}}
        puts -nonewline $::actual "[debug read_block memory 0xC2D3 1][debug read_block memory 0xE2A0 28][debug read_block memory 0xE2C0 30][binary format cu* [list [expr {{[reg F]&1}}] [debug read memory 0xC2BC]]]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_loader
    }}}}
    dispatch_loader
}}}}]
after time 120 {{fail_loader watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_TemplateLoader','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'TEMPLATE_LOADER_FAIL' in log:raise ValueError('actual template loader capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed template loader evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index} params={list(inputs[index*3:index*3+3])}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered template loader timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()) or any(digest(name)!=value for name,value in consumed.items()):raise ValueError('template loader producers/inputs changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,'input_files':consumed,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 lookup of all12800 original-control/root/Y-phase templates, eight Y boundaries and eight invalid parameter cases. Whole count/retained key bytes/program/error with canonical/descriptor/C6/heap/SP/IFF/slot/VRAM invariance. No NAME translation, game integration or complete-frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assets',type=Path,required=True)
    check(**vars(p.parse_args()))
