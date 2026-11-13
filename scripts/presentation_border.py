"""Declared aligned sea edge; canonical source physics is never transformed."""
LEFT=24
ROWS=range(8,22)

def left_mask(x):
    if type(x)is not int or x not in range(11):raise ValueError('left sourceX0..10 required')
    hidden=LEFT-(8+3*(x//2))
    return (1<<max(0,16-hidden))-1

def border_names(raw):
    if len(raw)!=768:raise ValueError('one complete NAME buffer required')
    result=bytearray(raw)
    for row in ROWS:result[row*32+2]=128
    return bytes(result)

def eligible(mode,raw,y,p0,base_count):
    if mode not in range(4)or not 0<=raw<=255 or not 0<=base_count<32:raise ValueError('bounded lane/count required')
    xs=[((raw+offset)&255)%160 for offset in((0,),(0,16),(0,32),(0,16,32))[mode]]
    if mode==0 and xs[0]==0:return False
    if base_count+len(xs)>=32 or mode and any(x<11 or x>152 for x in xs):return False
    return len(xs)+sum(abs(((sp[0]+1)&255)-y)<16 for sp in p0)<=4

def expected_frame(meta,original,description,ram,raw,palette):
    from copy import deepcopy
    from presentation_grid24 import expected_frame as grid,player_delta
    from presentation_model import pixels
    from presentation_player_palette import player_color
    from graphics_mapping import map_x,map_y,palette_map
    if not meta.get('border_clip'):return grid(meta,original,description,ram,raw,palette)
    if meta['border_clip']['view']!='border24-v1':raise ValueError('unknown declared border view')
    # Reconstruct background/actors independently of target patterns or NAME IDs.
    base=deepcopy(description)
    for row in base['player']['rows']:row['pattern']=row['prefix_pattern']=0
    result=bytearray(grid(meta,original,base,ram,raw,palette))
    for y in range(64,176):result[y*256+16:y*256+24]=bytes([1])*8
    if description['hud']['blanked']:return bytes(result)
    # Preserve existing P0 priority above the former black mask, including its
    # intentional edge overhang. No palette, glyph, contact or clock changes.
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
