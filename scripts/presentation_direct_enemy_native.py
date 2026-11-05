"""Actual-Z80 complete actor planes, typed keys and cache lifecycle proof."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from presentation_direct_enemy import normalized_keys,segments
from presentation_geometry_check import fixtures,ROW_BYTES
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def check(build,out):
    meta=json.loads((build/'build.json').read_text());rom=(build/meta['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=meta['rom']['sha256']:raise ValueError('ROM identity changed')
    s=symbols(build/'presentation.sym');directory=build/'geometry'
    geometry=json.loads((directory/'geometry.json').read_text())
    original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if hashlib.sha256(original).hexdigest()!=geometry['source_sha256']:raise ValueError('original authority differs')
    inputs,descriptors=fixtures(original,geometry,directory)
    if inputs[:3]!=bytes(3) or inputs[66*128*3]!=1:raise ValueError('complete66-group source geometry required')
    flat=b''.join((directory/f'geometry-{bank:03d}.bin').read_bytes() for bank in geometry['physical_banks'])
    if flat[:8]!=bytes(8):raise ValueError('raw geometry zero must be empty')
    cases,expected=bytearray(),bytearray();owners=[]
    for page in range(2):
        for lane in range(4):
            roles=segments(page,lane)
            owners.extend([roles[0]['pgt']-0x4000,roles[1]['pgt']-0x4000,roles[0]['key'],roles[1]['key'],0xE800+(page*4+lane)*4])
            for group in range(66):
                for variant in range(128):
                    offset=(group*128+variant)*ROW_BYTES
                    descriptor=descriptors[offset:offset+ROW_BYTES]
                    columns,rows=descriptor[:2]
                    ids=[int.from_bytes(descriptor[2+i*2:4+i*2],'little') for i in range(columns*rows)]
                    phases=[(variant%8,0)]
                    if lane==1 and variant%8==0:phases.append((128,1))
                    for y,coarse in phases:
                        keys=normalized_keys(ids,columns,rows,lane,coarse)
                        masks=b''.join(flat[i*8:i*8+8] for i in keys)
                        color=1+(group+variant)%15
                        # Real hits and color-only changes after complete cold/warm publication.
                        for current in (color,color,1+color%15):
                            cases.extend((page,lane,group,variant,y,coarse,current))
                            typed=b''.join(i.to_bytes(2,'little')+bytes([roles[k//3]['water'],0,current,0]) for k,i in enumerate(keys))
                            if meta['direct_enemy'].get('lazy_keys'):typed=b'\xff'*36
                            expected.extend(masks+bytes([(current<<4)|4])*48+typed+bytes([group,variant|(coarse<<7),current,0,0]))
    n=len(cases)//7;stride=137
    if len(expected)!=n*stride:raise ValueError('incomplete lifecycle oracle')
    out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(cases);(out/'expected.bin').write_bytes(expected)
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/DirectEnemy.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    def call(a):return bytes((205,a&255,a>>8))
    rpc=bytes.fromhex('dde5fde5')+call(s['qe_geometry'])+call(s['qe_bulk'])+bytes.fromhex('fde1dde1c371c718fe')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
set owners {{{' '.join(map(str,owners))}}}
proc fail_packet {{m}} {{puts stderr "DIRECT_ENEMY_FAIL $m case=$::index";exit 1;return -code error $m}}
proc dispatch_packet {{}} {{
 if {{$::index=={n}}} {{close $::actual;close $::timing;exit;return}}
 binary scan [string range $::cases [expr {{$::index*7}}] [expr {{$::index*7+6}}]] cu* values
 lassign $values page lane group variant y coarse color
 debug write memory {s['PAGE']} $page;debug write memory {s['p_w_row']} $lane;debug write memory {s['p_w_group']} $group
 debug write memory {s['p_w_x']} [expr {{$variant>>3}}];debug write memory {s['p_w_y']} $y
 debug write memory {s['p_w_coarse']} $coarse;debug write memory {s['p_w_color']} $color
 set ::owner [expr {{($page*4+$lane)*5}}]
 set ::canonical [debug read_block memory 0xC000 128];set ::abi [debug read_block memory 0xC600 256]
 reg AF 0;reg BC [expr {{$group*256+$variant}}];reg IX 0x1357;reg IY 0x2468;reg SP 0xF380;reg PC 0xC760
 set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {s['paced_frame_start']} {{}} {{debug remove_bp $::boot;debug break;after break {{
 if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_packet target}}
 debug write_block VRAM 0 [string repeat [binary format c 0] 16384]
 debug write_block memory 0xE800 [string repeat [binary format c 255] 128]
 debug write_block memory 0xE880 [string repeat [binary format c 165] 2752]
 set ::slot [debug read ioports 168]
 debug write_block memory 0xC760 [binary format H* {rpc.hex()}]
 set VDP.too_fast_vram_access_callback {{fail_packet fast-vram}}
 debug set_bp 0xC771 {{}} {{debug break;after break {{
  if {{[debug read_block memory 0xC000 128] ne $::canonical || [debug read_block memory 0xC600 256] ne $::abi}} {{fail_packet source}}
  if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot || [reg IX]!=0x1357 || [reg IY]!=0x2468}} {{fail_packet abi}}
  if {{[debug read_block memory 0xE880 2752] ne [string repeat [binary format c 165] 2752] || [debug read memory 0xC231]!=0}} {{fail_packet guard}}
  set pg1 [lindex $::owners $::owner];set pg2 [lindex $::owners [expr {{$::owner+1}}]]
  set key1 [lindex $::owners [expr {{$::owner+2}}]];set key2 [lindex $::owners [expr {{$::owner+3}}]];set cache [lindex $::owners [expr {{$::owner+4}}]]
  puts -nonewline $::actual "[debug read_block VRAM $pg1 24][debug read_block VRAM $pg2 24][debug read_block VRAM [expr {{$pg1+8192}}] 24][debug read_block VRAM [expr {{$pg2+8192}}] 24][debug read_block memory $key1 18][debug read_block memory $key2 18][debug read_block memory $cache 3][binary format cu* [list [expr {{[reg F]&1}}] [debug read memory {s['pt_error']}]]]"
  puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
  incr ::index;dispatch_packet
 }}}}
 dispatch_packet
}}}}]
after time 10000 {{fail_packet watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','DirectEnemy','-cart',str(build/meta['rom']['filename']),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=1200)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError((run.stdout+run.stderr)[-1500:])
    actual=(out/'actual.bin').read_bytes()
    if actual!=expected:
        first=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),min(len(actual),len(expected)))
        raise ValueError(f'actor band differs/truncates at case {first//stride} byte {first%stride}, input={list(cases[first//stride*7:first//stride*7+7])}')
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=n or any(row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete target timings')
    result=dict(complete=True,cases=n,groups=66,variants=128,owners=8,colors=15,rom_sha256=meta['rom']['sha256'],
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        original_sha256=hashlib.sha256(original).hexdigest(),
        max_cycles_including_rpc=max(row[1] for row in times),
        scope='Complete finite actor planes, padding, bank split, cache lifecycle and typed keys; not full-frame cadence or gameplay acceptance.')
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();check(args.build.resolve(),args.out.resolve())
