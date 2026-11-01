"""Immutable synthetic SCREEN2 tiles and complete 32-cell row lookup tables.

All ordinary colored tiles fit both banks. The crossing band's bottom adds
68 tiles; reserve eight page-specific dynamic slots for its omitted patterns.
Only inactive-page slots are patched, preserving the currently visible frame.
"""
import render_model as model


def tile_key(pattern,color):return (bytes(pattern),color if any(pattern) else 0)


def compile_atlas():
    phases=model.phase_tables();ordinary={tile_key(bytes(8),0):0}
    def block(kind,phase,shift=0,half=0):
        start=kind*4096+phase*256+(shift//2)*64+half*32
        return phases[start:start+32]
    def insert(tiles,data,color):
        for offset in range(0,32,8):
            key=tile_key(data[offset:offset+8],color)
            if key not in tiles:tiles[key]=len(tiles)
    for kind in range(5):
        for color in ((15,5) if kind<2 else (8+kind,)):
            for phase in range(16):insert(ordinary,block(kind,phase),color)
    atlases=[]
    for half in (0,1):
        tiles=dict(ordinary)
        for kind in range(2):
            for color in (15,5):
                for phase in range(16):insert(tiles,block(kind,phase,4,half),color)
        atlases.append(tiles)
    if len(ordinary)>248 or len(atlases[0])>256:raise ValueError('immutable atlas exceeds target tile capacity')
    patterns=[];colors=[]
    for bank,tiles in enumerate(atlases):
        p=bytearray(2048);c=bytearray(2048)
        for (pattern,color),code in tiles.items():
            if code>=(248 if bank else 256):continue
            p[code*8:code*8+8]=pattern;c[code*8:code*8+8]=bytes((color*16,))*8
        patterns.append(bytes(p));colors.append(bytes(c))
    # Four aligned floes; eighteen object rows; four crossing top rows and
    # eight page-specific crossing bottom rows. Every row includes wrap/clip.
    variants=[(k,color,3,32,0,0,0) for k in (0,1) for color in (15,5)]
    variants += [(k,8+k,count,gap,0,0,0) for k in (2,3,4) for gap in (16,32) for count in (1,2,3)]
    variants += [(k,color,3,32,4,0,0) for k in (0,1) for color in (15,5)]
    variants += [(k,color,3,32,4,1,page) for page in (0,1) for k in (0,1) for color in (15,5)]
    rows=bytearray();patch_flags=bytearray(64)
    for variant in variants:
        kind,color,count,gap,shift,half,page=variant
        tiles=atlases[half] if shift else ordinary
        for x in range(160):
            data=block(kind,x%16,shift,half);codes=[]
            for tx in range(4):
                key=tile_key(data[tx*8:tx*8+8],color);code=tiles[key]
                if shift and half and code>=248:
                    code=248+page*4+tx;patch_flags[(0 if color==15 else 32)+kind*16+x%16]=1
                codes.append(code)
            row=bytearray(32)
            for copy in range(count):
                column=model.display_x((x+copy*gap)%160)//8
                for tx,code in enumerate(codes):
                    if column+tx<31:row[column+tx]=code
            rows+=row
    patches=b''.join(block(kind,phase,4,1) for kind in (0,1) for phase in range(16))
    return {'patterns':patterns,'colors':colors,'rows':bytes(rows),'patches':patches,'patch_flags':bytes(patch_flags),
            'ordinary_tiles':len(ordinary),'colored_tiles':[len(a) for a in atlases],'variants':variants}
