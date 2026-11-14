"""Passive physical-ROM coverage for the accepted v30 ASCII16 runtime.

Coverage is a lower bound. It must never be used alone to remove unobserved
tables. This observer deliberately reuses the existing source/pixel oracle.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import types

from environment import ROOT
from reference_traces import private_output
from render_build import symbols
from compact_inventory import read_trace
import presentation_credit_reference_check as checker
import presentation_border_check as border
from presentation_credit_reference import expected_frame
from presentation_ready_clock import clocks

CONTROL_SHA = 'e75535923a5751e3f4924dc7a3a2f762041b825efb7a5336650d35890cd3ff1d'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observer_tcl(out, entry, syms):
    return f'''
set compact_enabled 0
set compact_phase startup
set compact_bank0 0
set compact_bank1 1
array set compact_reads {{}}
array set compact_maps {{}}
set compact_contacts 0
debug set_bp {entry} {{}} {{set ::compact_enabled 1}}
debug set_bp {syms['native_reset_done']} {{}} {{set ::compact_phase runtime}}
debug set_bp {syms['contact_compact']} {{}} {{incr ::compact_contacts}}
debug set_watchpoint write_mem {{0x6000 0x67FF}} {{$::compact_enabled}} {{
 set ::compact_bank0 $::wp_last_value
 incr ::compact_maps($::compact_phase,0,$::wp_last_value)
}}
debug set_watchpoint write_mem {{0x7000 0x77FF}} {{$::compact_enabled}} {{
 set ::compact_bank1 $::wp_last_value
 incr ::compact_maps($::compact_phase,1,$::wp_last_value)
}}
debug set_watchpoint read_mem {{0x4000 0xBFFF}} {{$::compact_enabled}} {{
 set bank [expr {{$::wp_last_address<0x8000 ? $::compact_bank0 : $::compact_bank1}}]
 set physical [expr {{$bank*16384+($::wp_last_address&16383)}}]
 set ::compact_reads($::compact_phase,$physical) 1
}}
proc compact_finish {{}} {{
 set f [open {{{out / 'rom-reads.tsv'}}} w]
 foreach key [lsort [array names ::compact_reads]] {{puts $f $key}}
 close $f
 set f [open {{{out / 'mapper.tsv'}}} w]
 foreach key [lsort [array names ::compact_maps]] {{puts $f "$key $::compact_maps($key)"}}
 close $f
 set f [open {{{out / 'contact-calls.txt'}}} w];puts $f $::compact_contacts;close $f
}}
'''


def instrument_harness(text, observer, mode):
    at = text.rfind('after time ')
    finish = 'exit;return}' if mode == 'matrix' else '\n  exit;return'
    if at < 0 or text.count(finish) != 1:
        raise ValueError('native harness completion differs')
    text = text[:at] + observer + text[at:]
    replacement = ('compact_finish;' + finish if mode == 'matrix'
                   else '\n  compact_finish' + finish)
    return text.replace(finish, replacement, 1)


def probe(build, out, mode, *, baseline=None, steps=None):
    build, out = Path(build).resolve(), private_output(out)
    if mode not in ('ntsc', 'pal', 'bear-ntsc', 'bear-pal', 'matrix'):
        raise ValueError('explicit regular/bear TV family or source matrix required')
    if out.exists():
        raise ValueError('fresh output directory required')
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = json.loads((build / 'build.json').read_text())
    if meta['rom']['sha256'] != CONTROL_SHA:
        raise ValueError('observer is qualified only for accepted v30 ASCII16')
    artifact = build / meta['rom']['filename']
    if sha(artifact) != CONTROL_SHA:
        raise ValueError('control ROM identity differs')
    rom = artifact.read_bytes()
    syms = symbols(build / 'presentation.sym')
    producer = Path(__file__).read_bytes()
    if steps is None:
        steps = 2115 if mode == 'matrix' else 620 if mode.startswith('bear-') else 2252
    maximum = 2115 if mode == 'matrix' else 620 if mode.startswith('bear-') else 2252
    if type(steps) is not int or not 2 <= steps <= maximum:
        raise ValueError('bounded coverage count required')
    base_run, base_probe = subprocess.run, border.legacy.probe

    def run(command, *args, **kwargs):
        if isinstance(command, list) and '-script' in command and 'openmsx' in Path(command[0]).name.lower():
            path = Path(command[command.index('-script') + 1])
            text = path.read_text()
            observer = observer_tcl(out, int.from_bytes(rom[2:4], 'little'), syms)
            path.write_text(instrument_harness(text, observer, mode))
            kwargs['timeout'] = 600
        return base_run(command, *args, **kwargs)

    if mode.startswith('bear-'):
        parent = ROOT / 'scripts/presentation_fixed_clock_probe.py'
        source = parent.read_text()
        needle = "source=ROOT/'outputs/progression/route-progression-v0-a'"
        if source.count(needle) != 1:
            raise ValueError('bear source-route substitution differs')
        source = source.replace(needle, "source=ROOT/'outputs/hazards/route-bear-chase-a'")
        copy = out.parent / (out.name + '-bear-probe.py')
        with copy.open('x') as stream:
            stream.write(source)
        module = types.ModuleType('compact_bear_probe')
        module.__file__ = str(copy)
        exec(compile(source, str(copy), 'exec'), module.__dict__)
        module.clocks, module.adapted_frame = clocks, expected_frame
        module.audit_row = lambda *a, **kw: border.legacy.audit_row(*a, **kw)
        module.audit_active = lambda *a, **kw: border.legacy.audit_active(*a, **kw)
        border.legacy.probe = module.probe
    subprocess.run = run
    try:
        result = checker.check(build, out, 'matrix' if mode == 'matrix' else mode.split('-')[-1], steps)
    finally:
        subprocess.run, border.legacy.probe = base_run, base_probe
    if Path(__file__).read_bytes() != producer or sha(artifact) != CONTROL_SHA:
        raise ValueError('observer or control changed during capture')
    phases = read_trace((out / 'rom-reads.tsv').read_text(), len(rom))
    buffers = (('captures.bin', 'ownership.bin', 'timing.tsv', 'scenes.bin', 'band-records.bin')
               if mode == 'matrix' else ('route-cpu.bin', 'owners.bin', 'irq.tsv', 'pictures.tsv', 'captures.bin'))
    parity = {name: sha(out / name) == sha(Path(baseline) / name) for name in buffers} if baseline else None
    receipt = dict(complete=True, runtime_changed=False, mode=mode, count=steps,
        rom_sha256=CONTROL_SHA, observed_bytes={k: len(v) for k, v in phases.items()},
        observed_union_bytes=len(phases['startup'] | phases['runtime']),
        baseline_buffer_parity=parity, original_oracle_complete=result['complete'],
        scope='Tested fetch/data read coverage only; unobserved bytes are unclassified.',
        producer_sha256=hashlib.sha256(producer).hexdigest(),
        files={p.name: sha(p) for p in out.iterdir() if p.is_file()})
    (out / 'live-set.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if parity is not None and not all(parity.values()):
        raise ValueError('observer changed baseline source/ownership/timing buffers')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mode', choices=('ntsc', 'pal', 'bear-ntsc', 'bear-pal', 'matrix'), required=True)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--steps', type=int)
    args = parser.parse_args()
    result = probe(args.build, args.out, args.mode, baseline=args.baseline, steps=args.steps)
    print({k: v for k, v in result.items() if k != 'files'})
