"""Actual Z80 fixed-role publication with a deterministic constructor stub.

The separate4705-case real constructor proof and full game integration remain
required. This component checks physical addresses and atomic key ownership.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from presentation_fixed import COUNTS,world_slot,header_slot,igloo_slot,footer_name
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=('scripts/presentation_fixed_runtime_check.py','scripts/presentation_fixed.py','src/presentation_fixed_runtime.asm','scripts/environment.py','scripts/smoke.py','scripts/render_build.py')
INPUT_BYTES=34
ROW_BYTES=20561


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixtures():
    operations=[]
    def add(page=0,bank=0,force=255,key=None,top=None,col=0,family=2,row=0,line=0,copy=0,coarse=0,footer=0,op=1):
        top=bank*8 if top is None else top
        key=bytes(6) if key is None else bytes(key)
        tile=hashlib.sha256(b'fixed tile'+bytes((bank&255,))+key).digest()[:16]
        operations.append(bytes((op,page,bank,force))+key+tile+bytes((top,col,family,row,line,copy,coarse,footer)))
    add(op=0)
    add(force=0,key=bytes([255])*6)
    for page in (0,1):
        for bank,count in enumerate(COUNTS):
            for slot in range(count):
                key=hashlib.sha256(f'fixed{page}:{bank}:{slot}'.encode()).digest()[:5]+bytes(1)
                add(page,bank,slot+page*64,key,col=slot%32);add(page,bank,slot+page*64,key,col=slot%32)
    for page in (0,1):
        for band in range(3):
            for col in range(5,15):add(page,0,key=bytes((col,band,0,0,0,16+band)),top=band,col=col)
        for top in range(3,6):
            for col in range(22,28):add(page,0,key=bytes((col,top,128,14,0,5)),top=top,col=col)
        for index in range(22):add(page,2,key=index.to_bytes(2,'little')+bytes((0,0,0,6)),top=22+index//11,col=4+index%11,footer=index)
        for coarse in (0,1):
            for row in range(4):
                top=(153-row*26+coarse)//8;rows=((153-row*26+coarse)%8+15)//8
                for grid_row in range(rows):
                    for line in range(3):
                        for copy in range(3):add(page,(top+grid_row)//8,key=bytes((row,line,0,0,15,0)),top=top+grid_row,col=3+copy*6+line,family=0,row=row,line=line,copy=copy,coarse=coarse)
        for grid_row in range(3):
            for line in range(4):add(page,(6+grid_row)//8,key=bytes((line,grid_row,0,0,15,0)),top=6+grid_row,col=3+line,line=line)
    key=bytes((1,2,3,4,5,0))
    for field in range(6):
        changed=bytearray(key);changed[field]^=1;add(0,0,0,changed,col=5)
    add(0,0,0,key,op=2);add(0,0,0,key);add(0,0,0,key,op=2)
    for page,bank,force,kind in ((0,0,64,0),(1,0,0,0),(0,1,60,0),(0,2,50,0),(1,2,114,0),(0,0,160,6),(0,2,182,6),(1,2,181,6),(1,2,204,6),(2,0,0,0),(0,3,0,0)):
        add(page,bank,force,bytes((0,0,0,0,0,kind)))
    add(key=bytes((0,0,0,0,0,16)),top=3,col=5)
    add(key=bytes((0,0,0,0,0,16)),top=0,col=15)
    metadata=bytearray([165])*2568;names=bytearray([165])*1536;vram=bytearray([165])*16384;fused=bytearray([165])*64
    counts=bytes([165])*6;expected=bytearray()
    for data in operations:
        op,page,bank,force=data[:4];key=data[4:10];tile=data[10:26];top,col,family,row,line,copy,coarse,footer=data[26:34]
        result=carry=fault=0
        if op==0:metadata[:]=bytes([255])*2568;counts=bytes(COUNTS)*2
        else:
            try:
                if page not in (0,1) or bank not in (0,1,2):raise ValueError('page/bank')
                if key[5]==255:raise ValueError('invalid unpublished-key marker')
                if force!=255:identifier=force
                elif key[5]==6:identifier=footer_name(page,footer)
                elif key[5]==5:identifier=igloo_slot(top,col)[1]+page*64
                elif 16<=key[5]<=18:identifier=header_slot(top,col)[1]+page*64
                elif key[5]==0:
                    role='bear' if family==2 else 'object' if family==0 else 'invalid'
                    first=6 if role=='bear' else (153-row*26+coarse)//8
                    identifier=world_slot(role,row,top-first,line,coarse)[1]+page*64
                else:raise ValueError('automatic key type')
                if identifier<128:
                    slot=identifier&63
                    if identifier//64!=page or slot>=COUNTS[bank]:raise ValueError('dynamic bounds')
                    address=(page*3+bank)*384+slot*6
                else:
                    if key[5]!=6 or bank!=2 or not 160+page*22<=identifier<182+page*22:raise ValueError('footer bounds')
                    address=2304+(identifier-160)*6
                if metadata[address:address+6]!=key:
                    if op==2:raise ValueError('constructor fault')
                    base=bank*2048+identifier*8;vram[base:base+8]=tile[:8];vram[base+0x2000:base+0x2008]=tile[8:]
                    metadata[address:address+6]=key
                names[page*768+top*32+col]=identifier
                if key[5]==0 and family==0 and ((coarse and top==12) or (not coarse and top in (15,20))):fused[(32 if top==20 else 0)+col]=copy*3+line
                result=identifier
            except ValueError:result=255;carry=fault=1
        expected.extend(bytes((result,carry,fault))+metadata+names+vram+fused+counts)
    return b''.join(operations),bytes(expected)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or actual!=expected:
        at=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),None)
        raise ValueError(f'fixed publication whole payload differs/truncates at{at}')


def check(out):
    producer={name:digest(ROOT/name) for name in FILES};out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    inputs,expected=fixtures();count=len(inputs)//INPUT_BYTES;(out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
PAGE EQU $C200
p_w_coarse EQU $C223
p_w_row EQU $C224
p_w_copy EQU $C225
p_w_family EQU $C227
p_w_col EQU $C229
p_w_top EQU $C22A
p_w_line EQU $C22B
p_w_name EQU $C22D
p_w_tile EQU $C22F
p_w_cachegroup EQU $C230
p_w_fault EQU $C231
p_h_footer_index EQU $C245
pt_tile EQU $C520
pt_error EQU $C53F
start:
    DI
    LD SP,$F380
    LD A,2
    CALL $005F
    DI
ready:
    JP ready
unit_run:
    XOR A
    LD (p_w_fault),A
    LD (pt_error),A
    LD A,($C2F0)
    OR A
    JP Z,p_fast_init
    JP p_fixed_put
presentation_typed_construct:
    LD B,A
    LD A,($C2F1)
    CP B
    JR NZ,.fault
    LD A,($C2F0)
    CP 2
    JR Z,.fault
    LD HL,$C480
    LD DE,pt_tile
    LD BC,16
    LDIR
    XOR A
    LD (pt_error),A
    RET
.fault:
    LD A,1
    LD (pt_error),A
    SCF
    RET
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
p_world_fail:
    LD A,1
    LD (p_w_fault),A
    RET
    INCLUDE "presentation_fixed_runtime.asm"
    DS $C000-$,$FF
'''
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('fixed publication assembler failed: '+compiled.stderr[-1500:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_FixedPut.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_fixedput {{message}} {{puts stderr "FIXED_PUT_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_fixedput {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set row [string range $::cases [expr {{$::index*{INPUT_BYTES}}}] [expr {{$::index*{INPUT_BYTES}+{INPUT_BYTES-1}}}]]
    binary scan [string range $row 0 3] cu* config;lassign $config op page bank force
    binary scan [string range $row 26 33] cu* fields;lassign $fields top col family source line copy coarse footer
    debug write memory 0xC2F0 $op;debug write memory 0xC2F1 $bank
    debug write memory 0xC200 $page;debug write memory 0xC230 [expr {{$page*3+$bank}}];debug write memory 0xC2E2 $force
    debug write memory 0xC22A $top;debug write memory 0xC229 $col;debug write memory 0xC227 $family;debug write memory 0xC224 $source
    debug write memory 0xC22B $line;debug write memory 0xC225 $copy;debug write memory 0xC223 $coarse;debug write memory 0xC245 $footer
    set address [expr {{($page ? 0xCD00 : 0xC800)+$top*32+$col}}]
    debug write memory 0xC22D [expr {{$address&255}}];debug write memory 0xC22E [expr {{$address>>8}}]
    set ::key [string range $row 4 9];set ::tile [string range $row 10 25]
    debug write_block memory 0xCC90 $::key;debug write_block memory 0xC480 $::tile
    reg SP 0xF380;reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_fixedput target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    debug write_block VRAM 0 [string repeat [binary format c 165] 16384]
    set ::slot [debug read ioports 168]
    set VDP.too_fast_vram_access_callback {{fail_fixedput fast-vram}}
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['unit_run']&255} {syms['unit_run']>>8} 195 102 199 24 254}}]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{0xC000 512 0xC300 256 0xC600 352 0xCB00 384 0xCC80 16 0xCC96 10 0xCCA6 90 0xDA08 2040 0xE200 64 0xE280 640 0xE800 2880}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_fixedput "guard $address"}}
        }}
        if {{[debug read_block memory 0xCC90 6] ne $::key || [debug read_block memory 0xC480 16] ne $::tile}} {{fail_fixedput input}}
        if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_fixedput abi}}
        puts -nonewline $::actual "[binary format cu* [list [reg A] [expr {{[reg F]&1}}] [debug read memory 0xC231]]][debug read_block memory 0xD000 2568][debug read_block memory 0xC800 768][debug read_block memory 0xCD00 768][debug read_block VRAM 0 16384][debug read_block memory 0xE240 64][debug read_block memory 0xCCA0 6]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_fixedput
    }}}}
    dispatch_fixedput
}}}}]
after time 60 {{fail_fixedput watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_FixedPut','-cart',str(artifact),'-romtype','ASCII16','-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=120)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or 'FIXED_PUT_FAIL' in log:raise ValueError('actual fixed publication failed: '+log[-1400:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=count*ROW_BYTES or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('fixed publication captures/fixtures incomplete or changed')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:
            (out/'failure.json').write_text(json.dumps({'index':index,'input':list(inputs[index*INPUT_BYTES:(index+1)*INPUT_BYTES]),'error':str(error)},indent=2)+'\n')
            raise
    times=[list(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete ordered fixed publication timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('fixed publication producers changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,'rom_sha256':digest(artifact),
        'artifacts':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual-Z80 fixed-role publication with deterministic constructor stub. Whole metadata,16KiB VRAM,both CPU NAME pages,fuse ordinals,all6groups/footer generations,cache hits/key changes/invalid bounds/constructor faults. Real typed constructor and game/frame acceptance separate.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({key:report[key] for key in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    check(**vars(parser.parse_args()))
