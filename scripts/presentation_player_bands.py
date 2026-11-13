"""Pixel-identical P0 rectangle packing, with a bounded signed cache format."""
from itertools import combinations

def cache_delta(count,cut,start):
    if any(type(n)is not int for n in(count,cut,start))or not 1<=count<=6 or not 0<=cut<=255 or not 0<=start<=255:raise ValueError('bounded source-produced sprite cache entry required')
    delta=start-cut
    if not -128<=delta<=0 or count>=4 and delta not in(0,-16):raise ValueError('unsafe cache rectangle displacement')
    return delta&255

def _pixels(entries):
    result={};overlap=False
    for top,color,pattern in entries:
        for row in range(16):
            mask=pattern[row]*256+pattern[row+16]
            for x in range(16):
                if mask&(32768>>x):
                    at=(top+row,x)
                    if at in result and result[at]!=color:overlap=True
                    result.setdefault(at,color)
    return result,overlap

def pack_recipe(entries,cut):
    if not 1<=len(entries)<=6 or type(cut)is not int or any(type(y)is not int or type(c)is not int or not 0<=c<=15 or len(p)!=32 or not any(p)for y,c,p in entries):raise ValueError('complete bounded P0 recipe required')
    original,overlap=_pixels(entries);fallback=dict(packed=False,cut=cut,entries=entries)
    if overlap:return fallback
    order=[];rows={}
    for y,c,p in entries:
        if c not in rows:order.append(c);rows[c]={}
        for j in range(16):
            value=p[j]*256+p[j+16]
            if value:rows[c][y+j]=rows[c].get(y+j,0)|value
    spans={c:(min(row),max(row))for c,row in rows.items()}
    pairs=[(a,b)for a,b in combinations(order,2)if spans[a][1]<spans[b][0]or spans[b][1]<spans[a][0]]
    if len(order)>3 or any(last-first>=16 for first,last in spans.values())or len(order)>2 and not pairs:return fallback
    starts={c:bounds[0]for c,bounds in spans.items()}
    if pairs:
        a,b=max(pairs,key=lambda pair:abs(spans[pair[1]][0]-spans[pair[0]][1]));a,b=(a,b)if spans[a][1]<spans[b][0]else(b,a)
        starts[a]=spans[a][1]-15;starts[b]=spans[b][0]
    result=[]
    for color in order:
        pattern=bytearray(32);start=starts[color]
        for row in range(16):value=rows[color].get(start+row,0);pattern[row]=value>>8;pattern[row+16]=value&255
        result.append((start,color,bytes(pattern)))
    pixels,_=_pixels(result)
    if pixels!=original:raise ValueError('packed P0 raster changed')
    if max(sum(y<=line<y+16 for y,c,p in result)for line in range(min(starts.values()),max(starts.values())+16))>2:raise ValueError('packed P0 scanline bound exceeded')
    return dict(packed=True,cut=max(starts.values()),entries=result)

def normal_assets(base):
    from pathlib import Path
    import json,hashlib
    base=Path(base);meta=json.loads((base/'build.json').read_text());rom=(base/meta['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=meta['rom']['sha256']:raise ValueError('sealed parent ROM differs')
    def address(i):
        if i<64:return 149*16384+0x3800+i*32
        if i<109:return 148*16384+0x3a60+(i-64)*32
        if i<133:return 147*16384+0x3d00+(i-109)*32
        return 146*16384+0x3d80+(i-133)*32
    oldpool=[rom[address(i):address(i)+32]for i in range(137)];pool=[];descriptors=bytearray();checks=[]
    for i in range(72):
        at=146*16384+0x3900+i*16;record=rom[at:at+16];count,cut=record[:2]
        if not 1<=count<=6 or any(record[4+j*3]>=137 for j in range(count)):raise ValueError('normal P0 descriptor changed')
        old=[(record[2+j*3],record[3+j*3],oldpool[record[4+j*3]])for j in range(count)];new=pack_recipe(old,cut);encoded=[]
        for y,c,pattern in new['entries']:
            if pattern not in pool:pool.append(pattern)
            if not 0<=y<=255:raise ValueError('source-relative descriptor displacement exceeded byte')
            encoded.append((y,c,pool.index(pattern)))
        packet=bytes((len(encoded),new['cut']))+b''.join(bytes(e)for e in encoded)
        if len(packet)>16:raise ValueError('normal recipe capacity exceeded')
        descriptors.extend(packet+bytes(16-len(packet)));checks.append(dict(index=i,packed=new['packed'],old_count=count,new_count=len(encoded),cut=new['cut']))
    if len(pool)!=70 or not all(x['packed']and x['new_count']==3 for x in checks):raise ValueError('audited complete normal packing domain changed')
    return dict(descriptors=bytes(descriptors),patterns=b''.join(pool),pattern_count=len(pool),checks=checks)
