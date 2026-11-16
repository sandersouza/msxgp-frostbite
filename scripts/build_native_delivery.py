"""Compile the complete native game from repository Z80 source and static data."""
import argparse
import json
from pathlib import Path
import subprocess

from artifact_hash import digest
from environment import ROOT
from native_asm import assemble
from build_native_plain32 import build as cartridge
from build_native_disk import build as disk
from release_check import PAYLOADS


def build(out, compressor):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    receipt = out/'native-delivery-build.json'
    receipt.unlink(missing_ok=True)
    source_files = [ROOT/'Makefile', *sorted((ROOT/'scripts').glob('*.py')),
                    *sorted(p for p in (ROOT/'src').rglob('*') if p.is_file())]
    before = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in source_files}
    print('Assembling native game and SCREEN 2 data...', flush=True)
    ram, native_symbols = assemble(out/'cold', 'cold-ram', ' INCLUDE "game/game.asm"\n')
    video, _ = assemble(out/'cold', 'cold-vram', ' INCLUDE "game/video.asm"\n')
    if len(ram) != 65536 or len(video) != 16384:
        raise ValueError('complete 64 KiB RAM and 16 KiB VRAM source layouts required')
    hints, hint_symbols = assemble(out/'cold', 'start-hints',
                                  ' INCLUDE "game/start_hints.asm"\n')
    ram = bytearray(ram)
    offset = 0
    # Source-linked replacements for the obsolete diagnostic/mapper bootstrap.
    # Native cold loaders enter C400h and initialize the clock directly.
    for first, end in ((0x4014, 0x40B1), (0x7C51, 0x7CF2), (0xE99D, 0xE9EE),
                       (0x4971, 0x49DB)):
        size = end-first
        ram[first:end] = hints[offset:offset+size]
        offset += size
    if len(hints) != offset or len(ram) != 65536:
        raise ValueError('exact source overlay extents required')
    (out/'cold/cold-ram.bin').write_bytes(ram)
    (out/'cold/cold-image.json').write_text(json.dumps(dict(
        ram_sha256=digest(ram), vram_sha256=digest(video),
        native_symbols={name[3:]: value for name, value in native_symbols.items()
                        if name.startswith('fb_nc_')},
        hint_symbols={name: value for name, value in hint_symbols.items()
                      if name.startswith('sh_')},
        emulator_state_used_as_input=False), indent=2)+'\n')
    print('Compressing payloads and assembling native loaders...', flush=True)
    cartridge(out/'cold', out/'cartridge', Path(compressor))
    disk(out/'cartridge', out/'disk')
    if any(digest((ROOT/name).read_bytes()) != sha for name, sha in before.items()):
        raise ValueError('source changed during compilation')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    files = {name: dict(size=(out/name).stat().st_size,
                        sha256=digest((out/name).read_bytes())) for name in PAYLOADS}
    result = dict(native_formats_built=True, source_commit=commit,
                  source_files=before, files=files, no_mapper=True,
                  RAM_KiB=64, VRAM_KiB=16, emulator_state_used_as_input=False)
    receipt.write_text(json.dumps(result, indent=2)+'\n')
    print('Built cartridge/FROSTBIT.ROM and four disk files.', flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'outputs/native')
    parser.add_argument('--compressor', type=Path, default=ROOT/'.tools/zx0')
    args = parser.parse_args()
    build(args.out, args.compressor)
