"""Actual-Z80 shared residency lifecycle across every finite floe template."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from presentation_shared_ice import SharedIce
from presentation_shared_ownership import audit_pool, physical
from render_build import symbols
from smoke import find_machine_profile, isolated_profile, validate_machine_profile


def check(build, out):
    meta = json.loads((build/'build.json').read_text())
    rom = (build/meta['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest() != meta['rom']['sha256']:
        raise ValueError('ROM identity changed')
    s = symbols(build/'presentation.sym')
    def logical(address, size):
        b = address//16384
        bank = b+3 if b<11 else b+242
        at = bank*16384+address%16384
        if address%16384+size>16384:
            raise ValueError('cross-bank logical record')
        return rom[at:at+size]
    deltas = rom[s['p_template_deltas']-16384:s['p_template_deltas']-16384+10]
    cases, requests = bytearray(), []
    for index in range(1280):
        phase, rest = divmod(index,160);d,root = divmod(rest,16)
        pointer = int.from_bytes(logical(s['p_template_template_index_offset']+index*2,2),'little')
        at = s['p_template_template_keys_offset']+pointer
        _, count = logical(at,2)
        data = logical(at+2,count*2)
        ids = [int.from_bytes(data[i:i+2],'little') for i in range(0,len(data),2)]
        page,row = divmod(index%8,4)
        color = 1+index%15
        for c in (color,color,1+color%15):
            cases.extend((page,row,root,deltas[d],88+phase,c))
            requests.append([(identifier,c) for identifier in ids])
    count = len(requests)
    out.mkdir(parents=True,exist_ok=False)
    (out/'cases.bin').write_bytes(cases)
    emulator = Path(shutil.which('openmsx')).resolve()
    profile = isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user = out/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/SharedIce.xml').write_bytes(profile)
    settings = out/'settings.xml'
    settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    def call(address):return bytes((205,address&255,address>>8))
    rpc = call(s['p_template_load'])+call(s['p_template_strip_publish'])+b'\x11\x00\xde'+call(s['q_decode_entry'])+b'\xc3\x6f\xc7\x18\xfe'
    script = f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_shared {{m}} {{puts stderr "SHARED_FAIL $m index=$::index";exit 1;return -code error $m}}
proc dispatch_shared {{}} {{
 if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
 binary scan [string range $::cases [expr {{$::index*6}}] [expr {{$::index*6+5}}]] cu* values
 lassign $values page row root delta y color
 debug write memory {s['PAGE']} $page
 debug write memory {s['p_w_row']} $row
 debug write memory {s['p_w_color']} $color
 set cache [expr {{0xDE00+($page*4+$row)*64}}]
 debug write memory 0xC767 [expr {{$cache&255}}];debug write memory 0xC768 [expr {{$cache>>8}}]
 set ::canonical [debug read_block memory 0xC000 128];set ::abi [debug read_block memory 0xC600 256]
 reg AF [expr {{$root*256}}];reg BC [expr {{$delta*256+$y}}];reg IX 0x1357;reg IY 0x2468;reg SP 0xF380;reg PC 0xC760
 set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {s['paced_frame_start']} {{}} {{debug remove_bp $::boot;debug break;after break {{
 if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_shared target}}
 debug write_block VRAM 0 [string repeat [binary format c 0] 16384]
 debug write_block memory 0xD000 [string repeat [binary format c 255] 2304]
 debug write_block memory 0xDE00 [string repeat [binary format c 0] 512]
 debug write_block memory 0xE800 [string repeat [binary format c 255] 2048]
 debug write_block memory 0xF000 [string repeat [binary format c 0] 576]
 debug write memory 0xF201 64
 debug write memory 0xF202 255
 debug write_block memory 0xF240 [string repeat [binary format c 165] 256]
 set ::slot [debug read ioports 168]
 debug write_block memory 0xC760 [binary format H* {rpc.hex()}]
 set VDP.too_fast_vram_access_callback {{fail_shared fast-vram}}
 debug set_bp 0xC76F {{}} {{debug break;after break {{
  if {{[debug read_block memory 0xC000 128] ne $::canonical || [debug read_block memory 0xC600 256] ne $::abi}} {{fail_shared source-mutated}}
  if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot || [reg IX]!=0x1357 || [reg IY]!=0x2468}} {{fail_shared abi}}
  if {{[debug read_block memory 0xF240 256] ne [string repeat [binary format c 165] 256] || [debug read memory 0xC231]!=0 || ([reg F]&1)}} {{fail_shared guard}}
  puts -nonewline $::actual "[debug read_block memory 0xE800 2624][debug read_block memory 0xDE00 512][debug read_block memory 0xD000 2304][debug read_block VRAM 0 16384]"
  puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
  incr ::index;dispatch_shared
 }}}}
 dispatch_shared
}}}}]
after time 600 {{fail_shared watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run = subprocess.run([str(emulator),'-setting',str(settings),'-machine','SharedIce',
        '-cart',str(build/meta['rom']['filename']),'-romtype','ASCII16','-script',str(out/'launch.tcl')],
        cwd=ROOT,env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
        capture_output=True,text=True,timeout=600)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode:
        raise ValueError((run.stdout+run.stderr)[-1500:])
    actual = (out/'actual.bin').read_bytes();stride=21824
    if len(actual) != count*stride:
        raise ValueError('incomplete target lifecycle stream')
    model = SharedIce()
    for index, request in enumerate(requests):
        page,row = cases[index*6:index*6+2]
        slots = model.replace(page,row,request)
        record = actual[index*stride:(index+1)*stride]
        pool,cache,keys,vram = record[:2624],record[2624:3136],record[3136:5440],record[5440:]
        audit_pool(pool,cache,keys)
        offset = 2432+(page*4+row)*16
        expected = [i+(64 if row<2 else 0) for i in slots]
        if pool[offset] != len(expected) or list(pool[offset+1:offset+1+len(expected)]) != expected:
            raise ValueError(f'physical clock allocation differs from independent model at {index}')
        for slot,color in enumerate(pool[2304:2432]):
            if not color:continue
            bank,identifier = physical(slot)
            group = bank+(3 if identifier&64 else 0)
            at = (group*64+(identifier&63))*6
            raw = int.from_bytes(keys[at:at+2],'little')
            pattern = logical(s['p_template_floe_patterns_offset']+raw*8,8)
            pg = bank*2048+identifier*8
            if vram[pg:pg+8] != pattern or vram[8192+pg:8192+pg+8] != bytes([(color<<4)|4])*8:
                raise ValueError(f'published physical key differs at {index}/{slot}')
    result = dict(complete=True,cases=count,templates=1280,colors=15,
        rom_sha256=meta['rom']['sha256'],scope='Controlled Z80 lifecycle/eviction/lookup and all published planes; not source-time or frame qualification.')
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();check(args.build.resolve(),args.out.resolve())
