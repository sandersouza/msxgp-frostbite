"""Run immutable F input/timing adapter with explicit shared-RAM/ownership audit."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

from environment import ROOT
from presentation_fixed_ownership import audit_row
from presentation_shared_ownership import audit_active_references, audit_pool, constructor
from presentation_experiment_evidence import owner_binding,validate_probe


def check(build, out, family):
    meta=json.loads((build/'build.json').read_text())
    if hashlib.sha256((build/meta['rom']['filename']).read_bytes()).hexdigest()!=meta['rom']['sha256']:
        raise ValueError('ROM identity mismatch')
    original_run = subprocess.run
    def intercepted(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            script = Path(args[args.index('-script')+1])
            text = script.read_text()
            text = text.replace('memory 0xE800 0xB40','memory 0xF240 0x100')
            text = text.replace('memory 0xE800 [string repeat [binary format c 165] 0xB40]',
                                'memory 0xF240 [string repeat [binary format c 165] 0x100]')
            text = text.replace('[string repeat [binary format c 165] 0xB40]',
                                '[string repeat [binary format c 165] 0x100]')
            from render_build import symbols
            s = symbols(build/'presentation.sym')
            text += f'''
set residency [open {{{out/'residency.bin'}}} wb]
debug set_bp {s['paced_wait']} {{}} {{
 puts -nonewline $::residency "[debug read_block memory 0xE800 2624][debug read_block memory 0xDE00 512][debug read_block memory 0xC800 768][debug read_block memory 0xCD00 768][debug read_block memory 0xD000 2304][debug read_block memory 0xD900 264][debug read_block memory 0xCCA0 6]"
}}
'''
            script.write_text(text)
        return original_run(args,*a,**kw)
    adapter = ROOT/'outputs/presentation/architecture-review-f/route_probe.py'
    expected = 'db9229dc9464646569386f18d88cf493d5b3eb2401a9829030d084da87e0958f'
    if hashlib.sha256(adapter.read_bytes()).hexdigest() != expected:
        raise ValueError('sealed input adapter changed')
    argv = sys.argv
    sys.argv = [str(adapter),str(build),str(out),family]
    subprocess.run = intercepted
    try:
        runpy.run_path(str(adapter),run_name='__main__')
    finally:
        subprocess.run = original_run
        sys.argv = argv
    frames = 2253 if family == 'ntsc' else 1886
    validate_probe(out,meta['rom']['sha256'],frames)
    pools = (out/'residency.bin').read_bytes()
    captures = (out/'captures.bin').read_bytes()
    if len(pools) != frames*7246 or len(captures) != frames*49304:
        raise ValueError('incomplete paired physical snapshots')
    tile = constructor(build)
    audits = []
    for index in range(frames):
        row = captures[index*49304:(index+1)*49304]
        audit_active_references(row[128:16512],row[16520:32904],row[16512:16520])
        record = pools[index*7246:(index+1)*7246]
        raw = record[3136:]
        audit_row(raw,row[32912:49296],tile,templates=True,shared_ice=True)
        audits.append(audit_pool(record[:2624],record[2624:3136],raw[1536:3840]))
    result = dict(complete=True,frames=frames,physical_reference_protection=True,pool_audits=audits,
        wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        adapter_sha256=expected,scope='Same F timing/input adapter plus shared-RAM and independent physical audits; no human/physical acceptance.')
    result.update(owner_binding(out,meta['rom']['sha256'],frames,'shared'))
    target=out/'shared-check-v2.json'
    if target.exists():raise ValueError('immutable physical audit receipt already exists')
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(dict(complete=True,frames=frames,shared_physical_checks=True))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--family',choices=('ntsc','pal'),required=True)
    args=parser.parse_args();check(args.build.resolve(),args.out.resolve(),args.family)
