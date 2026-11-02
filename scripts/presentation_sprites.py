"""Small source-derived native sprite tables; no scene or gameplay playback."""
from graphics_mapping import palette_map


def expand_pair(mask,parity):
    if type(mask)is not int or not 0<=mask<=255 or parity not in (0,1):raise ValueError('byte mask and pixel-scale parity required')
    result=bytearray(2)
    for x in range(8):
        if mask&(128>>x):
            for tx in range((parity+x)*3//2-parity*3//2,(parity+x+1)*3//2-parity*3//2):result[tx//8]|=128>>(tx%8)
    return bytes(result)


def tables(rom,measured_palette):
    if len(rom)!=4096 or set(measured_palette)!=set(range(0,256,2)):raise ValueError('complete source ROM and measured128-color palette required')
    mapped=palette_map(measured_palette);door=bytearray();logo=bytearray(64)
    for reflection in (0,1):
        pattern=bytearray(32)
        for y in range(12):
            row=rom[0xEF3+11-y]
            if reflection:row=int(f'{row:08b}'[::-1],2)
            left,right=expand_pair(row,1);pattern[y+4]=left;pattern[y+20]=right
        door.extend(pattern)
    for y in range(8):
        for glyph in range(5):
            row=rom[0xF68+glyph*8+7-y]
            for x in range(8):
                if row&(128>>x):
                    for tx in range((glyph*8+x)*3//2,(glyph*8+x+1)*3//2):logo[tx//16*16+y*2+(tx%16)//8]|=128>>(tx%8)
    holds={57}|{base+n for base in (78,90,104,116,130,142,156,168) for n in (2,3)}
    tails={77:91,**{y:118 for y in (78,89,104,115,130,141,156,167)},**{y:109 for y in (90,116,142,168)},**{y:130 for y in (103,129,155)}}
    return {'expansion':b''.join(expand_pair(mask,parity) for parity in (0,1) for mask in range(256)),
            'colors':bytes(mapped[c&254] for c in range(256)),'reverse':bytes(int(f'{c:08b}'[::-1],2) for c in range(256)),
            'holds':bytes(int(y in holds) for y in range(47,182)),'tails':bytes(tails.get(y,160) for y in range(47,182)),
            'door':bytes(door),'logo':bytes(logo)}
