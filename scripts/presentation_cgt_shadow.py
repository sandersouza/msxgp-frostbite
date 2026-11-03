"""Independent proof that retained constant CGT slots match physical VRAM."""


def audit(shadow,vram):
    if len(shadow)!=384 or len(vram)!=16384:raise ValueError('whole six-bank colour shadow and16KiB VRAM required')
    known=0
    for index,pair in enumerate(shadow):
        if pair==255:continue
        group,slot=divmod(index,64);bank=group%3;generation=group//3
        address=0x2000+bank*2048+(slot+generation*64)*8
        if vram[address:address+8]!=bytes([pair])*8:raise ValueError(f'constant colour shadow differs from physical CGT at group{group} slot{slot}')
        known+=1
    return known
