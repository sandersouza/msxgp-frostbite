"""Qualify generic8/18-row accumulation against sealed source and boundary cases."""
import argparse
import hashlib
from itertools import islice
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess

from compact_floe_edge import edge_row_convolve
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def check(control,out,limit=None):
    if limit is not None and (type(limit) is not int or limit<=0):raise ValueError('positive limit required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);control=Path(control).resolve()
    receipt_raw=(control/'component-result.json').read_bytes();receipt=json.loads(receipt_raw)
    if not receipt['complete_native_program_domain'] or receipt['cases']!=16170672 or not receipt['outputs_equal']:
        raise ValueError('complete sealed floe accumulation control required')
    if any(sha(control/s)!=h for s,h in receipt['files'].items()):raise ValueError('control file differs')
    if sha(ROOT/'src/compact_floe_edge_row.asm')!=receipt['sources']['src/compact_floe_edge_row.asm']:
        raise ValueError('qualified row evaluator differs')
    names=('scripts/compact_mask_probe.py','scripts/compact_floe_edge.py','src/compact_floe_edge_row.asm','src/compact_mask_program.asm')
    source={s:sha(ROOT/s) if (ROOT/s).exists() else None for s in names}
    for s in names:
        if (ROOT/s).exists():
            p=out/'source'/s;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/s).read_bytes())
    glyphs=(control/'glyphs.bin').read_bytes();bases=(control/'bases.bin').read_bytes()
    original_programs=(control/'programs.bin').read_bytes();original_expected=(control/'expected.bin').read_bytes()
    if len(original_programs)!=2086*39:raise ValueError('complete program control required')
    programs=[]
    for i in range(2086):
        old=original_programs[i*39:(i+1)*39]
        program=b''.join(old[row*4:row*4+4]+bytes((old[32+row] if row<7 else 0,)) for row in range(8))
        programs.append(program.ljust(90,b'\0'))
    views=[]
    for view in range(228):
        pose,remainder=divmod(view,38);shift,reflection=divmod(remainder,2)
        at=reflection*256+bases[pose]+shift
        views.append((pose,shift,reflection,glyphs[at:at+19]))
    def cases():
        for index in range(2086):
            for yi in range(34):
                view=(index*17+yi*19)%228
                pose,shift,reflection,_=views[view]
                y=0 if yi==0 else yi+44
                expected=original_expected[(index*34+yi)*228+view]
                yield bytes(((y-50)&255,0 if yi==0 else 8,pose,shift,reflection,index&255,index>>8)),expected
        for count in (0,1,8,18):
            fields=((0,0),) if count==0 else tuple((field,bit) for field in range(5) for bit in range(8))
            for field,bit in fields:
                program=bytearray(90);masks=[0]*5
                if count:
                    masks[field]=128>>bit;program[(count-1)*5+field]=128>>bit
                index=len(programs);programs.append(bytes(program))
                for tag in (*range(35),254,255):
                    for pose,shift,reflection,glyph in views:
                        last=(tag-count+1)&255
                        if last>=128:last-=256
                        expected=135 if count and edge_row_convolve(glyph,masks,last) else 7
                        yield bytes((tag,count,pose,shift,reflection,index&255,index>>8)),expected
    inputs,expected=bytearray(),bytearray()
    for row,value in islice(cases(),limit):inputs.extend(row);expected.append(value)
    count=len(expected)
    (out/'inputs.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    (out/'programs.bin').write_bytes(b''.join(programs));(out/'glyphs.bin').write_bytes(glyphs);(out/'bases.bin').write_bytes(bases)
    code=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
          'ce_glyphs EQU $5000','ce_bases EQU $5200',' DS $4100-$,$FF',' INCLUDE "compact_floe_edge_row.asm"',
          ' INCLUDE "compact_mask_program.asm"',' ASSERT $ <= $5000',' DS $5000-$,$FF',
          f' INCBIN "{out/"glyphs.bin"}"',f' INCBIN "{out/"bases.bin"}"',' DS $C000-$,$FF']
    (out/'fixture.asm').write_text('\n'.join(code)+'\n')
    assembler=verified_tool('sjasmplus');fixture=out/'component-fixture.rom'
    run=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={fixture}',f'--sym={out/"fixture.sym"}',str(out/'fixture.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('mask assembler failed: '+(run.stdout+run.stderr)[-1600:])
    if fixture.stat().st_size!=32768:raise ValueError('fixture size differs')
    q=symbols(out/'fixture.sym');entry=q['mp_contact']
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/Frostbite_MaskProgram.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set checking 0
set count 0
set f [open {{{out/'inputs.bin'}}} rb];set inputs [read $f];close $f
set f [open {{{out/'programs.bin'}}} rb];set programs [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
proc fail_program {{message}} {{puts stderr "PROGRAM_FAIL $message case=$::count";exit 1}}
proc dispatch_program {{}} {{
 if {{$::count=={count}}} {{close $::result;exit;return}}
 set ::checking 0
 set at [expr {{$::count*7}}]
 binary scan [string range $::inputs $at [expr {{$at+6}}]] cu* fields
 lassign $fields tag rows pose shift reflection low high
 set program [expr {{($low+256*$high)*90}}]
 debug write_block memory 0xC800 [string range $::programs $program [expr {{$program+89}}]]
 debug write_block memory 0xC7D0 [binary format cu* [list $tag $rows $pose $shift $reflection 0 200]]
 reg PC 0xC6D0
 set ::started [machine_info time]
 set ::checking 1
 debug cont
}}
set boot [debug set_bp {q['ready']} {{}} {{
 debug remove_bp $::boot
 debug break
 after break {{
  if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_program target}}
  reg IX 0xDDDD;reg IY 0xEEEE;reg SP 0xF380
  debug write_block memory 0xC6D0 [binary format cu* [list 205 {entry&255} {entry>>8} 195 214 198 24 254]]
  set ::checking 1
  foreach range {{{{0x0000 0xC78F}} {{0xC799 0xC7D6}} {{0xC7D9 0xF2FF}} {{0xF380 0xFFFF}}}} {{
   debug set_watchpoint write_mem $range {{$::checking}} {{fail_program "write address=$::wp_last_address PC=[reg PC]"}}
  }}
  debug set_bp 0xC6D6 {{}} {{debug break;after break {{
   if {{[reg IX]!=0xDDDD || [reg IY]!=0xEEEE || [reg SP]!=0xF380 || ([reg IFF]&3)!=0}} {{fail_program abi}}
   set cycles [expr {{round(([machine_info time]-$::started)*3579545)}}]
   if {{$cycles<=0 || $cycles>=65536}} {{fail_program cycle-range}}
   puts -nonewline $::result [binary format cu* [list [reg A] [expr {{$cycles&255}}] [expr {{$cycles>>8}}]]]
   incr ::count;dispatch_program
  }}}}
  dispatch_program
 }}
}}]
after time {60+count*0.02} {{fail_program watchdog}}
'''
    (out/'probe.tcl').write_text(tcl)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_MaskProgram','-cart',str(fixture),'-romtype','Normal','-script',str(out/'probe.tcl')],env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=1200)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode or 'PROGRAM_FAIL' in run.stdout+run.stderr:raise ValueError('native program failed: '+(run.stdout+run.stderr)[-1600:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=count*3 or actual[::3]!=expected:
        first=next((i for i,(a,b) in enumerate(zip(actual[::3],expected)) if a!=b),None)
        raise ValueError(f'native generic accumulation differs at{first}')
    cycles=[int.from_bytes(actual[i*3+1:i*3+3],'little') for i in range(count)]
    if {s:sha(ROOT/s) for s in names}!=source:raise ValueError('source changed')
    if (control/'component-result.json').read_bytes()!=receipt_raw or any(sha(control/s)!=h for s,h in receipt['files'].items()):raise ValueError('control changed')
    report=dict(complete=True,component_fixture_only=True,game_runtime_changed=False,cases=count,complete_declared_domain=count==1091680,
        outputs_equal=True,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),sources=source,
        control_receipt_sha256=hashlib.sha256(receipt_raw).hexdigest(),component_rom_sha256=sha(fixture),
        wrapper_code_bytes=q['mp_end']-entry,row_code_bytes=q['cer_end']-q['ce_test_row'],shared_data_bytes=518,
        programs=len(programs),floe_sampled_cases=min(count,2086*34),scratch_bytes=11,ix_iy_sp_preserved=True,bounded_writes=True,
        cycles_including_call_and_jump=dict(min=min(cycles),mean=statistics.mean(cycles),p95=sorted(cycles)[min(count-1,int(count*0.95))],max=max(cycles)),
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()},emulator_sha256=sha(emulator),assembler_sha256=sha(assembler),
        machine_profile_sha256=hashlib.sha256(profile).hexdigest(),
        scope='Generic0/1/8/18-row accumulation: sampled sealed floe classes and complete declared one-hot last-row boundary corpus. Native hazard geometry callers, game integration and cadence remain separate.')
    (out/'component-result.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--limit',type=int)
    a=p.parse_args();r=check(a.control,a.out,a.limit);print({k:v for k,v in r.items() if k not in ('files','sources')})
