#!/usr/bin/env python3
"""Stage exact tested diagnostic bytes; publishing remains an explicit release action."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from rom import ROOT, OUT, ROM, VERSION, validate_rom
from smoke import validate_build_identity


def validate_package(data,build,smoke,commit,dirty):
    if dirty or build.get('source_dirty') is not False or smoke.get('source_dirty') is not False:
        raise ValueError('package requires a clean source tree and clean build/smoke')
    if build.get('source_commit')!=commit or smoke.get('source_commit')!=commit:
        raise ValueError('build/smoke source commit must match current HEAD; rebuild and retest')
    problems=validate_rom(data)
    if problems:
        raise ValueError('; '.join(problems))
    validate_build_identity(data,build)
    if smoke.get('rom_sha256')!=hashlib.sha256(data).hexdigest():
        raise ValueError('smoke/ROM identity mismatch')
    if build.get('version')!=VERSION or smoke.get('version')!=VERSION or build['rom']['filename']!=ROM.name:
        raise ValueError('diagnostic version/filename mismatch')
    expected={'passed':True,'ram_bytes':65536,'configured_vram_kib':16,'vdp':'TMS9918A',
              'z80_hz':3579545,'extra_extensions':0}
    if any(smoke.get(key)!=value for key,value in expected.items()):
        raise ValueError('successful unexpanded MSX1 smoke required')


def main():
    latest=ROOT/'outputs/releases/latest-package.json'
    latest.unlink(missing_ok=True)
    try:
        data=ROM.read_bytes()
        build=json.loads((OUT/'build.json').read_text())
        smoke=json.loads((OUT/'smoke.json').read_text())
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
        validate_package(data,build,smoke,commit,dirty)
        notes=(ROOT/f'docs/releases/v{VERSION}.md').read_text()
        notes=notes.replace('{{SOURCE_COMMIT}}',commit).replace('{{ROM_SHA256}}',hashlib.sha256(data).hexdigest()).replace('{{ROM_FILENAME}}',ROM.name)
        latest.parent.mkdir(parents=True,exist_ok=True)
        directory=Path(tempfile.mkdtemp(prefix=f'v{VERSION}-',dir=latest.parent))
        (directory/ROM.name).write_bytes(data)
        for name,report in (('build.json',build),('smoke.json',smoke)):
            (directory/name).write_text(json.dumps(report,indent=2)+'\n')
        if 'screenshot' in smoke:
            source=(ROOT/smoke['screenshot']).resolve()
            if not source.is_relative_to(OUT.resolve()):
                raise ValueError('screenshot outside generated diagnostic outputs')
            (directory/'diagnostic.png').write_bytes(source.read_bytes())
        (directory/'release-notes.md').write_text(notes)
        files=[p for p in directory.iterdir() if p.is_file()]
        (directory/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(files)))
        summary={'tag':f'v{VERSION}','source_commit':commit,'rom_sha256':hashlib.sha256(data).hexdigest(),
                 'directory':str(directory.relative_to(ROOT)),
                 'files':[p.name for p in sorted(directory.iterdir())]}
        latest.write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary))
        return 0
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        print(f'Diagnostic packaging failed: {error}',file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
