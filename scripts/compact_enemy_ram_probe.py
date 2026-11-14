"""Prove the exact enemy window constructor and assets in native RAM."""
import argparse
import json
from pathlib import Path

from compact_enemy_windows_probe import assets
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run, sha
from environment import ROOT
from reference_traces import private_output


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
        (target/'data.bin').write_bytes(data['offsets']+data['pool'])
        asm = [' ORG $4000', ' DB "AB"', ' DW start', ' DS 12,0',
               'start:', ' DI', ' LD SP,$F380',
               ' LD HL,$5000', ' LD DE,$E300', ' LD BC,sw_end-sw_planes', ' LDIR',
               ' LD HL,$5100', ' LD DE,$DB00', ' LD BC,1214', ' LDIR',
               'ready:', ' JP ready', ' DS $4100-$,$FF',
               'sw_entry:', ' LD A,($C7B4)']
        if mode == 'read':
            asm += [' JP sw_read']
        else:
            asm += [' LD DE,$7800', ' CALL sw_upload', ' XOR A', ' OUT ($99),A',
                    ' LD A,$38', ' OUT ($99),A', ' LD HL,$C500', ' LD B,32',
                    '.read:', ' IN A,($98)', ' LD (HL),A', ' INC HL', ' DJNZ .read', ' RET']
        asm += ['sw_fixture_end:', 'vdp_stream:', '.byte:', ' OUTI', ' JP NZ,.byte', ' RET',
                'sw_directory EQU $DB00', 'sw_pool EQU $DD10',
                ' DS $5000-$,$FF', ' DISP $E300', ' INCLUDE "compact_enemy_windows.asm"',
                ' ENT', ' DS $5100-$,$FF', f' INCBIN "{target/"data.bin"}"', ' DS $C000-$,$FF']
        results[mode] = run(target, '\n'.join(asm)+'\n', bytes(range(132)), expected,
            input_address=0xC7B4, input_stride=1, output_address=0xC500, output_stride=32,
            entry_name='sw_entry', end_name='sw_fixture_end', writes=((0xC500, 0xC51F),))
    names = ('scripts/compact_enemy_ram_probe.py', 'src/compact_enemy_windows.asm',
             'scripts/compact_enemy_windows_probe.py')
    result = dict(complete=True, oracle_rom_sha256=CONTROL_SHA, cases=132,
        paths=results, RAM_code_address=0xE300, RAM_data_address=0xDB00,
        RAM_data_bytes=1214, sources={n: sha(ROOT/n) for n in names},
        scope='Actual native RAM code and immutable RAM assets, every pattern and real VDP upload/readback; component only.')
    for n in names:
        p = out/'source'/n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT/n).read_bytes())
    (out/'component-result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    check(args.build, args.out)
