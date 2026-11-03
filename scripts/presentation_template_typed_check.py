"""Actual Z80 complete raw-floe tile grammar; not a game/frame verdict."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from presentation_constructors import floe_key
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=('scripts/presentation_template_typed_check.py','scripts/presentation_constructors.py','src/presentation_typed.asm','src/presentation_template_reader.asm',
    'scripts/presentation_template_assets.py','scripts/presentation_floe_templates.py','src/movement.asm','scripts/environment.py','scripts/smoke.py','scripts/render_build.py')
ROW_BYTES=18


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('whole raw-floe tile/carry/error differs or truncates')


def fixtures(patterns):
    inputs=bytearray();expected=bytearray();count=len(patterns)//8
    if not count or len(patterns)%8:raise ValueError('complete raw floe masks required')
    for bank,water in ((1,130),(2,129)):
        for index in range(count):
            mask=patterns[index*8:index*8+8]
            for color in range(1,16):
                inputs.extend(bytes((bank,))+floe_key(index,water,color));expected.extend(mask+bytes([color*16+4])*8+bytes(2))
    valid=floe_key(0,130,15)
    invalid=[(0,valid),(3,valid),(1,count.to_bytes(2,'little')+valid[2:]),(1,bytes((255,255))+valid[2:]),
        (1,valid[:3]+bytes((1,))+valid[4:]),(1,valid[:4]+bytes((0,9))),(1,valid[:4]+bytes((16,9))),
        (1,valid[:2]+bytes((129,))+valid[3:]),(2,valid),(1,valid[:5]+bytes((10,)))]
    for bank,key in invalid:inputs.extend(bytes((bank,))+key);expected.extend(bytes([165])*16+bytes((1,1)))
    return bytes(inputs),bytes(expected)


def check(out,assets):
    producer={name:digest(ROOT/name) for name in FILES};assets=Path(assets).resolve();meta=json.loads((assets/'assets.json').read_text())
    consumed={str(assets/'assets.json'):digest(assets/'assets.json')}
    for name,value in meta['files'].items():
        if digest(assets/name)!=value:raise ValueError('template bank changed')
        consumed[str(assets/name)]=value
    for name in ('floe-patterns.bin','presentation_template.inc','presentation_static.inc'):consumed[str(assets/name)]=digest(assets/name)
    patterns=(assets/'floe-patterns.bin').read_bytes()
    if len(patterns)!=meta['floe_patterns']*8 or digest(assets/'floe-patterns.bin')!=meta['floe_patterns_sha256']:raise ValueError('raw floe identity changed')
    inputs,expected=fixtures(patterns);count=len(inputs)//7;out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    (out/'presentation_simple.inc').write_text('pt_water_id0 EQU 130\npt_water_id1 EQU 130\npt_water_id2 EQU 129\n')
    movement=(ROOT/'src/movement.asm').read_text();mapper=movement[movement.index('map_page2:\n'):movement.index('set_address:\n')]
    entry='''    DEFINE WITH_PRESENTATION_TEMPLATES
    ORG $4000
    DB "AB"
    DW start
    DS 12,0
p_bg_patterns0_data EQU $8000
p_bg_patterns1_data EQU $8000
p_bg_patterns2_data EQU $8000
p_bg_colors0_data EQU $8000
p_bg_colors1_data EQU $8000
p_bg_colors2_data EQU $8000
start:
    DI
    LD SP,$F380
    CALL map_page2
    DI
ready:
    JP ready
presentation_geometry_pattern:
    JP p_template_pattern
    INCLUDE "presentation_template_reader.asm"
    INCLUDE "presentation_typed.asm"
'''+mapper+'    DS $8000-$,$FF\n'
    for bank in range(1,256):
        entry+='    ORG $8000\n'
        entry+=f'    INCBIN "{assets/f"assets-{bank:03d}.bin"}"\n' if bank in meta['physical_banks'] else '    DS $4000,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={out}',f'--inc={assets}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('raw-floe constructor assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_FloeTyped.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    guards=((0xC000,0xC2BC),(0xC2BD,0xC520),(0xC530,0xC53C),(0xC53E,0xC53F),(0xC540,0xC760),(0xC768,0xCC80),(0xCC88,0xCC90),(0xCC96,0xF340))
    guard_list=' '.join(f'{a} {b-a}' for a,b in guards)
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_floe_typed {{message}} {{puts stderr "FLOE_TYPED_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_floe_typed {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*7}}] [expr {{$::index*7+6}}]]
    binary scan [string index $row 0] cu bank;set ::key [string range $row 1 6]
    debug write_block memory 0xCC90 $::key;debug write_block memory 0xC520 [string repeat [binary format c 165] 16]
    reg AF [expr {{$bank*256}}];reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_floe_typed target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['presentation_typed_construct']&255} {syms['presentation_typed_construct']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{{guard_list}}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_floe_typed "guard $address"}}
        }}
        if {{[debug read_block memory 0xCC90 6] ne $::key || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_floe_typed input-or-vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_floe_typed abi}}
        puts -nonewline $::actual "[debug read_block memory 0xC520 16][binary format cu* [list [expr {{[reg F]&1}}] [debug read memory 0xC53F]]]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_floe_typed
    }}}}
    dispatch_floe_typed
}}}}]
after time 120 {{fail_floe_typed watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_FloeTyped','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'FLOE_TYPED_FAIL' in log:raise ValueError('actual raw-floe constructor capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed raw-floe constructor evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index} key={list(inputs[index*7:index*7+7])}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered constructor timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()) or any(digest(name)!=value for name,value in consumed.items()):raise ValueError('raw-floe constructor producers/inputs changed')
    report={'complete':True,'cases':count,'floe_patterns':meta['floe_patterns'],'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,'input_files':consumed,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 typed tag9: every2049 raw mask ×15 foregrounds ×both original water banks, invalid namespace/index/background/clip/colour/bank/type rejection. Complete16-byte tile/carry/error, immutable key and canonical/C6/heap/SP/IFF/slot/VRAM guards. Other typed grammar/game/frame acceptance separate.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assets',type=Path,required=True)
    check(**vars(p.parse_args()))
