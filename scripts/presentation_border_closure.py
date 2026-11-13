"""Close the last left-edge sea tile, keeping source P0 foreground priority."""
from copy import deepcopy
from presentation_border import border_names as parent_names,expected_frame as parent_frame

def border_names(raw):
    result=bytearray(parent_names(raw));result[22*32+2]=128;return bytes(result)

def close_background(raw):
    if len(raw)!=256*192:raise ValueError('complete192x256 raster required')
    result=bytearray(raw)
    for y in range(176,184):result[y*256+16:y*256+24]=bytes([1])*8
    return bytes(result)

def expected_frame(meta,original,description,ram,raw,palette):
    if not meta.get('border_closure'):return parent_frame(meta,original,description,ram,raw,palette)
    if meta['border_closure']['black_rows']!=[8,22]:raise ValueError('unknown lower-edge closure')
    from presentation_grid24 import player_delta
    from presentation_model import pixels
    from presentation_player_palette import player_color
    from graphics_mapping import map_x,map_y,palette_map
    base=deepcopy(description)
    for row in base['player']['rows']:row['pattern']=row['prefix_pattern']=0
    result=bytearray(close_background(parent_frame(meta,original,base,ram,raw,palette)))
    if description['hud']['blanked']:return bytes(result)
    tagged=deepcopy(description)
    for row in tagged['player']['rows']:
        for key in('color','prefix_color','suffix_color'):row[key]|=1
    image=pixels(original,tagged);colors=palette_map(palette)
    delta=player_delta(ram[0x64],int(ram[0x68]>=150));normal=not ram[0x6b]and not ram[0x70]
    for at,code in enumerate(image):
        if not code&1:continue
        sy,x=divmod(at,160);y=map_y(sy)
        if y is None or not 0<=y+delta<192:continue
        color=player_color(code&254,colors[code&254])if normal else colors[code&254]
        first=(y+delta)*256+map_x(x);width=map_x(x+1)-map_x(x)
        result[first:first+width]=bytes([color])*width
    return bytes(result)
