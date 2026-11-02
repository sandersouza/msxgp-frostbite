"""Actual-Z80 finite-geometry reader microproof; no human game delivery."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from environment import ROOT, verified_tool
from native_shift_check import HELPERS as BASE_FILES
from original_graphics import catalog, view
from presentation_fragments import GEOMETRY_BANKS, compile_geometry, mask_tiles
from reference_provenance import snapshot_paths
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile, isolated_profile, validate_machine_profile

HELPERS = tuple(dict.fromkeys((*BASE_FILES, 'scripts/presentation_geometry_check.py', 'scripts/presentation_fragments.py',
    'scripts/presentation_model.py', 'scripts/graphics_mapping.py', 'scripts/original_graphics.py', 'src/presentation_geometry.asm', 'src/movement.asm')))
ROW_BYTES = 123


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_row(actual, expected):
    if len(actual) != ROW_BYTES or len(expected) != ROW_BYTES or actual != expected:
        raise ValueError('actual finite geometry grid/ID/pattern/error row differs')


def metadata(geometry, pointer_map):
    data = bytearray(pointer_map); labels = {'row_map': 0}
    for family in ('row', 'floe', 'bear'):
        labels[f'{family}_roots'] = len(data); data.extend(bytes(byte for root in geometry['roots'][family] for byte in root))
    labels['classes'] = len(data)
    for cls in geometry['classes']:
        data.extend(bytes((cls['columns'], cls['rows'], cls['stride'])) + cls['count'].to_bytes(2, 'little') + cls['offset'].to_bytes(3, 'little'))
    include = ''.join(f'p_geo_{name}_data EQU ${0x8000 + offset:04X}\n' for name, offset in labels.items())
    include += f'p_geo_class_count EQU {len(geometry["classes"])}\np_geo_pattern_count EQU {geometry["patterns"]}\n'
    return bytes(data).ljust(16384, b'\xff'), include


def fixtures(rom, geometry, directory):
    source = catalog(rom); pointers = sorted({0} | {a['range'][0] - 0xFD00 for k, a in source['assets'].items() if k.startswith('row-')})
    flat = b''.join((directory / f'geometry-{bank:03d}.bin').read_bytes() for bank in geometry['physical_banks'])
    pool = {flat[index * 8:index * 8 + 8]: index for index in range(geometry['patterns'])}; inputs = bytearray(); expected = bytearray()
    shifts = [0]
    for y in range(1, 7):
        value = rom[0xDD2 + 7 - y] >> 4; shifts.append(shifts[-1] - (value if value < 8 else value - 16))
    for family in range(3):
        count = (len(pointers) * 2, 9, 16)[family]
        for group in range(count):
            if family == 0:
                glyph = view(rom, 0xFD00 + pointers[group // 2], 8, bool(group & 1)); bitmap = glyph['pixels']; width = height = 8
            elif family == 1:
                size = group + 8; width = size + 8; height = 7; bitmap = bytearray(width * height)
                for y, delta in enumerate(shifts): bitmap[y * width + 8 + delta:y * width + 8 + delta + size] = bytes([1]) * size
            else:
                glyph = view(rom, 0xFD00 + rom[0xEE7 + group // 2], 19, bool(group & 1), 2)
                bitmap = glyph['pixels'] + glyph['pixels'][-16:]; width = 16; height = 20
            for variant in range(32 if family == 2 else 128):
                x = variant // (2 if family == 2 else 8); y = 3 + variant % 2 if family == 2 else variant % 8
                compiled = mask_tiles(bitmap, width, height, x, y); masks = compiled['patterns']
                ids = b''.join(pool[pattern].to_bytes(2, 'little') for pattern in masks)
                inputs.extend(bytes((family, group, variant)))
                expected.extend(bytes((compiled['columns'], compiled['rows'])) + ids.ljust(24, b'\xff') + b''.join(masks).ljust(96, b'\xa5') + bytes(1))
    return bytes(inputs), bytes(expected)


def check(out, explore=False):
    producer = {'tool_source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'utility_fingerprints': {name: digest(ROOT / name) for name in HELPERS}} if explore else snapshot_paths(HELPERS)
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    rom = (ROOT / 'references/roms/frostbite.bin').read_bytes(); geometry = compile_geometry(rom, out / 'geometry')
    boot, include = metadata(geometry, (out / 'geometry/row-pointer-map.bin').read_bytes())
    (out / 'boot.bin').write_bytes(boot); (out / 'presentation_geometry.inc').write_text(include)
    inputs, expected = fixtures(rom, geometry, out / 'geometry'); count = len(inputs) // 3
    (out / 'cases.bin').write_bytes(inputs); (out / 'expected.bin').write_bytes(expected)
    movement = (ROOT / 'src/movement.asm').read_text(); mapper = movement[movement.index('map_page2:\n'):movement.index('set_address:\n')]
    entry = '''    ORG $4000
    DB "AB"
    DW start
    DS 12,0
start:
    DI
    LD SP,$F380
    CALL map_page2
    DI
ready:
    JP ready
unit_run:
    CALL presentation_geometry_lookup
    RET C
    LD HL,$C2A0
    LD IX,$C480
    LD A,(p_geo_stride)
    SRL A
    LD B,A
.tile:
    PUSH BC
    PUSH HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    CALL presentation_geometry_pattern
    LD HL,$CC80
    PUSH IX
    POP DE
    LD BC,8
    LDIR
    PUSH DE
    POP IX
    POP HL
    INC HL
    INC HL
    POP BC
    DJNZ .tile
    RET
'''
    entry += mapper + '    INCLUDE "presentation_geometry.asm"\n    DS $8000-$,$FF\n    ORG $8000\n' + f'    INCBIN "{out/"boot.bin"}"\n    ORG $8000\n    DS $4000,$FF\n'
    for bank in range(3, 256):
        entry += '    ORG $8000\n'
        entry += f'    INCBIN "{out/"geometry"/f"geometry-{bank:03d}.bin"}"\n' if bank in geometry['physical_banks'] else '    DS $4000,$FF\n'
    (out / 'unit.asm').write_text(entry); artifact = out / 'unit.rom'; assembler = verified_tool('sjasmplus')
    compiled = subprocess.run([str(assembler), '--nologo', f'--inc={ROOT/"src"}', f'--inc={out}', f'--raw={artifact}', f'--sym={out/"unit.sym"}', str(out / 'unit.asm')], capture_output=True, text=True, timeout=60)
    (out / 'assembler.log').write_text(compiled.stdout + compiled.stderr)
    if compiled.returncode: raise ValueError('geometry microassembler failed: ' + compiled.stderr[:1200])
    syms = symbols(out / 'unit.sym'); emulator = Path(shutil.which('openmsx')).resolve()
    profile = isolated_profile(find_machine_profile(str(emulator))); validate_machine_profile(profile)
    user = out / 'user-data'; (user / 'machines').mkdir(parents=True); (user / 'machines/Frostbite_Geometry.xml').write_bytes(profile)
    settings = out / 'settings.xml'; settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    script = f'''set save_settings_on_exit false
set renderer none
set throttle off
set count 0
set f [open {{{out/'cases.bin'}}} rb];set cases [read $f];close $f
set result [open {{{out/'actual.bin'}}} wb]
set timing [open {{{out/'cycles.tsv'}}} w]
set blank [string repeat [binary format c 165] 128]
proc fail_geometry {{message}} {{puts stderr "GEOMETRY_FAIL $message case=$::count";exit 1;return -code error $message}}
proc dispatch_geometry {{}} {{
    if {{$::count=={count}}} {{close $::result;close $::timing;exit;return}}
    binary scan [string range $::cases [expr {{$::count*3}}] [expr {{$::count*3+2}}]] cu* data
    lassign $data family group variant
    debug write_block memory 0xC2A0 [string repeat [binary format c 255] 24]
    debug write_block memory 0xC480 [string repeat [binary format c 165] 96]
    reg AF [expr {{$family*256}}];reg BC [expr {{$group*256+$variant}}];reg SP 0xF380
    debug write_block memory 0xC760 [binary format cu* {{205 {syms['unit_run'] & 255} {syms['unit_run'] >> 8} 195 102 199 24 254}}]
    reg PC 0xC760;set ::started [machine_info time];debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{
    debug remove_bp $::boot;debug break
    after break {{
        if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_geometry target}}
        debug write_block memory 0xC000 [string repeat [binary format c 165] 0x3340]
        set ::slot [debug read ioports 168]
        debug set_bp 0xC766 {{}} {{debug break;after break {{
            if {{[debug read_block memory 0xC000 128] ne $::blank || [debug read_block memory 0xC600 256] ne [string repeat [binary format c 165] 256]}} {{fail_geometry source-state}}
            if {{[debug read_block memory 0xE800 0xB40] ne [string repeat [binary format c 165] 0xB40]}} {{fail_geometry heap-stack-redzone}}
            if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_geometry abi}}
            set row [debug read_block memory 0xC2B8 2]
            append row [debug read_block memory 0xC2A0 24] [debug read_block memory 0xC480 96] [debug read_block memory 0xC2BC 1]
            puts -nonewline $::result $row
            puts $::timing "$::count [expr {{round(([machine_info time]-$::started)*3579545)}}]"
            incr ::count;dispatch_geometry
        }}}}
        dispatch_geometry
    }}
}}]
after time 60 {{fail_geometry watchdog}}
'''
    (out / 'launch.tcl').write_text(script)
    executed = subprocess.run([str(emulator), '-setting', str(settings), '-machine', 'Frostbite_Geometry', '-cart', str(artifact), '-romtype', 'ASCII16', '-script', str(out / 'launch.tcl')],
        cwd=ROOT, env={**os.environ, 'OPENMSX_USER_DATA': str(user), 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}, capture_output=True, text=True, timeout=120)
    log = executed.stdout + executed.stderr; (out / 'emulator.log').write_text(log)
    if executed.returncode or 'GEOMETRY_FAIL' in log: raise ValueError('actual geometry reader failed: ' + log[-1400:])
    actual = (out / 'actual.bin').read_bytes()
    if len(actual) != len(expected): raise ValueError('incomplete actual geometry matrix')
    for offset in range(0, len(expected), ROW_BYTES): verify_row(actual[offset:offset + ROW_BYTES], expected[offset:offset + ROW_BYTES])
    if (out / 'cases.bin').read_bytes() != inputs or (out / 'expected.bin').read_bytes() != expected: raise ValueError('geometry fixture files changed')
    if any(digest(ROOT / name) != value for name, value in producer['utility_fingerprints'].items()): raise ValueError('geometry microproducer changed')
    if not explore and snapshot_paths(HELPERS) != producer: raise ValueError('geometry microrevision changed')
    report = {'producer': producer, 'exploratory': explore, 'complete': True, 'cases': count, 'geometry': geometry,
              'rom_sha256': digest(artifact), 'emulator_sha256': digest(emulator), 'profile_sha256': hashlib.sha256(profile).hexdigest(),
              'max_cycles_including_rpc': max(int(line.split()[1]) for line in (out / 'cycles.tsv').read_text().splitlines()),
              'artifacts': {str(path.relative_to(out)): digest(path) for path in out.rglob('*') if path.is_file()},
              'scope': 'Original-derived instrumented geometry microcartridge; full original masks/IDs, all declared bank/phase cases; not human game or whole-frame acceptance'}
    (out / 'check.json').write_text(json.dumps(report, indent=2) + '\n'); return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', type=Path, required=True); parser.add_argument('--explore', action='store_true')
    args = parser.parse_args(); result = check(args.out, args.explore)
    print(json.dumps({key: result[key] for key in ('cases', 'complete', 'max_cycles_including_rpc')}))
