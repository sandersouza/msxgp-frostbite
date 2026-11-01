"""Exact visible-boundary reduction plus rejected raster research helpers.

This adapter is separate from the static gameplay translator. Its CPU/RAM
effects must match unmodified original F019→F476 execution. Collision catalog
bytes for the accepted path are original-clock literal-view observations.
The raster-only helpers below remain solely for rejected-model reproduction.
"""


def overlap(sprite,x,y,mask_rows,top,wrap=False):
    if any(len(row)!=20 for row in mask_rows):raise ValueError('160-pixel raster rows required')
    for offset,bits in enumerate(sprite):
        line=y+offset-top
        if not 0<=line<len(mask_rows):continue
        row=mask_rows[line]
        for bit in range(8):
            column=(x+bit)%160 if wrap else x+bit
            if bits&(128>>bit) and 0<=column<160 and row[column//8]&(128>>(column%8)):return True
    return False


def recover_masks(observed):
    """Recover HMOVE-hidden bits from the unblanked X64 reference.

    Every visible pixel at every X must first agree with the cyclic placement.
    Separate electrical collision probes must validate the recovered bits;
    visible agreement alone is not a collision acceptance claim.
    """
    controls={key[:2] for key in observed};expected={(*c,x) for c in controls for x in range(160)}
    if not controls or set(observed)!=expected:raise ValueError('all160 positions required per control pair')
    result={}
    for control in sorted(controls):
        reference=observed[(*control,64)]
        if len(reference)!=7 or any(len(row)!=20 or row[0] for row in reference):raise ValueError('unblanked seven-line reference required')
        for x in range(160):
            rows=[]
            for raw in reference:
                row=bytearray(20)
                for column in range(160):
                    if raw[column//8]&(128>>(column%8)):
                        target=(column+x-64)%160;row[target//8]|=128>>(target%8)
                rows.append(bytes(row))
            actual=observed[(*control,x)]
            if len(actual)!=7 or any(len(a)!=20 or a[0] or a[1:]!=b[1:] for a,b in zip(actual,rows)):
                raise ValueError('actual visible raster differs from exact cyclic placement')
            result[(*control,x)]=tuple(rows)
    return result


def player_rows(rom,ram):
    if len(rom)!=4096 or len(ram)!=128 or ram[0x6E]>=6 or ram[0x6B]>18:raise ValueError('invalid source player table view')
    start=0xC00+((rom[0xCAA+ram[0x6E]]+ram[0x6B])&255)
    rows=bytes(rom[start:start+19])[::-1]
    if ram[0x6C]&8:rows=bytes(int(f'{v:08b}'[::-1],2) for v in rows)
    return rows


def visible_state(rom,ram,registers,contacts):
    if (len(rom)!=4096 or len(ram)!=128 or registers.get('sp',255)!=255 or registers.get('p',0x30)&8
            or len(contacts.get('rows',b''))!=8 or not 0<=contacts.get('shore',-1)<=255):
        raise ValueError('visible boundary requires full RAM, D0/SPFF and complete window samples')
    r=bytearray(ram)
    if r[0x45]&128:r[0x53]=r[0x4D];r[0x1E]=0
    night=bool(r[0x45]&128 or r[0x4B]&4)
    r[0x3B]=128 if night else 132;r[0x3C]=2 if night else 10;r[0x3D]=12 if night else 4
    door=0
    if r[0x4D]==15:
        if not r[0x45]&128 and not r[0x4B]&4:door=0
        elif not (r[1]^r[2])&8:door=56
    else:door=r[0x3C]
    r[0x3E]=door
    if r[0x4B]<3:r[0x3D]=r[0x3C]
    r[5:17]=bytes(value for low in range(0x90,0xC0,8) for value in (low,255))
    r[0x30:0x38]=contacts['rows'];r[0x38:0x3A]=b'\xff\xff';r[0x3A]=0
    if contacts['shore']&128:r[0x6D]=contacts['shore']
    r[0x78]=rom[0xFB8];r[0x79:0x7B]=b'\xff\xff';r[0x7E:0x80]=b'\x30\xf4'
    phase=r[0x46]&31
    phase=0 if phase<12 else phase-12 if phase<20 else 7
    return {'ram':bytes(r),'registers':{'a':0,'x':rom[0xF88+phase],'y':(phase-1)&255,
            'p':(registers.get('p',0x30)&0x3C)|0x81,'sp':255}}


def floe_contacts(rom,ram,catalog):
    """REJECTED raster-only candidate; never use for runtime or acceptance."""
    sprite=player_rows(rom,ram);result=bytearray([7]*8)
    control=(ram[0x1C],ram[0x1D])
    for row in range(4):
        x=ram[0x1F+row]
        if not 0<=x<160:raise ValueError('floe source X outside canonical0..159')
        mask=catalog[(*control,x)]
        if overlap(sprite,ram[0x66],ram[0x64]+28,mask,174-row*26):result[row*2]|=128
    return bytes(result)
