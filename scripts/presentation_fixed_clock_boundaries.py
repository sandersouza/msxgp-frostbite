"""Align real VDP interrupts with selected foreground transaction boundaries.

This adversarial test parks the CPU in an isolated diagnostic JR loop with IFF
clear until the next *hardware* VBlank is pending, then resumes at the saved
instruction with its original IFF. No source state, IRQ vector or ROM is injected.
Its deliberately delayed renderer timings are not performance measurements.
"""
import argparse
import json
from pathlib import Path
import subprocess

import presentation_fixed_clock_probe as clock
from render_build import symbols


def script(s,out,negative_register=False):
    targets=[('mapper-before',s['t_mapper']),('mapper-shadow',s['t_mapper']+3),
        ('address-low',s['t_vdp_write']+4),('fill-address-low',s['t_fill']+5),
        ('stream-byte',s['vdp_stream.byte']+2),('fill-byte',s['t_fill.byte']+2),
        ('snapshot-before',s['t_prepare_gate']),('snapshot-copy',s['t_prepare_gate']+17),
        ('snapshot-complete',s['t_prepare_gate']+19)]
    setup='\n'.join(f'debug set_bp {address} {{}} {{boundary_select {name}}}' for name,address in targets)
    return f'''
set boundary_names {{{' '.join(name for name,_ in targets)}}}
set boundary_seen {{}}
set boundary_state idle
set boundary_log [open {{{out/'boundaries.tsv'}}} w]
set boundary_registers {{AF BC DE HL IX IY AF2 BC2 DE2 HL2 I}}
proc boundary_select {{name}} {{
 if {{$::route_index<100 || $::boundary_state ne "idle" || $name in $::boundary_seen ||
     [debug read memory {s['t_in_irq']}] || [debug read memory {s['t_ready']}] ||
     ([debug read {{VDP status regs}} 0]&128)}} {{return}}
 set ::boundary_state parked;set ::boundary_name $name
 set ::boundary_pc [reg PC];set ::boundary_iff [reg IFF]
 debug break;after break {{
  reg IFF 0
  debug write_block memory 0xE8C0 [binary format H* 18fe]
  reg PC 0xE8C0
  after time 0.00002 boundary_pending
  debug cont
 }}
}}
proc boundary_pending {{}} {{
 if {{!([debug read {{VDP status regs}} 0]&128)}} {{after time 0.00002 boundary_pending;return}}
 debug break;after break {{
  set ::boundary_state resumed
  reg PC $::boundary_pc;reg IFF $::boundary_iff
  debug cont
 }}
}}
proc boundary_irq {{}} {{
 if {{$::boundary_state ne "resumed"}} {{return}}
 set ::boundary_state returning
 set ::boundary_saved {{}}
 foreach r $::boundary_registers {{lappend ::boundary_saved [reg $r]}}
 set ::boundary_stack [expr {{[reg SP]+2}}]
 set ::boundary_return [word [reg SP]]
 set ::boundary_bank [debug read memory {s['t_bank']}]
 set ::boundary_vram [debug read_block VRAM 0 16384]
 set ::boundary_snapshot [debug read_block memory 0xF000 128]
 if {{$::boundary_name in {{address-low fill-address-low snapshot-copy snapshot-complete}} &&
     ($::boundary_iff&3)!=0}} {{fail boundary-unprotected-critical-section}}
 if {{$::boundary_name in {{snapshot-copy snapshot-complete}} &&
     $::boundary_snapshot ne [debug read_block memory 0xC000 128]}} {{fail boundary-snapshot-before-irq}}
 set ::boundary_return_bp [debug set_bp $::boundary_return {{[reg SP]==$::boundary_stack}} boundary_returned]
}}
proc boundary_returned {{}} {{
 debug remove_bp $::boundary_return_bp
 {'reg AF2 [expr {[reg AF2]^1}]' if negative_register else ''}
 set actual {{}}
 foreach r $::boundary_registers {{lappend actual [reg $r]}}
 if {{$actual ne $::boundary_saved || ([reg IFF]&3)!=3 || [debug read memory {s['t_in_irq']}]}} {{fail boundary-register-restoration}}
 if {{[debug read memory {s['t_bank']}]!=$::boundary_bank}} {{fail boundary-bank-shadow}}
 if {{[debug read_block memory 0x8000 16384] ne [string range $::boundary_rom [expr {{$::boundary_bank*16384}}] [expr {{($::boundary_bank+1)*16384-1}}]]}} {{fail boundary-bank-hardware}}
 if {{[debug read_block VRAM 0 16384] ne $::boundary_vram}} {{fail boundary-irq-mutated-vram}}
 if {{[debug read_block memory 0xF000 128] ne $::boundary_snapshot}} {{fail boundary-irq-mutated-snapshot}}
 puts $::boundary_log "$::boundary_name $::boundary_pc $::boundary_return $::boundary_bank $::boundary_stack $::boundary_iff $::boundary_saved"
 flush $::boundary_log
 lappend ::boundary_seen $::boundary_name;set ::boundary_state idle
}}
set f [open {{{out/'boundary-rom.bin'}}} rb];set boundary_rom [read $f];close $f
{setup}
debug set_bp {s['t_irq']} {{}} boundary_irq
'''


