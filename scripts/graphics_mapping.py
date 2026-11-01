"""Offline asset-fit compiler, NOT a real-time renderer/upload strategy."""
from collections import Counter

# Nominal preview RGB; physical composite/RGB and Atari palettes vary.
TMS_RGB=((0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),
         (125,118,252),(212,82,77),(66,235,245),(252,85,84),(255,121,120),
         (212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255))


def map_x(x):
    if type(x) is not int or not 0<=x<=160:raise ValueError('source X outside0..160')
    return 8+3*x//2


def map_y(y):
    if type(y) is not int or not 0<=y<210:raise ValueError('source raster Y outside0..209')
    if 7<=y<186:return y-7
    if 189<=y<202:return y-10
    return None


def nearest(rgb, choices=range(1,16)):
    return min(choices,key=lambda c:(sum((int(rgb[i])-TMS_RGB[c][i])**2 for i in range(3)),c))


def palette_map(palette):
    if any(type(k) is not int or not 0<=k<=255 or len(v)!=3
           or any(type(c) is not int or not 0<=c<=255 for c in v) for k,v in palette.items()):
        raise ValueError('invalid measured Atari RGB palette')
    # Keep colored water/sky/creatures colored even when the TMS lacks their
    # dark luminance. Unconstrained RGB distance can incorrectly choose black.
    result={}
    for code,rgb in palette.items():
        if max(rgb)-min(rgb)<24:
            # Stretch the limited grayscale to retain bear/igloo/shore contrast;
            # source6(142)->gray, source10(192)->white rather than merging them.
            luminance=sum(rgb)//3
            result[code]=1 if luminance<128 else 14 if luminance<176 else 15
        else:result[code]=nearest(rgb,tuple(c for c in range(1,16) if c not in (1,14,15)))
    return result


def map_frame(source,palette):
    if len(source)!=160*210:raise ValueError('expected210x160 indexed source frame')
    colors=palette_map(palette)
    if not set(source)<=colors.keys():raise ValueError('source color missing from measured palette')
    result=bytearray([1])*(256*192)
    for y in range(210):
        target_y=map_y(y)
        if target_y is None:continue
        for x in range(160):
            start=target_y*256+map_x(x);width=map_x(x+1)-map_x(x)
            result[start:start+width]=bytes([colors[source[y*160+x]]])*width
    return bytes(result)


def compile_screen(pixels,restore=False):
    if len(pixels)!=256*192 or any(not 1<=c<=15 for c in pixels):raise ValueError('expected192x256 opaque TMS indexed frame')
    vram=bytearray(16384);names=bytearray(768);counts=[];changed=0;crowded=0
    for bank in range(3):
        tiles={}
        for ty in range(8):
            for tx in range(32):
                pattern=bytearray();colors=bytearray()
                for row in range(8):
                    start=(bank*64+ty*8+row)*256+tx*8;line=pixels[start:start+8]
                    ranked=sorted(Counter(line),key=lambda c:(-line.count(c),c))
                    chosen=ranked[:2];fg=chosen[0];bg=chosen[-1]
                    if len(ranked)>2:crowded+=1
                    adapted=[c if c in chosen else nearest(TMS_RGB[c],chosen) for c in line]
                    changed+=sum(a!=b for a,b in zip(line,adapted))
                    pattern.append(sum(128>>x for x,c in enumerate(adapted) if c==fg))
                    colors.append(fg*16+bg)
                tile=(bytes(pattern),bytes(colors))
                if tile not in tiles:tiles[tile]=len(tiles)
                code=tiles[tile];names[(bank*8+ty)*32+tx]=code
        if len(tiles)>192:raise ValueError('frame exceeds192 allocated tile IDs per bank')
        counts.append(len(tiles))
        for (pattern,colors),code in tiles.items():
            index=bank*2048+code*8;vram[index:index+8]=pattern;vram[0x2000+index:0x2008+index]=colors
    vram[0x1800:0x1B00]=names;vram[0x1C00:0x1F00]=names;vram[0x1B00]=208
    patched=peak=patterns=0
    if restore and changed:
        decoded=decode_screen(vram);slots=[];occupancy=[0]*192
        for y in range(0,192,16):
            for x in range(0,256,16):
                colors=sorted({pixels[(y+dy)*256+x+dx] for dy in range(16) for dx in range(16)
                               if pixels[(y+dy)*256+x+dx]!=decoded[(y+dy)*256+x+dx]})
                for color in colors:
                    slot=len(slots)
                    if slot>=32:raise ValueError('sprite repair exceeds32 hardware slots')
                    pattern=bytearray(32)
                    for dy in range(16):
                        for dx in range(16):
                            offset=(y+dy)*256+x+dx
                            if pixels[offset]==color and pixels[offset]!=decoded[offset]:
                                pattern[(dx//8)*16+dy]|=128>>(dx%8);patched+=1
                    vram[0x3800+slot*32:0x3820+slot*32]=pattern
                    slots.append(bytes(((y-1)&255,x,slot*4,color)))
                    for line in range(y,y+16):occupancy[line]+=1
        peak=max(occupancy);patterns=len(slots)*32
        if peak>4:raise ValueError('sprite repair exceeds4 scanline slots')
        sat=b''.join(slots)+(b'\xD0' if len(slots)<32 else b'')
        vram[0x1B00:0x1B00+len(sat)]=sat
        if decode_screen(vram)!=pixels:raise ValueError('sprite repair did not restore exact mapped pixels')
        changed=0
    return {'vram':bytes(vram),'tiles_per_bank':counts,'changed_pixels':changed,'patched_pixels':patched,
            'sprite_patterns_bytes':patterns,
            'overcolor_rows':crowded,
            'sprites_per_line':peak,
            'strategy':'Offline background plus bounded sprite pixel repairs; dynamic adapter/timing still required'}


def decode_screen(vram):
    if len(vram)!=16384:raise ValueError('expected16KiB VRAM')
    output=bytearray(256*192)
    for y in range(192):
        for x in range(256):
            code=vram[0x1800+(y//8)*32+x//8];index=(y//64)*2048+code*8+y%8
            pattern=vram[index];color=vram[0x2000+index]
            output[y*256+x]=(color>>4 if pattern&(128>>(x%8)) else color&15)
    sprites=[]
    for index in range(32):
        sat=vram[0x1B00+index*4:0x1B04+index*4]
        if sat[0]==208:break
        sprites.append(sat)
    for sy,sx,pattern,color in reversed(sprites):
        top=(sy+1)&255;left=sx-(32 if color&128 else 0);base=(pattern&252)*8
        if color&15:
            for dy in range(16):
                for dx in range(16):
                    if top+dy<192 and 0<=left+dx<256 and vram[0x3800+base+(dx//8)*16+dy]&(128>>(dx%8)):
                        output[(top+dy)*256+left+dx]=color&15
    return bytes(output)
