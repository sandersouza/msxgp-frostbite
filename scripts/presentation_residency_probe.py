"""Compare floe residency policies on sealed M-C state sequences, offline only."""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from environment import ROOT
from graphics_mapping import palette_map
from presentation_floe_templates import whole_masks
from presentation_palette import audit_palette
from presentation_residency import Residency
from stella_floe import control_pairs


def signed(value):
    return (value >> 4) - 16 if value & 128 else value >> 4


def capture_records(raw):
    if not raw or len(raw) % 49304:
        raise ValueError('empty or truncated capture stream')
    for offset in range(0, len(raw), 49304):
        page = raw[offset + 49298] - 6
        if page not in (0, 1):
            raise ValueError(f'invalid display page at capture {offset // 49304}')
        yield raw[offset:offset + 128], page


def probe(out):
    rom = (ROOT/'references/roms/frostbite.bin').read_bytes()
    if hashlib.sha256(rom).hexdigest() != 'cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834':
        raise ValueError('original ROM authority changed')
    colors = palette_map(audit_palette(ROOT/'outputs/presentation/palette-canonical-a'))
    @lru_cache(None)
    def masks(root, delta, phase):
        return whole_masks(rom, root, delta, phase)
    deltas = sorted({4+signed(a)-signed(b) for a,b in control_pairs(rom)})
    atlas = []
    for delta in deltas:
        for coarse in (0, 1):
            by_bank = {1: set(), 2: set()}
            by_row = []
            for row in range(4):
                y = 167 - 26*row + coarse
                unique = set()
                for phase in range(16):
                    for (dy, col), mask in masks(phase, delta, y % 8).items():
                        by_bank[(y//8+dy)//8].add(mask)
                        unique.add(mask)
                by_row.append(len(unique))
            atlas.append(dict(delta=delta, coarse=coarse,
                              distinct_masks={b:len(v) for b,v in by_bank.items()},
                              row_private_masks=by_row))
    reports = []
    for family in ('ntsc', 'pal'):
        path = ROOT/f'outputs/presentation/playfield-m-c/{family}-a/captures.bin'
        raw = path.read_bytes()
        states = list(capture_records(raw))
        requests = []
        fixed = {}; fixed_misses = 0; peak = {1:0, 2:0}
        previous = {1:set(), 2:set()}
        for ram, page in states:
            by_bank = {1:[], 2:[]}
            # Exact captured final NAME generation; no guessed parity.
            if not ram[0x3f] & 128:
                delta = 4 + signed(ram[0x1c]) - signed(ram[0x1d])
                coarse = int(ram[0x68] >= 150)
                for row in range(4):
                    color = colors[ram[0x2b+row]]
                    if color == 4:
                        continue
                    root = (ram[0x1f+row] - signed(ram[0x1c])) % 160
                    y = 167 - 26*row + coarse
                    cells = masks(root % 16, delta, y % 8)
                    ordered = list(dict.fromkeys((cells[c], color) for c in sorted(cells)))
                    old = fixed.setdefault((page,row), [None]*14)
                    for n,key in enumerate(ordered):
                        if old[n] != key:
                            fixed_misses += 1
                            old[n] = key
                    for (dy,col),mask in cells.items():
                        # Full strip publication includes the clipped column;
                        # retain it in both models to avoid a visibility shortcut.
                        by_bank[(y//8+dy)//8].append((mask,color))
            by_bank = {b:list(dict.fromkeys(v)) for b,v in by_bank.items()}
            for bank in (1,2):
                peak[bank] = max(peak[bank],len(previous[bank] | set(by_bank[bank])))
                previous[bank] = set(by_bank[bank])
            requests.append(by_bank)
        for capacity in (56, 64, 80, 112, 144, 176, 200):
            caches = {b:Residency(capacity) for b in (1,2)}
            active = {b:set() for b in (1,2)}
            misses = 0
            for req in requests:
                for bank in (1,2):
                    names,count = caches[bank].prepare(req[bank],active[bank])
                    assert len(set(names.values())) == len(names)
                    active[bank] = set(req[bank])
                    misses += count
            reports.append(dict(family=family, frames=len(states),
                                slots_per_bank=capacity, fixed_semantic_misses=fixed_misses,
                                persistent_semantic_misses=misses,
                                reduction=1-misses/fixed_misses, peak_pinned=peak,
                                captures_sha256=hashlib.sha256(raw).hexdigest()))
    result = dict(scope='HOST MODEL ONLY: semantic floe residency misses, not measured CPU cycles, transfer bytes or FPS. Excludes enemy/fusion/static slot allocation and runtime lookup/eviction cost. Original pixels, vertical phases and both simultaneous colors retained. Full atlas counts are capacity pressure, not a complete VRAM packing proof.',
                  finite_width_atlas=atlas, route_models=reports)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(reports,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    probe(parser.parse_args().out)
