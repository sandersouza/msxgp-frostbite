"""Assemble maintained native source with the pinned Z80 toolchain."""
from pathlib import Path
import re
import subprocess
from environment import ROOT, verified_tool


def symbols(path):
    return {m[1]: int(m[2], 16) for line in Path(path).read_text().splitlines()
            if (m := re.match(r'([^:]+): EQU 0x([0-9A-Fa-f]+)', line))}


def assemble(out, name, text):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    source, binary, sym = (out/(name+ext) for ext in ('.asm', '.bin', '.sym'))
    source.write_text(text)
    result = subprocess.run([str(verified_tool('sjasmplus')), '--nologo',
        f'--inc={ROOT/"src"}', f'--inc={ROOT/"src/game"}',
        f'--raw={binary}', f'--sym={sym}', f'--lst={out/(name+".lst")}', str(source)],
        capture_output=True, text=True)
    (out/(name+'.log')).write_text(result.stdout+result.stderr)
    if result.returncode:
        raise ValueError(f'{name} assembly failed: '+(result.stdout+result.stderr)[-2000:])
    return binary.read_bytes(), symbols(sym)
