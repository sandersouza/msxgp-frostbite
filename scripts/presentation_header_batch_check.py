"""Actual complete live-header masks/tiles against independent synthetic font."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from presentation_constructors import HEADER_PARTS
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=('scripts/presentation_header_batch_check.py','scripts/presentation_constructors.py','src/presentation_header_batch.asm',
    'src/presentation_header.asm','src/presentation_typed.asm','src/movement.asm','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')
INPUT_BYTES=10
ROW_BYTES=238


def fixtures():
    font=bytes(((glyph*71+part*39+row*17)^(glyph<<(row%3)))&255 for glyph in range(34) for part in range(5) for row in range(8))
    inputs=bytearray();expected=bytearray();cache=bytearray([165])*160;keys=bytearray(60)
    operations=[((0,0,0,0),0,0,0,1,2,3)]
    for first in range(34):
        for second in range(34):
            glyphs=(first,second,(first+17)%34,(second+11)%34)
            for part,(left,right) in enumerate(HEADER_PARTS):
                for band in range(3):
                    index=len(operations);column=index%10
                    upper=1+(first+part)%15;lower=1+(second+band)%15;sky=1+(column+part)%15
                    operations.append((glyphs,part,column,band,upper,lower,sky))
    for column in range(10):
        for part in range(5):
            for repeat in range(6):
                operations.append(((1,8,17,29),part,column,repeat%3,1+repeat,2+repeat,3+repeat))
    for glyphs,part,column,band,upper,lower,sky in operations:
        left,right=HEADER_PARTS[part]
        masks=bytes(font[(glyphs[pair]*5+left)*8+y]|(0 if right is None else font[(glyphs[pair+1]*5+right)*8+y]) for pair in (0,2) for y in range(8))
        inputs.extend(bytes((*glyphs,part,column,band,upper,lower,sky)))
        cache[column*16:column*16+16]=masks;keys[column*6:column*6+6]=bytes((1,*glyphs,part))
        tile=bytearray(8)+bytearray([sky*17])*8
        if band==0:tile[3:8]=masks[:5];tile[11:16]=bytes([upper*16+sky])*5
        elif band==1:
            tile[:3]=masks[5:8];tile[7]=masks[8];tile[8:11]=bytes([upper*16+sky])*3;tile[15]=lower*16+sky
        else:tile[:7]=masks[9:16];tile[8:15]=bytes([lower*16+sky])*7
        expected.extend(cache+tile+keys+bytes(2))
    return bytes(inputs),bytes(expected),font


def verify_cache_timing(inputs,times):
    keys={};hits=[]
    if len(times)!=len(inputs)//INPUT_BYTES:raise ValueError('complete ordered timing required')
    for index,row in enumerate(times):
        data=inputs[index*INPUT_BYTES:(index+1)*INPUT_BYTES];key=bytes(data[:5]);column=data[5]
        if row[0]!=index or row[1]<=0:raise ValueError('ordered positive timing required')
        if keys.get(column)==key:hits.append(row[1])
        keys[column]=key
    if len(hits)<100 or max(hits)>1800:raise ValueError('repeated unchanged font masks must meet1800-cycle microbudget')
    return {'mask_cache_hits':len(hits),'max_mask_cache_hit_cycles_including_rpc':max(hits),'mask_cache_hit_microbudget':1800}


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:
        mismatch=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),None)
        raise ValueError(f'whole font cache/tile/carry/error differs or truncates at{mismatch}')


def check(out):
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest();producer={name:sha(ROOT/name) for name in FILES}
    inputs,expected,font=fixtures();count=len(inputs)//INPUT_BYTES;out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected);(out/'font.bin').write_bytes(font)
    typed=(ROOT/'src/presentation_typed.asm').read_text()
    fragments=typed[typed.index('pt_header_fragment:\n'):typed.index('    IFDEF WITH_PRESENTATION_HEADER_FAST\n',typed.index('pt_header_fragment:\n'))]
    colors=typed[typed.index('pt_header_color:\n'):typed.index('pt_header_copy:\n')]
    movement=(ROOT/'src/movement.asm').read_text();mapper=movement[movement.index('map_page2:\n'):movement.index('set_address:\n')]
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
pt_key EQU $CC90
pt_tile EQU $C520
pt_mask EQU $C530
pt_glyphs EQU $C538
pt_bank EQU $C53C
pt_kind EQU $C53D
pt_pair EQU $C53E
pt_error EQU $C53F
p_h_index EQU $C238
p_h_y EQU $C23A
p_static_header_data EQU $8000
p_static_header_bank EQU 255
start:
    DI
    LD SP,$F380
    CALL map_page2
ready:
    JP ready
unit_run:
    LD IX,$E630
    CALL p_template_header_mask_column
    RET C
    CALL p_template_header_live_construct
    LD A,0
    ADC A,0
    LD ($C2F0),A
    RET
pt_fail:
    LD A,1
    LD (pt_error),A
    SCF
    RET
    INCLUDE "presentation_header.asm"
    INCLUDE "presentation_header_batch.asm"
'''+fragments+colors+mapper+'    DS $8000-$,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    run=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('header batch assembler failed: '+run.stderr[-1500:])
    artifact.write_bytes(artifact.read_bytes()+bytes([255])*(254*16384)+font+bytes([255])*(16384-len(font)))
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_HeaderBatch.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    guards=((0xC000,0xC238),(0xC239,0xC23A),(0xC23B,0xC2F0),(0xC2F1,0xC520),(0xC530,0xC538),(0xC540,0xC760),
        (0xC768,0xCC90),(0xCC96,0xE630),(0xE633,0xE650),(0xE6F0,0xE700),(0xE73C,0xF340))
    spans=' '.join(f'{a} {b-a}' for a,b in guards)
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_batch {{message}} {{puts stderr "HEADER_BATCH_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_batch {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*10}}] [expr {{$::index*10+9}}]]
    set ::glyphs [string range $row 0 3];debug write_block memory 0xC538 $::glyphs
    binary scan [string range $row 4 9] cu* config;lassign $config part column band upper lower sky
    debug write memory 0xE632 $part;debug write memory 0xC238 $column;debug write memory 0xC23A $band
    set colors [expr {{$band==0 ? $upper : $band==1 ? ($upper|($lower<<4)) : ($lower<<4)}}]
    set ::key [binary format cu* [list 0 0 0 $colors $sky [expr {{16+$band}}]]]
    debug write_block memory 0xCC90 $::key
    debug write_block memory 0xC520 [string repeat [binary format c 165] 16]
    debug write memory 0xC2F0 255
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_batch target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    debug write_block memory 0xE700 [string repeat [binary format c 0] 60]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['unit_run']&255} {syms['unit_run']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{{spans}}} {{if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_batch "guard $address"}}}}
        if {{[debug read_block memory 0xCC90 6] ne $::key || [debug read_block memory 0xC538 4] ne $::glyphs}} {{fail_batch key-or-glyphs}}
        if {{[debug read_block VRAM 0 16384] ne $::vram || [reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_batch abi-or-vram}}
        puts -nonewline $::actual "[debug read_block memory 0xE650 160][debug read_block memory 0xC520 16][debug read_block memory 0xE700 60][debug read_block memory 0xC2F0 1][debug read_block memory 0xC53F 1]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_batch
    }}}}
    dispatch_batch
}}}}]
after time 180 {{fail_batch watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_HeaderBatch','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=240)
    log=run.stdout+run.stderr;(out/'emulator.log').write_text(log)
    if run.returncode or 'HEADER_BATCH_FAIL' in log:raise ValueError('header batch native failed: '+log[-1500:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed batch evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered batch timing')
    timing=verify_cache_timing(inputs,times)
    if any(sha(ROOT/name)!=value for name,value in producer.items()):raise ValueError('batch producers changed')
    report={'complete':True,'cases':count,**timing,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,
        'rom_sha256':sha(artifact),'emulator_sha256':sha(emulator),'artifacts':{p.name:sha(p) for p in out.iterdir() if p.is_file()},
        'frame_deadline_accepted':False,'scope':'Actual Z80 complete160-byte live-mask cache/16-byte tile/carry/error against independent synthetic34-glyph/five-part font. Every upper/lower glyph pair and all three bands; source/key/glyph/ABI/heap/VRAM/slot guards. Not original-font/game integration or frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);check(**vars(p.parse_args()))
