"""Actual PSG callbacks, source-register isolation and both GPIO direction bits.

Synthetic hardware-register streams, separate from original-game integration.
Every callback is retained even when it produces no physical PSG write.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from environment import ROOT,verified_tool
from presentation_audio import tables,psg_step
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile

FILES=('scripts/presentation_audio_native_check.py','scripts/presentation_audio.py','src/presentation_audio.asm',
    'scripts/environment.py','scripts/reference_traces.py','scripts/render_build.py','scripts/smoke.py')
INPUT_BYTES=5
ROW_BYTES=48


def fixtures():
    inputs=bytearray();expected=bytearray();expected_writes=[];groups=[]
    for group,ports in enumerate((0,64,128,192)):
        source=bytearray(6);state={'psg':bytes((1,0,1,0,165,3,1,ports|63,0,0,0,0,0,0,0,0))}
        def add(address,value,method):
            nonlocal state
            index=len(inputs)//INPUT_BYTES
            inputs.extend(bytes((group,method))+address.to_bytes(2,'little')+bytes((value,)))
            if 0xC715<=address<=0xC71A:
                source[address-0xC715]=value
                state=psg_step(bytes(source),state)
                expected_writes.extend((index,reg,data) for reg,data in state['writes'])
            else:state={**state,'writes':()}
            mask=state.get('source_registers',bytes(6))
            parts=bytes(9 if mask[ch]in(0,11) else 1 if mask[ch]==8 else 8 for ch in (0,1))
            cached=bytearray(state['psg'][:11]);cached[4:6]=bytes(2)
            work=mask+bytes(cached)+bytes((ports,255 if state.get('noise_owner')is None else state['noise_owner']))+parts+bytes([165])*11
            expected.extend(state['psg']+work);groups.append(group)
        for control in range(16):
            for frequency in range(32):
                values=(control,(control+7)%16,frequency,31-frequency,(frequency+control)%16,15)
                for channel,value in enumerate(values):
                    add(0xC715+channel,value,0);add(0xC715+channel,value,1)
        for field in range(6):
            for value in range(256):add(0xC715+field,value,value&1)
        for other in range(16):
            add(0xC715,8,0);add(0xC716,other,1);add(0xC719,15,0);add(0xC71A,15,1)
            add(0xC717,2,0);add(0xC718,5,1);add(0xC719,0,0);add(0xC71A,0,1)
        for address in (0xC714,0xC71B,0xC615,0xC015,0xC795):add(address,12,1)
    return bytes(inputs),bytes(expected),expected_writes,groups


def verify_row(actual,expected,peripherals):
    if len(actual)!=ROW_BYTES or len(expected)!=ROW_BYTES or len(peripherals)!=5:raise ValueError('complete PSG/work/peripheral capture required')
    wanted=expected[:11]+peripherals+expected[16:]
    if actual!=wanted:raise ValueError('whole PSG/audio work differs')


def check(out,inject_gpio=False):
    if type(inject_gpio)is not bool:raise ValueError('explicit GPIO negative-control selection required')
    digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();producer={name:digest(ROOT/name) for name in FILES}
    inputs,expected,writes,groups=fixtures();count=len(inputs)//INPUT_BYTES;out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'cases.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected);data=tables();(out/'tables.bin').write_bytes(data['data'])
    include='    ALIGN 256\np_audio_periods:\n'+f'    INCBIN "{out/"tables.bin"}"\n'
    include+='p_audio_noise_periods EQU p_audio_periods+384\np_audio_mixer_parts EQU p_audio_periods+416\np_audio_defaults EQU p_audio_periods+432\n    ALIGN 32\np_audio_tone_pointers:\n    DW '+','.join('0' if row is None else f'p_audio_periods+{row*64}' for row in data['tone_rows'])+'\n'
    (out/'tables.inc').write_text(include)
    entry='''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
start:
    DI
    LD SP,$F380
ready:
    JP ready
    INCLUDE "presentation_audio.asm"
'''+include+'    DS $C000-$,$FF\n'
    (out/'unit.asm').write_text(entry);artifact=out/'unit.rom';assembler=verified_tool('sjasmplus')
    compiled=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={artifact}',f'--sym={out/"unit.sym"}',str(out/'unit.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:raise ValueError('audio assembler failed: '+compiled.stderr[-1800:])
    syms=symbols(out/'unit.sym');emulator=Path(shutil.which('openmsx')).resolve()
    effective=ET.fromstring(isolated_profile(find_machine_profile(str(emulator))))
    # Standard PSG silicon supports both direction bits. Disable openMSX's
    # convenience repair so this component cannot hide a bad GPIO write.
    ET.SubElement(effective.find('.//PSG'),'ignorePortDirections').text='false'
    profile=b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">'+ET.tostring(effective);validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Audio.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    targets=' '.join(str(syms[f'p_audio_event_{n:02X}']) for n in range(21,27))
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set index 0
set group -1
set active 0
set observe_io 0
set selected -1
if {{[info exists invalid_psg_directions_callback]}} {{set invalid_psg_directions_callback {{}}}}
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set actual [open {{{out/'actual.bin'}}} wb];set timing [open {{{out/'cycles.tsv'}}} w]
set writes [open {{{out/'writes.tsv'}}} w];set peripherals [open {{{out/'peripherals.bin'}}} wb]
proc fail_audio {{message}} {{puts stderr "AUDIO_NATIVE_FAIL $message index=$::index";exit 1;return -code error $message}}
proc registers_audio {{}} {{return [list [reg AF] [reg BC] [reg DE] [reg HL] [reg IX] [reg IY] [reg SP] [reg IFF]]}}
debug set_watchpoint write_io {{160 161}} {{}} {{
    if {{![info exists ::wp_last_address] || ![info exists ::wp_last_value]}} {{fail_audio watchpoint-payload}}
    if {{($::wp_last_address&255)==160}} {{
        set ::selected $::wp_last_value
        if {{$::observe_io && $::selected ni {{0 1 2 3 6 7 8 9 10}}}} {{fail_audio unowned-register-selected}}
    }} elseif {{$::observe_io}} {{
        if {{$::selected ni {{0 1 2 3 6 7 8 9 10}}}} {{fail_audio unowned-register-written}}
        if {{$::selected==7 && ($::wp_last_value&192)!=$::ports}} {{fail_audio gpio-write}}
        if {{$::active}} {{puts $::writes "$::index $::selected $::wp_last_value"}}
    }}
}}
proc dispatch_audio {{}} {{
    if {{$::index=={count}}} {{close $::actual;close $::timing;close $::writes;close $::peripherals;exit;return}}
    binary scan [string range $::cases [expr {{$::index*5}}] [expr {{$::index*5+4}}]] cu* data
    lassign $data group method lo hi value;set ::address [expr {{$hi*256+$lo}}];set ::value $value
    if {{$group!=$::group}} {{
        set ::group $group;set ::ports [expr {{$group*64}}]
        set ::active 0
        for {{set reg 0}} {{$reg<16}} {{incr reg}} {{debug write {{PSG regs}} $reg 0}}
        debug write {{PSG regs}} 4 165;debug write {{PSG regs}} 5 3
        set ::ctone [debug read_block {{PSG regs}} 4 2]
        debug write {{PSG regs}} 7 [expr {{$::ports|63}}]
        debug write {{PSG regs}} 14 90;debug write {{PSG regs}} 15 165
        set ::unowned [debug read_block {{PSG regs}} 11 5];puts -nonewline $::peripherals $::unowned
        debug write_block memory 0xE000 [string repeat [binary format c 165] 32]
        debug write_block memory 0xC715 [string repeat [binary format c 0] 6]
        debug write_block memory 0xC760 [binary format cu* {{205 {syms['p_audio_init']&255} {syms['p_audio_init']>>8} 195 107 199 24 254 0 0 0 0}}]
        reg SP 0xF380;reg PC 0xC760;set ::observe_io 1;debug cont;return
    }}
    set target [expr {{$method ? {syms['p_audio_event_indexed']} : [lindex [list {targets}] [expr {{$::address-0xC715}}]]}}]
    debug write memory $::address $value
    debug write_block memory 0xC760 [binary format cu* [list 205 [expr {{$target&255}}] [expr {{$target>>8}}] 195 102 199 24 254]]
    reg AF 0xA9D7;reg BC 0x57A9;reg DE 0x713F;reg HL [expr {{$method ? $::address : 0x8765}}];reg IX 0xDEAD;reg IY 0xFEDC;reg SP 0xF380;reg PC 0xC760
    set ::before_regs [registers_audio]
    set ::before_ram "[debug read_block memory 0xC000 0x760][debug read_block memory 0xC768 0x1898][debug read_block memory 0xE020 0x1320]"
    set ::started [machine_info time];set ::active 1;debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{debug remove_bp $::boot;debug break;after break {{
    if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_audio target}}
    debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
    set ::slot [debug read ioports 168];set ::vram [debug read_block VRAM 0 16384]
    if {{{int(inject_gpio)}}} {{debug set_bp {syms['p_audio_write_port']} {{$::active && [reg B]==7}} {{reg A [expr {{[reg A]^64}}]}}}}
    debug set_bp 0xC76B {{}} {{debug break;after break {{dispatch_audio}}}}
    debug set_bp 0xC766 {{}} {{debug break;after break {{
        set ::active 0
        if {{[registers_audio] ne $::before_regs || [reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_audio source-registers}}
        set after "[debug read_block memory 0xC000 0x760][debug read_block memory 0xC768 0x1898][debug read_block memory 0xE020 0x1320]"
        if {{$after ne $::before_ram || [debug read_block VRAM 0 16384] ne $::vram}} {{fail_audio guarded-ram-or-vram}}
        if {{[debug read_block {{PSG regs}} 4 2] ne $::ctone || [debug read_block {{PSG regs}} 11 5] ne $::unowned || ([debug read {{PSG regs}} 7]&192)!=$::ports}} {{fail_audio "unowned-psg expected=[binary encode hex $::unowned] actual=[binary encode hex [debug read_block {{PSG regs}} 11 5]] gpio=[debug read {{PSG regs}} 7] ports=$::ports"}}
        puts -nonewline $::actual "[debug read_block {{PSG regs}} 0 16][debug read_block memory 0xE000 32]"
        puts $::timing "$::index [expr {{round(([machine_info time]-$::started)*3579545)}}]"
        incr ::index;dispatch_audio
    }}}}
    dispatch_audio
}}}}]
after time 600 {{fail_audio watchdog}}
'''
    (out/'launch.tcl').write_text(script)
    result=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Audio','-cart',str(artifact),'-script',str(out/'launch.tcl')],cwd=ROOT,
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(out/'emulator.log').write_text(log)
    if result.returncode or any(term in log.lower() for term in ('audio_native_fail','error executing','invalid command name',"can't read")):raise ValueError('audio native capture failed: '+log[-1800:])
    actual=(out/'actual.bin').read_bytes();peripherals=(out/'peripherals.bin').read_bytes()
    if len(actual)!=len(expected) or len(peripherals)!=20 or (out/'cases.bin').read_bytes()!=inputs or (out/'expected.bin').read_bytes()!=expected:raise ValueError('incomplete/changed native audio evidence')
    for index,group in enumerate(groups):
        try:verify_row(actual[index*ROW_BYTES:(index+1)*ROW_BYTES],expected[index*ROW_BYTES:(index+1)*ROW_BYTES],peripherals[group*5:group*5+5])
        except ValueError as error:raise ValueError(f'case{index} {list(inputs[index*5:index*5+5])}: {error}') from error
    observed=[tuple(map(int,line.split())) for line in (out/'writes.tsv').read_text().splitlines()]
    if observed!=writes:raise ValueError('physical PSG write order/value/count differs')
    times=[tuple(map(int,line.split())) for line in (out/'cycles.tsv').read_text().splitlines()]
    if len(times)!=count or any(len(row)!=2 or row[0]!=i or row[1]<=0 for i,row in enumerate(times)):raise ValueError('incomplete native audio timing')
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('native audio producer changed')
    report={'complete':True,'callbacks':count,'physical_psg_writes':len(writes),'max_cycles_including_rpc':max(row[1] for row in times),
        'producer_files':producer,'rom_sha256':digest(artifact),'emulator_sha256':digest(emulator),'artifacts':{str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()},
        'native_accepted':False,'frame_deadline_accepted':False,
        'scope':'Synthetic actual-Z80 fixed/indexed source-audio callbacks and physical PSG write histories: all16 controls/32 frequencies/both channels, raw mask bytes, same-value events, noise ownership and four GPIO direction settings. WholePSG/audio32B work; AF/BC/DE/HL/IX/IY/SP/IFF/canonical/C6/heap/VRAM/slot and unownedPSG preserved. No original-game hooks, listening, physical hardware or combined timing acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','callbacks','physical_psg_writes','max_cycles_including_rpc')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--inject-gpio',action='store_true')
    check(**vars(p.parse_args()))
