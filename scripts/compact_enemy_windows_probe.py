"""Prove every enemy SGT through literal-plane RAM and real VDP paths."""
import argparse
import json
from pathlib import Path

from compact_byte_windows import pack_windows, restore_windows
from compact_enemy_sgt_probe import assets as source_assets
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run, sha
from environment import ROOT
from reference_traces import private_output


def assets(build):
    _, atlas = source_assets(build)
    planes = []
    for offset in range(0, len(atlas), 32):
        tile = atlas[offset:offset+32]
        if tile[8:16] != bytes(8) or tile[24:] != bytes(8):
            raise ValueError('original eight-row SGT padding required')
        planes.extend((tile[:8], tile[16:24]))
    packed = pack_windows(planes)
    if restore_windows(packed) != planes:
        raise ValueError('literal planes differ')
    if (len(packed['offsets']), len(packed['pool'])) != (528, 686):
        raise ValueError('complete132-pattern dictionary required')
    return packed, atlas


def check(build, out):
    out = private_output(out)
    if out.exists():
        raise ValueError('fresh output required')
    data, expected = assets(build.resolve())
    out.mkdir(parents=True)
    results = {}
    for mode in ('read', 'upload'):
        target = out/mode
        target.mkdir()
        for name in ('offsets', 'pool'):
            (target/(name+'.bin')).write_bytes(data[name])
        asm = [' ORG $4000', ' DB "AB"', ' DW start', ' DS 12,0',
               'start:', ' DI', ' LD SP,$F380', 'ready:', ' JP ready',
               ' DS $4100-$,$FF', 'sw_entry:', ' LD A,($C7B4)']
        if mode == 'read':
            asm += [' JP sw_read']
        else:
            asm += [' LD DE,$7800', ' CALL sw_upload',
                    ' LD A,0', ' OUT ($99),A', ' LD A,$38', ' OUT ($99),A',
                    ' LD HL,$C500', ' LD B,32', '.read:', ' IN A,($98)',
                    ' LD (HL),A', ' INC HL', ' DJNZ .read', ' RET']
        asm += ['vdp_stream:', '.byte:', ' OUTI', ' JP NZ,.byte', ' RET',
                ' INCLUDE "compact_enemy_windows.asm"', ' ASSERT $ <= $5000',
                ' DS $5000-$,$FF', 'sw_directory:',
                f' INCBIN "{target/"offsets.bin"}"', 'sw_pool:',
                f' INCBIN "{target/"pool.bin"}"', ' DS $C000-$,$FF']
        results[mode] = run(target, '\n'.join(asm)+'\n', bytes(range(132)), expected,
            input_address=0xC7B4, input_stride=1, output_address=0xC500,
            output_stride=32, entry_name='sw_entry', end_name='sw_end',
            writes=((0xC500, 0xC51F),))
    names = ('scripts/compact_enemy_windows_probe.py', 'src/compact_enemy_windows.asm',
             'scripts/compact_byte_windows.py', 'scripts/compact_enemy_sgt_probe.py')
    result = dict(complete=True, oracle_rom_sha256=CONTROL_SHA, cases=132,
        paths=results, original_atlas_bytes=4224, directory_bytes=528,
        plane_pool_bytes=686, padding_bytes=8,
        sources={n: sha(ROOT/n) for n in names},
        scope='Every original SGT, RAM clipping input and paced real VDP upload; component evidence only.')
    for name in names:
        copy = out/'source'/name
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes((ROOT/name).read_bytes())
    (out/'component-result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    check(args.build, args.out)
