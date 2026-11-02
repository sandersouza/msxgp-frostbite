"""Actual source-fixture presentation RPC; natural/full-frame gates are separate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from environment import ROOT
from graphics_mapping import decode_screen, map_frame
from presentation_build import FILES, validate_rom
from presentation_fragments import background_tables, background_vram
from presentation_model import describe, pixels
from presentation_palette import audit_palette
from presentation_reference import HELPERS as SOURCE_FILES
from reference_provenance import audit_manifest
from reference_traces import private_output
from render_build import symbols
from smoke import find_machine_profile, isolated_profile, validate_machine_profile


def sha(data): return hashlib.sha256(data).hexdigest()


def decode_target(vram, registers):
    if len(vram) != 16384 or len(registers) != 8: raise ValueError('complete16KiB VRAM and eight actual VDP registers required')
    if (registers[0] != 2 or registers[1] != 0xC2 or registers[2] not in (6, 7) or registers[3:7] != bytes((255, 3, 0x36, 7))):
        raise ValueError('unsupported actual VDP mode/table/sprite registers')
    occupancy = [0] * 192
    for offset in range(0x1B00, 0x1B80, 4):
        sy = vram[offset]
        if sy == 208: break
        if sy > 190 and sy != 255: raise ValueError('sprite Y outside declared visible domain')
        top = (sy + 1) & 255
        for line in range(top, min(192, top + 16)): occupancy[line] += 1
    if max(occupancy) > 4: raise ValueError('actual SAT exceeds4 full rectangles per scanline')
    projected = bytearray(vram); names = registers[2] * 1024
    projected[0x1800:0x1B00] = vram[names:names + 768]
    return bytes(color or (registers[7] & 15) for color in decode_screen(projected))


def check_frame(build_dir, out, *, fixture=0, family='ntsc', explore=False, background_only=False, world_only=False, hud_only=False, player_budget=0, repeats=1):
    if sum((background_only, world_only, hud_only)) > 1: raise ValueError('choose one component')
    if family not in ('ntsc', 'pal') or type(fixture) is not int or not 0 <= fixture < 1690: raise ValueError('declared source fixture and TV family required')
    if type(repeats)is not int or not 1<=repeats<=8:raise ValueError('one to eight controlled repeat RPCs required')
    build_dir = Path(build_dir).resolve(); metadata = json.loads((build_dir / 'build.json').read_text())
    artifact = build_dir / metadata['rom']['filename']; rom = artifact.read_bytes()
    if validate_rom(rom) or sha(rom) != metadata['rom']['sha256']: raise ValueError('presentation ROM identity mismatch')
    if not explore: audit_manifest({'tool_source_commit': metadata['source_commit'], 'utility_fingerprints': metadata['source_files']}, FILES)
    if any(sha((ROOT / name).read_bytes()) != value for name, value in metadata['source_files'].items()): raise ValueError('build source changed since artifact compilation')
    if metadata['source_dirty'] and not explore: raise ValueError('canonical target checks require committed build producers')
    config = json.loads((ROOT / 'references/presentation-source-config.json').read_text()); source = ROOT / config['fixtures'][0]
    summary = json.loads((ROOT / 'references/presentation-source-result.json').read_text()); raw_report = (source / 'report.json').read_bytes()
    if sha(raw_report) != summary['groups']['fixtures']['report_sha256']: raise ValueError('source fixture report changed')
    report = json.loads(raw_report); audit_manifest(report['producer'], SOURCE_FILES)
    fixtures_raw = (source / 'fixtures.json').read_bytes()
    if sha(fixtures_raw) != report['fixture_sha256']: raise ValueError('original fixture input changed')
    sample = json.loads(fixtures_raw)[fixture]; point = report['points'][fixture]
    original = (source / f'{fixture:04d}-{sample["name"]}.tia').read_bytes()
    if sha(original) != point['raster_sha256'] or sha(bytes(sample['ram'])) != point['before_ram_sha256']: raise ValueError('source fixture pixels/RAM changed')
    palette_config = json.loads((ROOT / 'references/presentation-assets-config.json').read_text()); palette = audit_palette(ROOT / palette_config['palette'])
    expected = map_frame(original, palette)
    if background_only:
        tables = background_tables((ROOT / 'references/roms/frostbite.bin').read_bytes(), palette)
        expected = decode_target(background_vram(tables, sample['ram']), bytes((2, 0xC2, 6, 255, 3, 0x36, 7, 1)))
    if world_only or hud_only:
        original_rom = (ROOT / 'references/roms/frostbite.bin').read_bytes()
        model = describe(original_rom, sample)
        if world_only:
            model['hud']['score'] = []; model['hud']['status'] = []; model['igloo'] = []
        model['door'] = []
        for row in model['player']['rows']:
            row['pattern'] = row['prefix_pattern'] = 0
        for key in ('prefix', 'logo', 'playfield', 'ball'): model['footer'][key] = []
        expected = map_frame(pixels(original_rom, model), palette)
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    (out / 'source-ram.bin').write_bytes(bytes(sample['ram'])); (out / 'expected.tms').write_bytes(expected)
    syms = symbols(build_dir / 'presentation.sym'); emulator = Path(shutil.which('openmsx')).resolve()
    profile = ET.fromstring(isolated_profile(find_machine_profile(str(emulator))))
    profile.find('.//VDP/version').text = 'TMS9918A' if family == 'ntsc' else 'TMS9929A'
    profile_raw = b'<?xml version="1.0"?><!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">' + ET.tostring(profile); validate_machine_profile(profile_raw)
    user = out / 'user-data'; (user / 'machines').mkdir(parents=True); (user / 'machines/Frostbite_Presentation.xml').write_bytes(profile_raw)
    settings = out / 'settings.xml'; settings.write_text('<?xml version="1.0"?><!DOCTYPE settings SYSTEM "settings.dtd"><settings><settings><setting id="save_settings_on_exit">false</setting></settings></settings>')
    calls = [syms[name] for name in ('presentation_prepare', 'wait_vblank', 'presentation_commit')]
    # Controlled pixel RPC may intentionally exceed a frame. Drain its stale
    # status before waiting for the next real edge; record preparation cost
    # explicitly, never promote this component RPC into a frame-deadline pass.
    rpc = [205, calls[0] & 255, calls[0] >> 8, 219, 153]
    rpc += [byte for entry in calls[1:] for byte in (205, entry & 255, entry >> 8)] + [195, 142, 193, 24, 254]
    script = f'''set save_settings_on_exit false
set renderer none
set throttle off
set repetition 0
set history ""
proc fail_presentation {{message}} {{puts stderr "PRESENTATION_FAIL $message";exit 1;return -code error $message}}
proc dump_presentation {{name data}} {{set f [open [file join {{{out}}} $name] wb];puts -nonewline $f $data;close $f}}
set boot [debug set_bp {syms['paced_frame_start']} {{}} {{
    debug remove_bp $::boot;debug break
    after break {{
        if {{[machine_info z80_freq]!=3579545 || [debug size {{Main RAM}}]!=65536}} {{fail_presentation target}}
        set f [open {{{out/'source-ram.bin'}}} rb];set ::ram [read $f];close $f
        debug write_block memory 0xC000 $::ram
        set ::abi [debug read_block memory 0xC600 256]
        debug write_block memory 0xE800 [string repeat [binary format c 165] 0xB40]
        set ::slot [debug read ioports 168]
        dump_presentation before.vram [debug read_block VRAM 0 16384]
        dump_presentation before.regs [debug read_block {{VDP regs}} 0 8]
        dump_presentation before-0.vram [debug read_block VRAM 0 16384]
        dump_presentation before-0.regs [debug read_block {{VDP regs}} 0 8]
        set VDP.too_fast_vram_access_callback {{fail_presentation fast-vram}}
        set ::player_cycles 0
        debug set_bp {syms['p_player_prepare']} {{}} {{set ::player_started [machine_info time]}}
        debug set_bp {syms['p_player_prepare.candidate']} {{}} {{if {{![info exists ::player_candidate]}} {{set ::player_candidate [machine_info time]}}}}
        debug set_bp {syms['p_player_emit_all']} {{}} {{set ::player_emit [machine_info time]}}
        debug set_bp {syms['presentation_sprites_prepare.black']} {{}} {{
            if {{[info exists ::player_started]}} {{
                set ::player_cycles [expr {{round(([machine_info time]-$::player_started)*3579545)}}]
                if {{[info exists ::player_candidate] && [info exists ::player_emit]}} {{dump_presentation player-phases.txt "[expr {{round(($::player_candidate-$::player_started)*3579545)}}] [expr {{round(($::player_emit-$::player_candidate)*3579545)}}] [expr {{round(([machine_info time]-$::player_emit)*3579545)}}]"}}
                unset ::player_started
            }}
        }}
        debug set_bp 0xC183 {{}} {{debug break;after break {{
            set ::prepare_cycles [expr {{round(([machine_info time]-$::prepare_started)*3579545)}}]
            if {{[debug read memory 0xC231]!=0}} {{fail_presentation "world-compositor miss=[debug read memory 0xCCA6] group=[debug read memory 0xCCA7] family=[debug read memory 0xC227] col=[debug read memory 0xC229] top=[debug read memory 0xC22A]"}}
            if {{[debug read_block memory 0xC000 128] ne $::ram || [debug read_block memory 0xC600 256] ne $::abi}} {{fail_presentation prepare-source-state}}
            dump_presentation prepared.vram [debug read_block VRAM 0 16384]
            dump_presentation prepared.regs [debug read_block {{VDP regs}} 0 8]
            dump_presentation prepared-$::repetition.vram [debug read_block VRAM 0 16384]
            dump_presentation prepared-$::repetition.regs [debug read_block {{VDP regs}} 0 8]
            debug cont
        }}}}
        debug set_bp 0xC188 {{}} {{
            set ::commit_y [machine_info VDP_msx_y_pos]
            if {{$::commit_y>=0 && $::commit_y<192}} {{fail_presentation "commit-visible y=$::commit_y prepare_cycles=$::prepare_cycles"}}
        }}
        debug set_bp 0xC18E {{}} {{debug break;after break {{
            if {{[debug read_block memory 0xC000 128] ne $::ram || [debug read_block memory 0xC600 256] ne $::abi}} {{fail_presentation commit-source-state}}
            if {{[debug read_block memory 0xE800 0xB40] ne [string repeat [binary format c 165] 0xB40]}} {{fail_presentation heap-stack-redzone}}
            if {{[reg SP]!=0xF380 || ([reg IFF]&3)!=0 || [debug read ioports 168]!=$::slot}} {{fail_presentation abi}}
            set end_y [machine_info VDP_msx_y_pos]
            if {{$end_y>=0 && $end_y<192}} {{fail_presentation commit-end-visible}}
            dump_presentation presented.vram [debug read_block VRAM 0 16384]
            dump_presentation presented.regs [debug read_block {{VDP regs}} 0 8]
            dump_presentation presented-$::repetition.vram [debug read_block VRAM 0 16384]
            dump_presentation presented-$::repetition.regs [debug read_block {{VDP regs}} 0 8]
            dump_presentation marker.txt "$::commit_y $end_y $::prepare_cycles $::player_cycles"
            append ::history "$::repetition $::prepare_cycles $::player_cycles\n"
            dump_presentation repeats.tsv $::history
            incr ::repetition
            if {{$::repetition<{repeats}}} {{
                unset -nocomplain ::player_candidate ::player_emit
                dump_presentation before.vram [debug read_block VRAM 0 16384]
                dump_presentation before.regs [debug read_block {{VDP regs}} 0 8]
                dump_presentation before-$::repetition.vram [debug read_block VRAM 0 16384]
                dump_presentation before-$::repetition.regs [debug read_block {{VDP regs}} 0 8]
                reg PC 0xC180;set ::prepare_started [machine_info time];debug cont;return
            }}
            exit
        }}}}
        debug write_block memory 0xC180 [binary format cu* {{{' '.join(str(v) for v in rpc)}}}]
        reg SP 0xF380;reg PC 0xC180;set ::prepare_started [machine_info time];debug cont
    }}
}}]
after time 8 {{fail_presentation watchdog}}
'''
    (out / 'launch.tcl').write_text(script)
    executed = subprocess.run([str(emulator), '-setting', str(settings), '-machine', 'Frostbite_Presentation', '-cart', str(artifact), '-romtype', 'ASCII16', '-script', str(out / 'launch.tcl')],
        cwd=ROOT, env={**os.environ, 'OPENMSX_USER_DATA': str(user), 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}, capture_output=True, text=True, timeout=90)
    log = executed.stdout + executed.stderr; (out / 'emulator.log').write_text(log)
    if executed.returncode or 'PRESENTATION_FAIL' in log or not (out / 'marker.txt').is_file(): raise ValueError('actual presentation capture failed: ' + log[-1500:])
    images = {name: decode_target((out / f'{name}.vram').read_bytes(), (out / f'{name}.regs').read_bytes()) for name in ('before', 'prepared', 'presented')}
    if images['before'] != images['prepared'] or (out / 'before.regs').read_bytes() != (out / 'prepared.regs').read_bytes(): raise ValueError('preparation changed the visible page/registers')
    actual = images['presented']; (out / 'actual.tms').write_bytes(actual)
    different = sum(a != b for a, b in zip(actual, expected))
    history=[list(map(int,line.split())) for line in (out/'repeats.tsv').read_text().splitlines()]
    if len(history)!=repeats or any(len(row)!=3 or row[0]!=i or row[1]<=0 or row[2]<0 for i,row in enumerate(history)):raise ValueError('incomplete ordered controlled repeats')
    for i in range(repeats):
        image=lambda phase:decode_target((out/f'{phase}-{i}.vram').read_bytes(),(out/f'{phase}-{i}.regs').read_bytes())
        if image('before')!=image('prepared') or (out/f'before-{i}.regs').read_bytes()!=(out/f'prepared-{i}.regs').read_bytes():raise ValueError('repeat preparation changed visible state')
        if image('presented')!=expected:raise ValueError(f'repeat{i} source pixels differ')
    result = {'fixture': sample['name'], 'family': family, 'rom_sha256': sha(rom), 'different_pixels': different,
              'prepare_cycles_including_rpc': int((out / 'marker.txt').read_text().split()[2]), 'frame_deadline_accepted': False,
              'player_cycles': int((out / 'marker.txt').read_text().split()[3]), 'declared_player_microbudget': player_budget or None,
              'controlled_repeats':repeats,'repeat_cycle_history':history,
              'player_microbudget_scope':'Last controlled RPC only; cold-start and whole-frame budgets remain separate',
              'complete': different == 0, 'canonical_ram_injected': True, 'prepare_invariance': True,
              'component': 'background' if background_only else 'world' if world_only else 'world-hud' if hud_only else 'full-scene',
              'full_source_pixels_accepted': not (background_only or world_only or hud_only) and different == 0,
              'scope': 'Controlled graphics RPC; background-only compares the component constructor and cannot qualify full-source pixels; natural gameplay, all views and full-frame performance remain separate'}
    (out / 'check.json').write_text(json.dumps(result, indent=2) + '\n')
    if different: raise ValueError(f'actual native presentation differs at{different} mapped pixels')
    if player_budget and result['player_cycles'] > player_budget: raise ValueError(f'player component costs{result["player_cycles"]} cycles, exceeds declared microbudget{player_budget}; no frame acceptance implied')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--build-dir', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--fixture', type=int, default=0); parser.add_argument('--family', choices=('ntsc', 'pal'), default='ntsc'); parser.add_argument('--explore', action='store_true')
    parser.add_argument('--background-only', action='store_true')
    parser.add_argument('--world-only', action='store_true')
    parser.add_argument('--hud-only', action='store_true')
    parser.add_argument('--player-budget', type=int, default=0)
    parser.add_argument('--repeats',type=int,default=1)
    args = parser.parse_args(); print(json.dumps(check_frame(**vars(args))))
