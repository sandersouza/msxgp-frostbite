"""Actual Z80 shoreline body planes against the original-space player model.

Generated unit wrappers consume the actual setup/store/general assembly spans;
source-derived table selections are crossed with explicitly derived geometry.
No whole-game, paced-frame or original-raster acceptance is implied.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from environment import ROOT,verified_tool
from graphics_mapping import palette_map
from presentation_model import player
from presentation_palette import audit_palette
from presentation_source_cases import collect,verify_files,FILES as SOURCE_FILES
from presentation_sprites import tables
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=tuple(dict.fromkeys((*SOURCE_FILES,'scripts/presentation_player_body_check.py','src/presentation_sprites.asm',
    'scripts/presentation_sprites.py','scripts/presentation_model.py','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')))
ROW_BYTES=104
INPUT_BYTES=7


def planes(rows,reflect,coarse,palette):
    colors=[];result=bytearray(96);top=255;bottom=165
    for row in rows:
        mask=row['pattern']
        if reflect:mask=int(f'{mask:08b}'[::-1],2)
        if not mask:continue
        color=palette[row['color']]
        if color not in colors:
            if len(colors)==4:raise ValueError('player model exceeds the four-plane body domain')
            colors.append(color)
        ys=[row['y']-7+int(coarse and row['y']>=57)]
        if coarse and row['y']==56:ys.append(50)
        for y in ys:
            if top==255:top=y
            at=y-top
            if not 0<=at<24:raise ValueError('player model exceeds24 source-plane rows')
            bottom=y;result[colors.index(color)*24+at]|=mask
    return bytes((len(colors),top,bottom))+bytes(colors+[165]*(4-len(colors)))+result+bytes(1)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('whole body extents/colors/planes/fault differ or truncate')


def fixtures(domain,rom,palette):
    selectors=sorted({(case['ram'][0x6E],case['ram'][0x6B],case['ram'][0x70]) for case in domain['cases']})
    inputs=bytearray();expected=bytearray()
    for pose,displacement,offset in selectors:
        for y in range(19,30):
            for reflect in (0,8):
                ram=bytearray(128);ram[0x64]=y;ram[0x66]=24;ram[0x6E]=pose;ram[0x6B]=displacement;ram[0x70]=offset;ram[0x6C]=reflect
                rows=player(rom,bytes(ram))['rows']
                for coarse in (0,1):
                    wanted=planes(rows,bool(reflect),bool(coarse),palette)
                    for x in (24,83):
                        inputs.extend(bytes((y,x,pose,displacement,offset,reflect,coarse)));expected.extend(wanted)
    return bytes(inputs),bytes(expected),selectors


def check(out,*,fast=False,max_body_cycles=0):
    if type(max_body_cycles)is not int or max_body_cycles<0:raise ValueError('nonnegative component budget required')
    names=FILES+(('src/presentation_player_shore.asm',) if fast else ())
    digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    producer={name:digest(ROOT/name) for name in names};domain=collect()
    palette_path=ROOT/'outputs/presentation/palette-canonical-a';measured=audit_palette(palette_path);mapped=palette_map(measured)
    rom_path=ROOT/'references/roms/frostbite.bin';rom=rom_path.read_bytes()
    consumed={**domain['files'],str(rom_path.relative_to(ROOT)):digest(rom_path)}
    consumed.update({str(p.relative_to(ROOT)):digest(p) for p in palette_path.rglob('*') if p.is_file()})
    inputs,expected,selectors=fixtures(domain,rom,mapped);count=len(inputs)//INPUT_BYTES
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected);(out/'original-data.bin').write_bytes(rom[0xC00:])
    sprite=tables(rom,measured)
    for name in ('colors','reverse','holds','tails'):(out/f'{name}.bin').write_bytes(sprite[name])
    source=(ROOT/'src/presentation_sprites.asm').read_text()
    equates='\n'.join(re.findall(r'^p_p_\w+ EQU .+$',source,re.M))
    preparation=source[source.index('p_player_prepare:'):source.index('.rows_done:\n')]
    if fast:
        preparation=preparation[:preparation.index('    ; Fully visible body,')]+f'    CALL p_player_shore_stream\n'
    preparation+='\n.rows_done:\n    RET\n'
    ordinary=source[source.index('p_player_body_stream:'):source.index('p_p_wholemask EQU')]
    store=source[source.index('p_player_zone:'):source.index('p_player_bandtop:')]
    entry=('    DEFINE WITH_PRESENTATION_TEMPLATES\n' if fast else '')+'''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
p_w_coarse EQU $C223
p_w_fault EQU $C231
start:
    DI
    LD SP,$F380
ready:
    JP ready
p_player_cache_lookup:
    SCF
    RET
p_world_fail:
    LD A,1
    LD (p_w_fault),A
    RET
'''+equates+'\n'+preparation+'\n'+ordinary+'\n'+store
    if fast:entry+='\n    INCLUDE "presentation_player_shore.asm"\n'
    entry+='\np_player_zones:\n    DB 0,128,192,224,240,248,252,254,255\n'
    for name in ('colors','reverse','holds','tails'):
        entry+=f'    ALIGN 256\np_sprite_{name}_data:\n    INCBIN "{out/name}.bin"\n'
    entry+=f'    ALIGN 256\noriginal_data:\n    INCBIN "{out/"original-data.bin"}"\n    DS $C000-$,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('body assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Body.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_body {{message}} {{puts stderr "PLAYER_BODY_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_body {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    binary scan [string range $::cases [expr {{$::index*7}}] [expr {{$::index*7+6}}]] cu* values
    lassign $values y x pose displacement offset reflection coarse
    debug write memory 0xC064 $y;debug write memory 0xC066 $x;debug write memory 0xC06E $pose
    debug write memory 0xC06B $displacement;debug write memory 0xC070 $offset;debug write memory 0xC06C $reflection
    debug write memory 0xC223 $coarse;debug write memory 0xC231 0
    debug write memory 0xC262 165;debug write_block memory 0xC4E0 [string repeat [binary format c 165] 4]
    debug write memory 0xC28F 255;debug write_block memory 0xC280 [binary format cu* {{255 0}}]
    set ::canonical [debug read_block memory 0xC000 128]
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_body target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['p_player_prepare']&255} {syms['p_player_prepare']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{0xC080 0x1A3 0xC224 13 0xC232 46 0xC293 0x1ED 0xC4E4 12 0xC500 0x260 0xC768 0x2BD8}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_body "guard $address"}}
        }}
        if {{[debug read_block memory 0xC000 128] ne $::canonical || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_body source-or-vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_body abi}}
        puts -nonewline $::actual "[debug read_block memory 0xC260 3][debug read_block memory 0xC4E0 4][debug read_block memory 0xC480 96][debug read_block memory 0xC231 1]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_body
    }}}}
    dispatch_body
}}}}]
after time 600 {{fail_body watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Body','-cart',str(artifact),'-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'PLAYER_BODY_FAIL' in log:raise ValueError('actual body capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed body evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete body timing')
    if max_body_cycles and max(row[1] for row in times)>max_body_cycles:raise ValueError(f'body microbudget exceeded: {max(row[1] for row in times)} > {max_body_cycles}')
    verify_files(consumed)
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('body producers changed')
    report={'complete':True,'cases':count,'source_selector_count':len(selectors),'source_selectors':selectors,'fast':fast,
        'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,'input_files':consumed,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 consumed setup/store spans and general or fast shoreline body; all observed source table selectors crossed with derived Y19..29/X24,83/coarse/reflection. Independent source-space rows determine whole96-byte planes/four colors/extents/fault. Canonical/C6/heap/SP/IFF/slot/VRAM guards. Derived component cases, not additional original rasters or whole-game/frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','source_selector_count','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--fast',action='store_true');p.add_argument('--max-body-cycles',type=int,default=0)
    check(**vars(p.parse_args()))
