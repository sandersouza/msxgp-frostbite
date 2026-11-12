"""Keep border/source/pixel guards and explicitly prove immutable atlas ownership."""
import argparse,hashlib,json
from pathlib import Path
import presentation_border_check as border
import presentation_fixed_clock_probe as clock
import presentation_matrix_check as matrix
import presentation_prepared_check as prepared
from presentation_fixed_ownership import audit_row,audit_active
from presentation_ice_atlas import audit_atlas,shadow_names
from environment import ROOT

def check(build,out,mode,steps=2252):
    build,out=Path(build).resolve(),Path(out).resolve();m=json.loads((build/'build.json').read_text())
    if 'ice_atlas'not in m:return border.check(build,out,mode,steps)
    a=m['ice_atlas'];rom=(build/m['rom']['filename']).read_bytes();at=a['bank']*16384+a['patterns_address']-0x8000
    patterns=rom[at:at+len(a['ids'])*8]
    if hashlib.sha256(patterns).hexdigest()!=a['patterns_sha256']:raise ValueError('atlas ROM pattern hash differs')
    table={identifier:patterns[i*8:(i+1)*8]+bytes([0xf4])*8 for i,identifier in enumerate(a['ids'])};counts=dict(owners=0,active=0)
    def owners(raw,vram,tile,**kw):
        shadow,video=shadow_names(raw,vram,table);counts['owners']+=1
        return audit_row(shadow,video,tile,**kw)
    def active(before,after,registers):
        audit_atlas(before,table);audit_atlas(after,table);counts['active']+=1
        return audit_active(before,after,registers)
    old=(clock.audit_row,clock.audit_active,matrix.audit_active,prepared.audit_row)
    clock.audit_row=prepared.audit_row=owners;clock.audit_active=matrix.audit_active=active
    try:result=border.check(build,out,mode,steps)
    finally:clock.audit_row,clock.audit_active,matrix.audit_active,prepared.audit_row=old
    negative=(mode=='boundary-negative' and result.get('complete') and result.get('expected_failure')=='boundary-register-restoration')
    if not negative and (not counts['owners']or not counts['active']):raise ValueError('atlas ownership audits were not exercised')
    producers={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(Path(__file__).resolve(),ROOT/'scripts/presentation_ice_atlas.py')}
    receipt=dict(complete=True,rom_sha256=m['rom']['sha256'],mode=mode,atlas_ids=len(table),audits=counts,negative_control=bool(negative),producers=producers,scope=('Expected AF2 rejection before picture decoding; no atlas ownership acceptance from this negative test.' if negative else 'Actual pixels/source/active-page guards retained. Both thirds immutable atlas bytes explicitly checked before shadow NAME ownership audit; footer and unregistered high IDs retain original guards.'))
    (out/'ice-atlas-contract.json').write_text(json.dumps(receipt,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('mode',choices=('ntsc','pal','matrix','density','header','boundary-ntsc','boundary-pal','boundary-negative'));p.add_argument('steps',type=int,nargs='?',default=2252);a=p.parse_args();check(a.build,a.out,a.mode,a.steps)
