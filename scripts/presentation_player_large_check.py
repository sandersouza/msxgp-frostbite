"""Synthetic eight-pattern P0 proof on an identified immutable game cartridge."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from presentation_build import validate_rom
from presentation_fixed_ownership import audit_active
from presentation_sprites import expand_pair
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=('scripts/presentation_player_large_check.py','scripts/presentation_build.py','scripts/presentation_fixed_ownership.py',
    'scripts/presentation_sprites.py','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')
ROW_BYTES=32768+256+32+7


def expected(page):
    before=bytearray([165])*16384
    active=(1-page)*24
    for sprite in range(4):before[0x1B00+sprite*4:0x1B04+sprite*4]=bytes((0,40+sprite*24,(active+sprite)*4,2))
    before[0x1B10]=208;after=bytearray(before);sat=bytearray()
    for band,top in enumerate((32,48)):
        for plane,mask in enumerate((192,48,12,3)):
            pattern=bytearray(32)
            for row in range(16):
                source_row=top+row-40
                if 0<=source_row<24:pattern[row],pattern[row+16]=expand_pair(mask,0)
            slot=page*24+band*4+plane;at=0x3800+slot*32;after[at:at+32]=pattern
            sat.extend(bytes(((top-1)&255,104,slot*4,2+plane)))
    metadata=bytearray([1])*256
    for way in range(4):metadata[page*128+way*32]=0
    pointer=0xC080+page*128
    fields=bytes((8,0,0,page*96))+pointer.to_bytes(2,'little')+bytes(1)
    return bytes(before+after+metadata+sat+fields)


def verify_case(row,wanted,page):
    if len(row)!=ROW_BYTES or len(wanted)!=ROW_BYTES or page not in (0,1):raise ValueError('complete large P0 page evidence required')
    regs=bytearray(8);regs[2]=7-page
    audit_active(row[:16384],row[16384:32768],regs)
    if row!=wanted:
        at=next(i for i,(a,b) in enumerate(zip(row,wanted)) if a!=b)
        raise ValueError(f'large P0 page{page}: full VRAM/metadata/SAT/fallback fields differ at{at}')


def check(out,build_dir):
    digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    producer={name:digest(ROOT/name) for name in FILES};build_dir=Path(build_dir).resolve();meta=json.loads((build_dir/'build.json').read_text())
    artifact=build_dir/meta['rom']['filename']
    if validate_rom(artifact.read_bytes()) or digest(artifact)!=meta['rom']['sha256'] or meta['profile'].get('player_variants_per_generation')!=4:raise ValueError('identified four-way native cartridge required')
    consumed={str(path):digest(path) for path in (build_dir/'build.json',build_dir/'presentation.sym',artifact)}
    # An immutable earlier ROM is deliberately accepted as a negative control.
    # Its archived producer closure is retained as input metadata, not relabeled
    # as the current working tree or a clean source/build acceptance.
    syms=symbols(build_dir/'presentation.sym');out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    wanted=expected(0)+expected(1);(out/'expected.bin').write_bytes(wanted)
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_LargeP0.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    target=syms['p_player_emit_all'];script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_large {{message}} {{puts stderr "LARGE_P0_FAIL $message page=$::index";exit 1;return -code error $message}}
proc dispatch_large {{}} {{
    if {{$::index==2}} {{close $::actual;close $::timing;exit;return}}
    set page $::index
    debug write memory 0xC200 $page;debug write memory 0xC066 64;debug write memory 0xC064 19;debug write memory 0xC04D 0
    debug write memory 0xC223 0;debug write memory 0xC231 0
    debug write memory 0xC250 0;debug write_block memory 0xC251 [binary format cu* {{0 196}}]
    debug write memory 0xC260 4;debug write memory 0xC261 40;debug write memory 0xC262 63;debug write memory 0xC277 48
    debug write_block memory 0xC280 [binary format cu* {{255 0}}]
    debug write memory 0xC293 1;debug write memory 0xC297 3
    set pointer [expr {{0xC080+$page*128+96}}];debug write memory 0xC294 [expr {{$pointer&255}}];debug write memory 0xC295 [expr {{$pointer>>8}}]
    debug write memory 0xC29B 1;debug write memory 0xC29C 255
    debug write_block memory 0xC080 [string repeat [binary format c 1] 256];debug write memory $pointer 0
    debug write_block memory 0xE610 [binary format cu* [list 0 0 [expr {{$page*96+72}}] 8]]
    debug write_block memory 0xC480 "[string repeat [binary format cu 192] 24][string repeat [binary format cu 48] 24][string repeat [binary format cu 12] 24][string repeat [binary format cu 3] 24]"
    debug write_block memory 0xC4E0 [binary format cu* {{2 3 4 5}}]
    debug write_block memory 0xC400 [string repeat [binary format c 165] 128]
    debug write_block memory 0xE800 [string repeat [binary format c 165] 0xB40]
    debug write_block VRAM 0 [string repeat [binary format c 165] 16384]
    set active [expr {{(1-$page)*24}}]
    for {{set sprite 0}} {{$sprite<4}} {{incr sprite}} {{
        debug write_block VRAM [expr {{0x1B00+$sprite*4}}] [binary format cu* [list 0 [expr {{40+$sprite*24}}] [expr {{($active+$sprite)*4}}] 2]]
    }}
    debug write VRAM 0x1B10 208
    set ::before [debug read_block VRAM 0 16384];set ::source [debug read_block memory 0xC000 128];set ::abi [debug read_block memory 0xC600 256]
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['paced_frame_start']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_large target}}
    set ::slot [debug read ioports 168]
    set VDP.too_fast_vram_access_callback {{fail_large spacing}}
    debug write_block memory 0xC760 [binary format cu* {{62 2 50 0 112 205 {target&255} {target>>8} 195 107 199 24 254}}]
    debug set_bp 0xC76B {{}} {{debug break;after break {{
        if {{[debug read_block memory 0xC000 128] ne $::source || [debug read_block memory 0xC600 256] ne $::abi || [debug read_block memory 0xE800 0xB40] ne [string repeat [binary format c 165] 0xB40]}} {{fail_large source-abi-heap}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_large caller}}
        set fields [binary format cu* [list [debug read memory 0xC250] [debug read memory 0xC293] [debug read memory 0xC297] [debug read memory 0xE612] [debug read memory 0xC294] [debug read memory 0xC295] [debug read memory 0xC231]]]
        puts -nonewline $::actual "$::before[debug read_block VRAM 0 16384][debug read_block memory 0xC080 256][debug read_block memory 0xC400 32]$fields"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_large
    }}}}
    dispatch_large
}}}}]
after time 120 {{fail_large watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_LargeP0','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=120)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'LARGE_P0_FAIL' in log:raise ValueError('large P0 native capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(wanted) or (out/'expected.bin').read_bytes()!=wanted:raise ValueError('incomplete/changed large P0 evidence')
    for page in (0,1):
        row=actual[page*ROW_BYTES:(page+1)*ROW_BYTES]
        verify_case(row,wanted[page*ROW_BYTES:(page+1)*ROW_BYTES],page)
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=2 or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete large P0 timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()) or any(digest(name)!=value for name,value in consumed.items()):raise ValueError('large P0 producers/inputs changed')
    report={'complete':True,'cases':2,'patterns_each':8,'full_rectangles_per_line':4,'max_cycles_including_rpc':max(row[1] for row in times),
        'rom_sha256':digest(artifact),'archived_build_source_files':meta['source_files'],'producer_files':producer,'input_files':consumed,
        'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Synthetic actual native eight-pattern P0 emission on both inactive generations, starting from way3 with other ways valid and opposite-generation sprites active. Wholebefore/after16KiB VRAM/metadata/eight SAT entries/fallback fields; active full patterns, source128/C6/heap/SP/IFF/slot/29IO preserved. Immutable earlier ROMs may be tested as explicitly identified negatives; no current-tree build/source-game/whole-frame acceptance is implied.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','patterns_each','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True)
    check(**vars(p.parse_args()))
