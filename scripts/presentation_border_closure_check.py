"""Exact closed-edge source oracle plus all existing source/owner/active guards."""
import argparse,json
from pathlib import Path
import presentation_border_check as border
from presentation_bear_three_check import check as parent_check
from presentation_border_closure import expected_frame

def check(build,out,mode,steps=2252):
    previous=border.expected_frame;border.expected_frame=expected_frame
    try:result=parent_check(build,out,mode,steps)
    finally:border.expected_frame=previous
    m=json.loads((Path(build)/'build.json').read_text())
    (Path(out)/'border-closure-contract.json').write_text(json.dumps(dict(complete=bool(result['complete']),rom_sha256=m['rom']['sha256'],black_rows=[8,22],added_rectangle=[16,176,24,184],new_sprites=0,source_and_owner_guards_retained=True),indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('mode');p.add_argument('steps',type=int,nargs='?',default=2252);a=p.parse_args();check(a.build,a.out,a.mode,a.steps)
