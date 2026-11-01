"""Original-free renderer workload, table generator and independent pixel oracle.

Synthetic masks are not extracted Frostbite graphics. Collision/game RAM is not
part of this presentation ABI. Original asset integration must remeasure it.
"""
from functools import lru_cache

BAND_Y=((80,88,104,112,136,144,160,168),(80,88,104,124,136,144,160,168))
PLAYER_COLORS=(6,7,15)
FONT={
 'A':('01110','10001','10001','11111','10001','10001','10001'),
 'B':('11110','10001','10001','11110','10001','10001','11110'),
 'C':('01111','10000','10000','10000','10000','10000','01111'),
 'D':('11110','10001','10001','10001','10001','10001','11110'),
 'E':('11111','10000','10000','11110','10000','10000','11111'),
 'F':('11111','10000','10000','11110','10000','10000','10000'),
 'G':('01111','10000','10000','10111','10001','10001','01111'),
 'H':('10001','10001','10001','11111','10001','10001','10001'),
 'I':('11111','00100','00100','00100','00100','00100','11111'),
 'J':('00111','00010','00010','00010','10010','10010','01100'),
 'K':('10001','10010','10100','11000','10100','10010','10001'),
 'L':('10000','10000','10000','10000','10000','10000','11111'),
 'M':('10001','11011','10101','10101','10001','10001','10001'),
 'N':('10001','11001','10101','10011','10001','10001','10001'),
 'O':('01110','10001','10001','10001','10001','10001','01110'),
 'P':('11110','10001','10001','11110','10000','10000','10000'),
 'Q':('01110','10001','10001','10001','10101','10010','01101'),
 'R':('11110','10001','10001','11110','10100','10010','10001'),
 'S':('01111','10000','10000','01110','00001','00001','11110'),
 'T':('11111','00100','00100','00100','00100','00100','00100'),
 'U':('10001','10001','10001','10001','10001','10001','01110'),
 'V':('10001','10001','10001','10001','10001','01010','00100'),
 'W':('10001','10001','10001','10101','10101','11011','10001'),
 'X':('10001','10001','01010','00100','01010','10001','10001'),
 'Y':('10001','10001','01010','00100','00100','00100','00100'),
 'Z':('11111','00001','00010','00100','01000','10000','11111'),
 '0':('01110','10001','10011','10101','11001','10001','01110'),
 '1':('00100','01100','00100','00100','00100','00100','01110'),
 '2':('01110','10001','00001','00010','00100','01000','11111'),
 '3':('11110','00001','00001','01110','00001','00001','11110'),
 '4':('00010','00110','01010','10010','11111','00010','00010'),
 '5':('11111','10000','10000','11110','00001','00001','11110'),
 '6':('01110','10000','10000','11110','10001','10001','01110'),
 '7':('11111','00001','00010','00100','01000','01000','01000'),
 '8':('01110','10001','10001','01110','10001','10001','01110'),
 '9':('01110','10001','10001','01111','00001','00001','01110')}
GLYPHS='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def display_x(x):return 8+(3*x)//2


