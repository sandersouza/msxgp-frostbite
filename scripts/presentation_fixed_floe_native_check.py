"""Actual Z80 complete floe grid proof; not a game or frame acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from presentation_fixed_floe import strip
from presentation_fixed_floe_check import FILES as BASE_FILES
from presentation_fast_model import prepare
from presentation_geometry_check import metadata
from presentation_palette import audit_palette
from presentation_source_cases import verify_files
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=tuple(dict.fromkeys((*BASE_FILES,'scripts/presentation_fixed_floe_native_check.py','scripts/presentation_geometry_check.py',
    'src/presentation_fixed_floe.asm','src/presentation_geometry.asm','src/movement.asm')))
ROW_BYTES=321


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:
        raise ValueError('whole floe count/first/second grid differs or is truncated')


def grid_row(rendered,y,previous):
    if len(previous)!=256:raise ValueError('complete retained ID arrays required')
    counts=bytearray(64);ids=bytearray(previous)
    for (row,column),layers in rendered['layers'].items():
        cell=(row-y//8)*32+column
        if not 0<=cell<64:raise ValueError('strip escaped its two-row grid')
        values=sorted({layer['id'] for layer in layers})
        if not 1<=len(values)<=2 or any(not 0<value<65536 for value in values):raise ValueError('invalid complete floe cell')
        counts[cell]=len(values)
        for plane,value in enumerate(values):ids[plane*128+cell*2:plane*128+cell*2+2]=value.to_bytes(2,'little')
    return bytes((0,))+counts+ids


def fixtures(tables,limit):
    inputs=bytearray();expected=bytearray();previous=bytes([165])*256
    params=((root,delta,88+phase) for phase in range(8) for delta in range(-11,20) for root in range(160))
    if limit:
        # A private smoke subset includes signed/mod160 and union boundaries.
        params=((root,delta,88+phase) for phase in range(8) for delta in (-11,-1,0,8,9,19) for root in (0,7,8,29,127,159))
    for root,delta,y in params:
        row=grid_row(strip(tables,root,delta,y,15),y,previous);previous=row[65:]
        inputs.extend(bytes((root,delta&255,y)));expected.extend(row)
    for y in (0,7,63,64,127,128,179,185):
        row=grid_row(strip(tables,0,-11,y,15),y,previous);previous=row[65:]
        inputs.extend(bytes((0,245,y)));expected.extend(row)
    last=expected[-ROW_BYTES:]
    for root,delta,y in ((160,0,88),(255,0,88),(0,-12,88),(0,20,88),(0,-128,88),(0,127,88),(0,0,186),(0,0,255)):
        inputs.extend(bytes((root,delta&255,y)));expected.extend(bytes((1,))+last[1:])
    return bytes(inputs),bytes(expected)


def check(out,geometry,limit=False):
    producer={name:digest(ROOT/name) for name in FILES};out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    geometry=Path(geometry).resolve();geo=json.loads((geometry/'geometry.json').read_text())
    config=json.loads((ROOT/'references/presentation-assets-config.json').read_text());palette_path=ROOT/config['palette']
    palette=audit_palette(palette_path);original=ROOT/'references/roms/frostbite.bin'
    palette_inputs=sorted(p for p in palette_path.rglob('*') if p.is_file()) if palette_path.is_dir() else [palette_path]
    consumed={str(p.relative_to(ROOT)):digest(p) for p in (original,*palette_inputs,geometry/'geometry.json',geometry/'row-pointer-map.bin',*sorted(geometry.glob('geometry-*.bin')))}
    tables=prepare(original.read_bytes(),palette,geometry);inputs,expected=fixtures(tables,limit);count=len(inputs)//3
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    boot,include=metadata(geo,(geometry/'row-pointer-map.bin').read_bytes())
    (out/'boot.bin').write_bytes(boot);(out/'presentation_geometry.inc').write_text(include)
    movement=(ROOT/'src/movement.asm').read_text();mapper=movement[movement.index('map_page2:\n'):movement.index('set_address:\n')]
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
start:
    DI
    LD SP,$F380
    CALL map_page2
    DI
ready:
    JP ready
p_fast_geometry_lookup:
    JP presentation_geometry_lookup
    INCLUDE "presentation_fixed_floe.asm"
    INCLUDE "presentation_geometry.asm"
'''+mapper+'    DS $8000-$,$FF\n    ORG $8000\n'+f'    INCBIN "{out/"boot.bin"}"\n'
    for bank in range(2,256):
        entry+='    ORG $8000\n'
        entry+=f'    INCBIN "{geometry/f"geometry-{bank:03d}.bin"}"\n' if bank in geo['physical_banks'] else '    DS $4000,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={out}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('floe grid assembler failed: '+compiled.stderr[-1600:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_FloeGrid.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_grid {{message}} {{puts stderr "FIXED_FLOE_GRID_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_grid {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    binary scan [string range $::cases [expr {{$::index*3}}] [expr {{$::index*3+2}}]] cu* data
    lassign $data root delta y
    reg AF [expr {{$root*256}}];reg BC [expr {{$delta*256+$y}}]
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_grid target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['p_fixed_floe_build']&255} {syms['p_fixed_floe_build']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{0xC000 672 0xC2C4 39 0xC2FB 1125 0xC768 6808 0xE240 192 0xE380 128 0xE480 3776}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_grid "guard $address"}}
        }}
        if {{[debug read_block VRAM 0 16384] ne $::vram}} {{fail_grid vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_grid abi}}
        if {{[debug read memory 0xC2FA]!=([reg F]&1)}} {{fail_grid error-flag}}
        puts -nonewline $::actual "[binary format cu [expr {{[reg F]&1}}]][debug read_block memory 0xE200 64][debug read_block memory 0xE300 128][debug read_block memory 0xE400 128]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_grid
    }}}}
    dispatch_grid
}}}}]
after time 600 {{fail_grid watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_FloeGrid','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=300)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'FIXED_FLOE_GRID_FAIL' in log:raise ValueError('actual floe grid capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('floe grid fixtures/capture incomplete or changed')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index} params={list(inputs[index*3:index*3+3])}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered floe grid timing')
    verify_files(consumed)
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('floe grid producers changed')
    report={'complete':True,'cases':count,'smoke_subset':limit,'max_cycles_including_rpc':max(row[1] for row in times),
        'producer_files':producer,'input_files':consumed,'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'profile_sha256':hashlib.sha256(profile).hexdigest(),
        'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 complete two-row floe grids; all160 roots/signed delta-11..19/eight phases (unless smoke_subset), retained unused bytes, invalid parameter rejection, canonical/ABI/heap/VRAM/slot guards. Not original rasters, game integration or frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({key:report[key] for key in ('complete','cases','smoke_subset','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True);p.add_argument('--limit',action='store_true',help='Private boundary smoke subset only')
    check(**vars(p.parse_args()))
