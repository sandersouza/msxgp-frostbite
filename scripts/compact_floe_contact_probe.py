"""Native edge-program accumulation from qualified masks, not a game ROM."""
import argparse
from array import array
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from compact_floe import FloeOracle
from compact_floe_edge import build_edge_assets,compile_edge_rows,visible_player_mask
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def check(build,mask_proof,out,limit=None):
    if limit is not None and (type(limit) is not int or limit<=0):raise ValueError('positive case limit required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    build=Path(build).resolve();metadata=(build/'build.json').read_bytes();m=json.loads(metadata)
    rom=build/m['rom']['filename']
    if m['rom']['sha256']!=CONTROL_SHA or sha(rom)!=CONTROL_SHA:raise ValueError('accepted oracle required')
    if any(sha(ROOT/s)!=h for s,h in m['source_files'].items()):raise ValueError('baseline source differs')
    names=('scripts/compact_floe.py','scripts/compact_floe_edge.py','scripts/compact_floe_contact_probe.py',
           'src/compact_floe_edge.asm','src/compact_floe_edge_row.asm','src/compact_floe_edge_contact.asm')
    source={s:sha(ROOT/s) if (ROOT/s).exists() else None for s in names}
    for s in names:
        if (ROOT/s).exists():
            p=out/'source'/s;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/s).read_bytes())
    mask_proof=Path(mask_proof).resolve();receipt_path=mask_proof/'component-result.json'
    receipt_raw=receipt_path.read_bytes();receipt=json.loads(receipt_raw)
    if (not receipt['complete_native_horizontal_domain'] or receipt['cases']!=24000
            or not receipt.get('outputs_equal',receipt.get('masks_equal'))
            or receipt['oracle_rom_sha256']!=CONTROL_SHA
            or receipt['sources']['src/compact_floe_edge.asm']!=source['src/compact_floe_edge.asm']):
        raise ValueError('complete compatible native horizontal proof required')
    if any(sha(mask_proof/s)!=h for s,h in receipt['files'].items()):raise ValueError('native mask proof file differs')
    original=(ROOT/'references/roms/frostbite.bin').read_bytes();oracle=FloeOracle(rom.read_bytes(),m)
    assets,host=build_edge_assets(original,oracle)
    inputs=(mask_proof/'inputs.bin').read_bytes();native=(mask_proof/'actual.bin').read_bytes()
    if len(inputs)!=24000*7 or len(native)!=24000*34:raise ValueError('partial native mask corpus')
    programs={};seen=set()
    for i in range(24000):
        control,unused,dx,pose,shift,reflection,fx=inputs[i*7:i*7+7]
        px=(fx-dx)%160
        if (control not in range(10) or px not in (*range(9),*range(154,160)) or fx>=160
                or any((unused,pose,shift,reflection)) or (control,px,fx) in seen):
            raise ValueError('invalid or duplicated native geometry input')
        seen.add((control,px,fx))
        rows=native[i*34:i*34+32]
        pair=assets['edge_control_clocks'][control*2:control*2+2]
        if rows!=bytes(v for row in compile_edge_rows(pair,assets['edge_motion_clocks'],px,fx) for v in row):
            raise ValueError('native geometry disagrees with maintained compiler')
        group=assets['directory'][control*160+dx]
        clip=visible_player_mask(px)
        program=rows+bytes(v&clip for v in assets['footprints'][group*7:group*7+7])
        programs.setdefault(program,(control,px,fx))
    if len(programs)!=2086:raise ValueError('complete program domain differs')
    ordered=sorted(programs)
    expected=bytearray();maximum=len(ordered)*34*228;count=min(maximum,limit) if limit else maximum
    manifest=[]
    for index,program in enumerate(ordered):
        control,px,fx=programs[program];manifest.append(dict(index=index,control=control,player_x=px,floe_x=fx))
        for yi in range(34):
            mask=oracle.records[oracle.row(control,px,yi)[(fx-px)%160]][0]
            take=min(228,count-len(expected))
            if take>0:expected.extend(135 if mask&(1<<view) else 7 for view in range(take))
    if len(expected)!=count:raise ValueError('incomplete direct oracle corpus')
    (out/'programs.bin').write_bytes(b''.join(ordered));(out/'expected.bin').write_bytes(expected)
    (out/'cases.json').write_text(json.dumps(dict(programs=manifest,source_y=[0,*range(45,78)],literal_views=228,cases=count),indent=2)+'\n')
    for name in ('glyphs','bases'):(out/(name+'.bin')).write_bytes(assets[name])
    (out/'host-proof.json').write_text(json.dumps(host,indent=2)+'\n')
    code=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
          'ce_glyphs EQU $5000','ce_bases EQU $5200',' DS $4100-$,$FF',
          ' INCLUDE "compact_floe_edge_row.asm"',' INCLUDE "compact_floe_edge_contact.asm"',
          ' ASSERT $ <= $5000',' DS $5000-$,$FF',f' INCBIN "{out/"glyphs.bin"}"',
          f' INCBIN "{out/"bases.bin"}"',' DS $C000-$,$FF']
    (out/'fixture.asm').write_text('\n'.join(code)+'\n')
    assembler=verified_tool('sjasmplus');fixture=out/'component-fixture.rom'
    run=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={fixture}',f'--sym={out/"fixture.sym"}',str(out/'fixture.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('contact assembler failed: '+(run.stdout+run.stderr)[-1600:])
    if fixture.stat().st_size!=32768:raise ValueError('fixture size differs')
    q=symbols(out/'fixture.sym');entry=q['cec_contact']
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True)
    (user/'machines/Frostbite_EdgeContact.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set checking 0
set count 0
set f [open {{{out/'programs.bin'}}} rb];set programs [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
proc fail_contact {{message}} {{puts stderr "CONTACT_FAIL $message case=$::count";exit 1}}
proc dispatch_contact {{}} {{
 if {{$::count=={count}}} {{close $::result;exit;return}}
 set ::checking 0
 set view [expr {{$::count%228}}]
 set yi [expr {{($::count/228)%34}}]
 if {{$view==0 && $yi==0}} {{
  set at [expr {{($::count/(228*34))*39}}]
  debug write_block memory 0xC800 [string range $::programs $at [expr {{$at+38}}]]
 }}
 set y [expr {{$yi==0?0:$yi+44}}]
 debug write_block memory 0xC7D0 [binary format cu* [list $y [expr {{$view/38}}] [expr {{($view%38)/2}}] [expr {{$view%2}}]]]
 reg PC 0xC6D0
 set ::started [machine_info time]
 set ::checking 1
 debug cont
}}
set boot [debug set_bp {q['ready']} {{}} {{
 debug remove_bp $::boot
 debug break
 after break {{
  if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_contact target}}
  reg IX 0xDDDD;reg IY 0xEEEE;reg SP 0xF380
  debug write_block memory 0xC6D0 [binary format cu* [list 205 {entry&255} {entry>>8} 195 214 198 24 254]]
  set ::checking 1
  foreach range {{{{0x0000 0xC78F}} {{0xC799 0xC7D3}} {{0xC7D6 0xF2FF}} {{0xF380 0xFFFF}}}} {{
   debug set_watchpoint write_mem $range {{$::checking}} {{fail_contact "write address=$::wp_last_address PC=[reg PC]"}}
  }}
  debug set_bp 0xC6D6 {{}} {{debug break;after break {{
   if {{[reg IX]!=0xDDDD || [reg IY]!=0xEEEE || [reg SP]!=0xF380 || ([reg IFF]&3)!=0}} {{fail_contact abi}}
   set cycles [expr {{round(([machine_info time]-$::started)*3579545)}}]
   if {{$cycles<=0 || $cycles>=65536}} {{fail_contact cycle-range}}
   puts -nonewline $::result [binary format cu* [list [reg A] [expr {{$cycles&255}}] [expr {{$cycles>>8}}]]]
   incr ::count;dispatch_contact
  }}}}
  dispatch_contact
 }}
}}]
after time {60+count*0.003} {{fail_contact watchdog}}
'''
    (out/'probe.tcl').write_text(tcl)
    run=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_EdgeContact','-cart',str(fixture),'-romtype','Normal','-script',str(out/'probe.tcl')],env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=3600)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode or 'CONTACT_FAIL' in run.stdout+run.stderr:raise ValueError('native contact failed: '+(run.stdout+run.stderr)[-1600:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=count*3 or actual[::3]!=expected:
        first=next((i for i,(a,b) in enumerate(zip(actual[::3],expected)) if a!=b),None)
        raise ValueError(f'native contact differs: first={first},bytes={len(actual)} expected={count*3}')
    histogram=array('Q',[0])*65536
    for i in range(count):histogram[actual[i*3+1]+256*actual[i*3+2]]+=1
    low=next(i for i,n in enumerate(histogram) if n);high=max(i for i,n in enumerate(histogram) if n)
    p95=0;total=0
    for i,n in enumerate(histogram):
        total+=n
        if total>=int(count*0.95)+1:p95=i;break
    if {s:sha(ROOT/s) for s in names}!=source:raise ValueError('component source changed')
    if (build/'build.json').read_bytes()!=metadata or sha(rom)!=CONTROL_SHA:raise ValueError('oracle changed')
    if receipt_path.read_bytes()!=receipt_raw or any(sha(mask_proof/s)!=h for s,h in receipt['files'].items()):raise ValueError('native mask evidence changed')
    if (ROOT/'references/roms/frostbite.bin').read_bytes()!=original:raise ValueError('original changed')
    if any(sha(ROOT/s)!=h for s,h in m['source_files'].items()):raise ValueError('baseline source changed')
    report=dict(complete=True,component_fixture_only=True,game_runtime_changed=False,component='floe-edge-program-accumulation',
        cases=count,complete_native_program_domain=count==maximum,programs=len(ordered),classified_native_geometry_cases=len(seen),literal_views=228,
        outputs_equal=True,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),sources=source,
        oracle_rom_sha256=CONTROL_SHA,oracle_metadata_sha256=hashlib.sha256(metadata).hexdigest(),original_sha256=hashlib.sha256(original).hexdigest(),
        mask_proof=dict(path=str(receipt_path.relative_to(ROOT)),sha256=hashlib.sha256(receipt_raw).hexdigest()),
        component_rom_sha256=sha(fixture),accumulation_code_bytes=q['cec_end']-entry,row_code_bytes=q['cer_end']-q['ce_test_row'],
        component_data_bytes=518,scratch_reserved_bytes=11,program_input_bytes=39,ix_iy_sp_preserved=True,bounded_writes=True,mapper_accesses=0,
        cycles_including_call_and_jump=dict(min=low,mean=sum(i*n for i,n in enumerate(histogram))/count,p95=p95,max=high),
        emulator_sha256=sha(emulator),assembler_sha256=sha(assembler),machine_profile_sha256=hashlib.sha256(profile).hexdigest(),
        host_proof=host,files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='Native bit7 accumulation for all qualified intermediate program classes. Geometry generator is separately qualified; combined caller, shadow merge, default game integration and cadence remain separate.')
    (out/'component-result.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--mask-proof',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--limit',type=int)
    a=p.parse_args();r=check(a.build,a.mask_proof,a.out,a.limit)
    print({k:v for k,v in r.items() if k not in ('files','sources','host_proof')})
