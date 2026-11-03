"""Actual Z80 cached NAME-row rotation; no game or frame acceptance."""
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

FILES=('scripts/presentation_name_rows_check.py','src/presentation_name_rows.asm','scripts/environment.py','scripts/smoke.py','scripts/render_build.py')
ROW_BYTES=2050
INPUT_BYTES=36


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rotated(row,root):
    if len(row)!=30 or type(root)is not int or not 0<=root<160:raise ValueError('whole source NAME row and valid root required')
    result=bytearray([128])*32
    for column,value in enumerate(row,1):
        target=1+(column-1+3*(root//16))%30
        if target>=2:result[target]=value
    return bytes(result)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('whole two-page names/cache/carry/error differ or truncate')


def fixtures():
    operations=[]
    for page in (0,1):
        for root in range(160):
            for row in range(24):
                owner=(root+row)%4;half=(root//4+row//4)&1;source=0xDE00+page*256+owner*64+half*30
                destination=(0xC800 if not page else 0xCD00)+row*32
                data=bytes((root*7+row*11+i*13+page*64)&255 for i in range(30))
                operations.append((page,root,source,destination,data))
    for page,root,source,destination in ((0,160,0xDE00,0xC800),(0,255,0xDE00,0xC800),(2,0,0xDE00,0xC800),
        (0,0,0xDF00,0xC800),(0,0,0xDE01,0xC800),(0,0,0xC600,0xC800),(0,0,0xDE00,0xC000),
        (0,0,0xDE00,0xC801),(0,0,0xDE00,0xCD00),(0,0,0xDE00,0xCB00),(1,0,0xDF00,0xD000)):
        operations.append((page,root,source,destination,bytes([37])*30))
    names=bytearray([165])*1536;cache=bytearray([165])*512;inputs=bytearray();expected=bytearray()
    for page,root,source,destination,data in operations:
        inputs.extend(bytes((page,root))+source.to_bytes(2,'little')+destination.to_bytes(2,'little')+data)
        if 0xDE00<=source<=0xE000-30:cache[source-0xDE00:source-0xDE00+30]=data
        valid=(page in (0,1) and root<160 and source>>8==0xDE+page and source%64 in (0,30)
            and destination%32==0 and (0xC800 if not page else 0xCD00)<=destination<(0xCB00 if not page else 0xD000))
        if valid:
            at=page*768+destination-(0xC800 if not page else 0xCD00);names[at:at+32]=rotated(data,root)
        expected.extend(names+cache+bytes((int(not valid),))*2)
    return bytes(inputs),bytes(expected)


def check(out):
    producer={name:digest(ROOT/name) for name in FILES};inputs,expected=fixtures();count=len(inputs)//INPUT_BYTES
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
PAGE EQU $C200
start:
    DI
    LD SP,$F380
ready:
    JP ready
    INCLUDE "presentation_name_rows.asm"
    DS $C000-$,$FF
'''
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('NAME-row assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_NameRows.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    guards=((0xC000,0xC200),(0xC201,0xC2BC),(0xC2BD,0xC760),(0xC768,0xC800),(0xCB00,0xCD00),(0xD000,0xDE00),(0xE000,0xF340))
    guard_list=' '.join(f'{a} {b-a}' for a,b in guards)
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_names {{message}} {{puts stderr "NAME_ROWS_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_names {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*{INPUT_BYTES}}}] [expr {{$::index*{INPUT_BYTES}+{INPUT_BYTES-1}}}]]
    binary scan [string range $row 0 5] cu* config;lassign $config page root sl sh dl dh
    set source [expr {{$sh*256+$sl}}];set destination [expr {{$dh*256+$dl}}]
    debug write memory 0xC200 $page
    if {{$source>=0xDE00 && $source<=0xE000-30}} {{debug write_block memory $source [string range $row 6 35]}}
    reg AF [expr {{$root*256}}];reg HL $source;reg DE $destination;reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_names target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['p_template_name_row']&255} {syms['p_template_name_row']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{{guard_list}}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_names "guard $address"}}
        }}
        if {{[debug read_block VRAM 0 16384] ne $::vram}} {{fail_names vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_names abi}}
        puts -nonewline $::actual "[debug read_block memory 0xC800 768][debug read_block memory 0xCD00 768][debug read_block memory 0xDE00 512][binary format cu* [list [expr {{[reg F]&1}}] [debug read memory 0xC2BC]]]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_names
    }}}}
    dispatch_names
}}}}]
after time 120 {{fail_names watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_NameRows','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'NAME_ROWS_FAIL' in log:raise ValueError('actual NAME-row capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed NAME-row evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered NAME-row timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('NAME-row producer changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,'rom_sha256':digest(artifact),
        'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 all160 roots ×both pages ×all24 NAME rows, cycling allpage-cache owner/row pointers; eleven invalid root/page/source/destination cases. Whole two CPU NAME pages and512-byte source cache plus canonical/C6/heap/SP/IFF/slot/VRAM guards. No game or frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    check(**vars(p.parse_args()))
