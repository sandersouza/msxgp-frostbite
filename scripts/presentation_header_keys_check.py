"""Actual Z80 header-key packing against independent source-coordinate geometry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from presentation_constructors import HEADER_PARTS,header_key
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=('scripts/presentation_header_keys_check.py','scripts/presentation_constructors.py','src/presentation_header_keys.asm',
    'src/presentation_fast_hud.asm','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')
INPUT_BYTES=19
ROW_BYTES=43+180+6+1


def columns():
    # Source glyphs start atX22, 8source pixels apart: target41,53,... .
    parts={(1,0):0,(1,1):1,(5,0):2,(5,1):3,(5,2):4};result=[]
    for column in range(5,15):
        members=[]
        for glyph in range(6):
            start=41+12*glyph
            if start<column*8+8 and start+12>column*8:members.append((glyph,parts[start%8,column-start//8]))
        fragment=(members[0][1],members[1][1] if len(members)==2 else None)
        result.append((members[0][0],members[1][0] if len(members)==2 else 0,HEADER_PARTS.index(fragment)))
    return result


def packed(codes,level,upper,lower,sky):
    ids=[value//8 for value in codes];ids[8]=32
    if level>=20:ids[9]=33
    commands=columns();keys=[];table=bytearray()
    for first,second,kind in commands:
        four=(ids[first],ids[second] if kind in (1,3) else 0,ids[first+6],ids[second+6] if kind in (1,3) else 0)
        bits=sum(value<<(6*i) for i,value in enumerate(four))
        table.extend(bits.to_bytes(3,'little')+bytes((kind*16+sky,)))
    table.extend(bytes((upper,upper+lower*16,lower*16)))
    for band in range(3):
        for first,second,kind in commands:
            keys.append(header_key((ids[first],ids[second],ids[first+6],ids[second+6]),upper,lower,sky,kind,band))
    return bytes(table),b''.join(keys)


def fixtures():
    operations=[];base=bytes(i*16 for i in range(12))
    for field in range(12):
        for value in range(256):
            codes=bytearray(base);codes[field]=value;operations.append((0,19,5,6,4,0,0,bytes(codes)))
    for level in (0,19,20,255):
        for field in range(3):
            for value in range(1,16):
                colors=[5,6,4];colors[field]=value;operations.append((0,level,*colors,0,0,base))
    for field in range(3):
        for value in (0,16,255):
            colors=[5,6,4];colors[field]=value;operations.append((0,19,*colors,0,0,base))
    operations.extend((1,19,5,6,4,band,col,base) for band in range(3) for col in range(10))
    operations.extend((1,19,5,6,4,band,col,base) for band,col in ((3,0),(255,0),(0,10),(0,255)))
    table=bytes([165])*43;keys=bytes([165])*180;key=bytes([165])*6;inputs=bytearray();expected=bytearray()
    for op,level,upper,lower,sky,band,col,codes in operations:
        inputs.extend(bytes((op,level,upper,lower,sky,band,col))+codes);carry=0
        if op==0:
            if all(1<=color<=15 for color in (upper,lower,sky)):table,keys=packed(codes,level,upper,lower,sky);key=keys[-6:]
            else:carry=1
        elif band<3 and col<10:key=keys[(band*10+col)*6:(band*10+col+1)*6]
        else:carry=1
        expected.extend(table+keys+key+bytes((carry,)))
    return bytes(inputs),bytes(expected)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('whole header table/thirty keys/current key/carry differs or truncates')


def check(out):
    digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    producer={name:digest(ROOT/name) for name in FILES};inputs,expected=fixtures();count=len(inputs)//INPUT_BYTES
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    hud=(ROOT/'src/presentation_fast_hud.asm').read_text();glyph=hud[hud.index('p_fast_header_glyph:\n'):hud.index('p_fast_igloo_prepare:\n')]
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
p_h_index EQU $C238
p_h_y EQU $C23A
pfh_upper EQU $C247
pfh_lower EQU $C248
pfh_sky EQU $C249
p_h_codes EQU $C4C0
pt_glyphs EQU $C538
pf_key EQU $CC90
unit_op EQU $C2F0
unit_out EQU $C2F1
start:
    DI
    LD SP,$F380
ready:
    JP ready
unit_run:
    LD A,(unit_op)
    OR A
    JP NZ,p_template_header_key
    CALL p_template_header_keys
    RET C
    LD HL,$E680
    LD (unit_out),HL
    XOR A
    LD (p_h_y),A
.band:
    XOR A
    LD (p_h_index),A
.column:
    CALL p_template_header_key
    RET C
    LD HL,pf_key
    LD DE,(unit_out)
    LD BC,6
    LDIR
    LD (unit_out),DE
    LD HL,p_h_index
    INC (HL)
    LD A,(HL)
    CP 10
    JR NZ,.column
    LD HL,p_h_y
    INC (HL)
    LD A,(HL)
    CP 3
    JR NZ,.band
    OR A
    RET
    INCLUDE "presentation_header_keys.asm"
'''+glyph+'    DS $C000-$,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('header key assembler failed: '+compiled.stderr[-1600:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_HeaderKeys.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    guards=((0xC300,0xC4C0),(0xC4CC,0xC538),(0xC53C,0xC760),(0xC768,0xCC90),(0xCC96,0xE620),(0xE64B,0xE680),(0xE734,0xF340))
    guard_list=' '.join(f'{a} {b-a}' for a,b in guards);target=syms['unit_run']
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_header_keys {{message}} {{puts stderr "HEADER_KEYS_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_header_keys {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*19}}] [expr {{$::index*19+18}}]]
    binary scan [string range $row 0 6] cu* config;lassign $config op level upper lower sky band col
    debug write memory 0xC2F0 $op;debug write memory 0xC04B $level
    debug write_block memory 0xC247 [binary format cu* [list $upper $lower $sky]]
    debug write memory 0xC23A $band;debug write memory 0xC238 $col
    set ::codes [string range $row 7 18];debug write_block memory 0xC4C0 $::codes
    set ::source [debug read_block memory 0xC000 512]
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_header_keys target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {target&255} {target>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{{guard_list}}} {{if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_header_keys "guard $address"}}}}
        if {{[debug read_block memory 0xC000 512] ne $::source || [debug read_block memory 0xC4C0 12] ne $::codes || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_header_keys source-or-vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_header_keys abi}}
        puts -nonewline $::actual "[debug read_block memory 0xE620 43][debug read_block memory 0xE680 180][debug read_block memory 0xCC90 6][binary format cu [expr {{[reg F]&1}}]]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_header_keys
    }}}}
    dispatch_header_keys
}}}}]
after time 120 {{fail_header_keys watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_HeaderKeys','-cart',str(artifact),'-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'HEADER_KEYS_FAIL' in log:raise ValueError('actual header keys capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed header key evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index} {list(inputs[index*INPUT_BYTES:index*INPUT_BYTES+7])}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered header key timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('header key producers changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 key packing only. Source-coordinate glyph intersections derive ten fragment columns independently; every byte value in each of12 selectors, special-level boundaries, all15 palette values, all30 bands/columns and invalid palettes/indices. Whole43-byte table/thirty6-byte keys/current key/carry, source512/C6/heap/input/VRAM/SP/IFF/slot guards. No font pixel, runtime tile publication or frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    check(**vars(p.parse_args()))
