"""Explicit player-only presentation adaptation; source mechanics are unchanged."""
from copy import deepcopy
from graphics_mapping import map_frame,map_x,map_y,palette_map
from presentation_model import pixels

def player_color(code,baseline):
    return {0x24:10,0x36:11,0x16:11}.get(code&254,baseline)

def header_identity(codes,colors,level):
    if len(codes)!=12 or len(colors)!=3 or not 0<=level<=255:raise ValueError('complete header identity required')
    return bytes(codes)+bytes(colors)+bytes([int(level>=20)])

def changed_columns(before,after):
    if len(after)!=16 or (before is not None and len(before)!=16):raise ValueError('sixteen-byte identities required')
    if before is None or before[12:]!=after[12:]:return 1023
    mask=0
    for i,(a,b) in enumerate(zip(before[:12],after[:12])):
        if a!=b:mask|=(3,14,24,112,192,896)[i%6]
    return mask

def adapt_tagged(raw,tagged,palette):
    if len(raw)!=33600 or len(tagged)!=33600 or any((a&254)!=b for a,b in zip(tagged,raw)):
        raise ValueError('tagged player compositor differs from original raster')
    result=bytearray(map_frame(raw,palette));colors=palette_map(palette)
    for at,code in enumerate(tagged):
        if not code&1:continue
        target=player_color(code,colors[code&254])
        if target==colors[code&254]:continue
        y,x=divmod(at,160);ty=map_y(y)
        if ty is not None:
            first=ty*256+map_x(x);width=map_x(x+1)-map_x(x)
            result[first:first+width]=bytes([target])*width
    return bytes(result)

def expected_frame(original,description,raw,palette):
    tagged=deepcopy(description)
    for row in tagged['player']['rows']:
        for key in ('color','prefix_color','suffix_color'):row[key]|=1
    return adapt_tagged(raw,pixels(original,tagged),palette)

def adapted_frame(meta,original,description,ram,raw,palette):
    if not meta.get('player_palette') or ram[0x6b] or ram[0x70]:return map_frame(raw,palette)
    if meta['player_palette']['normal_overrides']!={'22':11,'36':10,'54':11}:
        raise ValueError('undeclared player adaptation')
    return expected_frame(original,description,raw,palette)
