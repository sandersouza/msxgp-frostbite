"""Decode local Frostbite tables. No original bytes or generated pixels in source."""
import hashlib

SOURCE_SHA256='cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834'


def view(rom, address, height, reflect=False, scale=1):
    if (len(rom)!=4096 or type(address) is not int or type(height) is not int
            or height<1 or address<0xF000 or address+height>0x10000 or scale not in (1,2)):
        raise ValueError('invalid table range or pixel scale')
    rows=rom[address-0xF000:address-0xF000+height][::-1]
    pixels=[]
    for row in rows:
        bits=[int(bool(row&(128>>x))) for x in range(8)]
        if reflect:bits.reverse()
        pixels.extend(value for value in bits for _ in range(scale))
    return {'range':[address,address+height-1],'width':8*scale,'height':height,
            'reflected':reflect,'pixels':pixels}


def catalog(rom):
    if len(rom)!=4096 or hashlib.sha256(rom).hexdigest()!=SOURCE_SHA256:
        raise ValueError('original ROM identity mismatch')
    read=lambda address:rom[address-0xF000]
    assets={}
    for pose in range(6):
        for reflect in (False,True):
            for displacement in range(19):
                address=0xFC00+read(0xFCAA+pose)+displacement
                item=view(rom,address,19,reflect)
                item['color_range']=[0xFC00+read(0xFCB0+pose)+displacement,
                                     0xFC00+read(0xFCB0+pose)+displacement+18]
                # The kernel masks CPY>=19, so terminal displacement reads the
                # following original bytes intentionally; these are table views.
                item['colors']=list(rom[item['color_range'][0]-0xF000:item['color_range'][1]-0xF000+1][::-1])
                assets[f'player-{pose}-{int(reflect)}-{displacement}']=item
    for frame in range(8):
        for reflect in (False,True):
            assets[f'bear-{frame}-{int(reflect)}']=view(rom,0xFD00+read(0xFEE7+frame),19,reflect,2)
    for kind in range(4):
        for phase in range(2):
            for sway in range(1 if kind==0 else 5):
                for reflect in (False,True):
                    item=view(rom,0xFD00+read(0xFD0A+kind*2+phase)+sway,8,reflect)
                    item['color']=read(0xFD00+kind)&254
                    assets[f'row-{kind}-{phase}-{sway}-{int(reflect)}']=item
    for digit in range(10):assets[f'digit-{digit}']=view(rom,0xFF00+digit*8,8)
    assets['blank']=view(rom,0xFF50,8)
    for part in range(11):assets[f'footer-{part}']=view(rom,0xFF68+part*8,8)
    return {'schema_version':1,'source_sha256':SOURCE_SHA256,'assets':assets,
            'raster_only':['floes/HMP1+HMM1 scanline shaping','igloo/PF1 construction',
                           'shore/sky color gradient','six-copy HUD placement'],
            'qualification':'Table views include controlled terminal offsets; reachability is not asserted.'}
