"""Independent source CPU versus actual-Z80 guarded-loop microproof.

The generated original-derived microcartridge and raw fixtures stay private.
This is an instrumented proof cartridge, not a human-testable game release.
"""
import argparse
from functools import lru_cache
from importlib.metadata import version
import inspect
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

from py65.devices.mpu6502 import MPU
from environment import ROOT, verified_tool
from mechanics_probe import SliceBus
from native_shift_check import HELPERS as BASE_HELPERS
from native_write_loop import summaries, emit_summary, emit_tables, manifest
from reference_inventory import verified_input
from reference_provenance import snapshot_paths
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile, isolated_profile, validate_machine_profile
from stella_floe import digest

HELPERS = tuple(dict.fromkeys((*BASE_HELPERS, 'scripts/native_write_loop.py',
    'scripts/native_write_loop_check.py', 'scripts/mechanics_probe.py', 'requirements-ci.txt')))
ROW_BYTES = 148


def verify_case(row, expected):
    if len(row) != ROW_BYTES: raise ValueError('complete pure-loop CPU/RAM row required')
    a, x, y, flags, e, v, mode, fast = row[:8]
    ix, iy, sp, iff = struct.unpack('<4H', row[8:16]); cycles = struct.unpack('<I', row[144:148])[0]
    p = (flags & 128) | ((flags & 64) >> 5) | (e & 1) | v | mode
    if (a, x, y, p) != tuple(expected[k] for k in ('a', 'x', 'y', 'p')):
        raise ValueError('actual pure-loop CPU differs')
    if (e != expected['p'] & 1 or v != expected['p'] & 64 or mode != expected['p'] & 0x3C
            or fast != int(expected['fast']) or ix != 0xC07F or iy != expected['iy'] or sp != 0xF380
            or iff & 3 or not 0 < cycles < 2000):
        raise ValueError('actual pure-loop flags/guard/ABI differs')
    if row[16:144] != bytes(expected['ram']):
        index = next(i for i, (a, b) in enumerate(zip(row[16:144], expected['ram'])) if a != b)
        raise ValueError(f'actual pure-loop RAM {index + 128:02X} differs')
    return cycles


def cases_for(summary):
    for n in range(summary['limit']):
        for a in range(256):
            for flags in range(16):
                p = ((a & 15) << 2) | ((flags & 1) << 7) | (flags & 2) | ((flags & 4) >> 2) | ((flags & 8) << 3)
                yield n, a, 0, (a * 17 + n * 3) & 255, p
    for x in range(256):
        for n in range(256):
            yield n, (x * 37 + n) & 255, x, (n * 13 + x) & 255, ((x + n) * 37) & 255


def case_ram(case, summary):
    n, a, x, y, p = case
    ram = bytearray((i * 37 + a * 11 + y + p * 3 + x * 7) & 255 for i in range(128))
    ram[summary['bound_offset']] = n
    return ram


class ObservedBus(SliceBus):
    def __init__(self, rom):
        super().__init__(rom, {}); self.effects = {}

    def __setitem__(self, address, value):
        super().__setitem__(address, value)
        kind, offset = self.decode(address, True)
        if kind == 'ram': self.effects[offset] = value


def original_oracle(rom, summary):
    @lru_cache(None)
    def run(n, p):
        bus = ObservedBus(rom); bus.ram[:] = bytes([165]) * 128
        bus.ram[summary['bound_offset']] = n
        cpu = MPU(memory=bus, pc=summary['start']); cpu.a = 17; cpu.x = 0; cpu.y = 42; cpu.p = p; cpu.sp = 255
        count = 0
        while cpu.pc != summary['end']:
            if count >= 2000: raise ValueError('bounded original pure loop did not exit')
            cpu.step(); count += 1
        if bus.reads or bus.writes or summary['bound_offset'] in bus.effects or cpu.sp != 255:
            raise ValueError('original pure-loop preconditions violated')
        return {k: getattr(cpu, k) for k in ('a', 'x', 'y', 'p')}, dict(bus.effects)
    return run


