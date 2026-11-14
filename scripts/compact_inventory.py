"""Read-only storage inventory; stored/observed bytes are not liveness proof."""
import argparse
import csv
import hashlib
import json
import lzma
from pathlib import Path
import zlib

from environment import ROOT
from reference_traces import private_output

BANK_SIZE = 16384


def sha(data):
    return hashlib.sha256(data).hexdigest()


def image_inventory(data: bytes, bank_size: int = BANK_SIZE) -> dict:
    if not data or type(bank_size) is not int or bank_size <= 0 or len(data) % bank_size:
        raise ValueError('nonempty image containing complete banks required')
    banks = [data[at:at + bank_size] for at in range(0, len(data), bank_size)]
    return dict(size_bytes=len(data), bank_size=bank_size, bank_count=len(banks),
                non_ff_bytes=len(data) - data.count(255),
                trailing_ff_bytes=len(data) - len(data.rstrip(b'\xff')),
                all_ff_banks=sum(bank == b'\xff' * bank_size for bank in banks),
                unique_banks=len(set(banks)),
                host_zlib9_bytes=len(zlib.compress(data, 9)),
                host_lzma6_bytes=len(lzma.compress(data, preset=6)))


def physical_offset(bank: int, address: int, image_size: int) -> int:
    """Map a *known* selected 16 KiB bank/window, not inferred mapper state."""
    if (type(bank) is not int or type(address) is not int or
            image_size <= 0 or image_size % BANK_SIZE or
            not 0 <= bank < image_size // BANK_SIZE or
            not 0x4000 <= address < 0xC000):
        raise ValueError('known ROM bank and CPU ROM window required')
    return bank * BANK_SIZE + (address & (BANK_SIZE - 1))


def read_trace(text: str, image_size: int) -> dict:
    """Read exact observed fetch/data addresses, never infer unobserved liveness."""
    phases = {'startup': set(), 'runtime': set()}
    if not text.strip():
        raise ValueError('nonempty physical read trace required')
    for line in text.splitlines():
        fields = line.split(',')
        if len(fields) != 2 or fields[0] not in phases:
            raise ValueError('known phase and physical address required')
        address = int(fields[1])
        bank, offset = divmod(address, BANK_SIZE)
        physical_offset(bank, 0x8000 + offset, image_size)
        phases[fields[0]].add(address)
    return phases


def inventory(build: Path, out: Path) -> dict:
    metadata_raw = (build / 'build.json').read_bytes()
    meta = json.loads(metadata_raw)
    rom_path = build / meta['rom']['filename']
    rom = rom_path.read_bytes()
    if sha(rom) != meta['rom']['sha256']:
        raise ValueError('ROM identity differs from build metadata')
    for name, digest in meta['source_files'].items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError('bound source differs: ' + name)
    report = dict(schema_version=1, complete=True, runtime_changed=False,
                  evidence_class='read-only host storage inventory',
                  rom_sha256=sha(rom), build_metadata_sha256=sha(metadata_raw),
                  symbols_sha256=sha((build / 'presentation.sym').read_bytes()),
                  source_commit=meta['source_commit'],
                  bound_source_files=len(meta['source_files']),
                  inventory=image_inventory(rom),
                  declared_banks=meta['banks'],
                  contact_tables={k: meta['tables'][k] for k in
                                  ('used_bytes', 'banks', 'unique_records',
                                   'unique_blocks', 'unique_rows', 'codec')},
                  compression_scope='Host reference codecs only; no Z80 decoder, flat layout, RAM feasibility or target startup time proved.',
                  liveness_scope='No bytes classified dead. FF and duplicates can be semantically live.',
                  producer_sha256=sha(Path(__file__).read_bytes()))
    out = private_output(out)
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'banks.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(('bank', 'sha256', 'non_ff_bytes', 'trailing_ff_bytes',
                         'host_zlib9_bytes', 'host_lzma6_bytes'))
        for bank in range(len(rom) // BANK_SIZE):
            data = rom[bank * BANK_SIZE:(bank + 1) * BANK_SIZE]
            info = image_inventory(data)
            writer.writerow((bank, sha(data), *(info[k] for k in
                             ('non_ff_bytes', 'trailing_ff_bytes',
                              'host_zlib9_bytes', 'host_lzma6_bytes'))))
    report['bank_ledger_sha256'] = sha((out / 'banks.csv').read_bytes())
    if rom_path.read_bytes() != rom or (build / 'build.json').read_bytes() != metadata_raw:
        raise ValueError('input changed during inventory')
    (out / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.build.resolve(), args.out.resolve())
    print(json.dumps(result['inventory'], sort_keys=True))
