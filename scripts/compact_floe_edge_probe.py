"""Native horizontal masks / row evaluator fixtures, not playable game ROMs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
from itertools import islice

from compact_floe import FloeOracle
from compact_floe_edge import build_edge_assets, compile_edge_rows, edge_row_domain
from compact_live_probe import CONTROL_SHA
from environment import ROOT, verified_tool
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def check(build,out,limit=None,stage='masks'):
    if stage not in ('masks','row'):
        raise ValueError('declared native component stage required')
    if limit is not None and (type(limit) is not int or limit<=0):
        raise ValueError('positive case limit required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    build=Path(build).resolve();metadata=(build/'build.json').read_bytes();m=json.loads(metadata)
    rom=build/m['rom']['filename']
    if m['rom']['sha256']!=CONTROL_SHA or sha(rom)!=CONTROL_SHA:
        raise ValueError('accepted v30 oracle required')
    if any(sha(ROOT/s)!=h for s,h in m['source_files'].items()):
        raise ValueError('baseline source differs')
    names=('scripts/compact_floe.py','scripts/compact_floe_edge.py',
           'scripts/compact_floe_edge_probe.py','src/compact_floe_edge.asm','src/compact_floe_edge_row.asm')
    source={s:sha(ROOT/s) if (ROOT/s).exists() else None for s in names}
    for s in names:
        if (ROOT/s).exists():
            p=out/'source'/s;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/s).read_bytes())
    original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    assets,proof=build_edge_assets(original,FloeOracle(rom.read_bytes(),m))
    inputs,expected=bytearray(),bytearray()
    if stage=='masks':
        for control in range(10):
            for px in (*range(9),*range(154,160)):
                for fx in range(160):
                    if limit is not None and len(inputs)//7>=limit:break
                    inputs.extend((control,0,(fx-px)%160,0,0,0,fx))
                    pair=assets['edge_control_clocks'][control*2:control*2+2]
                    expected.extend(v for row in compile_edge_rows(pair,assets['edge_motion_clocks'],px,fx) for v in row)
        locations=dict(edge_windows=0x5000,edge_low_masks=0x5200,edge_bits=0x5220,
                       edge_control_clocks=0x5240,edge_motion_clocks=0x5260,edge_reverse=0x5300)
        input_size,data_size,input_address=7,32,0xC780
        assembly_file='compact_floe_edge.asm';entry_name,end_name='ce_build_masks','ce_end'
        poison='debug write_block memory 0xC800 [string repeat [binary format cu 165] 32]'
        result_expression='[debug read_block memory 0xC800 32]'
        complete_count=24000
        scope='Native geometry masks only; view/Y convolution, combined kernel, default game integration and whole-frame timing remain separate.'
    else:
        domain=edge_row_domain(assets)
        if len(domain)!=666:raise ValueError('qualified row-mask domain differs')
        def row_cases():
            for masks in domain:
                before,equal,different,exiting,visible=masks
                for tag in (-2,-1,*range(20)):
                    for view in range(228):
                        pose,remainder=divmod(view,38);shift,reflection=divmod(remainder,2)
                        at=reflection*256+assets['bases'][pose]+shift
                        new=assets['glyphs'][at+tag] if 0<=tag<19 else 0
                        old=assets['glyphs'][at+tag+1] if 0<=tag<18 else 0
                        if tag==-1:hit=bool(assets['glyphs'][at]&exiting)
                        elif 0<=tag<19:
                            hit=bool(new&visible or old&before or (old&equal if old==new else new&different))
                        else:hit=False
                        yield bytes((tag&255,pose,shift,reflection,*masks)),135 if hit else 7
        for row,value in islice(row_cases(),limit):
            inputs.extend(row);expected.append(value)
        (out/'row-domain.bin').write_bytes(bytes(v for row in domain for v in row))
        locations=dict(glyphs=0x5000,bases=0x5200)
        input_size,data_size,input_address=9,1,0xC790
        assembly_file='compact_floe_edge_row.asm';entry_name,end_name='ce_test_row','cer_end'
        poison='';result_expression='[binary format cu [reg A]]'
        complete_count=len(domain)*22*228
        scope='Every declared native row-mask/tag/view input; full-program accumulation, combined geometry calls, default integration and cadence remain separate.'
    assets['edge_reverse']=bytes(int(f'{v:08b}'[::-1],2) for v in range(256))
    for name in locations:(out/(name+'.bin')).write_bytes(assets[name])
    (out/'inputs.bin').write_bytes(inputs);(out/'expected.bin').write_bytes(expected)
    (out/'host-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    code=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready']
    code += [f'ce_{name} EQU ${address:04X}' for name,address in locations.items()]
    code += [' DS $4100-$,$FF',f' INCLUDE "{assembly_file}"',' ASSERT $ <= $5000']
    previous_end=None
    for name,address in locations.items():
        code += [f' ASSERT $ <= ${address:04X}']
        if previous_end!=address:code += [f' DS ${address:04X}-$,$FF']
        code += [f' INCBIN "{out/(name+".bin")}"']
        previous_end=address+len(assets[name])
    code += [' ASSERT $ <= $C000',' DS $C000-$,$FF']
    (out/'fixture.asm').write_text('\n'.join(code)+'\n')
    assembler=verified_tool('sjasmplus');fixture=out/'component-fixture.rom'
    run=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={fixture}',f'--sym={out/"fixture.sym"}',str(out/'fixture.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('edge assembler failed: '+(run.stdout+run.stderr)[-1800:])
    if fixture.stat().st_size!=32768:raise ValueError('fixture capacity differs')
    syms=symbols(out/'fixture.sym');entry=syms[entry_name]
    emulator=Path(shutil.which('openmsx')).resolve()
    profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/Frostbite_EdgeMasks.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    allowed='($::wp_last_address>=0xF300 && $::wp_last_address<0xF380)'
    if stage=='masks':allowed+='||($::wp_last_address>=0xC7A0 && $::wp_last_address<0xC7C0)||($::wp_last_address>=0xC800 && $::wp_last_address<0xC820)'
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set checking 0
set count 0
set f [open {{{out/'inputs.bin'}}} rb];set inputs [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
proc fail_masks {{message}} {{puts stderr "MASK_FAIL $message case=$::count";exit 1}}
proc dispatch_masks {{}} {{
 if {{$::count=={len(inputs)//input_size}}} {{close $::result;exit;return}}
 set ::checking 0
 set at [expr {{$::count*{input_size}}}]
 debug write_block memory {input_address} [string range $::inputs $at [expr {{$at+{input_size-1}}}]]
 {poison}
 reg PC 0xC6D0
 set ::started [machine_info time]
 set ::checking 1
 debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{
 debug remove_bp $::boot
 debug break
 after break {{
  if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_masks target}}
  reg IX 0xDDDD;reg IY 0xEEEE;reg SP 0xF380
  debug write_block memory 0xC6D0 [binary format cu* [list 205 {entry&255} {entry>>8} 195 214 198 24 254]]
  set ::checking 1
  debug set_watchpoint write_mem {{0x0000 0xFFFF}} {{$::checking && !({allowed})}} {{fail_masks "write address=$::wp_last_address PC=[reg PC]"}}
  debug set_bp 0xC6D6 {{}} {{debug break;after break {{
   if {{[reg IX]!=0xDDDD || [reg IY]!=0xEEEE || [reg SP]!=0xF380 || ([reg IFF]&3)!=0}} {{fail_masks abi}}
   set cycles [expr {{round(([machine_info time]-$::started)*3579545)}}]
   if {{$cycles<=0 || $cycles>=65536}} {{fail_masks cycle-range}}
   puts -nonewline $::result {result_expression}
   puts -nonewline $::result [binary format cu* [list [expr {{$cycles&255}}] [expr {{$cycles>>8}}]]]
   incr ::count;dispatch_masks
  }}}}
  dispatch_masks
 }}
}}]
after time {60+len(inputs)//input_size*0.02} {{fail_masks watchdog}}
'''
    (out/'probe.tcl').write_text(tcl)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_EdgeMasks','-cart',str(fixture),'-romtype','Normal','-script',str(out/'probe.tcl')],env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=1200)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode or 'MASK_FAIL' in run.stdout+run.stderr:
        raise ValueError('native masks failed: '+(run.stdout+run.stderr)[-1800:])
    actual=(out/'actual.bin').read_bytes();count=len(inputs)//input_size;width=data_size+2
    masks=b''.join(actual[i*width:i*width+data_size] for i in range(count))
    if len(actual)!=count*width or masks!=expected:
        first=next((i for i,(a,b) in enumerate(zip(masks,expected)) if a!=b),None)
        raise ValueError(f'native component differs: first byte={first}, case={first//data_size if first is not None else None}')
    cycles=[int.from_bytes(actual[i*width+data_size:i*width+width],'little') for i in range(count)]
    if {s:sha(ROOT/s) for s in names}!=source:raise ValueError('component source changed')
    if (build/'build.json').read_bytes()!=metadata or sha(rom)!=CONTROL_SHA:
        raise ValueError('oracle changed')
    if (ROOT/'references/roms/frostbite.bin').read_bytes()!=original:raise ValueError('original changed')
    if any(sha(ROOT/s)!=h for s,h in m['source_files'].items()):raise ValueError('baseline changed')
    report=dict(complete=True,component_fixture_only=True,game_runtime_changed=False,
        component='floe-edge-horizontal-masks' if stage=='masks' else 'floe-edge-row-evaluator',
        stage=stage,cases=count,complete_native_stage_domain=count==complete_count,
        complete_native_horizontal_domain=stage=='masks' and count==24000,
        outputs_equal=True,output_bytes_per_case=data_size,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        sources=source,oracle_rom_sha256=CONTROL_SHA,oracle_metadata_sha256=hashlib.sha256(metadata).hexdigest(),
        original_sha256=hashlib.sha256(original).hexdigest(),component_rom_sha256=sha(fixture),
        component_code_bytes=syms[end_name]-entry,component_data_bytes=sum(len(assets[k]) for k in locations),
        scratch_reserved_bytes=32 if stage=='masks' else 0,mask_output_bytes=32 if stage=='masks' else 0,
        ix_iy_sp_preserved=True,bounded_writes=True,mapper_accesses=0,
        cycles_including_call_and_jump=dict(min=min(cycles),mean=statistics.mean(cycles),p95=sorted(cycles)[min(len(cycles)-1,int(len(cycles)*0.95))],max=max(cycles)),
        host_proof=proof,emulator_sha256=sha(emulator),assembler_sha256=sha(assembler),machine_profile_sha256=hashlib.sha256(profile).hexdigest(),
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope=scope)
    (out/'component-result.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--limit',type=int)
    p.add_argument('--stage',choices=('masks','row'),default='masks')
    a=p.parse_args();r=check(a.build,a.out,a.limit,a.stage)
    print({k:v for k,v in r.items() if k not in ('files','sources','host_proof')})
