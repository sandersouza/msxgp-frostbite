"""Directed query integration against v30 electrical rows, outside natural routes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from compact_floe import FloeOracle
from compact_live_probe import CONTROL_SHA
from environment import ROOT
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def check(build,out,kind):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes());rom=build/m['rom']['filename']
    sha=lambda b:hashlib.sha256(b).hexdigest()
    if sha(rom.read_bytes())!=m['rom']['sha256']:raise ValueError('ROM changed')
    if any(sha((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    control=ROOT/'outputs/presentation/credit-reference-at/build-final'
    cm=json.loads((control/'build.json').read_bytes());cr=(control/cm['rom']['filename']).read_bytes()
    if sha(cr)!=CONTROL_SHA:raise ValueError('sealed control required')
    oracle=FloeOracle(cr,cm);s=symbols(build/'presentation.sym')
    inputs=bytearray();expected=bytearray()
    def emit(mode,y,x,px,view):
        pose,remainder=divmod(view,38);shift,reflect=divmod(remainder,2)
        inputs.extend((mode,y,x,px,pose,shift,reflect))
        if kind=='enemy':want=oracle.ordinary_sample(s['hazard_ordinary_common_modes'],mode,y,x,view)
        else:
            mask,shadow=oracle.records[oracle.shore_row(s['hazard_shore_modes'],mode,px,y)[x]]
            want=7|(128 if mask>>view&1 else 0)|(64 if shadow>>view&1 else 0)
        expected.append(want)
    if kind=='enemy':
        for mode in range(66):
            for y in range(26):
                for dx in range(15):emit(mode,y,dx,25+(len(expected)%127),len(expected)%228)
        for view in range(228):emit(view%66,view%26,view%15,80,view)
        entry=symbols(build/'ci-code.sym')['ci_common']
    else:
        for mode in range(6):
            for px in range(160):
                for bx in range(160):emit(mode,len(expected)%35,bx,px,len(expected)%228)
        for mode in range(6):
            for y in range(35):
                for view in range(228):
                    px=(*range(25),*range(152,160))[view%33]
                    emit(mode,y,(y*17+view)%160,px,view)
        entry=symbols(build/'cs-code.sym')['cs_common']
    allowed=set(range(0xF300,0xF380))
    for first,last in ((0x3300,0x3307),(0x0FC0,0x0FE0),(0x2970,0x2999),(0x0E10,0x0E6A),(0x7000,0x7001),(0xE882,0xE883)):
        allowed.update(range(first,last))
    forbidden=[];start=None
    for address in range(65537):
        if address<65536 and address not in allowed:
            if start is None:start=address
        elif start is not None:forbidden.append((start,address-1));start=None
    ranges=' '.join('{' +str(a)+' '+str(b)+'}' for a,b in forbidden)
    out.mkdir(parents=True);(out/'inputs.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_Glue.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set checking 0
set index 0
set f [open {{{out/'inputs.bin'}}} rb];set inputs [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
proc fail_glue {{message}} {{puts stderr "GLUE_FAIL $message case=$::index";exit 1}}
proc dispatch_glue {{}} {{
 if {{$::index=={len(expected)}}} {{close $::result;exit;return}}
 set ::checking 0
 binary scan [string range $::inputs [expr {{$::index*7}}] [expr {{$::index*7+6}}]] cu* values
 lassign $values mode y x px pose shift reflect
 debug write memory 0xC793 $x;debug write memory 0xC794 $y
 debug write memory 0xC066 $px;debug write memory 0xC06E $pose
 debug write memory 0xC06B $shift;debug write memory 0xC06C [expr {{$reflect*8}}]
 set view [expr {{$pose*38+$shift*2+$reflect}}]
 debug write memory 0xC785 [expr {{$view/8}}];debug write memory 0xC786 [expr {{1<<($view%8)}}]
 reg HL $mode;reg AF [expr {{$px*256}}];reg IX 0xDDDD;reg IY 0xEEEE;reg SP 0xF380
 reg PC 0xC6D0;set ::checking 1;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {s['t_main.frame']} {{}} {{debug remove_bp $::boot;debug break;after break {{
 if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_glue machine}}
 debug write_block memory 0xC6D0 [binary format cu* [list 243 205 {entry&255} {entry>>8} 195 215 198 24 254]]
 foreach range {{{ranges}}} {{debug set_watchpoint write_mem $range {{$::checking}} {{fail_glue "undeclared-write $::wp_last_address"}}}}
 debug set_bp 0xC6D7 {{}} {{debug break;after break {{
  if {{[reg IX]!=0xDDDD || [reg IY]!=0xEEEE || [reg SP]!=0xF380 || ([reg IFF]&3)!=0}} {{fail_glue abi}}
  set cycles [expr {{round(([machine_info time]-$::started)*3579545)}}]
  puts -nonewline $::result [binary format cu [expr {{[reg AF]>>8}}]]
  puts -nonewline $::result [binary format cu* [list [expr {{$cycles&255}}] [expr {{($cycles>>8)&255}}] [expr {{($cycles>>16)&255}}] [expr {{($cycles>>24)&255}}]]]
  incr ::index;dispatch_glue
 }}}}
 dispatch_glue
}}}}]
after time {60+len(expected)*.03} {{fail_glue watchdog}}
'''
    (out/'probe.tcl').write_text(script)
    r=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_Glue','-cart',str(rom),'-romtype','ASCII16','-script',str(out/'probe.tcl')],
        env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=1200)
    (out/'emulator.log').write_text(r.stdout+r.stderr)
    if r.returncode or 'GLUE_FAIL' in r.stdout+r.stderr:raise ValueError('native glue failed: '+(r.stdout+r.stderr)[-1200:])
    raw=(out/'actual.bin').read_bytes();count=len(expected)
    if len(raw)!=count*5:raise ValueError('partial shore output')
    actual=raw[::5]
    cycles=[int.from_bytes(raw[i*5+1:i*5+5],'little') for i in range(count)]
    if actual!=expected:
        i=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
        raise ValueError(f'shore differs at{i}: inputs={list(inputs[i*7:(i+1)*7])}, got={actual[i]:02x} want={expected[i]:02x}')
    if any(sha((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    receipt=dict(complete=True,kind="complete-shore-query",cases=len(expected),rom_sha256=m['rom']['sha256'],oracle_rom_sha256=CONTROL_SHA,
        directed_integration_only=True,all_axes_covered=True,cartesian_all_views=False,bounded_cpu_writes=True,
        cycles_including_call=dict(min=min(cycles),mean=sum(cycles)/count,max=max(cycles)),
        output_sha256=sha(actual),producer_sha256=sha(Path(__file__).read_bytes()))
    (out/'glue-check.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out,'shore')
