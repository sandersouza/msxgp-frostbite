"""Actual Z80 proof of every packed contact block/field against sealed M-C."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from presentation_band_spike import COMPANIONS,PARENT_SHA,verified_bytes
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def check(build,out):
    meta=json.loads((build/'build.json').read_text());rom=build/meta['rom']['filename']
    if hashlib.sha256(rom.read_bytes()).hexdigest()!=meta['rom']['sha256']:
        raise ValueError('candidate identity changed')
    base=ROOT/'outputs/presentation/playfield-m-c/build'
    oldmeta=json.loads(verified_bytes(base/'build.json',COMPANIONS['build.json']))
    oldrom=verified_bytes(base/oldmeta['rom']['filename'],PARENT_SHA)
    codec=meta['tables']['codec'];count=codec['block_count']
    expected=bytearray()
    for index in range(count):
        at=(codec['block_bank']+index//512)*16384+(index%512)*32
        expected.extend(oldrom[at:at+32])
    out.mkdir(parents=True,exist_ok=False);(out/'expected.bin').write_bytes(expected)
    s=symbols(build/'presentation.sym')
    assembly=f'''    ORG $E800
start:
    XOR A
    LD ({s['hazard_leaf']}),A
    LD IX,$E900
.loop:
    LD DE,($C780)
    LD A,D
    SRL A
    ADD A,{codec['block_bank']}
    LD ($7000),A
    CALL {s['c14_slot']}
    CALL {s['c14_read']}
    LD (IX+0),E
    LD (IX+1),D
    INC IX
    INC IX
    LD HL,{s['hazard_leaf']}
    INC (HL)
    LD A,(HL)
    CP 16
    JR NZ,.loop
done:
    JR done
'''
    (out/'rpc.asm').write_text(assembly)
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--raw={out/"rpc.bin"}',
        f'--sym={out/"rpc.sym"}',str(out/'rpc.asm')],capture_output=True,text=True)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    rpc=(out/'rpc.bin').read_bytes();q=symbols(out/'rpc.sym')
    emulator=Path(shutil.which('openmsx')).resolve()
    profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/Contact14.xml').write_bytes(profile)
    settings=out/'settings.xml'
    settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_c14 {{m}} {{puts stderr "C14_FAIL $m block=$::index";exit 1;return -code error $m}}
proc dispatch_c14 {{}} {{
 if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
 debug write memory 0xC780 [expr {{$::index&255}}]
 debug write memory 0xC781 [expr {{$::index>>8}}]
 reg PC 0xE800;reg SP 0xF380;reg IY 0x2468
 set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {s['paced_frame_start']} {{}} {{debug remove_bp $::boot;debug break;after break {{
 if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_c14 target}}
 set ::canonical [debug read_block memory 0xC000 128];set ::abi [debug read_block memory 0xC600 256];set ::slot [debug read ioports 168]
 debug write_block memory 0xE800 [binary format H* {rpc.hex()}]
 debug write_block memory 0xE980 [string repeat [binary format c 165] 2496]
 debug set_bp {q['done']} {{}} {{debug break;after break {{
  if {{[debug read_block memory 0xC000 128] ne $::canonical || [debug read_block memory 0xC600 256] ne $::abi}} {{fail_c14 source}}
  if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot || [reg IX]!=0xE920 || [reg IY]!=0x2468}} {{fail_c14 abi}}
  if {{[debug read_block memory 0xE980 2496] ne [string repeat [binary format c 165] 2496]}} {{fail_c14 guard}}
  puts -nonewline $::actual [debug read_block memory 0xE900 32]
  puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
  incr ::index;dispatch_c14
 }}}}
 dispatch_c14
}}}}]
after time 6000 {{fail_c14 watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Contact14','-cart',str(rom),
        '-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
        capture_output=True,text=True,timeout=600)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError((run.stdout+run.stderr)[-1500:])
    actual=(out/'actual.bin').read_bytes()
    if actual!=expected:raise ValueError('native packed fields differ or truncate')
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(row[0]!=i or row[1]<=0 for i,row in enumerate(times)):
        raise ValueError('incomplete or reordered component timing')
    result=dict(complete=True,blocks=count,fields=count*16,rom_sha256=meta['rom']['sha256'],
        expected_sha256=hashlib.sha256(expected).hexdigest(),actual_sha256=hashlib.sha256(actual).hexdigest(),
        max_block_cycles_including_rpc=max(row[1] for row in times),
        scope='All actual immutable blocks and16 fields on real MSX1 Z80; source/ABI/stack/DI guards; not full-frame cadence or original-time acceptance.')
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();check(args.build.resolve(),args.out.resolve())
