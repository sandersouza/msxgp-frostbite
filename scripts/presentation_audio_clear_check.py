"""Actual-Z80 clear lowering: source event order, epochs and unchanged VM ABI.

Apply handlers are intentionally destructive logging stubs here. The real PSG
callbacks have their own complete I/O proof; this checks the clear wrapper.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

from environment import ROOT,verified_tool
from native_audio_codegen import clear_events
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=('scripts/presentation_audio_clear_check.py','scripts/native_audio_codegen.py','src/presentation_audio_clear.asm','src/native_cpu.asm',
    'scripts/environment.py','scripts/reference_traces.py','scripts/render_build.py','scripts/smoke.py')
ROW_BYTES=513


def fixtures():
    inputs=bytearray();expected=bytearray()
    for whole in (0,1):
        for start in range(256):
            inputs.extend(bytes((whole,start)));ram=bytearray([165])*128;io=bytearray([165])*64;abi=bytearray([165])*256;log=bytearray([165])*48
            events=clear_events(start)
            for ordinal,(reg,value) in enumerate(events):
                io[reg]=0;log[ordinal*4:ordinal*4+4]=bytes((reg,value,0,165))
            registers=(0xA9D7,start*256+169,0x713F,0x8765,0xDEAD,0xFEDC,0xF380,0)
            if whole:
                for index in range(start,256):
                    if index<128:io[index&63]=0
                    else:ram[index-128]=0
                abi[11]=128;registers=(0x0044,169,0x713F,0xC07F,0xC07F,0xC000,0xF380,0)
            expected.extend(ram+io+abi+log+bytes((len(events),))+struct.pack('<8H',*registers))
    return bytes(inputs),bytes(expected)


def verify_row(actual,expected):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES:raise ValueError('whole clear payload truncates')
    if actual!=expected:
        at=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
        raise ValueError(f'clear RAM/IO/ABI/event order/epoch/CPU differs at byte{at}')


def check(out,inject_late=False):
    if type(inject_late)is not bool:raise ValueError('explicit late-clear negative control required')
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest();producer={name:sha(ROOT/name) for name in FILES}
    inputs,expected=fixtures();count=len(inputs)//2;out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    source=(ROOT/'src/native_cpu.asm').read_text();clear=source[source.index('core_clear:'):source.index('core_bit:')]
    helper=(ROOT/'src/presentation_audio_clear.asm').read_text()
    if inject_late:
        old='    CALL p_audio_emit_clear\n    JP core_clear'
        if helper.count(old)!=1:raise ValueError('clear wrapper negative boundary missing')
        helper=helper.replace(old,'    CALL core_clear\n    JP p_audio_emit_clear')
    (out/'clear.asm').write_text(helper)
    stubs=''.join(f'p_audio_apply_{reg:02X}:\n    LD C,{reg}\n    LD HL,${0xC700+reg:04X}\n    JP log_clear\n' for reg in range(21,27))
    stubs+='''log_clear:
    LD B,A
    LD A,(HL)
    PUSH AF
    LD A,($E130)
    ADD A,A
    ADD A,A
    LD E,A
    LD D,0
    LD HL,$E100
    ADD HL,DE
    LD (HL),C
    INC HL
    LD (HL),B
    INC HL
    POP AF
    LD (HL),A
    INC HL
    LD A,($C001)
    LD (HL),A
    LD HL,$E130
    INC (HL)
    LD BC,$1357
    LD DE,$2468
    LD HL,$369C
    LD A,$12
    SCF
    RET
'''
    entry='''    DEFINE FAST_PHASE
    ORG $4000
    DB "AB"
    DW start
    DS 12,0
core_stack_high EQU $C60B
start:
    DI
    LD SP,$F380
ready:
    JP ready
'''+f'    INCLUDE "{out/"clear.asm"}"\n'+clear+stubs+'    DS $C000-$,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    result=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('clear wrapper assembler failed: '+result.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_AudioClear.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
proc fail_clear {{message}} {{puts stderr "AUDIO_CLEAR_FAIL $message index=$::index";exit 1;return -code error $message}}
proc dispatch_clear {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;exit;return}}
    set whole [expr {{$::index/256}}];set source_x [expr {{$::index%256}}]
    debug write_block memory 0xC000 [string repeat [binary format c 165] 128]
    debug write_block memory 0xC600 [string repeat [binary format c 165] 256]
    debug write_block memory 0xC700 [string repeat [binary format c 165] 64]
    debug write_block memory 0xE100 [string repeat [binary format c 165] 48];debug write memory 0xE130 0
    set target [expr {{$whole ? {syms['p_audio_core_clear']} : {syms['p_audio_emit_clear']}}}]
    debug write_block memory 0xC760 [binary format cu* [list 205 [expr {{$target&255}}] [expr {{$target>>8}}] 195 102 199 24 254]]
    reg AF 0xA9D7;reg BC [expr {{$source_x*256+169}}];reg DE 0x713F;reg HL 0x8765;reg IX 0xDEAD;reg IY 0xFEDC;reg SP 0xF380;reg PC 0xC760
    set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_clear target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384];set ::psg [debug read_block {{PSG regs}} 0 16]
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        foreach {{address size}} {{0xC080 0x580 0xC740 32 0xC768 0x1998 0xE131 0x120F}} {{
            if {{[debug read_block memory $address $size] ne [string repeat [binary format c 165] $size]}} {{fail_clear "guard $address"}}
        }}
        if {{[debug read_block VRAM 0 16384] ne $::vram || [debug read_block {{PSG regs}} 0 16] ne $::psg || [debug read ioports 168]!=$::slot}} {{fail_clear devices}}
        puts -nonewline $::actual "[debug read_block memory 0xC000 128][debug read_block memory 0xC700 64][debug read_block memory 0xC600 256][debug read_block memory 0xE100 49]"
        foreach name {{AF BC DE HL IX IY SP IFF}} {{puts -nonewline $::actual [binary format cu* [list [expr {{[reg $name]&255}}] [expr {{[reg $name]>>8}}]]]}}
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_clear
    }}}}
    dispatch_clear
}}}}]
after time 120 {{fail_clear watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_AudioClear','-cart',str(artifact),'-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=run.stdout+run.stderr;(out/'emulator.log').write_text(log)
    if run.returncode or any(term in log.lower() for term in ('audio_clear_fail','error executing','fatal error',"can't read")):raise ValueError('clear native capture failed: '+log[-1500:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=len(expected) or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed clear-wrapper evidence')
    for index in range(count):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES])
        except ValueError as error:raise ValueError(f'case{index}: {error}') from error
    times=[tuple(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete clear-wrapper timing')
    if any(sha(ROOT/name)!=value for name,value in producer.items()):raise ValueError('clear-wrapper producer changed')
    report={'complete':True,'cases':count,'max_cycles_including_rpc':max(row[1] for row in times),'producer_files':producer,'rom_sha256':sha(artifact),
        'artifacts':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},'frame_deadline_accepted':False,
        'scope':'Actual Z80 clear audio emission and existing shared clear summary at all256 entry-X values. Destructive apply stubs log decoded address/raw value/actual bus value/canonical frame epoch before RAM clearing. Wholecanonical128/IO64/ABI256/event49/CPU registers plus otherRAM/heap/VRAM/PSG/slot guards. Stubbed PSG apply, not real audio/source-game/combined-frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--inject-late',action='store_true')
    check(**vars(p.parse_args()))
