"""Exact typed tile-constructor grammar: five payload bytes plus a type byte.

This is a presentation oracle, never native gameplay or whole-frame playback.
"""
LITERAL_ROWS={1:((0,0),(7,1)),2:((0,1),(1,1),(7,0)),3:((0,1),(6,0),(7,0))}
HEADER_PARTS=((0,None),(1,2),(3,None),(4,0),(4,None))


def value(number,low,high):
    if type(number)is not int or not low<=number<=high:raise ValueError('constructor argument outside declared domain')
    return number


def word(number):return value(number,0,16383).to_bytes(2,'little')


def mono_key(pattern,background,color,clip=False):
    if type(clip)is not bool:raise ValueError('explicit source viewport clip required')
    return word(pattern)+bytes((value(background,128,255),int(clip),value(color,1,15),0))


def floe_key(pattern,background,color):
    return word(pattern)+bytes((value(background,128,255),0,value(color,1,15),9))


def union_key(first,second,color,clip=False):
    if type(clip)is not bool:raise ValueError('explicit source viewport clip required')
    return word(first)+word(second)+bytes((value(color,1,15)*16+4,8 if clip else 7))


def literal_key(masks,object_color,floe_color,kind):
    if kind not in LITERAL_ROWS or len(masks)!=3 or kind==1 and masks[2]:raise ValueError('declared shared-row geometry required')
    return bytes(value(v,0,255) for v in masks)+bytes((value(object_color,1,15)*16+value(floe_color,1,15),0,kind))


def header_key(glyphs,score_color,status_color,background,column,band):
    if len(glyphs)!=4:raise ValueError('both source glyph pairs required')
    ids=[value(v,0,33) for v in glyphs]
    score_color=value(score_color,1,15);status_color=value(status_color,1,15)
    background=value(background,1,15);column=value(column,0,4);band=value(band,0,2)
    if column in (0,2,4):ids[1]=ids[3]=0
    if band==0:ids[2]=ids[3]=0;status_color=0
    if band==2:ids[0]=ids[1]=0;score_color=0
    packed=sum(n<<(index*6) for index,n in enumerate(ids))
    return packed.to_bytes(3,'little')+bytes((score_color+status_color*16,background+column*16,16+band))


def header_fields(key):
    if len(key)!=6 or key[5] not in (16,17,18):raise ValueError('typed header key required')
    packed=int.from_bytes(key[:3],'little');ids=tuple((packed>>(i*6))&63 for i in range(4))
    if any(v>=34 for v in ids) or key[4]>>4>=5:raise ValueError('unknown header glyph or fragment class')
    return ids,key[3]&15,key[3]>>4,key[4]&15,key[4]>>4,key[5]-16


def igloo_key(top,bottom,background):
    return bytes((value(top,0,255),value(bottom,0,255),value(background,128,255),14,0,5))


def footer_key(tile):
    return value(tile,0,65535).to_bytes(2,'little')+bytes((0,0,0,6))


def merge(background,mask,color):
    if len(background)!=16 or len(mask)!=8:raise ValueError('whole background and source mask required')
    result=bytearray(background)
    for y,m in enumerate(mask):
        if not m:continue
        p=result[y];a,b=result[y+8]>>4,result[y+8]&15
        if color==a:result[y]=p|m
        elif color==b:result[y]=p&~m
        elif a==b or not p&~m:result[y]=m;result[y+8]=color*16+b
        elif not (~p)&(~m)&255:result[y]=m;result[y+8]=color*16+a
        else:raise ValueError('constructor would require three actual colors in a row')
    return bytes(result)


def construct(key,*,patterns,backgrounds,header,footer,floe_patterns=None):
    if len(key)!=6:raise ValueError('whole typed constructor key required')
    kind=key[5]
    if kind==9:
        index=int.from_bytes(key[:2],'little')
        if (key[3] or not 1<=key[4]<=15 or index>=16384 or floe_patterns is None or index>=len(floe_patterns)
            or backgrounds.get(key[2])!=bytes([255])*8+bytes([68])*8):raise ValueError('invalid raw floe constructor or namespace')
        mask=floe_patterns[index]
        if len(mask)!=8:raise ValueError('complete raw floe mask required')
        return bytes(mask)+bytes([key[4]*16+4])*8
    def pattern(at):
        index=int.from_bytes(key[at:at+2],'little')
        if index>=16384:raise ValueError('unknown pattern')
        data=patterns[index]
        if len(data)!=8:raise ValueError('whole pattern required')
        return data
    if kind==0:
        if key[3] not in (0,1) or not 1<=key[4]<=15:raise ValueError('invalid monochrome constructor')
        mask=pattern(0)
        if key[3]:mask=bytes(v&15 for v in mask)
        if backgrounds[key[2]]==bytes([255])*8+bytes([68])*8:
            return mask+bytes([key[4]*16+4])*8
        return merge(backgrounds[key[2]],mask,key[4])
    if kind in (7,8):
        if key[4]&15!=4:raise ValueError('union belongs to the original water background')
        mask=bytes(a|b for a,b in zip(pattern(0),pattern(2)))
        if kind==8:mask=bytes(v&15 for v in mask)
        return mask+bytes((key[4],))*8
    if kind in LITERAL_ROWS:
        if key[4] or kind==1 and key[2]:raise ValueError('invalid literal constructor')
        result=bytearray(bytes(8)+bytes((68,))*8);colors=(key[3]>>4,key[3]&15)
        for index,(row,color) in enumerate(LITERAL_ROWS[kind]):result[row]=key[index];result[row+8]=colors[color]*16+4
        return bytes(result)
    if kind==5:
        if key[3]!=14 or key[4]:raise ValueError('invalid igloo constructor')
        return merge(backgrounds[key[2]],bytes((key[0],))*4+bytes((key[1],))*4,14)
    if kind==6:
        if any(key[2:5]):raise ValueError('invalid footer constructor')
        result=footer[int.from_bytes(key[:2],'little')]
        if len(result)!=16:raise ValueError('whole footer tile required')
        return result
    if kind in (16,17,18):
        ids,upper,lower,bg,column,band=header_fields(key)
        if len(header)!=1360:raise ValueError('whole34-glyph/5-fragment header pool required')
        first,second=HEADER_PARTS[column]
        def row(pair,source):
            result=header[pair[0]*40+first*8+source]
            if second is not None:result|=header[pair[1]*40+second*8+source]
            return result
        result=bytearray(bytes(8)+bytes((bg*17,))*8)
        if band==0:
            for y in range(5):result[y+3]=row(ids[:2],y);result[y+11]=upper*16+bg
        elif band==1:
            for y in range(3):result[y]=row(ids[:2],y+5);result[y+8]=upper*16+bg
            result[7]=row(ids[2:],0);result[15]=lower*16+bg
        else:
            for y in range(7):result[y]=row(ids[2:],y+1);result[y+8]=lower*16+bg
        return bytes(result)
    raise ValueError('unknown typed constructor')
