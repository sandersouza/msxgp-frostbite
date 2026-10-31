#!/usr/bin/env python3
"""Check staged public source blobs, never the ignored research tree."""
import hashlib
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ('.legacy/', '.tools/', '.venv/', 'outputs/', 'references/roms/',
             'references/dissasm/', 'references/generated/', 'assets/generated/')
SUFFIXES = {'.rom', '.bin', '.a26', '.car', '.zip', '.gz', '.tar', '.dsk', '.cas'}
ORIGINAL_SHA256 = 'cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834'


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], timeout=30)


def check_index(root=ROOT):
    problems = []
    for entry in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if not entry:
            continue
        info, raw_name = entry.split(b'\t', 1)
        mode, blob, stage = info.decode().split()
        name = raw_name.decode('utf-8')
        path = PurePosixPath(name)
        if stage != '0' or mode not in ('100644', '100755'):
            problems.append(f'{name}: unresolved index or non-regular source')
            continue
        if name.startswith(FORBIDDEN) or path.suffix.lower() in SUFFIXES:
            problems.append(f'{name}: prohibited local/generated/binary path')
            continue
        size = int(git(root, 'cat-file', '-s', blob))
        if size > 1024 * 1024:
            problems.append(f'{name}: oversized source blob requires provenance review')
            continue
        data = git(root, 'cat-file', 'blob', blob)
        if hashlib.sha256(data).hexdigest() == ORIGINAL_SHA256 or b'\0' in data:
            problems.append(f'{name}: original ROM or binary content')
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            problems.append(f'{name}: public sources must be UTF-8 text')
            continue
        if path.suffix.lower() in ('.asm', '.s', '.inc') and re.search(
                r'distella|disassembly of .*rom|generated.*original.*rom', text, re.I):
            problems.append(f'{name}: original-derived disassembly requires local-only storage')
    return problems


if __name__ == '__main__':
    try:
        problems = check_index()
        print('\n'.join(problems) if problems else 'Public staged-source policy passed (ignored inputs not read).')
        sys.exit(bool(problems))
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
        print(f'Source-policy inspection failed: {error}', file=sys.stderr)
        sys.exit(1)
