"""Prove512 native bear grids against original Atari glyph pixels."""
import argparse
import json
from pathlib import Path

from compact_native_fixture import run, sha
from environment import ROOT
from original_graphics import view
from presentation_fragments import mask_tiles
from reference_traces import private_output


def check(build, out, renderer='packet'):
    out = private_output(out)
    if out.exists():
        raise ValueError('fresh output required')
    m = json.loads((build/'build.json').read_bytes())
    artifact = build/m['rom']['filename']
    if sha(artifact) != m['rom']['sha256'] or not m.get('compact_enemy_resident'):
        raise ValueError('bound resident-enemy input required')
    rom = artifact.read_bytes()
    original_path = ROOT/'references/roms/frostbite.bin'
    original = original_path.read_bytes()
    if sha(original_path) != m['profile']['source_sha256']:
        raise ValueError('original gameplay/graphics authority changed')
    info = rom[132*16384+0x3C00:132*16384+0x3C20]
    pool = rom[132*16384+0x3C20:132*16384+0x3E60]
    if len(info) != 32 or len(pool) != 576:
        raise ValueError('all16 aliases and six complete sprite pictures required')
    decoded = []
    for frame in range(6):
        aliases = [g for g in range(16) if info[g*2] == frame]
        dys = {info[g*2+1] for g in aliases}
        if not aliases or len(dys) != 1:
            raise ValueError('one thin placement per complete shared picture required')
        dy = next(iter(dys))
        dy = dy if dy < 128 else dy-256
        picture = pool[frame*96:(frame+1)*96]
        rows = []
        for y in range(20):
            at = y+8 if y < 8 else y+24
            rows.append(bytes((picture[at], picture[at+16], picture[64+y-dy])))
        decoded.append(rows)
    row_values = sorted(set(row for frame in decoded for row in frame))
    if len(row_values) != 22:
        raise ValueError('complete22-row literal grammar required')
    rows = bytes(row_values.index(row) for frame in decoded for row in frame)
    shifted = b''.join((int.from_bytes(row+bytes(1), 'big') >> shift).to_bytes(4, 'big')
                       for shift in range(8) for row in row_values)
    inputs, expected = bytearray(), bytearray()
    unique_masks = set()
    for group in range(16):
        image = view(original, 0xFD00+original[0xEE7+group//2], 19, bool(group&1), 2)
        bitmap = image['pixels']+image['pixels'][-16:]
        for phase in range(16):
            for coarse in range(2):
                grid = mask_tiles(bitmap, 16, 20, phase, 3+coarse)
                if grid['columns'] not in (3, 4) or grid['rows'] != 3:
                    raise ValueError('bounded four-column grid required')
                row = bytearray()
                for y in range(3):
                    for x in range(4):
                        mask = grid['patterns'][y*grid['columns']+x] if x < grid['columns'] else bytes(8)
                        row.extend(mask)
                        unique_masks.add(mask)
                inputs.extend((group, phase, coarse))
                expected.extend(row)
    out.mkdir(parents=True)
    (out/'info.bin').write_bytes(info)
    (out/'pool.bin').write_bytes(pool)
    (out/'rows.bin').write_bytes(rows)
    (out/'shifted.bin').write_bytes(shifted)
    source = {'packet':'native_bear_grid.asm','rows':'native_bear_grid_rows.asm',
              'sparse':'native_bear_grid_sparse.asm'}[renderer]
    asm = [' ORG $4000', ' DB "AB"', ' DW start', ' DS 12,0',
           'start:', ' DI', ' LD SP,$F380', 'ready:', ' JP ready',
           ' DS $4100-$,$FF', 'ng_entry:', ' LD A,($C7B5)', ' LD B,A',
           ' LD A,($C7B6)', ' LD C,A', ' LD A,($C7B4)',
           f' INCLUDE "{source}"', ' ASSERT $ <= $5000',
           ' DS $5000-$,$FF', 'ng_info:', f' INCBIN "{out/"info.bin"}"']
    if renderer == 'packet':
        asm += ['ng_pool:', f' INCBIN "{out/"pool.bin"}"']
    else:
        asm += ['ng_rows:', f' INCBIN "{out/"rows.bin"}"', 'ng_shifted:', f' INCBIN "{out/"shifted.bin"}"']
    asm += [' DS $C000-$,$FF']
    result = run(out, '\n'.join(asm)+'\n', bytes(inputs), bytes(expected),
        input_address=0xC7B4, input_stride=3, output_address=0xC480, output_stride=96,
        entry_name='ng_entry', end_name='ng_end', writes=((0xC480, 0xC4DF), (0xC500, 0xC50F)))
    names = ('scripts/native_bear_grid_sparse_probe.py', 'src/'+source,
             'scripts/original_graphics.py', 'scripts/presentation_fragments.py')
    for name in names:
        p = out/'source'/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT/name).read_bytes())
    result.update(input_rom_sha256=m['rom']['sha256'], original_rom_sha256=sha(original_path),
        groups=16, source_phases=16, coarse_offsets=2, literal_sprite_bytes=576,
        alias_bytes=32, expanded_native_mask_tables_required=False,
        renderer=renderer, unique_row_bytes=22, row_selector_bytes=120, shifted_row_bytes=704,
        unique_generated_masks=len(unique_masks),
        sources={n: sha(ROOT/n) for n in names},
        files={p.name: sha(p) for p in out.iterdir() if p.is_file()},
        scope='All512 original-glyph mask grids including empty cells, duplicated last row and fixed four-column packing; native ABI/write guards. No integrated game/cadence claim.')
    (out/'component-result.json').write_text(json.dumps(result, indent=2)+'\n')
    print({k: v for k, v in result.items() if k not in ('sources', 'files')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--renderer', choices=('packet', 'rows', 'sparse'), default='packet')
    args = parser.parse_args()
    check(args.build.resolve(), args.out, args.renderer)
