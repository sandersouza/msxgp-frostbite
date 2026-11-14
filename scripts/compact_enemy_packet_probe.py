"""Qualify the native enemy packet constructor against every sealed v30 packet."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess

from compact_enemy_packets import packet,scatter
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile,isolated_profile,validate_machine_profile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def check(build,out):
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);build=Path(build).resolve()
    metadata=(build/'build.json').read_bytes();m=json.loads(metadata)
    rompath=build/m['rom']['filename'];rom=rompath.read_bytes();s=symbols(build/'presentation.sym')
    if sha(rompath)!=CONTROL_SHA:raise ValueError('accepted v30 required')
    if any(sha(ROOT/n)!=h for n,h in m['source_files'].items()):raise ValueError('baseline source differs')
    names=('scripts/compact_enemy_packets.py','scripts/compact_enemy_packet_probe.py','src/compact_enemy_packet.asm')
    source={n:sha(ROOT/n) if (ROOT/n).exists() else None for n in names}
    for n in names:
        if (ROOT/n).exists():
            p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    def read(bank,address,count):
        if not 0x8000<=address<address+count<=0xC000:raise ValueError('bank bounds')
        at=bank*16384+address-0x8000;return rom[at:at+count]
    mapping=read(1,s['p_geo_row_map_data'],256)
    roots={v:k for k,v in enumerate(mapping) if v<33}
    if set(roots)!=set(range(33)) or max(roots.values())>248:raise ValueError('shape directory differs')
    data=dict(original=read(2,s['original_data'],1024),expansion=read(2,s['p_sprite_expansion_data'],1024),
              reverse=read(2,s['p_sprite_reverse_data'],256),shapes=bytes(roots[i] for i in range(33)))
    directory=read(s['i_packets_bank'],s['i_packets'],3168)
    inputs,expected=bytearray(),bytearray()
    for group in range(66):
        glyph=data['original'][256+roots[group//2]:264+roots[group//2]]
        for phase in range(16):
            entry=directory[(group*16+phase)*3:(group*16+phase+1)*3]
            address=int.from_bytes(entry[:2],'little');flag=address&1
            horizontal=read(entry[2],address&65534,16 if flag else 24).ljust(24,b'\0')
            if horizontal!=packet(glyph,phase,bool(group&1)):raise ValueError('host packet differs')
            if flag!=int(not any(horizontal[16:])):raise ValueError('third-column flag differs')
            for vertical in range(8):
                inputs.extend((group,phase,vertical));expected.extend(scatter(horizontal,vertical)+bytes((flag,)))
    for n,value in {**data,'inputs':inputs,'expected':expected}.items():(out/(n+'.bin')).write_bytes(value)
    assembly=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
              'ct_original EQU $5000','ct_expansion EQU $5400','ct_reverse EQU $5800','ct_shapes EQU $5900',
              ' DS $4100-$,$FF',' INCLUDE "compact_enemy_packet.asm"',' ASSERT $ <= $5000']
    for n,address in (('original',0x5000),('expansion',0x5400),('reverse',0x5800),('shapes',0x5900)):
        if n in ('original','shapes'):assembly.append(f' DS ${address:04X}-$,$FF')
        assembly.append(f' INCBIN "{out/(n+".bin")}"')
    assembly.append(' DS $C000-$,$FF');(out/'fixture.asm').write_text('\n'.join(assembly)+'\n')
    assembler=verified_tool('sjasmplus');fixture=out/'component-fixture.rom'
    r=subprocess.run([str(assembler),'--nologo',f'--inc={ROOT/"src"}',f'--raw={fixture}',f'--sym={out/"fixture.sym"}',str(out/'fixture.asm')],capture_output=True,text=True,timeout=60)
    (out/'assembler.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError('assembler failed: '+(r.stdout+r.stderr)[-1600:])
    if fixture.stat().st_size!=32768:raise ValueError('fixture size')
    q=symbols(out/'fixture.sym');entry=q['ct_build'];count=len(inputs)//3
    emulator=Path(shutil.which('openmsx')).resolve();profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user-data';(user/'machines').mkdir(parents=True);(user/'machines/Frostbite_EnemyPacket.xml').write_bytes(profile)
    settings=out/'settings.xml';settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    tcl=f'''set save_settings_on_exit false
set renderer none
set throttle off
set checking 0
set count 0
set f [open {{{out/'inputs.bin'}}} rb];set inputs [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
proc fail_packet {{message}} {{puts stderr "PACKET_FAIL $message case=$::count";exit 1}}
proc dispatch_packet {{}} {{
 if {{$::count=={count}}} {{close $::result;exit;return}}
 set ::checking 0
 set at [expr {{$::count*3}}]
 debug write_block memory 0xC7E0 [string range $::inputs $at [expr {{$at+2}}]]
 debug write_block memory 0xC180 [string repeat [binary format c 165] 48]
 reg PC 0xC6D0;set ::started [machine_info time];set ::checking 1;debug cont
}}
set boot [debug set_bp {q['ready']} {{}} {{
 debug remove_bp $::boot;debug break
 after break {{
  if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_packet target}}
  reg IX 0xDDDD;reg IY 0xEEEE;reg SP 0xF380
  debug write_block memory 0xC6D0 [binary format cu* [list 205 {entry&255} {entry>>8} 195 214 198 24 254]]
  foreach range {{{{0x0000 0xC17F}} {{0xC1B0 0xC7E4}} {{0xC7EA 0xF2FF}} {{0xF380 0xFFFF}}}} {{
   debug set_watchpoint write_mem $range {{$::checking}} {{fail_packet "write address=$::wp_last_address PC=[reg PC]"}}
  }}
  debug set_bp 0xC6D6 {{}} {{debug break;after break {{
   if {{[reg IX]!=0xDDDD || [reg IY]!=0xEEEE || [reg SP]!=0xF380 || ([reg IFF]&3)!=0}} {{fail_packet abi}}
   set cycles [expr {{round(([machine_info time]-$::started)*3579545)}}]
   if {{$cycles<=0 || $cycles>=65536}} {{fail_packet cycle-range}}
   puts -nonewline $::result [debug read_block memory 0xC180 48]
   puts -nonewline $::result [binary format cu* [list [reg A] [expr {{$cycles&255}}] [expr {{$cycles>>8}}]]]
   incr ::count;dispatch_packet
  }}}}
  dispatch_packet
 }}
}}]
after time {60+count*.02} {{fail_packet watchdog}}
'''
    (out/'probe.tcl').write_text(tcl)
    r=subprocess.run([str(emulator),'-setting',str(settings),'-machine','Frostbite_EnemyPacket','-cart',str(fixture),'-romtype','Normal','-script',str(out/'probe.tcl')],env={**os.environ,'OPENMSX_USER_DATA':str(user),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=1200)
    (out/'emulator.log').write_text(r.stdout+r.stderr)
    if r.returncode or 'PACKET_FAIL' in r.stdout+r.stderr:raise ValueError('native packet failed: '+(r.stdout+r.stderr)[-1600:])
    actual=(out/'actual.bin').read_bytes()
    if len(actual)!=count*51:raise ValueError('native output size differs')
    for i in range(count):
        if actual[i*51:i*51+49]!=expected[i*49:i*49+49]:raise ValueError(f'native packet differs at{i}, input={list(inputs[i*3:i*3+3])}')
    cycles=[int.from_bytes(actual[i*51+49:i*51+51],'little') for i in range(count)]
    if source!={n:sha(ROOT/n) for n in names}:raise ValueError('source changed')
    if (build/'build.json').read_bytes()!=metadata or sha(rompath)!=CONTROL_SHA:raise ValueError('control changed')
    if any(sha(ROOT/n)!=h for n,h in m['source_files'].items()):raise ValueError('baseline source changed')
    result=dict(complete=True,component_fixture_only=True,game_runtime_changed=False,cases=count,
        outputs_equal=True,complete_packet_domain=count==8448,code_bytes=q['ct_end']-entry,
        reused_original_bytes=1024,reused_expansion_bytes=1024,reused_reverse_bytes=256,extra_shape_bytes=33,
        replaced_packet_bytes=21992,scratch_bytes=5,output_buffer_bytes=48,ix_iy_sp_preserved=True,bounded_writes=True,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),sources=source,
        oracle_rom_sha256=CONTROL_SHA,component_rom_sha256=sha(fixture),
        cycles_including_call_and_jump=dict(min=min(cycles),mean=statistics.mean(cycles),p95=sorted(cycles)[int(count*.95)],max=max(cycles)),
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()},emulator_sha256=sha(emulator),assembler_sha256=sha(assembler),
        machine_profile_sha256=hashlib.sha256(profile).hexdigest(),
        scope='All66groups x16horizontal x8vertical phases, all48bytes and third-column flags; unlinked native constructor, no game cadence claim.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(check(a.build,a.out))
