"""Actual Z80 four-way player-key selection; no SGT uploads or game acceptance."""
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

FILES=('scripts/presentation_player_variants_check.py','src/presentation_player_variants.asm','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')
INPUT_BYTES=42
ROW_BYTES=263


def fixtures():
    operations=[];metadata=bytearray(256);cursors=bytearray(2);pointer=0xA5A5;way=base=165;prior=None
    inputs=bytearray();expected=bytearray()
    keys=[bytes(7),bytes([255])*7]+[hashlib.sha256(f'player{i}'.encode()).digest()[:7] for i in range(80)]
    keys+=[bytes(1<<bit if i==field else 0 for i in range(7)) for field in range(7) for bit in range(8)]
    for page in (0,1):
        for key in keys:
            operations.extend(((1,page,key,False),(1,page,key,True),(1,page,key,False)))
        for key in keys[:6]*4:operations.append((1,page,key,True))
        operations.append((2,page,bytes(7),False))
        operations.append((0,page,bytes(7),False))
    operations.extend(((1,2,bytes(7),False),(0,255,bytes(7),False),(2,2,bytes(7),False)))
    for index,(op,page,key,publish) in enumerate(operations):
        seed=255;entry=bytes(32)
        if publish and prior is not None:
            seed,oldkey=prior;entry=bytes((1,))+oldkey+bytes((index+i)&255 for i in range(24))
            metadata[seed*32:seed*32+32]=entry
        inputs.extend(bytes((op,page,seed))+entry+key)
        carry=0
        if page not in (0,1):carry=1
        else:
            offset=page*128;way=0
            if op==2:
                for i in range(4):metadata[offset+i*32]=0
            elif op==1:
                matches=[i for i in range(4) if metadata[offset+i*32]==1 and metadata[offset+i*32+1:offset+i*32+8]==key]
                if matches:way=matches[0]
                else:
                    way=cursors[page]&3;cursors[page]=(way+1)&3;metadata[offset+way*32]=0;carry=1
            pointer=0xC080+offset+way*32;base=page*96+way*24;prior=(page*4+way,key)
        expected.extend(metadata+cursors+bytes((base,))+pointer.to_bytes(2,'little')+bytes((way,carry)))
    return bytes(inputs),bytes(expected)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('whole variant metadata/cursors/selection/carry differs or truncates')


def check(out):
    digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    producer={name:digest(ROOT/name) for name in FILES};inputs,expected=fixtures();count=len(inputs)//INPUT_BYTES
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
PAGE EQU $C200
p_pc_pointer EQU $C294
p_pc_key EQU $C4E4
start:
    DI
    LD SP,$F380
ready:
    JP ready
    INCLUDE "presentation_player_variants.asm"
    DS $C000-$,$FF
'''
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('player variant assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Variants.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_variant {{message}} {{puts stderr "PLAYER_VARIANT_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_variant {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*42}}] [expr {{$::index*42+41}}]]
    binary scan [string range $row 0 2] cu* config;lassign $config op page seed
    if {{$seed!=255}} {{debug write_block memory [expr {{0xC080+$seed*32}}] [string range $row 3 34]}}
    debug write memory 0xC200 $page;set ::key [string range $row 35 41];debug write_block memory 0xC4E4 $::key
    set target [lindex [list {syms['p_player_variant_default']} {syms['p_player_variant_lookup']} {syms['p_player_variant_uncached']}] $op]
    debug write_block memory 0xC760 [binary format cu* [list 205 [expr {{$target&255}}] [expr {{$target>>8}}] 195 102 199 24 254]]
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_variant target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    debug write_block memory 0xC080 [string repeat [binary format c 0] 256]
    debug write_block memory 0xE610 [binary format cu* {{0 0}}]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{0xC000 0x80 0xC180 0x80 0xC201 0x93 0xC296 1 0xC298 0x24C 0xC4EB 0x275 0xC768 0x1EA8 0xE613 0xD2D}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_variant "guard $address"}}
        }}
        if {{[debug read_block memory 0xC4E4 7] ne $::key || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_variant key-or-vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_variant abi}}
        puts -nonewline $::actual "[debug read_block memory 0xC080 256][debug read_block memory 0xE610 3][debug read_block memory 0xC294 2][debug read_block memory 0xC297 1][binary format cu [expr {{[reg F]&1}}]]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_variant
    }}}}
    dispatch_variant
}}}}]
after time 120 {{fail_variant watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Variants','-cart',str(artifact),'-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'PLAYER_VARIANT_FAIL' in log:raise ValueError('actual player variant capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed variant evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered variant timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('variant producers changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 selection only: four exact-key ways per generation, stateful metadata seeding, replacement/repeat/default/each key bit/invalid page and uncached fallback invalidation of all inactive ways, whole256-byte metadata/cursors/selected CID base/pointer/way/carry. Canonical/C6/heap/key/VRAM/SP/IFF/slot invariance. Seeded valid metadata models already-completed uploads; this does not prove runtime SGT upload/publication or game deadlines.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    check(**vars(p.parse_args()))
