"""ROM-derived normal P0 recipes, no captured route input."""
from itertools import product
from presentation_sprites import expand_pair
from presentation_model import player

def compile_recipes(rom,palette):
    recipes=[];pool=[];checks=0
    # Recipe index=(pose*4+reflection*2+parity)*3+tail.
    for pose,reflection,parity,tail in product(range(6),range(2),range(2),range(3)):
        ram=bytearray(128);ram[0x6e]=pose;ram[0x64]=60;ram[0x66]=24+parity;ram[0x6c]=reflection*8
        person=player(rom,bytes(ram));rows=[r for r in person['rows'] if 88<=r['y']<=106]
        colors=[];planes={};pixels={}
        for j,row in enumerate(rows+[rows[-1]]*tail):
            mask=row['pattern'];mask=int(f'{mask:08b}'[::-1],2)if reflection else mask
            if not mask:continue
            color=palette[row['color']]
            if color not in colors:colors.append(color);planes[color]={}
            planes[color][21+j]=mask
            for dx in range(8):
                if mask&(128>>dx):pixels[21+j,dx]=color
        if len(colors)>3:raise ValueError(('normal planes',pose,colors))
        top=min(y for y,x in pixels);bottom=max(y for y,x in pixels);cut=bottom-15
        # Earliest legal cut: both bands have <=3 entries and lower end=bottom.
        entries=[]
        for bandtop in (cut-16,cut):
            for color in colors:
                pat=bytearray(32)
                for row in range(16):
                    a,b=expand_pair(planes[color].get(bandtop+row,0),parity);pat[row]=a;pat[row+16]=b
                if any(pat):
                    if bytes(pat)not in pool:pool.append(bytes(pat))
                    entries.append((bandtop,color,pool.index(bytes(pat))))
        if len(entries)>6:raise ValueError('way capacity')
        if any(sum(e[0]==band for e in entries)>3 for band in (cut-16,cut)):raise ValueError('scanline bound')
        recipes.append(dict(pose=pose,reflection=reflection,parity=parity,tail=tail,cut=cut,entries=entries,pixels=pixels))
    # Independent model for every Y, both coarse variants and every declared selector.
    holds={57}|{base+n for base in(78,90,104,116,130,142,156,168)for n in(2,3)}
    for pose,reflection,parity,y,coarse in product(range(6),range(2),range(2),range(19,134),range(2)):
        if y<30 and coarse:continue
        tail=0
        while y+47+tail in holds:tail+=1
        ix=(pose*4+reflection*2+parity)*3+tail;recipe=recipes[ix]
        ram=bytearray(128);ram[0x6e]=pose;ram[0x64]=y;ram[0x66]=24+parity;ram[0x6c]=reflection*8
        person=player(rom,bytes(ram));want={}
        for row in person['rows']:
            assert row['update_x']<=22 and row['color_update_x']<=22 and row['suffix_x']>=91
            for dx in range(8):
                bit=dx if reflection else 7-dx
                if row['pattern']&(1<<bit):want[row['y']-7+int(coarse and row['y']>=57),dx]=palette[row['color']]
        actual={(y+coarse+dy,dx):color for(dy,dx),color in recipe['pixels'].items()}
        if want!=actual:raise ValueError(('pixels',pose,reflection,parity,y,coarse,tail))
        # Full sprite rectangles avoid logo at181+coarse even for phase0.
        assert max(y+coarse+e[0]+15 for e in recipe['entries'])<181+coarse
        checks+=1
    desc=bytearray()
    for r in recipes:
        row=bytes((len(r['entries']),r['cut']))+b''.join(bytes(e)for e in r['entries'])
        if len(row)>16:raise ValueError('descriptor16 capacity')
        desc.extend(row+bytes(16-len(row)))
    return bytes(desc),b''.join(pool),dict(recipe_count=len(recipes),pattern_count=len(pool),finite_checks=checks,domain='6 poses x 2reflection x 2parity x Y19..133; both coarse for Y30..133, coarse0 for shore19..29; X24..83 prefix/suffix proof',all_patterns_max=len(pool)-1,entries=sorted({len(r['entries'])for r in recipes}))
