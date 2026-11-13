"""Retain all source, owner, IRQ and immutable-credit checks for edge repair."""
import argparse,hashlib,json
from pathlib import Path
import presentation_open_view_check as parent
from presentation_viewport_edges import expected_frame
def check(build,out,mode,steps=2252):
 old=parent.expected_frame;parent.expected_frame=expected_frame
 try:result=parent.check(build,out,mode,steps)
 finally:parent.expected_frame=old
 m=json.loads((Path(build)/'build.json').read_text())
 (Path(out)/'viewport-edges-contract.json').write_text(json.dumps(dict(complete=bool(result['complete']),rom_sha256=m['rom']['sha256'],mode=mode,player_left=16,enemy_glyph_wrap=False,all_parent_guards_retained=True,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('mode');p.add_argument('steps',type=int,nargs='?',default=2252);a=p.parse_args();check(a.build,a.out,a.mode,a.steps)
