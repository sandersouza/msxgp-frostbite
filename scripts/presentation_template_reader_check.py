"""Actual Z80 lossless half-atlas reader; no game or frame acceptance."""
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

FILES=('scripts/presentation_template_reader_check.py','src/presentation_template_reader.asm','scripts/presentation_template_assets.py',
    'scripts/presentation_floe_templates.py','src/movement.asm','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')
ROW_BYTES=10


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:raise ValueError('complete compressed pattern/carry/error differs or truncates')


def check(out,assets):
    producer={name:digest(ROOT/name) for name in FILES};assets=Path(assets).resolve();meta=json.loads((assets/'assets.json').read_text())
    consumed={str(assets/'assets.json'):digest(assets/'assets.json')}
    for name,value in meta['files'].items():
        if digest(assets/name)!=value:raise ValueError('compressed asset bank changed')
        consumed[str(assets/name)]=value
    for name in ('logical-patterns.bin','floe-patterns.bin','presentation_template.inc'):consumed[str(assets/name)]=digest(assets/name)
    patterns=(assets/'logical-patterns.bin').read_bytes();count=meta['patterns']
    if len(patterns)!=count*8 or digest(assets/'logical-patterns.bin')!=meta['logical_patterns_sha256']:raise ValueError('whole logical atlas identity required')
    floes=(assets/'floe-patterns.bin').read_bytes();floe_count=meta['floe_patterns'];cases=count+floe_count+4
    if len(floes)!=floe_count*8 or digest(assets/'floe-patterns.bin')!=meta['floe_patterns_sha256']:raise ValueError('whole raw floe atlas identity required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    expected=b''.join(bytes(2)+patterns[i:i+8] for i in range(0,len(patterns),8))+(bytes((1,1))+bytes([165])*8)*2
    expected+=b''.join(bytes(2)+floes[i:i+8] for i in range(0,len(floes),8))+(bytes((1,1))+bytes([165])*8)*2
    (out/'expected.bin').write_bytes(expected)
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
    INCLUDE "presentation_template_reader.asm"
unit_targets:
    DW p_template_pattern,p_template_floe_pattern
'''+mapper+'    DS $8000-$,$FF\n'
    for bank in range(1,256):
        entry+='    ORG $8000\n'
        entry+=f'    INCBIN "{assets/f"assets-{bank:03d}.bin"}"\n' if bank in meta['physical_banks'] else '    DS $4000,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={assets}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('compressed pattern reader assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_HalfAtlas.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    guards=((0xC000,0xC2BC),(0xC2BD,0xC2D4),(0xC2D8,0xC760),(0xC768,0xCC80),(0xCC88,0xF340))
    guard_list=' '.join(f'{a} {b-a}' for a,b in guards)
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_half {{message}} {{puts stderr "HALF_ATLAS_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_half {{}} {{
    if {{$::index=={cases}}} {{close $::actual;close $::timing;exit;return}}
    if {{$::index<{count+2}}} {{
        set id $::index;if {{$::index=={count+1}}} {{set id 65535}}
        set entry {syms['p_template_pattern']}
    }} else {{
        set id [expr {{$::index-{count+2}}}];if {{$id=={floe_count+1}}} {{set id 65535}}
        set entry {syms['p_template_floe_pattern']}
    }}
    debug write_block memory 0xC760 [binary format cu* [list 205 [expr {{$entry&255}}] [expr {{$entry>>8}}] 195 102 199 24 254]]
    debug write_block memory 0xCC80 [string repeat [binary format c 165] 8]
    reg DE $id;reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_half target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{{guard_list}}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_half "guard $address"}}
        }}
        if {{[debug read_block VRAM 0 16384] ne $::vram}} {{fail_half vram}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_half abi}}
        puts -nonewline $::actual "[binary format cu* [list [expr {{[reg F]&1}}] [debug read memory 0xC2BC]]][debug read_block memory 0xCC80 8]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_half
    }}}}
    dispatch_half
}}}}]
after time 120 {{fail_half watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_HalfAtlas','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'HALF_ATLAS_FAIL' in log:raise ValueError('actual compressed pattern capture failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed compressed pattern evidence')
    for index in range(cases):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'logical pattern{index}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=cases or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered pattern reader timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()) or any(digest(name)!=value for name,value in consumed.items()):raise ValueError('pattern reader producers/inputs changed')
    report={'complete':True,'patterns':count,'floe_patterns':floe_count,'cases':cases,'max_cycles_including_rpc':max(row[1] for row in times),
        'max_raw_floe_cycles_including_rpc':max(row[1] for row in times[count+2:count+2+floe_count]),'producer_files':producer,'input_files':consumed,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 readback of EVERY logical eight-byte pattern from the half dictionary AND every complete raw floe mask, plus two invalid IDs per namespace, with full canonical/descriptor/C6/heap/SP/IFF/slot/VRAM invariance. No game integration or complete-frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','patterns','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assets',type=Path,required=True)
    check(**vars(p.parse_args()))
