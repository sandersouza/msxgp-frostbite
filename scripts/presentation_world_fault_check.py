"""Directed geometry-failure injection; verifies the real Z80 stack unwind.

This deliberately perturbed execution is not a gameplay or timing benchmark.
"""
import argparse
import json
from pathlib import Path
import subprocess

import presentation_fixed_clock_probe as clock
from render_build import symbols


def check(build,out,expect_rejection=False):
    meta=json.loads((build/'build.json').read_text());rom=(build/meta['rom']['filename']).read_bytes()
    if clock.sha(rom)!=meta['rom']['sha256']:raise ValueError('ROM identity differs')
    s=symbols(build/'presentation.sym');start=115*16384+0x3800
    call=b'\xcd'+s['qe_geometry'].to_bytes(2,'little')
    lo=start+s['v_cells']-0xe900;hi=start+meta['fixed_clock']['ram_code_bytes']
    if rom.count(call,lo,hi)!=1:raise ValueError('unique real fusion geometry call required')
    site=0xe900+rom.index(call,lo,hi)-start+3
    source=Path(__file__).read_bytes();original_run=subprocess.run
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            path=Path(args[args.index('-script')+1])
            text=f'''
set world_fault_injected 0
debug set_bp {site} {{!$::world_fault_injected}} {{
 set ::world_fault_injected 1
 set ::world_fault_expected_sp [expr {{[reg SP]+6}}]
 reg AF [expr {{[reg AF]|1}}]
}}
debug set_bp {s['p_world_fail']} {{$::world_fault_injected}} {{
 if {{[reg SP]!=$::world_fault_expected_sp}} {{puts stderr WORLD_FAULT_UNBALANCED;exit 1}}
 puts stderr WORLD_FAULT_PASS
 exit 0
}}
'''
            path.write_text(path.read_text()+text)
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:
        try:clock.probe(build,out,'ntsc',2252)
        except ValueError:
            log=(out/'emulator.log').read_text()
            expected='WORLD_FAULT_UNBALANCED' if expect_rejection else 'WORLD_FAULT_PASS'
            if expected not in log:raise
        else:raise ValueError('fault was not exercised')
    finally:subprocess.run=original_run
    if Path(__file__).read_bytes()!=source:raise ValueError('fault checker changed')
    report=dict(complete=True,rom_sha256=clock.sha(rom),injected_return=site,expected_rejection=expect_rejection,
        stack_balanced=not expect_rejection,producer_sha256=clock.sha(source),log_sha256=clock.sha((out/'emulator.log').read_bytes()),
        scope='Carry deliberately forced after real full geometry lookup; failure must enter the existing handler with all three saved register pairs removed. Not timing evidence.')
    (out/'fault-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--expect-rejection',action='store_true');a=p.parse_args();check(a.build.resolve(),a.out.resolve(),a.expect_rejection)
