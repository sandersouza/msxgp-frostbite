"""Independent whole-state audit for the integrated offscreen transactions."""
from presentation_dirty import scene,dirty_rows

ROW_BYTES=70
BOOT_BYTES=259


def boot_histories(raw,rng):
    if len(raw)!=BOOT_BYTES or raw[256]not in (0,1):raise ValueError('complete boot histories/page required')
    page,layout,width=raw[256:259]
    histories=[raw[128:192],raw[192:256]]
    if histories[page]!=scene(raw[:128],rng,layout=layout,width=width) or any(histories[page^1]):
        raise ValueError('boot visual history differs from the only prepared generation')
    histories[page^1]=None
    return histories


def audit_scene(raw,ram,rng,histories,page):
    if len(raw)!=ROW_BYTES or page not in (0,1) or raw[67]!=page or len(histories)!=2:
        raise ValueError('complete integrated dirty capture/current generation required')
    state=scene(ram,rng,layout=raw[68],width=raw[69])
    rows=dirty_rows(histories[page],state)
    flags=bytes(sum(1<<(row&7) for row in rows if row//8==bank) for bank in range(3))
    if raw[:67]!=state+flags:raise ValueError('actual normalized state or dirty flags differ')
    histories[page]=state
    return len(rows)


def audit_physical_names(vram,names):
    if len(vram)!=16384 or len(names)!=1536:raise ValueError('whole physical VRAM and both intended name pages required')
    if vram[0x1800:0x1B00]+vram[0x1C00:0x1F00]!=names:
        raise ValueError('physical name pages differ from CPU ownership')
