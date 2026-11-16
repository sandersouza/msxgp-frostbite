"""Exercise gain transitions through the real native ROM, not a helper ROM."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from environment import ROOT
from native_support import symbols
from smoke import isolated_profile,find_machine_profile,validate_machine_profile
from native_effect_gain import project_write
from presentation_audio import psg_step,MASKS,OWNED_REGISTERS
from presentation_audio_check import workspace
from native_effect_gain_check import qualification_inputs
from native_audio_codegen import clear_events


def check(base,delivery,out):
    producers=qualification_inputs(base,delivery)
    if out.exists():raise ValueError('fresh component output required')
    out.mkdir(parents=True)
    syms=symbols(base/'presentation.sym')
    linked=json.loads((delivery/'linked/native-link.json').read_bytes())
    syms.update(linked['native_symbols'])
    cold=json.loads((delivery/'cold/cold-image.json').read_bytes())
    rom=delivery/'cartridge/FROSTBIT.ROM'
    emulator=Path(shutil.which('openmsx')).resolve()
    profile=isolated_profile(find_machine_profile(str(emulator)));validate_machine_profile(profile)
    user=out/'user';(user/'machines').mkdir(parents=True)
    (user/'machines/Gain.xml').write_bytes(profile)
    cases=[]
    def add(method,reg,value):cases.append((method,reg,value))
    for control in (1,8,12):
        add(0,21,control);add(0,22,control)
        add(0,23,2);add(0,24,5)
        for reg in (25,26):
            for raw in (4,4,20,0,4,15,255,4):
                for method in (1,1,0,1,2,1,0):add(method,reg,raw)
            for raw in range(256):
                for method in (1,0,2):add(method,reg,raw)
    for threshold in range(256):
        add(1,25,4);add(1,26,4);add(3,21,threshold)
    (out/'cases.bin').write_bytes(bytes(v for row in cases for v in row))
    targets=' '.join(str(syms[f'p_audio_event_{r:02X}']) for r in range(21,27))
    gains=f"{syms['neg_event_0']} {syms['neg_event_1']}"
    script=f'''set save_settings_on_exit false
set renderer none
set throttle off
set active 0
set selected 0
set index 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
set writes [open {{{out/'writes.tsv'}}} w]
proc fail {{why}} {{puts stderr "GAIN_COMPONENT_FAIL $why index=$::index";exit 1}}
proc regs {{}} {{return [list [reg AF] [reg BC] [reg DE] [reg HL] [reg IX] [reg IY] [reg SP] [reg IFF]]}}
proc guard {{}} {{return "[debug read_block memory 0 0xC715][debug read_block memory 0xC71B 69][debug read_block memory 0xC768 0x1898][debug read_block memory 0xE020 0x1320]"}}
proc dispatch {{}} {{
 if {{$::index=={len(cases)}}} {{close $::result;close $::writes;exit;return}}
 binary scan [string range $::cases [expr {{$::index*3}}] [expr {{$::index*3+2}}]] cu* row
 lassign $row method reg value
 set target [lindex [list {targets}] [expr {{$reg-21}}]]
 if {{$method==1}} {{set target [lindex [list {gains}] [expr {{$reg-25}}]]}}
 if {{$method==2}} {{set target {syms['p_audio_event_indexed']}}}
 if {{$method==3}} {{set target {syms['p_audio_emit_clear']}}} else {{debug write memory [expr {{0xC700+$reg}}] $value}}
 debug write_block memory 0xC760 [binary format cu* [list 205 [expr {{$target&255}}] [expr {{$target>>8}}] 195 102 199 24 254]]
 reg AF 0xA9D7;reg BC [expr {{$method==3?$value*256+169:0x57A9}}];reg DE 0x713F;reg HL [expr {{$method==2?0xC700+$reg:0x8765}}];reg IX 0xDEAD;reg IY 0xFEDC;reg SP 0xF380;reg PC 0xC760
 set ::before [regs];set ::guard [guard];set ::active 1;debug cont
}}
debug set_watchpoint write_io {{160 161}} {{}} {{
 if {{($::wp_last_address&255)==160}} {{set ::selected $::wp_last_value}} elseif {{$::active}} {{
  if {{$::selected ni {{0 1 2 3 6 7 8 9 10}}}} {{fail unowned-PSG}}
  puts $::writes "$::index $::selected $::wp_last_value"
 }}
}}
set boot [debug set_bp {cold['native_symbols']['nc_entry']} {{}} {{
 debug remove_bp $::boot;debug break
 after break {{
  if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail machine}}
  set ::vram [debug read_block VRAM 0 16384];set ::slot [debug read ioports 168]
  set ::unowned "[debug read_block {{PSG regs}} 4 2][debug read_block {{PSG regs}} 11 5]"
  set ::gpio [expr {{[debug read {{PSG regs}} 7]&192}}]
  debug write_block memory 0xC760 [binary format cu* {{205 {syms['p_audio_init']&255} {syms['p_audio_init']>>8} 195 107 199 24 254 0 0 0 0}}]
  reg PC 0xC760;reg SP 0xF380;debug cont
 }}
}}]
debug set_bp 0xC76B {{}} {{debug break;after break {{
 set f [open {{{out/'initial.bin'}}} wb];puts -nonewline $f [debug read_block {{PSG regs}} 0 16];close $f
 dispatch
}}}}
debug set_bp 0xC766 {{}} {{debug break;after break {{
 set ::active 0
 if {{[regs] ne $::before || [guard] ne $::guard || [debug read ioports 168]!=$::slot || [debug read_block VRAM 0 16384] ne $::vram}} {{fail ABI-memory}}
 if {{"[debug read_block {{PSG regs}} 4 2][debug read_block {{PSG regs}} 11 5]" ne $::unowned || ([debug read {{PSG regs}} 7]&192)!=$::gpio}} {{fail peripherals}}
 puts -nonewline $::result "[debug read_block {{PSG regs}} 0 16][debug read_block memory 0xE000 21]"
 incr ::index;dispatch
}}}}
after time 300 {{fail timeout}}
'''
    (out/'probe.tcl').write_text(script)
    run=subprocess.run([str(emulator),'-machine','Gain','-cart',str(rom.resolve()),'-romtype','Normal','-script',str((out/'probe.tcl').resolve())],
        env={**os.environ,'OPENMSX_USER_DATA':str(user.resolve()),'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=300)
    (out/'emulator.log').write_text(run.stdout+run.stderr)
    if run.returncode or 'GAIN_COMPONENT_FAIL' in run.stdout+run.stderr:raise ValueError('native gain component failed: '+(run.stdout+run.stderr)[-1000:])
    actual=(out/'actual.bin').read_bytes();previous={'psg':(out/'initial.bin').read_bytes()}
    source=bytearray(6);writes=[]
    if len(actual)!=len(cases)*37:raise ValueError('complete native component capture required')
    for i,(method,address,value) in enumerate(cases):
        events=clear_events(value) if method==3 else ((address,value),)
        for reg,raw in events:
            source[reg-21]=raw&MASKS[reg-21]
            previous=project_write(bytes(source),previous,0xF4D7+(reg-25)*2 if method==1 else 0,reg)
            writes.extend((i,r,v) for r,v in previous['writes'])
        expected=previous['psg']+workspace(bytes(source),previous)
        if actual[i*37:(i+1)*37]!=expected:raise ValueError(f'gain component state mismatch at {i}: {cases[i]}')
    observed=[tuple(map(int,line.split())) for line in (out/'writes.tsv').read_text().splitlines()]
    if writes!=observed:raise ValueError('gain physical write order differs')
    if qualification_inputs(base,delivery)!=producers:raise ValueError('qualification inputs changed')
    result=dict(complete=True,cases=len(cases),physical_writes=len(writes),actual_native_ROM=True,
        ROM_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),source_registers_memory_VRAM_slots_GPIO_preserved=True,
        equal_raw_selected_repeated_normal_indexed_transitions=True,all_raw_volume_bytes=True,
        all_256_clear_entries=True,manual_listening=False,qualification_sources=producers,
        guard_scope='Main registers, canonical and immutable RAM, VRAM, slots and PSG GPIO. Source bus/audio workspace/RPC/stack excluded from byte invariance and checked separately.',
        evidence={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()})
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','delivery','out'):p.add_argument('--'+n,type=Path,required=True)
    check(**vars(p.parse_args()))
