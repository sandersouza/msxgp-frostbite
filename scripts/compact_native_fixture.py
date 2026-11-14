"""Bounded standard-MSX1 component runner; never a playable release builder."""
import hashlib
import os
from pathlib import Path
import shutil
import statistics
import subprocess

from environment import ROOT,verified_tool
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def run(out,assembly,inputs,expected,*,input_address,input_stride,output_address,
        output_stride,entry_name,end_name,writes):
    """Compare fixed-size output rows, poison output, guard all undeclared writes."""
    if not inputs or input_stride<=0 or len(inputs)%input_stride:raise ValueError('complete input rows required')
    count=len(inputs)//input_stride
    if output_stride<=0 or len(expected)!=count*output_stride:raise ValueError('complete expected rows required')
    if not 0xC000<=input_address<input_address+input_stride<=0xF300:raise ValueError('bounded input buffer required')
    if not 0xC000<=output_address<output_address+output_stride<=0xF300:raise ValueError('bounded output buffer required')
    allowed=set(range(0xF300,0xF380))
    for start,end in writes:
        if not 0xC000<=start<=end<0xF300:raise ValueError('bounded declared scratch required')
        allowed.update(range(start,end+1))
    if not set(range(output_address,output_address+output_stride))<=allowed:raise ValueError('output writes must be declared')
    if set(range(input_address,input_address+input_stride))&allowed:raise ValueError('inputs must be immutable')
    forbidden=[];start=None
    for address in range(65537):
        if address<65536 and address not in allowed:
            if start is None:start=address
        elif start is not None:forbidden.append((start,address-1));start=None
    out=Path(out);(out/'inputs.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    (out/'fixture.asm').write_text(assembly)
    assembler=verified_tool('sjasmplus');fixture=out/'component-fixture.rom'
    r=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={fixture}',f'--sym={out/"fixture.sym"}',str(out/'fixture.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError('component assembly failed: '+(r.stdout+r.stderr)[-1600:])
    if fixture.stat().st_size!=32768:raise ValueError('Normal32K component fixture required')
    q=symbols(out/'fixture.sym');entry=q[entry_name]
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Component.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    ranges=' '.join(f'{{{start} {end}}}' for start,end in forbidden)
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set checking 0
set count 0
set f [open {{{out/'inputs.bin'}}} rb];set inputs [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
proc fail_component {{message}} {{puts stderr "COMPONENT_FAIL $message case=$::count";exit 1}}
proc dispatch_component {{}} {{
 if {{$::count=={count}}} {{close $::result;exit;return}}
 set ::checking 0;set at [expr {{$::count*{input_stride}}}]
 debug write_block memory {input_address} [string range $::inputs $at [expr {{$at+{input_stride-1}}}]]
 debug write_block memory {output_address} [string repeat [binary format cu 165] {output_stride}]
 reg PC 0xC6D0;set ::started [machine_info time];set ::checking 1;debug cont
}}
set boot [debug set_bp {q['ready']} {{}} {{
 debug remove_bp $::boot;debug break
 after break {{
  if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_component target}}
  reg IX 0xDDDD;reg IY 0xEEEE;reg SP 0xF380
  debug write_block memory 0xC6D0 [binary format cu* [list 205 {entry&255} {entry>>8} 195 214 198 24 254]]
  foreach range {{{ranges}}} {{debug set_watchpoint write_mem $range {{$::checking}} {{fail_component "write address=$::wp_last_address PC=[reg PC]"}}}}
  debug set_bp 0xC6D6 {{}} {{debug break;after break {{
   if {{[reg IX]!=0xDDDD || [reg IY]!=0xEEEE || [reg SP]!=0xF380 || ([reg IFF]&3)!=0}} {{fail_component abi}}
   set cycles [expr {{round(([machine_info time]-$::started)*3579545)}}]
   if {{$cycles<=0 || $cycles>=65536}} {{fail_component cycle-range}}
   puts -nonewline $::result [debug read_block memory {output_address} {output_stride}]
   puts -nonewline $::result [binary format cu* [list [expr {{$cycles&255}}] [expr {{$cycles>>8}}]]]
   incr ::count;dispatch_component
  }}}}
  dispatch_component
 }}
}}]
after time {60+count*.02} {{fail_component watchdog}}
'''
    (out/'probe.tcl').write_text(tcl)
    r=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Component','-cart',str(fixture),'-romtype','Normal','-script',str(out/'probe.tcl')],env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=1200)
    (out/'emulator.log').write_text(r.stdout+r.stderr)
    if r.returncode or 'COMPONENT_FAIL' in r.stdout+r.stderr:raise ValueError('component failed: '+(r.stdout+r.stderr)[-1600:])
    actual=(out/'actual.bin').read_bytes();stride=output_stride+2
    if len(actual)!=count*stride:raise ValueError('component output count differs')
    for i in range(count):
        if actual[i*stride:i*stride+output_stride]!=expected[i*output_stride:(i+1)*output_stride]:
            raise ValueError(f'native output differs at{i}, input={list(inputs[i*input_stride:(i+1)*input_stride])}')
    cycles=[int.from_bytes(actual[i*stride+output_stride:(i+1)*stride],'little') for i in range(count)]
    return dict(complete=True,component_fixture_only=True,game_runtime_changed=False,cases=count,outputs_equal=True,
        component_rom_sha256=sha(fixture),code_bytes=q[end_name]-entry,
        bounded_writes=True,ix_iy_sp_preserved=True,
        cycles_including_call_and_jump=dict(min=min(cycles),mean=statistics.mean(cycles),p95=sorted(cycles)[int(count*.95)],max=max(cycles)),
        emulator_sha256=sha(emulator),assembler_sha256=sha(assembler),machine_profile_sha256=hashlib.sha256(profile).hexdigest())
