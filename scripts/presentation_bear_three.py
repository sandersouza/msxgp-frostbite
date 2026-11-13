"""Exact three-sprite full bear, retaining the existing left16-pixel pair."""
from presentation_bear_hybrid import sprite_prefix

def triple(pixels):
    if len(pixels)!=320 or any(v not in(0,1)for v in pixels):raise ValueError('complete16x20 monochrome source bear required')
    rows=[]
    for y in range(20):
        mask=0
        for x in range(16):
            if pixels[y*16+x]:
                for tx in range(3*x//2,3*(x+1)//2):
                    if tx>=16:mask|=128>>(tx-16)
        rows.append(mask)
    occupied=[y for y,v in enumerate(rows)if v]
    if not occupied or occupied[-1]-occupied[0]>=16:raise ValueError('thin bear strip exceeds one16-row rectangle')
    dy=occupied[-1]-15;thin=bytearray(32)
    for y,value in enumerate(rows):
        if value:thin[y-dy]=value
    return dict(patterns=sprite_prefix(pixels)+bytes(thin),dy=dy)

def full_admissible(tops,bear_y,thin_dy):
    if len(tops)>28 or any(type(n)is not int or not 0<=n<256 for n in tops)or type(bear_y)is not int or not 0<=bear_y<256 or thin_dy not in(-2,0):return False
    for line in range(256):
        extra=int(((line-bear_y+8)&255)<32)+int(((line-bear_y-thin_dy)&255)<16)
        if extra and sum(((line-top)&255)<16 for top in tops)+extra>4:return False
    return True

def full_assets(base):
    from pathlib import Path
    import json,hashlib
    from environment import ROOT
    from original_graphics import view
    base=Path(base);m=json.loads((base/'build.json').read_text());rom=(base/m['rom']['filename']).read_bytes();source=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if hashlib.sha256(rom).hexdigest()!=m['rom']['sha256']or hashlib.sha256(source).hexdigest()!=m['profile']['source_sha256']:raise ValueError('sealed source/parent ROM differs')
    directory=rom[132*16384+0x3800:132*16384+0x3c00];pool=[];info=bytearray();checks=[]
    for group in range(16):
        image=view(source,0xfd00+source[0xee7+group//2],19,bool(group&1),2);pixels=image['pixels']+image['pixels'][-16:];record=triple(pixels);data=record['patterns'];old=rom[132*16384+0x3c00+group*64:132*16384+0x3c00+(group+1)*64]
        if data[:64]!=old or record['dy']not in(-2,0):raise ValueError('original prefix compatibility/thin placement differs')
        if data not in pool:pool.append(data)
        info.extend((pool.index(data),record['dy']&255));checks.append(dict(group=group,packet=pool.index(data),thin_dy=record['dy']))
    if len(pool)!=6 or len(info)!=32:raise ValueError('audited three-sprite pool changed')
    payload=directory+bytes(info)+b''.join(pool)
    if len(payload)!=1632:raise ValueError('audited132-tail allocation changed')
    return dict(payload=payload,pool=b''.join(pool),info=bytes(info),groups=checks,packet_count=len(pool),prefixes_byte_identical=True)
