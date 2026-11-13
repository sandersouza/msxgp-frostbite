"""Native ordinary-copy coordinate fixture, independent of original assets."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess

from compact_hazard_edge import ordinary_context,ordinary_program
from hazard_domain import shapes
from original_graphics import SOURCE_SHA256
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def check(out,limit=None,stage='context'):
    if stage not in ('context','program'):raise ValueError('declared stage required')
    if limit is not None and (type(limit) is not int or limit<=0):raise ValueError('positive limit required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    names=('scripts/compact_hazard_edge.py','scripts/compact_floe.py','scripts/compact_hazard_probe.py',
           'src/compact_hazard_context.asm','src/compact_hazard_program.asm')
    source={s:sha(ROOT/s) if (ROOT/s).exists() else None for s in names}
    for s in names:
        if (ROOT/s).exists():
            p=out/'source'/s;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/s).read_bytes())
    inputs,expected=bytearray(),bytearray()
    original=None;assets={};locations={}
    if stage=='context':
        for px in range(160):
            for x in range(160):
                for copies in range(4):
                    if limit is not None and len(inputs)//3>=limit:break
                    inputs.extend((px,x,copies));expected.extend(ordinary_context(px,x,copies))
        input_size,data_size=3,4;output_address=0xC790
        entry_name,end_name='cx_context','cx_end';full_count=102400
    else:
        original=(ROOT/'references/roms/frostbite.bin').read_bytes()
        if hashlib.sha256(original).hexdigest()!=SOURCE_SHA256:raise ValueError('canonical original required')
        representatives={}
        for px in (*range(25),*range(152,160)):
            for x in range(160):
                for copies in range(4):representatives.setdefault(ordinary_context(px,x,copies),(px,x,copies))
        if len(representatives)!=1113:raise ValueError('complete exceptional context domain differs')
        domain=shapes(original)
        if len(domain)!=33:raise ValueError('complete shape domain differs')
        glyphs=original[0xD00:0xE00]
        assets=dict(enemy=glyphs+bytes(int(f'{v:08b}'[::-1],2) for v in glyphs),shapes=bytes(domain),samples=bytes(128>>i for i in range(8)))
        locations=dict(enemy=0x5600,shapes=0x5800,samples=0x5830)
        for context,(px,x,copies) in sorted(representatives.items()):
            for index,shape in enumerate(domain):
                for reflection in range(2):
                    if limit is not None and len(inputs)//5>=limit:break
                    inputs.extend((px,x,copies,index,reflection))
                    glyph=assets['enemy'][reflection*256+shape:reflection*256+shape+8]
                    expected.extend(v for row in ordinary_program(glyph,context) for v in row)
        (out/'contexts.json').write_text(json.dumps([dict(context=c,source=r) for c,r in sorted(representatives.items())])+'\n')
        input_size,data_size=5,40;output_address=0xC800
        entry_name,end_name='hp_build','hp_end';full_count=1113*33*2
    count=len(inputs)//input_size
    (out/'inputs.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    code=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380',
          'ready:',' JP ready']
    code += [f'hp_{k} EQU ${a:04X}' for k,a in locations.items()]
    code += [' DS $4100-$,$FF',' INCLUDE "compact_hazard_context.asm"']
    if stage=='program':code += [' INCLUDE "compact_hazard_program.asm"']
    previous_end=None
    for k,a in locations.items():
        (out/(k+'.bin')).write_bytes(assets[k])
        code += [f' ASSERT $ <= ${a:04X}']
        if previous_end!=a:code += [f' DS ${a:04X}-$,$FF']
        code += [f' INCBIN "{out/(k+".bin")}"']
        previous_end=a+len(assets[k])
    code += [' ASSERT $ <= $C000',' DS $C000-$,$FF']
    (out/'fixture.asm').write_text('\n'.join(code)+'\n')
    assembler=verified_tool('sjasmplus');fixture=out/'component-fixture.rom'
    run=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={fixture}',f'--sym={out/"fixture.sym"}',str(out/'fixture.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('context assembler failed: '+(run.stdout+run.stderr)[-1600:])
    if fixture.stat().st_size!=32768:raise ValueError('fixture capacity differs')
    q=symbols(out/'fixture.sym');entry=q[entry_name]
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/Frostbite_HazardContext.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    ranges='{{0x0000 0xC78F} {0xC794 0xF2FF} {0xF380 0xFFFF}}' if stage=='context' else '{{0x0000 0xC78F} {0xC794 0xC79F} {0xC7C0 0xC7FF} {0xC828 0xF2FF} {0xF380 0xFFFF}}'
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set checking 0
set count 0
set f [open {{{out/'inputs.bin'}}} rb];set inputs [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
proc fail_context {{message}} {{puts stderr "CONTEXT_FAIL $message case=$::count";exit 1}}
proc dispatch_context {{}} {{
 if {{$::count=={count}}} {{close $::result;exit;return}}
 set ::checking 0
 set at [expr {{$::count*{input_size}}}]
 debug write_block memory 0xC780 [string range $::inputs $at [expr {{$at+{input_size-1}}}]]
 debug write_block memory {output_address} [string repeat [binary format cu 165] {data_size}]
 reg PC 0xC6D0
 set ::started [machine_info time]
 set ::checking 1
 debug cont
}}
set boot [debug set_bp {q['ready']} {{}} {{
 debug remove_bp $::boot
 debug break
 after break {{
  if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_context target}}
  reg IX 0xDDDD;reg IY 0xEEEE;reg SP 0xF380
  debug write_block memory 0xC6D0 [binary format cu* [list 205 {entry&255} {entry>>8} 195 214 198 24 254]]
  set ::checking 1
  foreach range {ranges} {{
   debug set_watchpoint write_mem $range {{$::checking}} {{fail_context "write address=$::wp_last_address PC=[reg PC]"}}
  }}
  debug set_bp 0xC6D6 {{}} {{debug break;after break {{
   if {{[reg IX]!=0xDDDD || [reg IY]!=0xEEEE || [reg SP]!=0xF380 || ([reg IFF]&3)!=0}} {{fail_context abi}}
   set cycles [expr {{round(([machine_info time]-$::started)*3579545)}}]
   if {{$cycles<=0 || $cycles>=65536}} {{fail_context cycle-range}}
   puts -nonewline $::result [debug read_block memory {output_address} {data_size}]
   puts -nonewline $::result [binary format cu* [list [expr {{$cycles&255}}] [expr {{$cycles>>8}}]]]
   incr ::count;dispatch_context
  }}}}
  dispatch_context
 }}
}}]
after time {60+count*0.02} {{fail_context watchdog}}
'''
    (out/'probe.tcl').write_text(tcl)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_HazardContext','-cart',str(fixture),'-romtype','Normal','-script',str(out/'probe.tcl')],env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=1200)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode or 'CONTEXT_FAIL' in run.stdout+run.stderr:raise ValueError('native context failed: '+(run.stdout+run.stderr)[-1600:])
    actual=(out/'actual.bin').read_bytes();width=data_size+2
    contexts=b''.join(actual[i*width:i*width+data_size] for i in range(count))
    if len(actual)!=count*width or contexts!=expected:
        first=next((i for i,(a,b) in enumerate(zip(contexts,expected)) if a!=b),None)
        raise ValueError(f'native component differs at byte={first},case={first//data_size if first is not None else None}')
    cycles=[int.from_bytes(actual[i*width+data_size:i*width+width],'little') for i in range(count)]
    if {s:sha(ROOT/s) if (ROOT/s).exists() else None for s in names}!=source:raise ValueError('context source changed')
    if original is not None and (ROOT/'references/roms/frostbite.bin').read_bytes()!=original:raise ValueError('original changed')
    report=dict(complete=True,component_fixture_only=True,game_runtime_changed=False,component='ordinary-horizontal-context' if stage=='context' else 'ordinary-row-programs',stage=stage,
        cases=count,complete_native_domain=count==full_count,outputs_equal=True,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),sources=source,
        component_rom_sha256=sha(fixture),component_code_bytes=q[end_name]-entry,component_data_bytes=sum(len(v) for v in assets.values()),
        context_code_bytes=q['cx_end']-q['cx_context'],original_sha256=hashlib.sha256(original).hexdigest() if original else None,
        output_bytes=data_size,scratch_bytes=32 if stage=='program' else 0,ix_iy_sp_preserved=True,bounded_writes=True,mapper_accesses=0,
        cycles_including_call_and_jump=dict(min=min(cycles),mean=statistics.mean(cycles),p95=sorted(cycles)[min(count-1,int(count*0.95))],max=max(cycles)),
        emulator_sha256=sha(emulator),assembler_sha256=sha(assembler),machine_profile_sha256=hashlib.sha256(profile).hexdigest(),
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='Native coordinate/copy contexts only; glyph masks, collisions, game integration and whole-frame cadence remain separate.' if stage=='context'
              else 'Native ordinary row masks for every exceptional context/shape/reflection class; actual glyph/Y evaluation, game integration and cadence remain separate.')
    (out/'component-result.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--limit',type=int)
    p.add_argument('--stage',choices=('context','program'),default='context')
    a=p.parse_args();r=check(a.out,a.limit,a.stage);print({k:v for k,v in r.items() if k not in ('sources','files')})
