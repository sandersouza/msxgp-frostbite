"""Actual Z80 nibble NAME expansion into exclusive strip caches."""
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
from presentation_template_assets import name_pairs

FILES=('scripts/presentation_name_decode_check.py','src/presentation_name_decode.asm','src/movement.asm','scripts/presentation_template_assets.py','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')
ROW_BYTES=529
INPUT_BYTES=34
ROLES=((25,129),(9,129),(35,130),(19,130),(89,129),(73,129),(99,130),(83,130))


def fixtures():
    operations=[]
    for first in (0,9,19,25,35,73,83,89,99,241):
        for owner in range(8):
            for packed in range(256):
                for water in (129,130):
                    data=bytes((packed+i*17+owner*29)&255 for i in range(30))
                    operations.append((first,water,0xDE00+owner*64,data))
    for first,destination in ((242,0xDE00),(255,0xDE00),(9,0xDE01),(9,0xDE30),(9,0xDDC0),(9,0xE000),(9,0xC600)):
        operations.append((first,129,destination,bytes([255])*30))
    cache=bytearray([165])*512;codes=bytes([165])*16;inputs=bytearray();expected=bytearray()
    for first,water,destination,data in operations:
        inputs.extend(bytes((first,water))+destination.to_bytes(2,'little')+data)
        valid=first<=241 and 0xDE00<=destination<0xE000 and destination%64==0
        if valid:
            codes=bytes((water,))+bytes(range(first,first+15))
            result=bytes(codes[(data[index//2]>>(4*(index%2)))&15] for index in range(60))
            cache[destination-0xDE00:destination-0xDE00+60]=result
        expected.extend(cache+codes+bytes((int(not valid),)))
    return bytes(inputs),bytes(expected)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('whole cache/code-table/carry differs or truncates')


def fast_timing(inputs,times):
    selected=[]
    for index,row in enumerate(times):
        data=inputs[index*INPUT_BYTES:(index+1)*INPUT_BYTES]
        owner=(int.from_bytes(data[2:4],'little')-0xDE00)//64
        if 0<=owner<8 and tuple(data[:2])==ROLES[owner]:selected.append(row[1])
    if len(selected)!=2048 or max(selected)>3000:raise ValueError('complete fixed-role decoder domain must meet 3000-cycle microbudget')
    return {'fixed_role_cases':len(selected),'fixed_role_max_cycles_including_rpc':max(selected),'fixed_role_microbudget':3000}


def check(out):
    digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    producer={name:digest(ROOT/name) for name in FILES};inputs,expected=fixtures();count=len(inputs)//INPUT_BYTES
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    (out/'pairs.bin').write_bytes(name_pairs())
    movement=(ROOT/'src/movement.asm').read_text();mapper=movement[movement.index('map_page2:\n'):movement.index('set_address:\n')]
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
start:
    DI
    LD SP,$F380
    CALL map_page2
ready:
    JP ready
p_template_name_pairs_offset EQU 13*16384
    DEFINE WITH_PRESENTATION_TEMPLATES
    INCLUDE "presentation_name_decode.asm"
'''+mapper+'    DS $8000-$,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('NAME decoder assembler failed: '+compiled.stderr[-1800:])
    resident=artifact.read_bytes()
    if len(resident)!=16384:raise ValueError('complete resident unit bank required')
    artifact.write_bytes(resident+bytes([255])*(254*16384)+name_pairs()+bytes([255])*(16384-4096))
    syms=symbols(out/'unit.sym')
    if 'p_td_roles'not in syms:raise ValueError('fixed-role decoder fast path was not assembled')
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Decode.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_decode {{message}} {{puts stderr "NAME_DECODE_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_decode {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*34}}] [expr {{$::index*34+33}}]]
    binary scan [string range $row 0 3] cu* config;lassign $config first water dl dh
    set ::program [string range $row 4 33];debug write_block memory 0xE2C0 $::program
    reg AF [expr {{$first*256}}];reg BC [expr {{$water*256}}];reg DE [expr {{$dh*256+$dl}}]
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_decode target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['p_template_decode_names']&255} {syms['p_template_decode_names']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{0xC000 0x760 0xC768 0x1698 0xE000 0x2C0 0xE2DE 0x322 0xE610 0xD30}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_decode "guard $address"}}
        }}
        if {{[debug read_block memory 0xE2C0 30] ne $::program || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_decode program-or-vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_decode abi}}
        puts -nonewline $::actual "[debug read_block memory 0xDE00 512][debug read_block memory 0xE600 16][binary format cu [expr {{[reg F]&1}}]]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_decode
    }}}}
    dispatch_decode
}}}}]
after time 120 {{fail_decode watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Decode','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'NAME_DECODE_FAIL' in log:raise ValueError('actual NAME decode failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed decoder evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered decoder timing')
    fast=fast_timing(inputs,times)
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('decoder producers changed')
    report={'complete':True,'cases':count,**fast,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 complete60-byte nibble expansion, all256 packed-byte phases/eight destination owners/ten CID bases/two water IDs plus invalid base/destination bounds. Whole512-byte cache/16-byte code table/carry and canonical/C6/heap/program/VRAM/SP/IFF/slot invariance. Compiler grammar and frame acceptance separate.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    check(**vars(p.parse_args()))
