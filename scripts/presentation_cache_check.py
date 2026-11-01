"""Original-free actual-Z80 tile-cache microproof, not a human game ROM."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT, verified_tool
from native_shift_check import HELPERS as BASE_FILES
from reference_provenance import snapshot_paths
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile, isolated_profile, validate_machine_profile

HELPERS = tuple(dict.fromkeys((*BASE_FILES, 'scripts/presentation_cache_check.py', 'src/presentation_cache.asm')))
ROW_BYTES = 6200


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_row(actual, expected):
    if len(actual) != ROW_BYTES or len(expected) != ROW_BYTES: raise ValueError('complete cache result row required')
    if actual != expected:
        offset = next(i for i, (a, b) in enumerate(zip(actual, expected)) if a != b)
        raise ValueError(f'actual native cache differs at byte{offset}')


def verify_cycles(cycles):
    if not cycles or any(type(value) is not int or not 0 < value <= 6000 for value in cycles):
        raise ValueError('native cache microproof exceeds6000cycle lookup bound')


def fixtures():
    """Oracle uses complete byte equality, independently of native signatures."""
    operations = []; memory = bytearray([165]) * 6144; tables = [[] for _ in range(6)]; used = [set() for _ in range(6)]
    inputs = bytearray(); expected = bytearray()
    tile = lambda group, n: hashlib.sha256(f'cache fixture {group} {n}'.encode()).digest()[:16]
    # Full groups, duplicate reuse, overflow, generation resets and eviction.
    for epoch in range(3):
        for gen in (0, 1):
            operations.append((0, gen, bytes(16)))
            for group in range(gen * 3, gen * 3 + 3):
                values = list(range(64)) if epoch != 1 else list(reversed(range(64)))
                for n in values:
                    key = tile(group, n + (64 if epoch == 2 else 0)); operations.append((1, group, key))
                    if n % 7 == 0: operations.append((1, group, key))
                operations.append((1, group, tile(group, 200 + epoch)))
    # Four deliberately identical signatures with fourteen equal prefix bytes.
    # A shortcut that trusts a signature or short prefix returns the wrong ID.
    operations.append((0, 0, bytes(16)))
    collisions = [bytes(14) + bytes((n, -((n * 2) & 255) & 255)) for n in range(4)]
    for key in collisions + list(reversed(collisions)): operations.append((1, 0, key))
    for op, group in ((0, 2), (1, 6), (1, 255)): operations.append((op, group, bytes(16)))
    for op, group, key in operations:
        inputs.extend(bytes((op, group)) + key); result = miss = 0
        if op == 0 and group not in (0, 1) or op == 1 and group >= 6:
            result = 255; miss = 2
        elif op == 0:
            for index in range(group * 3, group * 3 + 3): used[index].clear()
        else:
            existing = next((index for index, value in enumerate(tables[group]) if value == key), None)
            if existing is not None: slot = existing
            else:
                slot = next((n for n in range(64) if n not in used[group]), None); miss = 1
                if slot is not None:
                    if slot == len(tables[group]): tables[group].append(key)
                    else: tables[group][slot] = key
                    start = (group * 64 + slot) * 16; memory[start:start + 16] = key
            if slot is None: result = 255; miss = 2
            else: used[group].add(slot); result = slot + (64 if group >= 3 else 0)
        bitmap = bytes(sum(1 << bit for bit in range(8) if byte * 8 + bit in selected) for selected in used for byte in range(8))
        expected.extend(bytes((result, miss)) + bytes(len(t) for t in tables) + bitmap + memory)
    return bytes(inputs), bytes(expected)


def audit_saved(out):
    out = Path(out); inputs, expected = fixtures(); count = len(inputs) // 18
    if (out / 'cases.bin').read_bytes() != inputs or (out / 'expected.bin').read_bytes() != expected:
        raise ValueError('persisted cache input/oracle matrix changed')
    actual = (out / 'actual.bin').read_bytes()
    if len(actual) != count * ROW_BYTES: raise ValueError('incomplete actual native cache matrix')
    for offset in range(0, len(actual), ROW_BYTES): verify_row(actual[offset:offset + ROW_BYTES], expected[offset:offset + ROW_BYTES])
    rows = [[int(v) for v in line.split()] for line in (out / 'cycles.tsv').read_text().splitlines()]
    if len(rows) != count or any(len(row) != 2 or row[0] != index for index, row in enumerate(rows)):
        raise ValueError('complete ordered cache timing matrix required')
    elapsed = [row[1] for row in rows]; verify_cycles(elapsed)
    if 'CACHE_FAIL' in (out / 'emulator.log').read_text(): raise ValueError('actual cache guard failure retained in log')
    return count, max(elapsed)


def check(out, explore=False):
    producer = {'tool_source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'utility_fingerprints': {name: digest(ROOT / name) for name in HELPERS}} if explore else snapshot_paths(HELPERS)
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    inputs, expected = fixtures(); count = len(inputs) // 18
    (out / 'cases.bin').write_bytes(inputs); (out / 'expected.bin').write_bytes(expected)
    assembly = '    ORG $4000\n    DB "AB"\n    DW start\n    DS 12,0\nstart:\n    DI\n    LD SP,$F380\nready:\n    JP ready\n    INCLUDE "presentation_cache.asm"\n    DS $C000-$,$FF\n'
    (out / 'unit.asm').write_text(assembly); rom = out / 'unit.rom'; assembler = verified_tool('sjasmplus')
    compiled = subprocess.run([str(assembler), '--nologo', f'--inc={ROOT/"src"}', f'--raw={rom}', f'--sym={out/"unit.sym"}', str(out / 'unit.asm')], capture_output=True, text=True, timeout=60)
    (out / 'assembler.log').write_text(compiled.stdout + compiled.stderr)
    if compiled.returncode: raise ValueError('cache unit assembler failed: ' + compiled.stderr[-1500:])
    syms = symbols(out / 'unit.sym'); emulator = Path(shutil.which('openmsx')).resolve()
    profile = isolated_profile(find_machine_profile(str(emulator))); validate_machine_profile(profile)
    user = out / 'user-data'; (user / 'machines').mkdir(parents=True); (user / 'machines/Frostbite_Cache.xml').write_bytes(profile)
    settings = out / 'settings.xml'; settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script = f'''set save_settings_on_exit false
set renderer none
set throttle off
set count 0
set input [open {{{out/'cases.bin'}}} rb];set cases [read $input];close $input
set result [open {{{out/'actual.bin'}}} wb]
set cycles [open {{{out/'cycles.tsv'}}} w]
set blank [string repeat [binary format c 165] 128]
proc fail_cache {{message}} {{puts stderr "CACHE_FAIL $message case=$::count";exit 1;return -code error $message}}
proc dispatch_cache {{}} {{
    if {{$::count=={count}}} {{close $::result;close $::cycles;exit;return}}
    set sample [string range $::cases [expr {{$::count*18}}] [expr {{$::count*18+17}}]]
    binary scan [string range $sample 0 1] cu* header;lassign $header op group
    set ::tile [string range $sample 2 17];debug write_block memory 0xCC80 $::tile
    set entry [expr {{$op ? {syms['presentation_cache_tile']} : {syms['presentation_cache_begin']}}}]
    reg AF [expr {{$group*256+197}}];reg BC 4951;reg DE 21760;reg HL 43981;reg IX 56797;reg IY 61166;reg SP 0xF380
    debug write_block memory 0xC180 [binary format cu* [list 205 [expr {{$entry&255}}] [expr {{$entry>>8}}] 195 134 193 24 254]]
    reg PC 0xC180;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{
    debug remove_bp $::boot;debug break
    after break {{
        if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_cache target}}
        debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
        debug write_block memory 0xCCA0 [string repeat [binary format c 0] 96]
        set ::slot [debug read ioports 168]
        debug set_bp 0xC186 {{}} {{debug break;after break {{
            if {{[debug read_block memory 0xC000 128] ne $::blank || [debug read_block memory 0xC600 256] ne [string repeat [binary format c 165] 256]}} {{fail_cache source-state}}
            if {{[debug read_block memory 0xE800 0xB40] ne [string repeat [binary format c 165] 0xB40]}} {{fail_cache heap-stack-redzone}}
            if {{[debug read_block memory 0xCC80 16] ne $::tile}} {{fail_cache source-tile}}
            if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_cache abi}}
            set row [binary format cu* [list [reg A] [debug read memory 0xCCA6]]]
            append row [debug read_block memory 0xCCA0 6] [debug read_block memory 0xCCB0 48] [debug read_block memory 0xD000 6144]
            puts -nonewline $::result $row
            puts $::cycles "$::count [expr {{round(([machine_info time]-$::started)*3579545)}}]"
            incr ::count;dispatch_cache
        }}}}
        dispatch_cache
    }}
}}]
after time 15 {{fail_cache watchdog}}
'''
    (out / 'launch.tcl').write_text(script)
    executed = subprocess.run([str(emulator), '-setting', str(settings), '-machine', 'Frostbite_Cache', '-cart', str(rom), '-romtype', 'ASCII16', '-script', str(out / 'launch.tcl')], cwd=ROOT,
        env={**os.environ, 'OPENMSX_USER_DATA': str(user), 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}, capture_output=True, text=True, timeout=120)
    log = executed.stdout + executed.stderr; (out / 'emulator.log').write_text(log)
    if executed.returncode or 'CACHE_FAIL' in log: raise ValueError('actual cache unit failed: ' + log[-1500:])
    actual_count, maximum = audit_saved(out)
    if any(digest(ROOT / name) != value for name, value in producer['utility_fingerprints'].items()): raise ValueError('cache unit producer changed')
    if not explore and snapshot_paths(HELPERS) != producer: raise ValueError('cache unit revision changed')
    report = {'producer': producer, 'exploratory': explore, 'cases': actual_count, 'complete': True, 'max_cycles_including_rpc': maximum,
              'declared_matrix_lookup_limit': 6000,
              'rom_sha256': digest(rom), 'emulator_sha256': digest(emulator), 'profile_sha256': hashlib.sha256(profile).hexdigest(),
              'artifacts': {str(path.relative_to(out)): digest(path) for path in out.rglob('*') if path.is_file()},
              'scope': 'Original-free instrumented cache microcartridge; measured lookup bound applies to this declared matrix, not all possible signatures or whole-game frame performance; not a human game ROM'}
    (out / 'check.json').write_text(json.dumps(report, indent=2) + '\n'); return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', type=Path, required=True); parser.add_argument('--explore', action='store_true')
    args = parser.parse_args(); result = check(args.out, args.explore)
    print(json.dumps({key: result[key] for key in ('cases', 'complete', 'max_cycles_including_rpc')}))
