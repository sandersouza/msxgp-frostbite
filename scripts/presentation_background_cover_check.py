"""Actual Z80 coverage predicate for complete floe NAME rows; no frame verdict."""
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

FILES=('scripts/presentation_background_cover_check.py','src/presentation_background_cover.asm','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')
PALETTE=bytes((index*7)%15+1 for index in range(256))
INPUT_BYTES=7


def covered(row,coarse,colors,blank):
    if blank or coarse not in (0,1) or not 0<=row<24:return False
    return any(PALETTE[colors[source_row]]!=4 and (167-source_row*26+coarse)//8<=row<=(173-source_row*26+coarse)//8 for source_row in range(4))


def fixtures():
    operations=[(row,coarse,bytes([color])*4,blank) for row in range(24) for coarse in (0,1) for color in range(256) for blank in (0,1)]
    for row in range(24):
        for coarse in (0,1):
            for owner in range(4):
                colors=bytearray([PALETTE.index(4)])*4;colors[owner]=PALETTE.index(15)
                operations.append((row,coarse,bytes(colors),0))
    operations.extend((row,coarse,bytes(4),0) for row,coarse in ((24,0),(255,0),(11,2),(11,255)))
    return b''.join(bytes((row,coarse))+colors+bytes((blank,)) for row,coarse,colors,blank in operations),bytes(int(covered(*row)) for row in operations)


def check(out):
    digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    producer={name:digest(ROOT/name) for name in FILES};inputs,expected=fixtures();count=len(expected)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
p_w_coarse EQU $C223
p_bg_profile EQU $C2E0
start:
    DI
    LD SP,$F380
ready:
    JP ready
    INCLUDE "presentation_background_cover.asm"
p_world_color_data:
'''+''.join('    DB '+','.join(map(str,PALETTE[i:i+16]))+'\n' for i in range(0,256,16))+'    DS $C000-$,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('coverage assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Cover.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_cover {{message}} {{puts stderr "COVER_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_cover {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set data [string range $::cases [expr {{$::index*7}}] [expr {{$::index*7+6}}]]
    binary scan $data cu* config
    lassign $config row coarse c0 c1 c2 c3 blank
    debug write memory 0xC223 $coarse;debug write memory 0xC2E0 [expr {{$blank*32}}]
    debug write_block memory 0xC02B [string range $data 2 5]
    set ::before [debug read_block memory 0xC000 0x3340]
    reg AF [expr {{$row*256}}];reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_cover target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['p_template_background_covered']&255} {syms['p_template_background_covered']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        if {{[debug read_block memory 0xC000 0x3340] ne $::before || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_cover mutation}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_cover abi}}
        puts -nonewline $::actual [binary format cu [expr {{[reg F]&1}}]]
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_cover
    }}}}
    dispatch_cover
}}}}]
after time 120 {{fail_cover watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Cover','-cart',str(artifact),'-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'COVER_FAIL' in log:raise ValueError('actual coverage capture failed: '+log[-1400:])
    if (out/'actual.bin').read_bytes()!=expected or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed/incorrect coverage evidence')
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered coverage timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('coverage producers changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 covered-row predicate for all24 rows/two coarse phases/256 synthetic palette inputs/blank states, isolated visible floe owners, plus invalid row/coarse. WholeC000-F33F RAM/VRAM/SP/IFF/slot invariance. Synthetic palette deliberately maps varied raw indices to every target color. Complete-row integration and frame acceptance separate.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    check(**vars(p.parse_args()))
