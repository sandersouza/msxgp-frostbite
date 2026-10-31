#!/usr/bin/env python3
"""Reconstruct the verified local Atari image; keep all generated source private."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from reference_inventory import MANIFEST, ROOT, load_manifest, verified_input


def identity(path):
    data = path.read_bytes()
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def executable(value):
    resolved = shutil.which(str(value))
    if resolved is None:
        raise ValueError(f'executable unavailable: {value}')
    return Path(resolved).resolve()


def run_tool(command, directory):
    result = subprocess.run(command, cwd=directory, capture_output=True, timeout=120)
    # Tool diagnostics may include original source; leave them local too.
    (directory / (Path(command[0]).name + '.stdout')).write_bytes(result.stdout)
    (directory / (Path(command[0]).name + '.stderr')).write_bytes(result.stderr)
    if result.returncode:
        raise ValueError(f'{Path(command[0]).name} exit {result.returncode}; see {directory}')
    return result.stdout


def reconstruct(rom, manifest, distella, dasm):
    source_identity = verified_input(rom, manifest)  # Fail before touching tools.
    distella, dasm = executable(distella), executable(dasm)
    root = ROOT / 'outputs/reference-rebuild'
    root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='run-', dir=root))
    # Pinned DiStella uses char file[50] + strcpy. Do not pass a host path.
    local_input = directory / 'input.bin'
    local_input.write_bytes(rom.read_bytes())
    verified_input(local_input, manifest)
    source = directory / 'reference.asm'
    binary = directory / 'rebuilt.bin'
    listing = directory / 'reference.lst'
    symbols = directory / 'reference.sym'
    commands = [[str(distella), '-paf', local_input.name],
                [str(dasm), str(source), '-f3', f'-o{binary}',
                 f'-l{listing}', f'-s{symbols}']]
    tools = {name: {'path': str(path), **identity(path)}
             for name, path in (('distella', distella), ('dasm', dasm))}
    source.write_bytes(run_tool(commands[0], directory))
    run_tool(commands[1], directory)
    original, rebuilt = rom.read_bytes(), binary.read_bytes()
    # Revalidate the input after external execution, including mid-run changes.
    verified_input(rom, manifest)
    if len(original) != len(rebuilt):
        raise ValueError(f'rebuilt size mismatch: {len(rebuilt)} != {len(original)}; see {directory}')
    if original != rebuilt:
        offset = next(i for i, pair in enumerate(zip(original, rebuilt)) if pair[0] != pair[1])
        raise ValueError(f'rebuilt byte mismatch at offset {offset:#x}; see {directory}')
    return {'schema_version': 1, 'input': source_identity,
            'byte_identical': True, 'rebuilt': identity(binary), 'tools': tools,
            'commands': commands, 'artifacts_directory': str(directory.relative_to(ROOT)),
            'artifacts': {path.name: identity(path) for path in (source, listing, symbols)},
            'utility_sha256': identity(Path(__file__))['sha256'],
            'scope': 'Byte identity only; automatic code/data classification is heuristic.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path)
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    parser.add_argument('--distella', default=str(ROOT / '.tools/distella/distella'))
    parser.add_argument('--dasm', default='dasm')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'outputs/reference-rebuild/report.json')
    args = parser.parse_args(argv)
    try:
        rom = args.rom or ROOT / load_manifest(args.manifest)['input']['path']
        report = reconstruct(rom, args.manifest, args.distella, args.dasm)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        print(f"Byte-identical reconstruction: {report['rebuilt']['size']} bytes, "
              f"SHA-256 {report['rebuilt']['sha256']}; report {args.output}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(f'Reference rebuild failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
