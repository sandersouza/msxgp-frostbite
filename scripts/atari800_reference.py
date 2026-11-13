"""Inspect owner-supplied CAR input and bounded Atari800 research captures.

No emulator or copyrighted input is downloaded by this tool. Outputs contain
metadata only; disassembly, RAM and screenshots belong in ignored outputs/.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct


def sha(data):
    return hashlib.sha256(data).hexdigest()


def cartridge(data):
    if len(data) < 16 or data[:4] != b'CART':
        raise ValueError('complete CART header required')
    kind, checksum, reserved = struct.unpack('>III', data[4:16])
    payload = data[16:]
    if kind != 1 or len(payload) != 8192 or reserved:
        raise ValueError('standard type1 8KiB input and zero reserved field required')
    if sum(payload) & 0xffffffff != checksum:
        raise ValueError('CAR payload checksum differs')
    run, marker, flags, init = struct.unpack('<HBBH', payload[-6:])
    if not 0xa000 <= run < 0xc000 or not 0xa000 <= init < 0xc000 or marker:
        raise ValueError('invalid standard cartridge vectors')
    return {'sha256': sha(data), 'bytes': len(data), 'type': kind,
            'payload_sha256': sha(payload), 'payload_checksum': checksum,
            'mapped_start': 0xa000, 'mapped_end_exclusive': 0xc000,
            'run': run, 'init': init, 'flags': flags}


def capture(ram, timing, antic, *, start=300, frames=1200, gtia=None):
    if type(start) is not int or not 0 < start < frames-1:
        raise ValueError('bounded post-startup sample required')
    if len(ram) != frames * 8192:
        raise ValueError('complete 8KiB RAM snapshot for every frame required')
    rows = [line.split() for line in timing.splitlines()]
    if len(rows) != frames or any(len(r) != 7 or int(r[0]) != i for i, r in enumerate(rows)):
        raise ValueError('complete ordered seven-column timing rows required')
    rates = {float(r[1]) for r in rows}
    if len(rates) != 1 or not 45 < next(iter(rates)) < 65:
        raise ValueError('one supported nominal emulator rate required')
    states = [ram[i*8192:(i+1)*8192] for i in range(frames)]
    if any(int(r[2]) != states[i][0x81] for i, r in enumerate(rows)):
        raise ValueError('frame counter timing/RAM mismatch')
    increments = Counter((b[0x81]-a[0x81]) & 255
                         for a, b in zip(states[start:], states[start+1:]))
    registers = {address: Counter() for address in (0xd404, 0xd405, 0xd409)}
    positions = {address: set() for address in registers}
    previous = (-1, -1, -1)
    for line in antic.splitlines():
        fields = line.split()
        if len(fields) != 6:
            raise ValueError('complete ANTIC trace rows required')
        frame, y, x = map(int, fields[:3])
        # The emulator global PC is sampled at CPU slices, not an instruction
        # address oracle; never attribute an exact store PC from this field.
        int(fields[3], 16)
        address, value = int(fields[4], 16), int(fields[5])
        if not 0 <= frame < frames or not 0 <= value <= 255 or frame < previous[0]:
            raise ValueError('out-of-range or unordered ANTIC trace')
        previous = frame, y, x
        if frame >= start and address in registers:
            registers[address][value & 15 if address != 0xd409 else value] += 1
            positions[address].add(y)
    if any(not values for values in registers.values()):
        raise ValueError('actual scroll/character-base evidence required')
    differences = {}
    for low, high in ((0x480, 0x4cc), (0x600, 0xa00), (0xa00, 0xb00), (0xb00, 0x1000)):
        counts = [sum(x != y for x, y in zip(a[low:high], b[low:high]))
                  for a, b in zip(states[start:], states[start+1:])]
        differences[f'{low:04x}-{high:04x}'] = {
            'mean_changed_bytes_between_snapshots': sum(counts)/len(counts),
            'maximum_changed_bytes_between_snapshots': max(counts)}
    result = {'output_frames': frames, 'sample_first_frame': start,
            'sample_intervals': frames-start-1, 'nominal_emulator_hz': next(iter(rates)),
            'loop_counter_increments': dict(sorted(increments.items())),
            'antic_register_writes': {f'{k:04x}': dict(sorted(v.items())) for k, v in registers.items()},
            'antic_write_scanlines': {f'{k:04x}': sorted(v) for k, v in positions.items()},
            'snapshot_differences': differences,
            'raw_sha256': {'ram': sha(ram), 'timing': sha(timing.encode()), 'antic': sha(antic.encode())},
            'scope': 'Counter cadence and hardware writes for this input sample only. Snapshot differences are not write counts. No full-game, source-mechanics, worst-density or physical-clock acceptance.'}
    if gtia is not None:
        reads, writes = Counter(), Counter()
        scanlines = set()
        previous_frame = -1
        for line in gtia.splitlines():
            fields = line.split()
            if len(fields) != 6:
                raise ValueError('complete GTIA trace required')
            frame, y, x = map(int, fields[:3])
            action, address, value = fields[3], int(fields[4], 16), int(fields[5])
            if (not 0 <= frame < frames or frame < previous_frame or action not in ('R', 'W')
                    or not 0 <= value <= 255):
                raise ValueError('invalid GTIA trace')
            previous_frame = frame
            if frame >= start:
                (reads if action == 'R' else writes)[f'{address:04x}'] += 1
                if action == 'R':
                    scanlines.add(y)
        if not reads or not writes:
            raise ValueError('GTIA reads and writes required')
        result['gtia'] = {'read_counts': dict(sorted(reads.items())),
                          'write_counts': dict(sorted(writes.items())),
                          'read_scanlines': sorted(scanlines),
                          'scope': 'Read events only; returned collision values are not recorded.'}
        result['raw_sha256']['gtia'] = sha(gtia.encode())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--car', type=Path, required=True)
    parser.add_argument('--capture', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = {'cartridge': cartridge(args.car.read_bytes())}
    if args.capture:
        p = args.capture
        result['capture'] = capture((p/'ram-frames.bin').read_bytes(),
                                    (p/'frames.tsv').read_text(), (p/'antic.tsv').read_text(),
                                    gtia=(p/'gtia.tsv').read_text() if (p/'gtia.tsv').exists() else None)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'cartridge_sha256': result['cartridge']['sha256'],
                      'capture_intervals': result.get('capture', {}).get('sample_intervals')}))


if __name__ == '__main__':
    main()
