"""Explicit kind10 bear reference; retain original source/pixel/owner/IRQ checks."""
import argparse
from functools import lru_cache
import json
from pathlib import Path

from build_compact_packet_experiment import digest
import compact_enemy_ram_check
from environment import ROOT
import native_bear_keys
import presentation_ice_atlas_check as atlas
from presentation_fast_model import prepare
from presentation_palette import audit_palette


def check(build,out,mode):
    build,out=build.resolve(),out.resolve()
    m=json.loads((build/'build.json').read_bytes())
    if m.get('native_bear_renderer',{}).get('kind')!=10:
        raise ValueError('explicit native bear constructor required')
    original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if digest(original)!=m['profile']['source_sha256']:raise ValueError('original changed')
    cfg=json.loads((ROOT/'references/presentation-assets-config.json').read_bytes())
    tables=prepare(original,audit_palette(ROOT/cfg['palette']),build/'geometry')
    backgrounds=[{128+i:tables['background']['patterns'][bank][i*8:i*8+8]+tables['background']['colors'][bank][i*8:i*8+8]
                  for i in range(tables['background']['tiles_per_bank'][bank])} for bank in range(3)]
    old_owner=atlas.audit_row
    counts=dict(rows=0,native_keys=0)
    @lru_cache(None)
    def native(bank,key):return native_bear_keys.construct(original,bank,key,backgrounds[bank])
    def owners(raw,vram,tile,**kw):
        counts['rows']+=1
        for page in range(2):
            for bank in range(3):
                for slot in range(64):
                    at=1536+((page*3+bank)*64+slot)*6
                    key=raw[at:at+6]
                    if key[5]==10:
                        native_bear_keys.validate_role(bank,page*64+slot,key)
                        counts['native_keys']+=1
        def extended(bank,key):return native(bank,key) if key[5]==10 else tile(bank,key)
        return old_owner(raw,vram,extended,native_bear=True,**kw)
    atlas.audit_row=owners
    try:compact_enemy_ram_check.check(build,out,mode)
    finally:atlas.audit_row=old_owner
    if not counts['rows'] or not counts['native_keys']:
        raise ValueError('native bear physical audits never exercised')
    result=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],audits=counts,
        original_glyph_constructor=True,exact_physical_roles=True,all_inherited_oracles_retained=True,
        producer_sha256=digest(Path(__file__).read_bytes()),scope='Original source/RGB, exact semantic key bytes, both NAME pages, physical PGT/CGT, active-page and IRQ checks. No native loader or physical hardware acceptance.')
    (out/'native-bear-renderer-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
