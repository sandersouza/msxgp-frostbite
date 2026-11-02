"""Actual-Z80 typed constructor microproof, separate from game frame acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from presentation_assets import compile_assets
from presentation_constructors import construct,literal_key,union_key,header_key,igloo_key,footer_key
from presentation_fast_model import prepare,frame
from presentation_fragments import background_tables,pack_background,pack_geometry_metadata
from presentation_palette import audit_palette
from presentation_source_cases import collect,verify_files,FILES as SOURCE_FILES
from presentation_static_assets import pack_static
from reference_provenance import snapshot_paths
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

HELPERS=tuple(dict.fromkeys((*SOURCE_FILES,'scripts/presentation_typed_check.py','src/presentation_typed.asm',
    'scripts/presentation_fast_model.py','scripts/presentation_constructors.py','scripts/presentation_static_assets.py',
    'scripts/presentation_fragments.py','scripts/presentation_assets.py','scripts/presentation_palette.py',
    'scripts/presentation_check.py','src/presentation_geometry.asm','src/movement.asm')))


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_row(actual,expected):
    if len(actual)!=17 or len(expected)!=17 or actual!=expected:
        raise ValueError('incomplete/different actual typed tile or error flag')


def fixtures(tables,domain):
    unique={}
    for case in domain['cases']:
        rendered=frame(tables,case['ram']);vram=rendered['vram']
        for (row,column),key in rendered['keys'].items():
            bank=row//8;identifier=vram[0x1800+row*32+column];at=bank*2048+identifier*8
            tile=vram[at:at+8]+vram[0x2000+at:0x2000+at+8]
            identity=(bank,key)
            if identity in unique and unique[identity]!=tile:raise ValueError('constructor key aliases different whole16-byte tiles')
            unique[identity]=tile
    # The observed corpus does not naturally exercise every clipped union.
    # Add explicit algebra boundaries, separately identified from source cases.
    observed=len(unique)
    for bank in range(3):
        backgrounds={128:tables['background']['patterns'][bank][:8]+tables['background']['colors'][bank][:8]}
        keys=[literal_key((170,204,0 if kind==1 else 85),2,15,kind) for kind in (1,2,3)]
        keys += [union_key(0,1,15,clip) for clip in (False,True)]
        keys += [igloo_key(bits,(bits*37)&255,128) for bits in range(256)]
        keys += [header_key((g,(g+1)%34,33-g,g),2,15,4,column,band)
                 for g in range(34) for column in range(5) for band in range(3)]
        if bank==2:keys += [footer_key(i) for i in range(len(tables['footer']['tiles']))]
        for key in keys:
            tile=construct(key,patterns=tables['patterns'],backgrounds=backgrounds,header=tables['header'],footer=tables['footer']['tiles'])
            identity=(bank,key)
            if identity in unique and unique[identity]!=tile:raise ValueError('source/synthetic constructor identity aliases')
            unique[identity]=tile
    entries=sorted(unique.items())
    inputs=b''.join(bytes((bank,))+key for (bank,key),tile in entries)
    expected=b''.join(tile+bytes(1) for identity,tile in entries)
    kinds=sorted({key[5] for bank,key in unique})
    if kinds!=[0,1,2,3,5,6,7,8,16,17,18]:raise ValueError('whole observed constructor grammar required')
    # Unsupported output bank/type must reject before changing the tile.
    inputs+=bytes((3,))+bytes(6)+bytes((0,))+bytes(5)+bytes((255,))
    expected+=(bytes((165,))*16+bytes((1,)))*2
    return inputs,expected,kinds,observed


def check(out,geometry,explore=False):
    producer={'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'utility_fingerprints':{name:digest(ROOT/name) for name in HELPERS}} if explore else snapshot_paths(HELPERS)
    domain=collect();config=json.loads((ROOT/'references/presentation-assets-config.json').read_text())
    palette=audit_palette(ROOT/config['palette']);original=ROOT/'references/roms/frostbite.bin';rom=original.read_bytes()
    geometry=Path(geometry).resolve();geo=json.loads((geometry/'geometry.json').read_text())
    input_files={str(path.relative_to(ROOT)):digest(path) for path in
        (original,geometry/'geometry.json',geometry/'row-pointer-map.bin',*sorted(geometry.glob('geometry-*.bin')))}
    tables=prepare(rom,palette,geometry);inputs,expected,kinds,observed=fixtures(tables,domain);count=len(inputs)//7
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    static=pack_static(rom,palette,geometry,geo,out/'static')
    (out/'presentation_static.inc').write_text((out/'static/presentation_static.inc').read_text())
    assets=compile_assets(rom,out/'assets',measured_palette=palette)
    boot=pack_background((out/'assets/fragments.bin').read_bytes(),assets['used_bytes'],background_tables(rom,palette))
    meta=pack_geometry_metadata(boot,geo,(geometry/'row-pointer-map.bin').read_bytes())
    (out/'boot.bin').write_bytes(meta['bank']);(out/'presentation_geometry.inc').write_text(meta['assembly'])
    (out/'presentation_background.inc').write_text(boot['assembly'])
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
unit_run:
    CALL presentation_typed_construct
    LD A,0
    ADC A,0
    LD (pt_error),A
    RET
    INCLUDE "presentation_background.inc"
    INCLUDE "presentation_geometry.asm"
    INCLUDE "presentation_typed.asm"
'''+mapper+'    DS $8000-$,$FF\n    ORG $8000\n'+f'    INCBIN "{out/"boot.bin"}"\n'
    for bank in range(2,256):
        entry+='    ORG $8000\n'
        entry+=f'    INCBIN "{out/"static"/f"assets-{bank:03d}.bin"}"\n' if bank in static['physical_banks'] else '    DS $4000,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={out}',f'--raw={artifact}',
        f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('typed microassembler failed: '+compiled.stderr[-1600:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve()
    profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Typed.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb]
set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_typed {{message}} {{puts stderr "TYPED_FAIL $message case=$::index";exit 1;return -code error $message}}
proc dispatch_typed {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*7}}] [expr {{$::index*7+6}}]]
    binary scan [string index $row 0] cu bank
    set ::key [string range $row 1 6]
    debug write_block memory 0xCC90 $::key
    debug write_block memory 0xC520 [string repeat [binary format c 165] 16]
    reg AF [expr {{$bank*256}}];reg SP 0xF380;reg PC 0xC760
    set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_typed target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168]
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['unit_run']&255} {syms['unit_run']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{0xC000 512 0xC300 256 0xC600 256 0xC800 1024 0xD000 0x2340}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_typed "guard $address"}}
        }}
        if {{[debug read_block memory 0xCC90 6] ne $::key}} {{fail_typed key-mutated}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_typed abi}}
        puts -nonewline $::actual "[debug read_block memory 0xC520 16][debug read_block memory 0xC53F 1]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_typed
    }}}}
    dispatch_typed
}}}}]
after time 120 {{fail_typed watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    executed=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Typed','-cart',str(artifact),
        '-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
        capture_output=True,text=True,timeout=180)
    log=executed.stdout+executed.stderr;(out/'emulator.log').write_text(log)
    if executed.returncode or 'TYPED_FAIL' in log:raise ValueError('typed actual capture failed: '+log[-1800:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected):raise ValueError('incomplete typed actual matrix')
    for index in range(count):
        try:verify_row(actual[index*17:index*17+17],expected[index*17:index*17+17])
        except ValueError as error:raise ValueError(f'case{index} input{list(inputs[index*7:index*7+7])}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete typed timing')
    verify_files(domain['files'])
    verify_files(input_files)
    if any(digest(ROOT/name)!=value for name,value in producer['utility_fingerprints'].items()):raise ValueError('typed producer changed')
    result={'producer':producer,'cases':count,'observed_unique_keys':observed,'synthetic_added_keys':count-observed,
        'source_observations':len(domain['cases']),'kinds':kinds,
        'max_cycles_including_rpc':max(row[1] for row in times),'rom_sha256':digest(artifact),
        'actual_sha256':digest(out/'actual.bin'),'expected_sha256':digest(out/'expected.bin'),
        'source_receipt_sha256':domain['source_receipt_sha256'],'source_files':domain['files'],'input_files':input_files,
        'complete':True,'frame_deadline_accepted':False,
        'scope':'Actual-Z80 whole-tile constructor microproof; no game integration, frame, audio or human-ROM acceptance'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('cases','kinds','max_cycles_including_rpc','complete')}));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--geometry',type=Path,required=True);p.add_argument('--explore',action='store_true')
    check(**vars(p.parse_args()))
