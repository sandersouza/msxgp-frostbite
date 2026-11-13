"""Real-Z80 prepared strips: all1280 templates, eight owners, all15 colors."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def check(build,out):
    meta=json.loads((build/'build.json').read_text());rom=(build/meta['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=meta['rom']['sha256']:raise ValueError('ROM identity changed')
    s=symbols(build/'presentation.sym')
    def logical(a,n):
        bank=a//16384;physical=bank+3 if bank<11 else bank+242
        if a%16384+n>16384:raise ValueError('cross-bank record')
        return rom[physical*16384+a%16384:physical*16384+a%16384+n]
    def far(a):
        bank=a//16384;physical=bank+3 if bank<11 else bank+242
        return (0x8000+a%16384).to_bytes(2,'little')+bytes([physical])
    deltas=rom[s['p_template_deltas']-16384:s['p_template_deltas']-16384+10]
    cases,expected=bytearray(),bytearray();owners=[]
    for page in range(2):
        for row,base in enumerate((25,9,35,19)):
            bank=2 if row<2 else 1
            owners.extend((bank*2048+(base+64*page)*8,0xC1D1+(page*4+row)*4,0xC1F1+page*4+row))
            patterns=bytearray(112)
            for index in range(1280):
                phase,rest=divmod(index,160);d,root=divmod(rest,16)
                offset=int.from_bytes(logical(s['p_template_template_index_offset']+index*2,2),'little')
                address=s['p_template_template_keys_offset']+offset
                program,count=logical(address,2)
                raw=logical(address+2,count*2)
                for slot in range(count):
                    identifier=int.from_bytes(raw[slot*2:slot*2+2],'little')
                    patterns[slot*8:slot*8+8]=logical(s['p_template_floe_patterns_offset']+identifier*8,8)
                color=1+index%15
                for c in (color,color,1+color%15):
                    cases.extend((page,row,root,deltas[d],88+phase,c))
                    expected.extend(patterns+bytes([(c<<4)|4])*128+far(address+2)+bytes([count,c,program,count,0,0]))
    n=len(cases)//6;stride=249
    if len(expected)!=n*stride:raise ValueError('incomplete expected records')
    out.mkdir(parents=True,exist_ok=False)
    (out/'cases.bin').write_bytes(cases);(out/'expected.bin').write_bytes(expected)
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/PreparedIce.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    def call(a):return bytes((205,a&255,a>>8))
    rpc=call(s['pk_load_entry'])+call(s['p_template_strip_publish'])+b'\xc3\x69\xc7\x18\xfe'
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
set owners {{{' '.join(map(str,owners))}}}
proc fail_packet {{m}} {{puts stderr "PACKET_FAIL $m case=$::index";exit 1;return -code error $m}}
proc dispatch_packet {{}} {{
 if {{$::index=={n}}} {{close $::actual;close $::timing;exit;return}}
 binary scan [string range $::cases [expr {{$::index*6}}] [expr {{$::index*6+5}}]] cu* values
 lassign $values page row root delta y color
 debug write memory {s['PAGE']} $page;debug write memory {s['p_w_row']} $row;debug write memory {s['p_w_color']} $color
 set ::owner [expr {{($page*4+$row)*3}}]
 set ::canonical [debug read_block memory 0xC000 128];set ::abi [debug read_block memory 0xC600 256]
 reg AF [expr {{$root*256}}];reg BC [expr {{$delta*256+$y}}];reg IX 0x1357;reg IY 0x2468;reg SP 0xF380;reg PC 0xC760
 set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {s['paced_frame_start']} {{}} {{debug remove_bp $::boot;debug break;after break {{
 if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_packet target}}
 debug write_block VRAM 0 [string repeat [binary format c 0] 16384]
 debug write_block memory 0xC1D1 [string repeat [binary format c 0] 32]
 debug write_block memory 0xC1F1 [string repeat [binary format c 255] 8]
 debug write_block memory 0xE800 [string repeat [binary format c 165] 2880]
 set ::slot [debug read ioports 168]
 debug write_block memory 0xC760 [binary format H* {rpc.hex()}]
 set VDP.too_fast_vram_access_callback {{fail_packet fast-vram}}
 debug set_bp 0xC769 {{}} {{debug break;after break {{
  if {{[debug read_block memory 0xC000 128] ne $::canonical || [debug read_block memory 0xC600 256] ne $::abi}} {{fail_packet source}}
  if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot || [reg IX]!=0x1357 || [reg IY]!=0x2468}} {{fail_packet abi}}
  if {{[debug read_block memory 0xE800 2880] ne [string repeat [binary format c 165] 2880] || [debug read memory 0xC231]!=0}} {{fail_packet guard}}
  set pg [lindex $::owners $::owner];set record [lindex $::owners [expr {{$::owner+1}}]];set color [lindex $::owners [expr {{$::owner+2}}]]
  puts -nonewline $::actual "[debug read_block VRAM $pg 112][debug read_block VRAM [expr {{$pg+8192}}] 128][debug read_block memory $record 4][debug read_block memory $color 1][debug read_block memory {s['p_tl_program']} 1][debug read_block memory {s['p_tl_count']} 1][binary format cu* [list [expr {{[reg F]&1}}] [debug read memory {s['pt_error']}]]]"
  puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
  incr ::index;dispatch_packet
 }}}}
 dispatch_packet
}}}}]
after time 6000 {{fail_packet watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','PreparedIce','-cart',str(build/meta['rom']['filename']),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=600)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError((run.stdout+run.stderr)[-1500:])
    actual=(out/'actual.bin').read_bytes()
    if actual!=expected:
        first=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),min(len(actual),len(expected)))
        raise ValueError(f'prepared strip differs/truncates at case {first//stride} byte {first%stride}')
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=n or any(row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete target timings')
    result=dict(complete=True,cases=n,templates=1280,owners=8,colors=15,rom_sha256=meta['rom']['sha256'],
        max_cycles_including_loader_rpc=max(row[1] for row in times),
        scope='Controlled complete finite strips, full16-slot CGT growth, owner publication and original ABI; not full-frame cadence or gameplay acceptance.')
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();check(args.build.resolve(),args.out.resolve())
