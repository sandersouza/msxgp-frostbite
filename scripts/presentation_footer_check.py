"""Actual Z80 owned footer publication on all finite source programs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from presentation_constructors import footer_key
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=('scripts/presentation_footer_check.py','scripts/presentation_constructors.py','src/presentation_footer.asm',
    'src/presentation_fast_world.asm','src/presentation.asm','src/movement.asm','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')
ROW_BYTES=264+1536+16384+2


def fixtures(programs,tiles):
    if len(programs)!=704 or not tiles or len(tiles)%16:raise ValueError('complete finite footer programs/tiles required')
    operations=[(page,coarse,phase,192) for page in (0,1) for phase in range(8) for coarse in (0,1) for repeat in range(2)]
    operations+=[(page,0,7,dirty) for page in (0,1) for dirty in (0,63,64,128)]
    operations+=list(((2,0,0,192),(255,0,0,192),(0,2,0,192),(0,255,0,192),(0,0,8,192),(0,0,255,192)))
    metadata=bytearray([255])*264;names=bytearray([165])*1536;vram=bytearray([165])*16384;expected=bytearray()
    for page,coarse,phase,dirty in operations:
        fault=bool(dirty&192) and not(page in (0,1) and coarse in (0,1) and phase<8)
        if dirty&192 and not fault:
            at=(phase*2+coarse)*44
            for cell in range(22):
                index=int.from_bytes(programs[at+cell*2:at+cell*2+2],'little')
                if not index:continue
                if index>=len(tiles)//16:raise ValueError('finite footer program references absent tile')
                slot=page*22+cell;identifier=160+slot;metadata[slot*6:slot*6+6]=footer_key(index)
                target=4096+identifier*8;vram[target:target+8]=tiles[index*16:index*16+8];vram[target+8192:target+8200]=tiles[index*16+8:index*16+16]
                names[page*768+(22+cell//11)*32+4+cell%11]=identifier
        expected.extend(metadata+names+vram+bytes((int(fault),))*2)
    return b''.join(bytes(row) for row in operations),bytes(expected)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:
        at=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),None)
        raise ValueError(f'whole footer metadata/NAME/VRAM/carry/fault differs or truncates at{at}')


def check(out,assets):
    digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    producer={name:digest(ROOT/name) for name in FILES};assets=Path(assets).resolve();meta=json.loads((assets/'assets.json').read_text())
    consumed={str(assets/'assets.json'):digest(assets/'assets.json')};images=[]
    for bank in meta['physical_banks']:
        path=assets/f'assets-{bank:03d}.bin'
        if digest(path)!=meta['files'][path.name]:raise ValueError('actual footer asset bank changed')
        consumed[str(path)]=digest(path);images.append(path.read_bytes())
    consumed[str(assets/'presentation_static.inc')]=digest(assets/'presentation_static.inc');image=b''.join(images)
    def section(name):
        item=meta['sections'][name];return image[item['offset']:item['offset']+item['size']]
    programs,tiles=section('footer_names'),section('footer_tiles');inputs,expected=fixtures(programs,tiles);count=len(inputs)//4
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    movement=(ROOT/'src/movement.asm').read_text();mapper=movement[movement.index('map_page2:\n'):movement.index('set_address:\n')]
    world=(ROOT/'src/presentation_fast_world.asm').read_text();cell=world[world.index('p_fast_cell:\n'):world.index('; All six bytes are retained')]
    display=(ROOT/'src/presentation.asm').read_text();stream=display[display.index('vdp_write:\n'):display.index('presentation_init:\n')]
    entry='''    DEFINE WITH_PRESENTATION_FIXED
    ORG $4000
    DB "AB"
    DW start
    DS 12,0
PAGE EQU $C200
p_w_coarse EQU $C223
p_w_col EQU $C229
p_w_top EQU $C22A
p_w_name EQU $C22D
p_w_tile EQU $C22F
p_w_cachegroup EQU $C230
p_w_fault EQU $C231
p_h_footer_phase EQU $C244
p_h_footer_index EQU $C245
p_fd_rows EQU $C2D8
pf_key EQU $CC90
start:
    DI
    LD SP,$F380
    CALL map_page2
    DI
ready:
    JP ready
    INCLUDE "presentation_static.inc"
    INCLUDE "presentation_footer.asm"
p_world_fail:
    LD A,1
    LD (p_w_fault),A
    RET
'''+cell+stream+mapper+'    DS $8000-$,$FF\n'
    for bank in range(1,256):
        entry+='    ORG $8000\n'
        entry+=f'    INCBIN "{assets/f"assets-{bank:03d}.bin"}"\n' if bank in meta['physical_banks'] else '    DS $4000,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={assets}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('footer assembler failed: '+compiled.stderr[-1600:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Footer.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    guards=((0xC000,0xC200),(0xC300,0xC760),(0xC768,0xC800),(0xCB00,0xCC90),(0xCC96,0xCD00),(0xD000,0xD900),(0xDA08,0xF340))
    guard_list=' '.join(f'{a} {b-a}' for a,b in guards);target=syms['p_template_footer_prepare']
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_footer {{message}} {{puts stderr "FOOTER_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_footer {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    binary scan [string range $::cases [expr {{$::index*4}}] [expr {{$::index*4+3}}]] cu* config
    lassign $config page coarse phase dirty
    debug write memory 0xC200 $page;debug write memory 0xC223 $coarse;debug write memory 0xC244 $phase;debug write memory 0xC2DA $dirty;debug write memory 0xC231 0
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_footer target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    debug write_block memory 0xD900 [string repeat [binary format c 255] 264]
    debug write_block VRAM 0 [string repeat [binary format c 165] 16384]
    set ::slot [debug read ioports 168];set VDP.too_fast_vram_access_callback {{fail_footer spacing}}
    debug write_block memory 0xC760 [binary format cu* {{205 {target&255} {target>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{{guard_list}}} {{if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_footer "guard $address"}}}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_footer abi}}
        puts -nonewline $::actual "[debug read_block memory 0xD900 264][debug read_block memory 0xC800 768][debug read_block memory 0xCD00 768][debug read_block VRAM 0 16384][binary format cu* [list [expr {{[reg F]&1}}] [debug read memory 0xC231]]]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_footer
    }}}}
    dispatch_footer
}}}}]
after time 120 {{fail_footer watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Footer','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'FOOTER_FAIL' in log:raise ValueError('actual footer publication failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed footer evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index} {list(inputs[index*4:index*4+4])}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered footer timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()) or any(digest(name)!=value for name,value in consumed.items()):raise ValueError('footer producers/inputs changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,'input_files':consumed,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 footer publication for all16 source programs/both generations/repeats/dirty selectors/invalid PAGE,coarse,phase. Whole264-byte metadata/both CPU NAME pages/16KiB VRAM/carry/fault and canonical/C6/heap/other-cache/SP/IFF/slot/29IO guards. Zero descriptors retain caller background. Whole-game active-generation/visible pixels/VBlank/deadline acceptance separate.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assets',type=Path,required=True)
    check(**vars(p.parse_args()))
