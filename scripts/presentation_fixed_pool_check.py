"""Actual Z80 exact16-entry floe pair-pool proof; not a game/frame verdict."""
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

FILES=('scripts/presentation_fixed_pool_check.py','src/presentation_fixed_pool.asm','scripts/environment.py','scripts/smoke.py','scripts/render_build.py')
ROW_BYTES=99


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bucket(key):return (key[0]^key[1]^key[2]^key[3])&15


def fixtures():
    ops=[(0,bytes(4))]+[(1,bytes((i,0,i,0))) for i in range(16)]
    ops += [(1,bytes((i,0,i,0))) for i in range(16)]+[(1,bytes((16,0,16,0)))]
    for field in range(4):
        for value in range(256):
            if value%19==0:ops.append((0,bytes(4)))
            key=bytearray((17,34,51,68));key[field]=value;ops.append((1,bytes(key)))
    inputs=bytearray();expected=bytearray();keys=bytearray([165])*64;heads=bytearray([165])*16;links=bytearray([165])*16;pool=[]
    for op,key in ops:
        inputs.extend(bytes((op,))+key);result=carry=0
        if op==0:pool=[];heads[:]=bytes([255])*16
        elif key in pool:result=pool.index(key)
        elif len(pool)==16:result=255;carry=1
        else:
            result=len(pool);pool.append(key);keys[result*4:result*4+4]=key
            at=bucket(key);links[result]=heads[at];heads[at]=result
        expected.extend(bytes((result,carry,len(pool)))+keys+heads+links)
    return bytes(inputs),bytes(expected)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('whole pair-pool payload differs or is truncated')
    count=actual[2];keys=actual[3:67];heads=actual[67:83];links=actual[83:99]
    if count>16:raise ValueError('pair-pool count exceeds its physical role block')
    seen=set()
    for index,head in enumerate(heads):
        node=head
        while node!=255:
            if node>=count or node in seen:raise ValueError('invalid, duplicated or cyclic pair-pool chain')
            seen.add(node)
            if bucket(keys[node*4:node*4+4])!=index:raise ValueError('pair key stored in the wrong bucket')
            node=links[node]
    if seen!=set(range(count)):raise ValueError('unreachable pair-pool key')


def check(out):
    producer={name:digest(ROOT/name) for name in FILES};out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    inputs,expected=fixtures();count=len(inputs)//5;(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
start:
    DI
    LD SP,$F380
ready:
    JP ready
unit_run:
    LD A,($C2F0)
    OR A
    JP Z,p_fixed_pool_init
    JP p_fixed_pool_resolve
    INCLUDE "presentation_fixed_pool.asm"
    DS $C000-$,$FF
'''
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('pair-pool assembler failed: '+compiled.stderr[-1500:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_PairPool.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_pool {{message}} {{puts stderr "FIXED_POOL_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_pool {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*5}}] [expr {{$::index*5+4}}]]
    binary scan [string index $row 0] cu op
    debug write memory 0xC2F0 $op;set ::key [string range $row 1 4]
    debug write_block memory 0xE2E0 $::key
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_pool target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['unit_run']&255} {syms['unit_run']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{0xC000 512 0xC300 1120 0xC780 6912 0xE2E4 4188}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_pool "guard $address"}}
        }}
        if {{[debug read_block memory 0xE2E0 4] ne $::key || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_pool input-or-vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_pool abi}}
        puts -nonewline $::actual "[binary format cu* [list [reg A] [expr {{[reg F]&1}}] [debug read memory 0xC2D3]]][debug read_block memory 0xE2A0 64][debug read_block memory 0xE280 16][debug read_block memory 0xE290 16]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_pool
    }}}}
    dispatch_pool
}}}}]
after time 60 {{fail_pool watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_PairPool','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=120)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'FIXED_POOL_FAIL' in log:raise ValueError('actual pair-pool capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=count*ROW_BYTES or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('pair-pool captures/fixtures incomplete or changed')
    for index in range(count):verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered pair-pool timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('pair-pool producers changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,'rom_sha256':digest(artifact),
        'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual-Z80 local16-entry four-byte key pool, forced16-key collision chain, full/capacity/duplicate/reset and structural/whole-byte guards. No game integration or frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({key:report[key] for key in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    check(**vars(parser.parse_args()))
