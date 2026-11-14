"""Reconstruct every accepted native bear record from nine-bit mask IDs."""
import argparse
import json
from pathlib import Path

from compact_bear_records import pack, unpack
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run, sha
from environment import ROOT
from reference_traces import private_output


def check(build, out):
    out = private_output(out)
    if out.exists():
        raise ValueError('fresh output required')
    m = json.loads((build/'build.json').read_bytes())
    rom_path = build/m['rom']['filename']
    if sha(rom_path) != m['rom']['sha256'] or not m.get('compact_bear_records'):
        raise ValueError('qualified compact native record input required')
    rom = rom_path.read_bytes()
    expected = b''.join(rom[b*16384+0x3800:(b+1)*16384] for b in range(67, 70))
    data = pack(expected)
    if unpack(data) != expected:
        raise ValueError('complete original64-byte record differs')
    out.mkdir(parents=True)
    for name, blob in data.items():
        (out/(name+'.bin')).write_bytes(blob)
    asm = [' ORG $4000', ' DB "AB"', ' DW start', ' DS 12,0',
           'start:', ' DI', ' LD SP,$F380', ' LD A,255', ' LD ($DFBE),A',
           'ready:', ' JP ready', ' DS $4100-$,$FF', 'br_entry:',
           ' LD A,($C7B4)', ' CALL br_record', ' LD A,($C7B4)', ' JP br_record',
           ' INCLUDE "compact_bear_records.asm"', ' ASSERT $ <= $5000',
           ' DS $5000-$,$FF', 'br_records:', f' INCBIN "{out/"records.bin"}"',
           'br_raw:', f' INCBIN "{out/"raw.bin"}"', ' DS $C000-$,$FF']
    result = run(out, '\n'.join(asm)+'\n', bytes(range(96)), expected,
        input_address=0xC7B4, input_stride=1, output_address=0xDFC0, output_stride=64,
        entry_name='br_entry', end_name='br_end', writes=((0xDFBE, 0xDFBE), (0xDFC0, 0xDFFF)))
    names = ('scripts/compact_bear_records.py', 'scripts/compact_bear_record_probe.py', 'src/compact_bear_records.asm')
    for name in names:
        p = out/'source'/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT/name).read_bytes())
    result.update(input_rom_sha256=m['rom']['sha256'], oracle_ancestry_rom_sha256=CONTROL_SHA,
        record_bytes=3168, raw_ID_map_bytes=940, original_record_bytes=6144,
        every_case_exercises_miss_then_hit=True,
        sources={n: sha(ROOT/n) for n in names},
        files={p.name: sha(p) for p in out.iterdir() if p.is_file()},
        scope='All96 complete original records, unused bytes, dense/empty predicates, native miss+hit, bounded cache writes and ABI. Whole-game cadence remains required.')
    (out/'component-result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    check(args.build.resolve(), args.out)
