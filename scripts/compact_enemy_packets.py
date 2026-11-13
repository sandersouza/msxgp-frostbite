"""Reconstruct native1.5x enemy packets from eight source glyph rows."""


def packet(glyph,phase,reflection=False):
    if len(glyph)!=8 or any(type(v) is not int or not 0<=v<=255 for v in glyph):
        raise ValueError('eight byte rows required')
    if type(phase) is not int or not 0<=phase<16 or type(reflection) is not bool:
        raise ValueError('horizontal phase0..15 and Boolean reflection required')
    out=bytearray(24);origin=(phase*3//2)//8*8
    for row,value in enumerate(reversed(glyph)):
        for bit in range(8):
            if value&(1<<bit if reflection else 128>>bit):
                for x in range((phase+bit)*3//2,(phase+bit+1)*3//2):
                    col,shift=divmod(x-origin,8)
                    out[col*8+row]|=128>>shift
    return bytes(out)


def scatter(horizontal,vertical):
    if len(horizontal)!=24 or type(vertical) is not int or not 0<=vertical<8:
        raise ValueError('24-byte packet and vertical phase0..7 required')
    out=bytearray(48)
    for col in range(3):
        for row in range(8):
            y=row+vertical
            out[(y//8)*24+col*8+y%8]=horizontal[col*8+row]
    return bytes(out)
