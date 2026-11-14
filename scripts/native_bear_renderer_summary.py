"""Bind the five exact integrated native-bear checks and whole-frame costs."""
import argparse
import json
from pathlib import Path
from compact_native_fixture import sha


def summarize(root):
    build=root/'build';m=json.loads((build/'build.json').read_bytes())
    if sha(build/m['rom']['filename'])!=m['rom']['sha256']:raise ValueError('ROM changed')
    rows={}
    for mode in ('ntsc','pal','bear-ntsc','bear-pal','matrix'):
        p=root/mode/'native-bear-renderer-check.json';d=json.loads(p.read_bytes())
        if not d['complete'] or d['rom_sha256']!=m['rom']['sha256'] or not d['audits']['native_keys']:
            raise ValueError('missing bound complete original constructor/role audit')
        row=dict(receipt_sha256=sha(p),native_key_audits=d['audits']['native_keys'])
        if mode!='matrix':
            q=json.loads((root/mode/'check.json').read_bytes())
            if not q['complete'] or q['rom_sha256']!=m['rom']['sha256']:raise ValueError('timing binding differs')
            row.update(active_pictures_per_second=q['active_pictures_per_second'],mean_prepare_elapsed_cycles=q['mean_prepare_elapsed_cycles'])
        rows[mode]=row
    result=dict(complete=True,rom_sha256=m['rom']['sha256'],routes=rows,human_test_candidate=False,mapperless=False)
    (root/'native-bear-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    a=p.parse_args();summarize(a.root.resolve())
