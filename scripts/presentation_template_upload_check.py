"""Actual Z80 stateful raw-mask publication; fixed resolver owns slot bounds."""
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

FILES=('scripts/presentation_template_upload_check.py','src/presentation_template_upload.asm','src/presentation_template_reader.asm',
    'src/movement.asm','scripts/environment.py','scripts/render_build.py','scripts/smoke.py')
ROW_BYTES=2+2304+16384
INPUT_BYTES=9


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixtures(patterns):
    if not patterns or len(patterns)%8:raise ValueError('complete raw masks required')
    count=len(patterns)//8;operations=[]
    def add(page,bank,slot,index,color=15,override=None):
        key=index.to_bytes(2,'little')+bytes((130 if bank==1 else 129,0,color,9)) if override is None else override
        operations.append(bytes((page,bank,slot+page*64))+key)
    for index in range(count):
        page=index&1;bank=1+((index//2)&1);slot=(19 if bank==1 else 9)+(index//4)%14
        add(page,bank,slot,index);add(page,bank,slot,index)
    for page in (0,1):
        for bank in (1,2):
            for color in range(1,16):
                for index in (0,1,1):add(page,bank,19 if bank==1 else 9,index,color)
            key=bytes((0,0,130 if bank==1 else 129,0,15,9))
            for field,value in ((0,255),(1,255),(2,128),(3,1),(4,0),(4,16),(5,8)):
                invalid=bytearray(key);invalid[field]=value
                # Low byte255 alone is a valid index; exercise full out-of-range.
                if field==0:invalid[:2]=count.to_bytes(2,'little')
                add(page,bank,19 if bank==1 else 9,0,override=bytes(invalid))
    metadata=bytearray([255])*2304;vram=bytearray([165])*16384;expected=bytearray()
    for data in operations:
        page,bank,tile=data[:3];key=data[3:];index=int.from_bytes(key[:2],'little')
        valid=bank in (1,2) and key[2]==(130 if bank==1 else 129) and key[3]==0 and 1<=key[4]<=15 and key[5]==9 and index<count
        if valid:
            address=(page*3+bank)*384+(tile&63)*6;metadata[address:address+6]=key
            address=bank*2048+tile*8;vram[address:address+8]=patterns[index*8:index*8+8]
            vram[address+8192:address+8200]=bytes([key[4]*16+4])*8
        expected.extend(bytes((int(not valid),))*2+metadata+vram)
    return b''.join(operations),bytes(expected)


def strip_fixtures(patterns):
    if not patterns or len(patterns)%8:raise ValueError('complete raw masks required')
    count=len(patterns)//8;operations=[]
    def add(page,row,color,keys,declared=None):
        keys=bytes().join(index.to_bytes(2,'little') for index in keys)
        operations.append(bytes((page,row,color,len(keys)//2 if declared is None else declared))+keys+bytes([165])*(28-len(keys)))
    for page in (0,1):
        for row in range(4):
            for start in range(0,count,14):
                keys=list(range(start,min(start+14,count)))
                add(page,row,15,keys);add(page,row,15,keys)
            for color in range(1,16):
                add(page,row,color,[0,1]);add(page,row,color,[1,0]);add(page,row,color,[1,0])
            for length in range(1,15):
                add(page,row,15,[i%count for i in range(length)]);add(page,row,15,[i%count for i in range(length)])
    for page,row,color,declared in ((2,0,15,1),(255,0,15,1),(0,4,15,1),(0,255,15,1),(0,0,0,1),(0,0,16,1),(0,0,15,0),(0,0,15,15)):
        add(page,row,color,[0],declared)
    for page in (0,1):
        for row in range(4):
            add(page,row,15,[count]);add(page,row,15,[2,65535])
    metadata=bytearray([255])*2304;vram=bytearray([165])*16384;expected=bytearray()
    for data in operations:
        page,row,color,length=data[:4];fault=not(page in (0,1) and row<4 and 1<=color<=15 and 1<=length<=14)
        if not fault:
            bank,base=((2,25),(2,9),(1,35),(1,19))[row];water=130 if bank==1 else 129
            for slot in range(length):
                index=int.from_bytes(data[4+slot*2:6+slot*2],'little')
                if index>=count:fault=True;break
                tile=page*64+base+slot;key=index.to_bytes(2,'little')+bytes((water,0,color,9))
                address=(page*3+bank)*384+(base+slot)*6;metadata[address:address+6]=key
                address=bank*2048+tile*8;vram[address:address+8]=patterns[index*8:index*8+8]
                vram[address+8192:address+8200]=bytes([color*16+4])*8
        expected.extend(bytes((int(fault),))*2+metadata+vram)
    return b''.join(operations),bytes(expected)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:
        at=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),None)
        raise ValueError(f'whole publication carry/error/metadata/VRAM differs or truncates at{at}')


def check(out,assets,*,strip=False):
    files=(*FILES,'src/presentation_template_strip.asm','src/presentation_fixed_runtime.asm') if strip else FILES
    producer={name:digest(ROOT/name) for name in files};assets=Path(assets).resolve();meta=json.loads((assets/'assets.json').read_text())
    consumed={str(assets/'assets.json'):digest(assets/'assets.json')}
    for name,value in meta['files'].items():
        if digest(assets/name)!=value:raise ValueError('template asset changed')
        consumed[str(assets/name)]=value
    for name in ('floe-patterns.bin','presentation_template.inc'):consumed[str(assets/name)]=digest(assets/name)
    patterns=(assets/'floe-patterns.bin').read_bytes()
    if digest(assets/'floe-patterns.bin')!=meta['floe_patterns_sha256']:raise ValueError('raw masks changed')
    inputs,expected=(strip_fixtures if strip else fixtures)(patterns);stride=32 if strip else INPUT_BYTES;count=len(inputs)//stride
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    movement=(ROOT/'src/movement.asm').read_text();mapper=movement[movement.index('map_page2:\n'):movement.index('set_address:\n')]
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
pf_key EQU $CC90
p_fx_meta EQU $C2E3
p_fx_bank EQU $C2E5
p_w_tile EQU $C22F
pt_error EQU $C53F
pt_tile EQU $C520
pt_water_id1 EQU 130
pt_water_id2 EQU 129
start:
    DI
    LD SP,$F380
    CALL map_page2
    DI
ready:
    JP ready
    INCLUDE "presentation_template_reader.asm"
    INCLUDE "presentation_template_upload.asm"
vdp_write:
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    LD C,$98
.byte:
    OUTI
    JP NZ,.byte
    RET
'''+mapper
    if strip:
        runtime=(ROOT/'src/presentation_fixed_runtime.asm').read_text()
        entry+='''PAGE EQU $C200
p_w_color EQU $C222
p_w_row EQU $C224
p_w_cachegroup EQU $C230
p_tf_water EQU $C2F8
p_tf_namebase EQU $C2F9
p_tl_count EQU $C2D3
p_tl_keys EQU $E2A0
    INCLUDE "presentation_template_strip.asm"
'''+runtime[runtime.index('p_fixed_key_address:\n'):runtime.index('p_fixed_mark_object:\n')]+runtime[runtime.index('p_fast_key_roots:\n'):runtime.index('    ALIGN 8\np_fast_bits:')]
    entry+='    DS $8000-$,$FF\n'
    for bank in range(1,256):
        entry+='    ORG $8000\n'
        entry+=f'    INCBIN "{assets/f"assets-{bank:03d}.bin"}"\n' if bank in meta['physical_banks'] else '    DS $4000,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--inc={assets}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('raw publisher assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_RawPublish.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    guards=((0xC000,0xC22F),(0xC230,0xC2BC),(0xC2BD,0xC2E3),(0xC2E6,0xC2E7),(0xC2E8,0xC528),(0xC530,0xC53F),
        (0xC540,0xC760),(0xC768,0xCC90),(0xCC96,0xD000),(0xD900,0xF340))
    if strip:
        guards=((0xC000,0xC200),(0xC201,0xC222),(0xC223,0xC224),(0xC225,0xC22F),(0xC231,0xC2BC),(0xC2BD,0xC2D3),
            (0xC2D4,0xC2E3),(0xC2E8,0xC2F8),(0xC2FA,0xC528),(0xC530,0xC53F),(0xC540,0xC760),(0xC768,0xCC90),
            (0xCC96,0xD000),(0xD900,0xE2A0),(0xE2BC,0xF340))
    guard_list=' '.join(f'{a} {b-a}' for a,b in guards)
    dispatch='''
    binary scan [string range $row 0 3] cu* config;lassign $config page source color count
    debug write memory 0xC200 $page;debug write memory 0xC224 $source;debug write memory 0xC222 $color;debug write memory 0xC2D3 $count
    set ::key [string range $row 4 31];debug write_block memory 0xE2A0 $::key
''' if strip else '''
    binary scan [string range $row 0 2] cu* config;lassign $config page bank tile
    debug write memory 0xC22F $tile;debug write memory 0xC2E5 $bank
    set address [expr {0xD000+($page*3+$bank)*384+($tile&63)*6}]
    debug write memory 0xC2E3 [expr {$address&255}];debug write memory 0xC2E4 [expr {$address>>8}]
    set ::key [string range $row 3 8];debug write_block memory 0xCC90 $::key
'''
    input_guard='[debug read_block memory 0xE2A0 28]' if strip else '[debug read_block memory 0xCC90 6]'
    target=syms['p_template_strip_publish' if strip else 'p_template_floe_upload']
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_publish {{message}} {{puts stderr "RAW_PUBLISH_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_publish {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*{stride}}}] [expr {{$::index*{stride}+{stride-1}}}]]
    {dispatch}
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_publish target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    debug write_block memory 0xD000 [string repeat [binary format c 255] 2304]
    debug write_block VRAM 0 [string repeat [binary format c 165] 16384]
    set ::slot [debug read ioports 168]
    debug write_block memory 0xC760 [binary format cu* {{205 {target&255} {target>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{{guard_list}}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_publish "guard $address"}}
        }}
        if {{{input_guard} ne $::key || [reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_publish abi-or-key}}
        puts -nonewline $::actual "[binary format cu* [list [expr {{[reg F]&1}}] [debug read memory 0xC53F]]][debug read_block memory 0xD000 2304][debug read_block VRAM 0 16384]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_publish
    }}}}
    dispatch_publish
}}}}]
after time 120 {{fail_publish watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_RawPublish','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'RAW_PUBLISH_FAIL' in log:raise ValueError('actual raw publication failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed publication evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index} key={list(inputs[index*stride:index*stride+stride])}: {error}') from error
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered publication timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()) or any(digest(name)!=value for name,value in consumed.items()):raise ValueError('publisher producers/inputs changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,'input_files':consumed,
        'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,'strip_mode':strip,
        'scope':('Actual Z80 owned strip publisher: every raw mask in every source-row role and both generations; lengths1..14, all15 foregrounds, repeated/shortened/replaced strips, invalid PAGE/row/FG/count and raw IDs. Full2304-byte metadata/16KiB VRAM/carry/error and immutable source IDs/canonical/C6/heap/names/cache/SP/IFF/slot. On a later invalid ID, already completed offscreen keys remain valid but the driver must not publish its strip identity. Whole-game active-generation/VBlank/spacing/deadline acceptance separate.' if strip else
        'Actual Z80 raw publisher stateful whole2304-byte metadata/16KiB VRAM/carry/error. Every raw mask, repeated/replaced masks, both pages/water banks, all15 foregrounds, invalid grammar. Canonical/C6/heap/names/cache/key/SP/IFF/slot guards. Caller fixed-resolver bounds and whole-game VBlank/spacing/deadline acceptance separate.')}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('--strip',action='store_true')
    check(**vars(p.parse_args()))
