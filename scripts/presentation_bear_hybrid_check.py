"""Preserve source/pixel/owner guards with a bounded synthetic bear namespace."""
import argparse,json,hashlib
from functools import lru_cache
from pathlib import Path
from environment import ROOT
from presentation_bear_hybrid import BASE,cropped_mask,validate_synthetic_role
import presentation_ice_atlas_check as atlas
import presentation_border_check as border

def check(build,out,mode,steps=2252):
    build,out=Path(build).resolve(),Path(out).resolve();m=json.loads((build/'build.json').read_text())
    if 'bear_hybrid'not in m:return atlas.check(build,out,mode,steps)
    from presentation_fast_model import prepare
    from presentation_palette import audit_palette
    from presentation_constructors import construct
    source=(ROOT/'references/roms/frostbite.bin').read_bytes();cfg=json.loads((ROOT/'references/presentation-assets-config.json').read_text());tables=prepare(source,audit_palette(ROOT/cfg['palette']),build/'geometry')
    r=m['bear_hybrid']['synthetic_registry'];registry={q['synthetic_ID']:(q['original_ID'],q['cut'])for q in r}
    if sorted(registry)!=list(range(BASE,BASE+80)):raise ValueError('bounded80-mask extension required')
    masks={sid:cropped_mask(tables['patterns'][orig],cut)for sid,(orig,cut)in registry.items()}
    if len(set(masks.values()))!=80:raise ValueError('synthetic registry repeats masks')
    rom=(build/m['rom']['filename']).read_bytes();regbytes=b''.join(orig.to_bytes(2,'little')+bytes((cut,))for sid,(orig,cut)in sorted(registry.items()));maskbytes=b''.join(masks[sid]for sid in sorted(masks))
    at=m['bear_hybrid']['registry_bank']*16384+m['bear_hybrid']['registry_address']-0x8000
    if rom[at:at+len(regbytes)]!=regbytes or hashlib.sha256(maskbytes).hexdigest()!=m['bear_hybrid']['synthetic_mask_sha256']:raise ValueError('source-derived mask registry/ROM bytes differ')
    backgrounds=[{128+i:tables['background']['patterns'][bank][i*8:i*8+8]+tables['background']['colors'][bank][i*8:i*8+8]for i in range(tables['background']['tiles_per_bank'][bank])}for bank in range(3)]
    old_audit=atlas.audit_row;old_dirty=border.dirty_rows;counts=dict(owner_rows=0,synthetic_keys=0,late_dirty_rows=0)
    @lru_cache(None)
    def synthetic(bank,key):return construct(key,patterns=masks,backgrounds=backgrounds[bank],header=b'',footer=[])
    def owners(raw,vram,tile,**kw):
        for page in range(2):
            for bank in range(3):
                for slot in range(64):
                    at=1536+((page*3+bank)*64+slot)*6;key=raw[at:at+6]
                    if validate_synthetic_role(bank,page*64+slot,key,registry):counts['synthetic_keys']+=1
        counts['owner_rows']+=1
        def extended(bank,key):
            if key[5]==0 and int.from_bytes(key[:2],'little')>=BASE:
                if int.from_bytes(key[:2],'little')not in masks:raise ValueError('unregistered synthetic ID')
                return synthetic(bank,key)
            return tile(bank,key)
        return old_audit(raw,vram,extended,**kw)
    def dirty(previous,current):
        rows=old_dirty(previous,current)
        if current[19]and current[1]!=32:rows.update((6,7,8));counts['late_dirty_rows']+=3
        return rows
    atlas.audit_row=owners;border.dirty_rows=dirty
    try:result=atlas.check(build,out,mode,steps)
    finally:atlas.audit_row=old_audit;border.dirty_rows=old_dirty
    if not result['complete']:return result
    receipt=dict(complete=True,rom_sha256=m['rom']['sha256'],mode=mode,synthetic_masks=80,original_mask_base=BASE,role_allowlist='bank0:2/6/66/70;bank1:2/66',audits=counts,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Original source/RGB/active/atlas/fixed role guards retained. Synthetic masks independently derived from original geometry, confined to crop boundary roles; exact late forced bear-row union independently checked.')
    (out/'bear-hybrid-contract.json').write_text(json.dumps(receipt,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('mode',choices=('ntsc','pal','matrix','density','header','boundary-ntsc','boundary-pal','boundary-negative'));p.add_argument('steps',type=int,nargs='?',default=2252);a=p.parse_args();check(a.build,a.out,a.mode,a.steps)