def scene(x=0):
    return {'floes':[(x+row*17)%160 for row in range(4)],
        'threats':[(x+row*29)%160 for row in range(4)],'colors':[(x+row)%2 for row in range(4)],
        'kinds':[(x+row)%3 for row in range(4)],'counts':[3]*4,'spacing':[x%2]*4,
        'player_x':x,'player_y':48,'bear_x':min(x,151),'bear_y':48,
        'palette':x%2,'igloo':x%4,'width':x%2,'layout':(x//8)%2}


def encode_scene(s):
    result=[]
    for name,limit in (('floes',159),('threats',159),('colors',1),('kinds',2),('counts',3),('spacing',1)):
        values=s[name]
        if not isinstance(values,list) or len(values)!=4 or any(type(v) is not int or not 0<=v<=limit for v in values):
            raise ValueError(f'invalid renderer {name}')
        result+=values
    for name,limit in (('player_x',159),('player_y',191),('bear_x',151),('bear_y',191),
                       ('palette',1),('igloo',3),('width',1),('layout',1)):
        value=s[name]
        if type(value) is not int or not 0<=value<=limit:raise ValueError(f'invalid renderer {name}')
        result.append(value)
    return bytes(result)


def vram_regions():
    return {'patterns':(0,6144),'name0':(0x1800,768),'sat':(0x1B00,128),
            'name1':(0x1C00,768),'colors':(0x2000,6144),'sprites':(0x3800,2048)}


def schedule(frames,period):
    if type(frames) is not int or frames<0 or period not in (59736,71364):raise ValueError('unsupported pacing contract')
    return [((i+1)*period)//59736-(i*period)//59736 for i in range(frames)]


def mask(kind,x,y):
    if kind<2:
        width=16 if kind==0 else 8
        return max(0,3-y//2)<=x<width-max(0,y-5) and 0<=y<8
    if not 0<=x<8 or not 0<=y<8:return False
    if kind==2:return abs(2*x-7)+abs(2*y-7)<=10
    if kind==3:return (2<=y<=5 and 1<=x<=6) or (y in (1,6) and x in (0,2,5,7))
    return y in (3,4) or (y==2 and x in (0,1,6,7)) or (y==5 and x in (2,5))


@lru_cache(maxsize=1)
def phase_tables():
    data=bytearray()
    for kind in range(5):
        for phase in range(16):
            left=(3*phase)//2;offset=left%8
            for shift in (0,2,4,6):
                bits=[[0]*32 for _ in range(16)]
                for y in range(8):
                    for x in range(16 if kind==0 else 8):
                        if mask(kind,x,y):
                            for dx in range((3*(phase+x))//2-left+offset,(3*(phase+x+1))//2-left+offset):
                                bits[y+shift][dx]=1
                for ty in range(2):
                    for tx in range(4):
                        for y in range(8):
                            data.append(sum(bits[ty*8+y][tx*8+x]<<(7-x) for x in range(8)))
    return bytes(data)


def player_bit(layer,x,y):
    if layer==0:return 1<=y<=5 and 2<=x<=5
    if layer==1:return 6<=y<=12 and 1<=x<=6
    return (13<=y<=18 and x in (1,2,5,6)) or (y==18 and 0<=x<8)


def bear_bit(x,y):return (5<=y<=13 and 1<=x<=7) or (2<=y<=8 and 0<=x<=3) or (14<=y<=18 and x in (1,2,5,6))


def sprite_block(kind,layer,origin,segment):
    pixels=[[False]*16 for _ in range(16)];base=(3*origin)//2
    for y in range(16):
        for x in range(8):
            bit=player_bit(layer,x,y+segment*16) if kind=='player' else bear_bit(x,y+segment*16)
            if bit and origin+x<160:
                for dx in range((3*(origin+x))//2-base,(3*(origin+x+1))//2-base):pixels[y][dx]=True
    # TMS16x16: top-left,bottom-left,top-right,bottom-right.
    return bytes(sum(int(pixels[y][half*8+x])<<(7-x) for x in range(8)) for half in range(2) for y in range(16))


@lru_cache(maxsize=1)
def sprite_patterns():
    data=bytearray()
    for origin in (0,1,*range(152,160)):
        for segment in range(2):
            for layer in range(3):data+=sprite_block('player',layer,origin,segment)
    for origin in (0,1):
        for segment in range(2):data+=sprite_block('bear',0,origin,segment)
    return bytes(data)


def sprite_attributes(s):
    encode_scene(s);data=bytearray();x=s['player_x'];variant=x%2 if x<=151 else x-150
    for segment in range(2):
        for layer,color in enumerate(PLAYER_COLORS):
            data+=bytes(((s['player_y']+segment*16-1)&255,display_x(x),4*(variant*6+segment*3+layer),color))
    for segment in range(2):
        data+=bytes(((s['bear_y']+segment*16-1)&255,display_x(s['bear_x']),4*(60+(s['bear_x']%2)*2+segment),15))
    return bytes(data+b'\xD0')


def occupancy(sat):
    result=[0]*192
    for offset in range(0,len(sat)-3,4):
        y=sat[offset]
        if y==208:break
        top=(y+1)&255
        for line in range(top,min(top+16,192)):result[line]+=1
    return result


def all_sprite_peak():return 3+3+3+1  # ice+threat copies, player colors, bear


@lru_cache(maxsize=1)
def static_patterns():
    patterns=bytearray(512);colors=bytearray(512)
    patterns[8:32]=bytes([255])*24
    colors[8:16]=bytes([0xE0])*8;colors[16:24]=bytes([0xF0])*8;colors[24:32]=bytes([0x50])*8
    for index,char in enumerate(GLYPHS,16):
        patterns[index*8:index*8+8]=bytes([int(row,2)<<2 for row in FONT[char]]+[0])
        colors[index*8:index*8+8]=bytes([0xF0])*8
    return bytes(patterns),bytes(colors)


def text(names,row,column,value):
    for index,char in enumerate(value):names[row*32+column+index]=16+GLYPHS.index(char) if char in GLYPHS else 0


def static_names(s):
    names=bytearray(768)
    names[3*32:8*32]=bytes([1])*(5*32)
    text(names,0,1,'FROSTBITE RENDER BENCH')
    text(names,1,1,'SYNTHETIC NO GAMEPLAY')
    text(names,2,1,'ARROWS MOVE SPACE CHANGES')
    text(names,1,27,f'{s["player_x"]:02X}')
    text(names,1,30,str(s['palette']))
    for y in range(4):
        for x in range(8):
            fill=(y*8+x)<s['igloo']*11
            names[(3+y)*32+22+x]=2 if fill else 1
    if s['igloo']==3:names[6*32+25:6*32+27]=bytes([3,3])
    return bytes(names)


def background_pixels(s):
    encode_scene(s);water=4 if not s['palette'] else 1;pixels=bytearray([water])*(256*192)
    patterns,colors=static_patterns();names=static_names(s)
    for y in range(64):
        for x in range(256):
            tile=names[(y//8)*32+x//8];index=tile*8+y%8
            color=colors[index]>>(4 if patterns[index]&(128>>(x%8)) else 0)&15
            pixels[y*256+x]=color or water
    # Independent source-pixel placement; never consumes phase/cache/name tables.
    for band,y0 in enumerate(BAND_Y[s['layout']]):
        row=band//2;ice=band%2
        kind=s['width'] if ice else 2+s['kinds'][row]
        origin=s['floes' if ice else 'threats'][row]
        count=3 if ice else s['counts'][row];gap=32 if ice or s['spacing'][row] else 16
        color=(5 if s['colors'][row] else 15) if ice else 10+s['kinds'][row]
        for copy in range(count):
            root=(origin+copy*gap)%160
            for sy in range(8):
                for sx in range(16 if kind==0 else 8):
                    if root+sx<160 and mask(kind,sx,sy):
                        for dx in range(display_x(root+sx),display_x(root+sx+1)):
                            pixels[(y0+sy)*256+dx]=color
    return pixels


def cache_base(layout,page,band):return 64+(band%4)*32+layout*16+page*8


def cache_segments(layout,page,band):
    y=BAND_Y[layout][band];base=cache_base(layout,page,band);shift=y%8;segments=[]
    for column in range(4):
        address=(y//64)*2048+(base+column)*8+shift
        segments.append((address,8-shift,column*8+shift))
        if shift:
            address=((y+7)//64)*2048+(base+4+column)*8
            segments.append((address,shift,32+column*8))
    return segments


def decode_pixels(vram,regs):
    if len(vram)!=16384 or len(regs)!=8 or regs[0]&2!=2 or regs[1]&3!=2:
        raise ValueError('exact16KiB SCREEN2/16x16 unmagnified state required')
    water=regs[7]&15;names=(regs[2]&15)*1024;pixels=bytearray(256*192)
    for y in range(192):
        bank=(y//64)*2048
        for column in range(32):
            tile=vram[names+(y//8)*32+column];index=bank+tile*8+y%8
            bits=vram[index];color=vram[0x2000+index]
            for bit in range(8):
                value=(color>>(4 if bits&(128>>bit) else 0))&15
                pixels[y*256+column*8+bit]=value or water
    sprites=[];sat=(regs[5]&127)*128;spt=(regs[6]&7)*2048
    for offset in range(0,128,4):
        sy,sx,pattern,color=vram[sat+offset:sat+offset+4]
        if sy==208:break
        sprites.append(((sy+1)&255,sx-32 if color&128 else sx,pattern&252,color&15))
    for sy,sx,pattern,color in reversed(sprites):
        if not color:continue
        for y in range(min(16,192-sy)):
            for x in range(16):
                if 0<=sx+x<256 and vram[spt+pattern*8+(x//8)*16+y]&(128>>(x%8)):
                    pixels[(sy+y)*256+sx+x]=color
    return pixels


def expected_pixels(s):
    pixels=background_pixels(s)
    # Lower SAT index wins. Paint bear first, then player in reverse priority.
    for actor in ('bear','player'):
        origin=s[actor+'_x'];top=s[actor+'_y']
        for layer in (range(2,-1,-1) if actor=='player' else (0,)):
            color=PLAYER_COLORS[layer] if actor=='player' else 15
            for sy in range(min(19,192-top)):
                for sx in range(8):
                    bit=player_bit(layer,sx,sy) if actor=='player' else bear_bit(sx,sy)
                    if bit and origin+sx<160:
                        for dx in range(display_x(origin+sx),display_x(origin+sx+1)):pixels[(top+sy)*256+dx]=color
    return pixels
