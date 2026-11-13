"""Actual Z80 component proof; fixture ROM is not a playable Frostbite version."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess

from compact_floe import FloeOracle, build_assets
from compact_live_probe import CONTROL_SHA
from environment import ROOT, verified_tool
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile, isolated_profile, validate_machine_profile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases(assets):
    representatives = {}
    for i, group in enumerate(assets['directory']):
        representatives.setdefault(group, divmod(i, 160))
    for control, dx in representatives.values():
        for y in (0, *range(45, 78)):
            for view in range(228):
                pose, remainder = divmod(view, 38)
                shift, reflect = divmod(remainder, 2)
                yield bytes((control, y, dx, pose, shift, reflect, (80 + dx) % 160))
    # Every control/Y/absolute-X value for the independent electrical channel.
    for control in range(10):
        for y in (0, *range(45, 78)):
            for fx in range(160):
                yield bytes((control, y, (fx - 80) % 160, 0, 0, 0, fx))


def check(build, out, limit=None):
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError('positive finite native-case limit required')
    out = private_output(out)
    out.mkdir(parents=True, exist_ok=False)
    build = Path(build).resolve()
    metadata_raw = (build / 'build.json').read_bytes()
    meta = json.loads(metadata_raw)
    artifact = build / meta['rom']['filename']
    if meta['rom']['sha256'] != CONTROL_SHA or sha(artifact) != CONTROL_SHA:
        raise ValueError('accepted v30 contact oracle required')
    for name, digest in meta['source_files'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('bound baseline source differs: ' + name)
    sources = ('scripts/compact_floe.py', 'scripts/compact_floe_probe.py', 'src/compact_floe_kernel.asm')
    source_hashes = {name:sha(ROOT / name) if (ROOT / name).exists() else None for name in sources}
    for name in sources:
        if (ROOT / name).exists():
            copy = out / 'source' / name
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes((ROOT / name).read_bytes())
    oracle = FloeOracle(artifact.read_bytes(), meta)
    original = (ROOT / 'references/roms/frostbite.bin').read_bytes()
    assets, proof = build_assets(original, oracle)
    for name, data in assets.items():
        (out / (name + '.bin')).write_bytes(data)
    (out / 'host-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    inputs, expected = bytearray(), bytearray()
    for index, row in enumerate(cases(assets)):
        if limit is not None and index >= limit:
            break
        control, y, dx, pose, shift, reflect, fx = row
        yi = y - 44 if y else 0
        view = pose * 38 + shift * 2 + reflect
        inputs.extend(row)
        expected.append(oracle.sample(control, 80, yi, dx, view))
    (out / 'inputs.bin').write_bytes(inputs)
    (out / 'expected.bin').write_bytes(expected)
    locations = dict(directory=0x5000, footprints=0x5800, glyphs=0x6300, bases=0x6500)
    assembly = ['    ORG $4000', '    DB "AB"', '    DW start', '    DS 12,0',
                'start:', '    DI', '    LD SP,$F380', 'ready:', '    JP ready']
    assembly += [f'cf_{name} EQU ${address:04X}' for name,address in locations.items()]
    assembly += ['    DS $4100-$,$FF', '    INCLUDE "compact_floe_kernel.asm"',
                 '    ASSERT $ <= $5000']
    for name, address in locations.items():
        assembly += [f'    DS ${address:04X}-$,$FF', f'    INCBIN "{out / (name + ".bin")}"']
    assembly += ['    ASSERT $ <= $C000', '    DS $C000-$,$FF']
    (out / 'fixture.asm').write_text('\n'.join(assembly) + '\n')
    assembler = verified_tool('sjasmplus')
    rom = out / 'component-fixture.rom'
    result = subprocess.run([str(assembler), '--nologo', f'--inc={ROOT / "src"}',
        f'--raw={rom}', f'--sym={out / "fixture.sym"}', str(out / 'fixture.asm')],
        capture_output=True, text=True, timeout=60)
    (out / 'assembler.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise ValueError('component assembler failed: ' + (result.stdout + result.stderr)[-1800:])
    if rom.stat().st_size != 32768:
        raise ValueError('component fixture capacity differs')
    syms = symbols(out / 'fixture.sym')
    emulator = Path(shutil.which('openmsx')).resolve()
    profile = isolated_profile(find_machine_profile(str(emulator)))
    validate_machine_profile(profile)
    user = out / 'user-data'
    (user / 'machines').mkdir(parents=True)
    (user / 'machines/Frostbite_CompactComponent.xml').write_bytes(profile)
    settings = out / 'settings.xml'
    settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    tcl = f'''set save_settings_on_exit false
set renderer none
set throttle off
set checking 0
set count 0
set f [open {{{out / 'inputs.bin'}}} rb];set inputs [read $f];close $f
set result [open {{{out / 'actual.bin'}}} wb]
proc fail_kernel {{message}} {{puts stderr "KERNEL_FAIL $message case=$::count";exit 1}}
proc dispatch_kernel {{}} {{
 if {{$::count=={len(expected)}}} {{close $::result;exit;return}}
 set ::checking 0
 set at [expr {{$::count*7}}]
 debug write_block memory 0xC780 [string range $::inputs $at [expr {{$at+6}}]]
 reg PC 0xC6D0
 set ::started [machine_info time]
 set ::checking 1
 debug cont
}}
set boot [debug set_bp {syms['ready']} {{}} {{
 debug remove_bp $::boot
 debug break
 after break {{
  if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_kernel target}}
  reg IX 0xDDDD;reg IY 0xEEEE;reg SP 0xF380
  debug write_block memory 0xC6D0 [binary format cu* [list 205 {syms['cf_contact'] & 255} {syms['cf_contact'] >> 8} 195 214 198 24 254]]
  set ::checking 1
  debug set_watchpoint write_mem {{0x0000 0xFFFF}} {{$::checking && ($::wp_last_address<0xF300 || $::wp_last_address>=0xF380)}} {{fail_kernel "unexpected-write address=$::wp_last_address PC=[reg PC]"}}
  debug set_bp 0xC6D6 {{}} {{debug break;after break {{
   if {{[reg IX]!=0xDDDD || [reg IY]!=0xEEEE || [reg SP]!=0xF380 || ([reg IFF]&3)!=0}} {{fail_kernel abi}}
   set cycles [expr {{round(([machine_info time]-$::started)*3579545)}}]
   if {{$cycles<=0 || $cycles>=65536}} {{fail_kernel cycle-range}}
   puts -nonewline $::result [binary format cu* [list [reg A] [expr {{$cycles&255}}] [expr {{$cycles>>8}}]]]
   incr ::count;dispatch_kernel
  }}}}
  dispatch_kernel
 }}
}}]
after time {60 + len(expected) * 0.002} {{fail_kernel watchdog}}
'''
    (out / 'probe.tcl').write_text(tcl)
    run = subprocess.run([str(emulator), '-setting', str(settings), '-machine', 'Frostbite_CompactComponent',
        '-cart', str(rom), '-romtype', 'Normal', '-script', str(out / 'probe.tcl')],
        env={**os.environ, 'OPENMSX_USER_DATA':str(user), 'SDL_VIDEODRIVER':'dummy',
             'SDL_AUDIODRIVER':'dummy'}, capture_output=True, text=True, timeout=1200)
    (out / 'emulator.log').write_text(run.stdout + run.stderr)
    if run.returncode or 'KERNEL_FAIL' in run.stdout + run.stderr:
        raise ValueError('native component failed: ' + (run.stdout + run.stderr)[-1800:])
    actual = (out / 'actual.bin').read_bytes()
    if len(actual) != len(expected) * 3 or actual[::3] != expected:
        first = next((i for i,(a,b) in enumerate(zip(actual[::3], expected)) if a != b), None)
        raise ValueError(f'native component differs: actual={len(actual)} expected={len(expected)*3} first={first}')
    cycles = [int.from_bytes(actual[i+1:i+3], 'little') for i in range(0, len(actual), 3)]
    if {name:sha(ROOT / name) for name in sources} != source_hashes:
        raise ValueError('component source changed during qualification')
    if (build / 'build.json').read_bytes() != metadata_raw or sha(artifact) != CONTROL_SHA:
        raise ValueError('contact oracle changed during qualification')
    if (ROOT / 'references/roms/frostbite.bin').read_bytes() != original:
        raise ValueError('original input changed during qualification')
    if any(sha(ROOT / name) != digest for name,digest in meta['source_files'].items()):
        raise ValueError('baseline source changed during qualification')
    report = dict(complete=True, game_runtime_changed=False, component_fixture_only=True,
        no_playable_rom_release=True, oracle_rom_sha256=CONTROL_SHA, component_rom_sha256=sha(rom),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        oracle_metadata_sha256=hashlib.sha256(metadata_raw).hexdigest(),
        original_sha256=hashlib.sha256(original).hexdigest(),
        sources=source_hashes, cases=len(expected), host_proof=proof,
        complete_native_domain=len(expected) == proof['footprint_groups'] * 34 * 228 + 10 * 34 * 160,
        outputs_equal=True, ix_iy_sp_preserved=True, only_stack_writes=True, mapper_accesses=0,
        component_code_bytes=syms['cf_end']-syms['cf_contact'],
        component_data_bytes=sum(len(v) for v in assets.values()),
        cycles_including_call_and_jump=dict(min=min(cycles), mean=statistics.mean(cycles),
            p95=sorted(cycles)[min(len(cycles)-1, int(len(cycles)*0.95))], max=max(cycles)),
        emulator_sha256=sha(emulator), assembler_sha256=sha(assembler),
        machine_profile_sha256=hashlib.sha256(profile).hexdigest(),
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='Actual Z80 floe component at interiorX9..153 plus full uniform shadow channel; no edge/enemy/shore, default game integration or whole-frame cadence proof.')
    (out / 'component-result.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    result = check(args.build, args.out, args.limit)
    print({k:v for k,v in result.items() if k not in ('files','sources')})
