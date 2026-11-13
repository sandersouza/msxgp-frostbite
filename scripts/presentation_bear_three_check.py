"""Original source/owner/atlas guards plus unconditional active extra-SGT safety."""
import argparse,hashlib,json
from pathlib import Path
import presentation_bear_hybrid_check as hybrid

def freeze_active_extra(before,prepared,registers):
    if len(before)!=16384 or len(prepared)!=16384 or len(registers)!=8 or registers[2]not in(6,7):raise ValueError('complete active-page snapshot required')
    slot=58+registers[2]-6;at=0x3800+slot*32
    if before[at:at+32]!=prepared[at:at+32]:raise ValueError('active three-sprite bear pattern changed, including cached unreferenced slot')

def check(build,out,mode,steps=2252):
    build,out=Path(build).resolve(),Path(out).resolve();m=json.loads((build/'build.json').read_text())
    if 'bear_three'not in m:return hybrid.check(build,out,mode,steps)
    if m['bear_three']['extra_pattern_slots']!=[58,59]:raise ValueError('declared private extra SGT slots differ')
    previous=hybrid.atlas.audit_active;count=0
    def active(before,prepared,registers):
        nonlocal count
        result=previous(before,prepared,registers);freeze_active_extra(before,prepared,registers);count+=1;return result
    hybrid.atlas.audit_active=active
    try:result=hybrid.check(build,out,mode,steps)
    finally:hybrid.atlas.audit_active=previous
    negative=mode=='boundary-negative'and result.get('complete')and result.get('expected_failure')=='boundary-register-restoration'
    if not negative and not count:raise ValueError('active extra-SGT guard was not exercised')
    receipt=dict(complete=bool(result['complete']),rom_sha256=m['rom']['sha256'],mode=mode,extra_sgt_active_audits=count,source_rgb_owner_atlas_guards_unchanged=True,exception_regions=0,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Original complete source/RGB/owner/atlas/active guards retained; unconditional activePAGE58/59 pattern freeze added even while not SAT-referenced. No blanket guard exemption.')
    (out/'bear-three-contract.json').write_text(json.dumps(receipt,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('mode',choices=('ntsc','pal','matrix','density','header','boundary-ntsc','boundary-pal','boundary-negative'));p.add_argument('steps',type=int,nargs='?',default=2252);a=p.parse_args();check(a.build,a.out,a.mode,a.steps)