def audit_saved(out):
    out = Path(out); rom = (ROOT / 'references/roms/frostbite.bin').read_bytes()
    selected = summaries(rom)
    if len(selected) != 1: raise ValueError('one independently audited loop required')
    summary = selected[0]; oracle = original_oracle(rom, summary)
    inputs = (out / 'cases.bin').read_bytes(); actual = (out / 'actual.bin').read_bytes()
    count = fast_count = maximum = 0
    for index, case in enumerate(cases_for(summary)):
        n, a, x, y, p = case; ram = case_ram(case, summary)
        if inputs[index * 132:(index + 1) * 132] != bytes((a, x, y, p)) + ram:
            raise ValueError('complete declared pure-loop input matrix differs')
        fast = x == 0 and n < summary['limit']
        if fast:
            registers, effects = oracle(n, p)
            for offset, value in effects.items(): ram[offset] = value
            expected = {**registers, 'ram': ram, 'fast': True, 'iy': 0xC000 + n}
        else:
            expected = {'a': a, 'x': x, 'y': y, 'p': p, 'ram': ram, 'fast': False, 'iy': 0xC000 + x}
        try: cycles = verify_case(actual[index * ROW_BYTES:(index + 1) * ROW_BYTES], expected)
        except ValueError as error: raise ValueError(f'pure-loop case{index} {case}: {error}') from error
        count += 1; fast_count += fast; maximum = max(maximum, cycles)
    if len(inputs) != 132 * count or len(actual) != ROW_BYTES * count:
        raise ValueError('partial/trailing pure-loop observations')
    return {'cases': count, 'fast_path_cases': fast_count, 'guard_fallback_cases': count - fast_count,
            'guard_index_bound_pairs': 65536, 'max_cycles_including_rpc': maximum}


def launch_script(out, syms, count):
    return f'''set save_settings_on_exit false
set renderer none
set throttle off
set count 0
set inputs [open {{{out/'cases.bin'}}} rb];fconfigure $inputs -translation binary
set actual [open {{{out/'actual.bin'}}} wb];fconfigure $actual -translation binary
proc fail_loop {{message}} {{puts stderr "WRITE_LOOP_FAIL $message case=$::count";exit 1;return -code error $message}}
proc dispatch_loop {{}} {{
    set row [read $::inputs 132]
    if {{[string length $row]==0}} {{
        close $::inputs;close $::actual
        if {{$::count!={count} || [debug read_block memory 0xD000 0x2300] ne [string repeat [binary format c 165] 0x2300]
            || [debug read_block memory 0xC080 0x580] ne [string repeat [binary format c 165] 0x580]}} {{fail_loop matrix-or-guard}}
        set f [open {{{out/'complete.json'}}} w]
        puts $f "\\{{\\"complete\\":true,\\"cases\\":$::count,\\"clock_hz\\":[machine_info z80_freq],\\"ram_bytes\\":[debug size {{Main RAM}}],\\"heap_guard\\":true\\}}"
        close $f;exit;return
    }}
    if {{[string length $row]!=132}} {{fail_loop truncated-input}}
    binary scan [string range $row 0 3] cu* r;lassign $r a x y p
    debug write_block memory 0xC000 [string range $row 4 131]
    debug write memory 0xC600 [expr {{$p&64}}];debug write memory 0xC601 [expr {{$p&60}}];debug write memory 0xC6EF 0
    reg AF [expr {{256*$a+($p&128)+(($p&2)<<5)+21}}];reg BC [expr {{256*$x+$y}}]
    reg DE [expr {{21760+($p&1)}}];reg IX 0xC07F;reg IY [expr {{0xC000+$x}}];reg SP 0xF380
    reg PC 0xC6D0;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{
    debug remove_bp $::boot;debug break
    after break {{
        if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_loop target}}
        debug write_block memory 0xD000 [string repeat [binary format c 165] 0x2300]
        debug write_block memory 0xC080 [string repeat [binary format c 165] 0x580]
        debug write_block memory 0xC6D0 [binary format cu* [list 205 {syms['run_loop']&255} {syms['run_loop']>>8} 195 214 198 24 254]]
        debug set_bp 0xC6D6 {{}} {{debug break;after break {{
            puts -nonewline $::actual [binary format cu* [list [reg A] [reg B] [reg C] [reg F] [reg E] [debug read memory 0xC600] [debug read memory 0xC601] [debug read memory 0xC6EF]]][binary format ssss [reg IX] [reg IY] [reg SP] [reg IFF]][debug read_block memory 0xC000 128][binary format i [expr {{round(([machine_info time]-$::started)*3579545)}}]]
            incr ::count;dispatch_loop
        }}}}
        dispatch_loop
    }}
}}]
after time 120 {{fail_loop watchdog}}
'''

