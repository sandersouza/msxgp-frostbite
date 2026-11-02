"""Conservative source-kernel identity for translated ordinary player sprites."""


def template_key(ram,holds):
    if len(ram)!=128 or len(holds)!=135:raise ValueError('whole source RAM and visible kernel hold table required')
    y,x=ram[0x64],ram[0x66]
    if not 30<=y<=133 or not 0<=x<=83:return None
    tail=0
    while y+tail<135 and holds[y+tail]:tail+=1
    clip=(1<<x)-1 if x<8 else 255
    return bytes((ram[0x6E],ram[0x6B],ram[0x70],ram[0x6C]&8,x&1,clip,tail))