def check(build,out,family,expanded=False,negative_register=False):
    meta=json.loads((build/'build.json').read_text());rom=(build/meta['rom']['filename']).read_bytes()
    source=Path(__file__).read_bytes();s=symbols(build/'presentation.sym')
    # Emitted boundaries: never infer an address from bytes in asset data.
    kernel=clock.ram_code(meta,rom)
    def body(address,size):return kernel[address-0xE900:address-0xE900+size]
    if body(s['t_prepare_gate']+17,2)!=bytes.fromhex('edb0'):
        raise ValueError('snapshot LDIR boundary changed')
    if body(s['t_vdp_write']+4,1)!=b'\x7a' or body(s['t_fill']+5,1)!=b'\x7a':
        raise ValueError('VDP low-byte boundaries changed')
    original_run=subprocess.run
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            path=Path(args[args.index('-script')+1]);out=path.parent
            (out/'boundary-rom.bin').write_bytes(rom)
            (out/'boundary-producer.py').write_bytes(source)
            path.write_text(path.read_text()+script(s,out,negative_register))
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:
        try:result=clock.probe(build,out,family,320,expanded)
        except ValueError as error:
            if not negative_register or 'CLOCK_FAIL boundary-register-restoration' not in str(error):raise
            if (out/'check.json').exists():raise ValueError('negative control produced a positive receipt')
            result=dict(complete=True,negative_control='AF2 mutation after RETI must fail register oracle',
                expected_failure='boundary-register-restoration',rom_sha256=clock.sha(rom),producer_sha256=clock.sha(source),
                launch_sha256=clock.sha((out/'launch.tcl').read_bytes()),log_sha256=clock.sha((out/'emulator.log').read_bytes()))
            (out/'negative-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result);return result
    finally:subprocess.run=original_run
    if negative_register:raise ValueError('negative register control was accepted')
    rows=[line.split() for line in (out/'boundaries.tsv').read_text().splitlines()]
    expected={'mapper-before','mapper-shadow','address-low','fill-address-low','stream-byte','fill-byte','snapshot-before','snapshot-copy','snapshot-complete'}
    if len(rows)!=9 or {r[0] for r in rows}!=expected:raise ValueError('not all9 directed IRQ boundaries were exercised')
    if Path(__file__).read_bytes()!=source:raise ValueError('boundary producer changed')
    report=dict(complete=True,rom_sha256=clock.sha(rom),family=family,expanded_ram_slot=expanded,
        boundaries=rows,main_alternate_index_sp_bank_restored=True,hardware_vblank_interrupts=True,
        irq_vram_and_snapshot_unchanged=True,source_cpu_all_ram_equal=result['source_cpu_all_ram_equal'],
        coherent_picture_pixels_equal=result['coherent_picture_pixels_equal'],canonical_source_writes=0,
        probe_receipt_sha256=clock.sha((out/'check.json').read_bytes()),producer_sha256=clock.sha(source),
        boundary_log_sha256=clock.sha((out/'boundaries.tsv').read_bytes()),
        scope='Directed real VDP interrupt alignment with temporary diagnostic PC/IFF parking. Timing deliberately perturbed; do not use these rates as performance evidence.')
    (out/'boundary-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--family',choices=('ntsc','pal'),required=True);parser.add_argument('--expanded',action='store_true')
    parser.add_argument('--negative-register',action='store_true',help='prove ABI oracle rejects post-RETI AF2 corruption')
    a=parser.parse_args();check(a.build.resolve(),a.out.resolve(),a.family,a.expanded,a.negative_register)