def check(out, explore=False):
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    if dirty and not explore: raise ValueError('clean committed pure-loop producer required')
    if version('py65') != '1.2.0': raise ValueError('pinned independent source CPU required')
    source = verified_input(ROOT / 'references/roms/frostbite.bin'); original = (ROOT / 'references/roms/frostbite.bin').read_bytes()
    producer = {'tool_source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'utility_fingerprints': {p: digest(ROOT / p) for p in HELPERS}} if explore else snapshot_paths(HELPERS)
    selected = summaries(original)
    if len(selected) != 1: raise ValueError('one independently audited loop required')
    summary = selected[0]; prefix = 'unit_write_loop'
    assembly = ['    ORG $4000', '    DB "AB"', '    DW start', '    DS 12,0', '    DB "FBW0"',
                'start:', '    DI', '    LD SP,$F380', 'ready:', '    JP ready', 'run_loop:']
    assembly += [line if line.endswith(':') else '    ' + line for line in emit_summary(summary, prefix, 'loop_fast', 'loop_slow')]
    assembly += ['    RET', 'loop_fast:', '    LD HL,$C6EF', '    LD (HL),1', '    RET', emit_tables(summary, prefix), '    DS $C000-$,$FF']
    (out / 'unit.asm').write_text('\n'.join(assembly) + '\n')
    inputs = bytearray(); count = 0
    for case in cases_for(summary):
        n, a, x, y, p = case; inputs.extend(bytes((a, x, y, p)) + case_ram(case, summary)); count += 1
    (out / 'cases.bin').write_bytes(inputs)
    assembler = verified_tool('sjasmplus'); rom = out / 'unit.rom'
    result = subprocess.run([str(assembler), '--nologo', f'--raw={rom}', f'--sym={out/"unit.sym"}', str(out / 'unit.asm')],
                            capture_output=True, text=True, timeout=60)
    (out / 'assembler.log').write_text(result.stdout + result.stderr)
    if result.returncode: raise ValueError('pure-loop micro assembler failed: ' + result.stderr[-1000:])
    syms = symbols(out / 'unit.sym'); emulator = Path(shutil.which('openmsx')).resolve()
    profile = isolated_profile(find_machine_profile(str(emulator))); validate_machine_profile(profile)
    user = out / 'user-data'; (user / 'machines').mkdir(parents=True)
    (user / 'machines/Frostbite_WriteLoop.xml').write_bytes(profile)
    settings = out / 'settings.xml'; settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    tcl = launch_script(out, syms, count)
    (out / 'launch.tcl').write_text(tcl)
    result = subprocess.run([str(emulator), '-setting', str(settings), '-machine', 'Frostbite_WriteLoop',
        '-cart', str(rom), '-romtype', 'ASCII16', '-script', str(out / 'launch.tcl')], cwd=ROOT,
        env={**os.environ, 'OPENMSX_USER_DATA': str(user), 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'},
        capture_output=True, text=True, timeout=240)
    (out / 'emulator.log').write_text(result.stdout + result.stderr)
    if result.returncode or not (out / 'complete.json').exists():
        raise ValueError('actual pure-loop micro failed: ' + (result.stdout + result.stderr)[-1000:])
    receipt = json.loads((out / 'complete.json').read_text())
    if (receipt.get('complete') is not True or receipt.get('cases') != count or receipt.get('heap_guard') is not True
            or receipt.get('clock_hz') != 3579545 or receipt.get('ram_bytes') != 65536):
        raise ValueError('incomplete/unsafe pure-loop target receipt')
    stats = audit_saved(out)
    if verified_input(ROOT / 'references/roms/frostbite.bin') != source or any(digest(ROOT / p) != h for p, h in producer['utility_fingerprints'].items()):
        raise ValueError('pure-loop source/producer changed')
    if not explore and snapshot_paths(HELPERS) != producer: raise ValueError('pure-loop producer revision changed')
    report = {**producer, **stats, 'complete': True, 'exploratory': explore, 'source': source,
        'lowering': manifest(original), 'rom_sha256': digest(rom), 'emulator_sha256': digest(emulator),
        'profile_sha256': digest(user / 'machines/Frostbite_WriteLoop.xml'),
        'cpu_source_sha256': digest(Path(inspect.getfile(MPU))), 'canonical_ram_guard': True,
        'artifacts': {str(p.relative_to(out)): digest(p) for p in out.rglob('*') if p.is_file()},
        'scope': 'Controlled independent original-CPU effect oracle versus actual MSX1 Z80. Complete CPU/all128RAM, all A and NZCV combinations, all256x256 rejected-guard pairs, preserved mode/V/IX/IY/SP/DI and heap guards. Whole-game/native/paced/manual/physical acceptance separate.'}
    (out / 'check.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--explore', action='store_true'); args = p.parse_args()
    r = check(args.out, args.explore)
    print(json.dumps({k: r[k] for k in ('cases', 'fast_path_cases', 'guard_fallback_cases', 'max_cycles_including_rpc')}))
