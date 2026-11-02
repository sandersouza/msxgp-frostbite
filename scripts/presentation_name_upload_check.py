"""Actual Z80 owned NAME bursts; complete VRAM/CPU and invalid-list checks."""
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

FILES=('scripts/presentation_name_upload_check.py','src/presentation_name_upload.asm','scripts/environment.py','scripts/smoke.py','scripts/render_build.py')
ROW_BYTES=16384+1536+1
INPUT_BYTES=27


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('whole NAME VRAM/CPU/carry differ or truncate')


def fixtures():
    operations=[]
    for page in (0,1):
        for first in range(24):
            for count in range(1,25-first):
                operations.append((0,page,list(range(first,first+count))))
                operations.append((1,page,list(range(first,first+count))))
        for stride in range(2,8):
            for first in range(stride):
                operations.append((0,page,list(range(first,24,stride))))
        operations.extend(((0,page,[]),(1,page,[])))
    operations.extend(((0,2,[0]),(0,255,[23]),(0,0,[24]),(0,1,[255]),(0,0,[1,1]),(0,1,[5,3]),(0,0,list(range(25)))))
    names=bytes((i*13+(i//32)*17+37)&255 for i in range(1536))
    vram=bytearray([165])*16384;inputs=bytearray();expected=bytearray()
    for mode,page,rows in operations:
        inputs.extend(bytes((mode,page,len(rows)))+bytes((rows+[0]*24)[:24]))
        valid=page in (0,1) and len(rows)<=24 and all(0<=r<24 for r in rows) and rows==sorted(set(rows))
        if valid:
            for row in rows:
                base=(0x1800 if not page else 0x1C00)+row*32
                source=page*768+row*32
                vram[base:base+32]=names[source:source+32]
        expected.extend(vram+names+bytes((int(not valid),)))
    return bytes(inputs),bytes(expected)


def check(out):
    producer={name:digest(ROOT/name) for name in FILES};inputs,expected=fixtures();count=len(inputs)//INPUT_BYTES
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
PAGE EQU $C200
p_fd_count EQU $C2CE
p_fd_cursor EQU $C2CF
p_fd_loop EQU $C2CB
p_fd_list EQU $E580
start:
    DI
    LD SP,$F380
ready:
    JP ready
    INCLUDE "presentation_name_upload.asm"
vdp_write:
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    LD C,$98
.loop:
    OUTI
    JP NZ,.loop
    RET
    DS $C000-$,$FF
'''
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('NAME-row assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_NameRows.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    guards=((0xC000,0xC200),(0xC201,0xC2CB),(0xC2CC,0xC2CE),(0xC2D0,0xC760),(0xC768,0xC800),(0xCB00,0xCD00),(0xD000,0xE580),(0xE598,0xF340))
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
    binary scan [string range $row 0 2] cu* config;lassign $config mode page count
    debug write memory 0xC200 $page;debug write memory 0xC2CE $count
    set ::expected_list [string range $row 3 26]
    debug write_block memory 0xE580 $::expected_list
    set ::expected_page $page;set ::expected_count $count
    set target [expr {{$mode ? {syms['p_template_upload_names_known']} : {syms['p_template_upload_names']}}}]
    debug write memory 0xC761 [expr {{$target&255}}];debug write memory 0xC762 [expr {{$target>>8}}]
    reg AF 0;reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_names target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168]
    set VDP.too_fast_vram_access_callback {{fail_names spacing}}
    debug write_block VRAM 0 [string repeat [binary format c 165] 16384]
    set names [binary format H* {{{bytes((i*13+(i//32)*17+37)&255 for i in range(1536)).hex()}}}]
    debug write_block memory 0xC800 [string range $names 0 767];debug write_block memory 0xCD00 [string range $names 768 1535]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['p_template_upload_names']&255} {syms['p_template_upload_names']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{{guard_list}}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_names "guard $address"}}
        }}
        if {{[debug read_block memory 0xE580 24] ne $::expected_list || [debug read memory 0xC200]!=$::expected_page || [debug read memory 0xC2CE]!=$::expected_count}} {{fail_names input-list}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_names abi}}
        puts -nonewline $::actual "[debug read_block VRAM 0 16384][debug read_block memory 0xC800 768][debug read_block memory 0xCD00 768][binary format cu [expr {{[reg F]&1}}]]"
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
        'scope':'Actual Z80 every contiguous row interval on both pages through checked and producer-validated entries, gapped lists, empty lists and seven invalid page/list cases. Whole16KiB VRAM/two CPU NAME pages/carry plus canonical/C6/heap/SP/IFF/slot/29IO guards. No whole-game/frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    check(**vars(p.parse_args()))
