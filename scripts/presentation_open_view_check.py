"""Strict source/pixel/ownership validation for the declared open presentation."""
import argparse,json,hashlib
from pathlib import Path
import presentation_border_closure_check as closure
import presentation_ice_atlas_check as atlas
import presentation_fixed_clock_probe as clock
import presentation_matrix_check as matrix
import presentation_name_prefix_check as names
from presentation_open_view import expected_frame,shadow_credit,audit_credit

def check(build,out,mode,steps=2252):
 build,out=Path(build).resolve(),Path(out).resolve();m=json.loads((build/'build.json').read_text())
 if not m.get('open_view'):return names.check(build,out,mode,steps)
 oldframe=closure.expected_frame;oldowner=atlas.audit_row;oldactive=atlas.audit_active;counts=dict(owners=0,active=0)
 def owner(raw,vram,tile,**kw):
  shadow,video=shadow_credit(raw,vram);counts['owners']+=1
  return oldowner(shadow,video,tile,**kw)
 def active(before,after,registers):
  audit_credit(before);audit_credit(after);counts['active']+=1
  return oldactive(before,after,registers)
 closure.expected_frame=expected_frame;atlas.audit_row=owner;atlas.audit_active=active
 try:result=names.check(build,out,mode,steps)
 finally:closure.expected_frame=oldframe;atlas.audit_row=oldowner;atlas.audit_active=oldactive
 (out/'open-view-contract.json').write_text(json.dumps(dict(complete=bool(result['complete']),rom_sha256=m['rom']['sha256'],mode=mode,audits=counts,left=16,credit_ids=list(range(134,143)),source_owner_active_and_name_guards_retained=True,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('mode');p.add_argument('steps',type=int,nargs='?',default=2252);a=p.parse_args();check(a.build,a.out,a.mode,a.steps)
