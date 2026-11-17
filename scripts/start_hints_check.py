"""Compare real keyboard-driven pre-game/play pictures with the 1.0.0 control.

Requires openMSX with C-BIOS MSX1 and EU profiles; Python standard library only.
No target RAM, PC or state injection. Raw evidence stays in ignored outputs.
"""
import argparse
import collections
import json
import os
import re
from pathlib import Path
import shutil
import struct
import subprocess
import zlib

from artifact_hash import digest

RECORD = 3+128+128+16384
TEXT = ('F1: START ', 'F2: SELECT')
GLYPHS = 'F1: STAR2ELC'
PALETTE = ((0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),
           (125,118,252),(212,82,77),(66,235,245),(252,85,84),(255,121,120),
           (212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255))


def picture(video, page, sat):
    pixels = bytearray(256*192)
    for y in range(192):
        for col in range(32):
            tile = video[0x1800+page*1024+(y//8)*32+col]
            at = (y//64)*2048+tile*8+y%8
            pattern, color = video[at], video[8192+at]
            for bit in range(8):
                pixels[y*256+col*8+bit] = color>>4 if pattern & (128>>bit) else color&15
    # Compose the staged 16x16 SAT that presentation_commit is about to publish.
    sprites=[]
    for i in range(0,128,4):
        y,x,pattern,color=sat[i:i+4]
        if y==208:break
        sprites.append((y+1 if y<224 else y-255,x-(32 if color&128 else 0),pattern&252,color&15))
    for y in range(192):
        visible=[s for s in sprites if s[0]<=y<s[0]+16][:4]
        for sy,sx,pattern,color in reversed(visible):
            if not color:continue
            for dx in range(16):
                bits=video[0x3800+pattern*8+(y-sy)+(16 if dx>=8 else 0)]
                if 0<=sx+dx<256 and bits&(128>>(dx%8)):
                    pixels[y*256+sx+dx]=color
    return bytes(pixels)


def png(path, pixels):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    data=b''.join(b'\0'+b''.join(bytes(PALETTE[c])*3 for c in pixels[y*256:(y+1)*256])
                  for y in range(192) for _ in range(3))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',768,576,8,2,0,0,0))
                     +chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b''))


def run(delivery,out,family,changed,ticks,matrix=False):
    out.mkdir(parents=True)
    metadata=json.loads((delivery/'native-delivery-build.json').read_text())
    rom=delivery/'cartridge/FROSTBIT.ROM'
    if digest(rom.read_bytes())!=metadata['files']['cartridge/FROSTBIT.ROM']['sha256']:
        raise ValueError('ROM differs from its source build receipt')
    cold=json.loads((delivery/'cold/cold-image.json').read_text())
    ram=(delivery/'cold/cold-ram.bin').read_bytes()
    commit=ram.find(bytes.fromhex('CD154AAF3284E8'),0xE900,0xF000)
    if commit<0:raise ValueError('review the actual presentation-commit boundary')
    guards=''
    if changed:
        s=cold['hint_symbols']
        guards=f'''
debug set_bp {s['sh_load_font']} {{$::native_seen}} {{
 set page [debug read memory 0xC200]
 set names [debug read_block memory [expr {{0xC800+$page*1280}}] 256]
 binary scan $names cu* values
 foreach tile $values {{
  if {{$tile>=38+$page*64 && $tile<50+$page*64}} {{hint_fail "hint font aliases a live igloo tile"}}
 }}
}}
'''
    injection=''
    if matrix:
        injection='if {$::ticks>=900 && $::ticks<1412} {debug write memory 0xC04D [expr {($::ticks-900)/32}]} '
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set native_seen 0
set ticks 0
set frames [open {{{out/'frames.bin'}}} wb]
set timings [open {{{out/'timings.tsv'}}} w]
proc hint_fail {{message}} {{
 set f [open {{{out/'failure.txt'}}} w];puts $f $message;close $f;exit 1
}}
debug set_bp {cold['native_symbols']['nc_entry']} {{!$::native_seen}} {{
 if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{hint_fail "MSX1 target differs"}}
 set ::native_seen 1
}}
{guards}
debug set_bp 0xE9EE {{$::native_seen}} {{
 incr ::ticks
 {injection}
 switch $::ticks {{
  90 - 150 - 210 - 270 {{keymatrixdown 6 64}}
  98 - 158 - 218 - 278 {{keymatrixup 6 64}}
  330 {{keymatrixdown 6 32}}
  338 {{keymatrixup 6 32}}
  390 {{keymatrixdown 8 128}}
  450 {{keymatrixup 8 128;keymatrixdown 8 32}}
  458 {{keymatrixup 8 32}}
  510 {{keymatrixdown 8 16}}
  570 {{keymatrixup 8 16;keymatrixdown 8 1}}
  578 {{keymatrixup 8 1}}
  2100 {{keymatrixdown 6 64}}
  2108 {{keymatrixup 6 64}}
  2250 {{keymatrixdown 6 32}}
  2258 {{keymatrixup 6 32}}
 }}
 if {{$::ticks>={ticks}}} {{close $::frames;close $::timings;exit}}
}}
debug set_bp {commit+3} {{$::native_seen}} {{
 puts -nonewline $::frames [binary format cu* [list [expr {{$::ticks&255}}] [expr {{$::ticks>>8}}] [debug read memory 0xC200]]]
 puts -nonewline $::frames [debug read_block memory 0xF000 128]
 puts -nonewline $::frames [debug read_block VRAM 0x1B00 128]
 puts -nonewline $::frames [debug read_block VRAM 0 16384]
 puts $::timings "$::ticks\t[machine_info time]"
}}
after realtime 180 {{hint_fail "hint check watchdog"}}
'''
    if matrix:
        tcl=re.sub(r'keymatrix(?:down|up) 8 \d+', '', tcl)
    (out/'probe.tcl').write_text(tcl)
    settings=out/'settings.xml'
    settings.write_text('<!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    command=[shutil.which('openmsx'),'-setting',str(settings),'-machine',
             'C-BIOS_MSX1' if family=='ntsc' else 'C-BIOS_MSX1_EU',
             '-cart',str(rom),'-romtype','Normal','-script',str(out/'probe.tcl')]
    result=subprocess.run(command,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=210)
    (out/'emulator.log').write_text(result.stdout+result.stderr)
    raw=(out/'frames.bin').read_bytes()
    if result.returncode or (out/'failure.txt').exists() or not raw or len(raw)%RECORD:
        raise ValueError('emulator run failed: '+result.stderr[-1200:])
    return [(struct.unpack('<HB',raw[a:a+3]),raw[a+3:a+131],raw[a+131:a+259],raw[a+259:a+RECORD])
            for a in range(0,len(raw),RECORD)]


def check(baseline,delivery,out,ticks=3600,matrix=False):
    out=out.resolve()
    if out.exists():raise ValueError('fresh evidence output required')
    out.mkdir(parents=True)
    original=(baseline/'cold/cold-ram.bin').read_bytes()
    modified=(delivery/'cold/cold-ram.bin').read_bytes()
    for lo,hi in ((0x4014,0x40B1),(0x7C51,0x7CF2)):
        if original[lo:hi]!=modified[lo:hi]:raise ValueError('immutable native assets overwritten')
    summary={}
    for family in ('ntsc','pal'):
        control=run(baseline.resolve(),out/(family+'-control'),family,False,ticks,matrix)
        actual=run(delivery.resolve(),out/family,family,True,ticks,matrix)
        known=collections.defaultdict(set)
        for (tick,page),state,sat,video in control:
            known[state].add(picture(video,page,sat))
        matches=shown=hidden=0;variations=set();examples={};active_ticks=[];stages=set();stage_pages=set()
        control_ticks=[tick for (tick,_),state,_,_ in control if tick>=360 and not state[0x46]]
        for (tick,page),state,sat,video in actual:
            pixels=picture(video,page,sat)
            hint=state[0x46]!=0 and state[0x4D]==255
            if matrix and 900<=tick<1412 and state[0x4D]<16:
                if any(pixels[y*256+x]==14 for y in range(24,48) for x in range(176,224)):
                    stages.add(state[0x4D]);stage_pages.add((state[0x4D],page))
            visible=b''.join(video[0x1800+page*1024+row*32+21:0x1800+page*1024+row*32+31] for row in (1,2))
            if hint:
                expected=bytes(38+page*64+GLYPHS.index(c) for line in TEXT for c in line)
                if visible!=expected:raise ValueError(f'{family}: misaligned/missing hint at tick {tick}')
                shown+=1;variations.add(state[0]);examples.setdefault('waiting',pixels)
                if state[0]:examples.setdefault('selected',pixels)
            else:
                if any(38+page*64<=tile<50+page*64 for tile in visible):
                    raise ValueError(f'{family}: hint survives during gameplay at tick {tick}')
                hidden+=1
                if tick>=360:examples.setdefault('playing',pixels)
                if tick>=360:active_ticks.append(tick)
            if state in known:
                if hint:
                    def masked(p):return b''.join(p[y*256:y*256+168]+p[y*256+248:(y+1)*256] if 8<=y<24 else p[y*256:(y+1)*256] for y in range(192))
                    if masked(pixels) not in {masked(p) for p in known[state]}:
                        raise ValueError(f'{family}: pre-game picture changed outside text at tick {tick}')
                elif pixels not in known[state]:
                    raise ValueError(f'{family}: active picture differs at tick {tick}')
                matches+=1
        if not shown or not hidden or variations!={0,1,2,3} or matches<0.95*len(actual):
            raise ValueError(f'{family}: insufficient lifecycle/control coverage {shown,hidden,variations,matches}')
        if matrix and (stages!=set(range(16)) or len(stage_pages)!=32):raise ValueError('all sixteen igloo stages required')
        for name,pixels in examples.items():png(out/f'{family}-{name}.png',pixels)
        cadence=(len(active_ticks)-1)/(active_ticks[-1]-active_ticks[0])
        control_cadence=(len(control_ticks)-1)/(control_ticks[-1]-control_ticks[0])
        summary[family]=dict(shown=shown,hidden=hidden,matching_source_pictures=matches,variations=sorted(variations),
                             igloo_stages=sorted(stages),igloo_stage_pages=len(stage_pages),committed_pictures=len(actual),control_pictures=len(control),
                             play_pictures_per_vblank=cadence,control_pictures_per_vblank=control_cadence,
                             cadence_change_percent=100*(cadence/control_cadence-1))
        print(family,summary[family],flush=True)
    result=dict(complete=True,keyboard_only=not matrix,emulator_state_injected=matrix,physical_hardware=False,families=summary)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','delivery','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--ticks',type=int,default=3600)
    p.add_argument('--igloo-matrix',action='store_true',help='controlled renderer diagnostic: inject stages 0..15, not natural gameplay evidence')
    a=p.parse_args();check(a.baseline,a.delivery,a.out,a.ticks,a.igloo_matrix)
