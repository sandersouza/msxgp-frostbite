"""Lossless row-plane dictionary; preserve both six-byte physical owner keys."""


def pack(programs):
    if not programs or any(len(p)!=44 for p in programs):
        raise ValueError('complete44-byte programs required')
    pools=[[],[]];lookup=[{},{}];recipes=bytearray()
    for p in programs:
        keys=[p[32:38],p[38:44]]
        contexts={(k[2],k[4]) for k in keys if k!=bytes([255])*6}
        if len(contexts)>1:raise ValueError('one row context required')
        if any(k!=bytes([255])*6 and (k[3]!=0 or k[5]!=0 or k[:2]==b'\xff\xff') for k in keys):
            raise ValueError('unclipped valid physical keys required')
        recipes.extend(keys[0][:2]+keys[1][:2])
        for plane in range(4):
            group=plane//2;value=p[plane*8:plane*8+8]
            if value not in lookup[group]:
                lookup[group][value]=len(pools[group]);pools[group].append(value)
            if lookup[group][value]>255:raise ValueError('byte plane index overflow')
            recipes.append(lookup[group][value])
        recipes.extend(next(iter(contexts)) if contexts else (0,0))
    return dict(recipes=bytes(recipes),patterns=b''.join(pools[0]),colors=b''.join(pools[1]))


def unpack(data):
    recipes=data['recipes'];result=[]
    if len(recipes)%10 or len(data['patterns'])%8 or len(data['colors'])%8:
        raise ValueError('whole compact records/planes required')
    for at in range(0,len(recipes),10):
        row=recipes[at:at+10];p=bytearray()
        for i in range(4):
            pool=data['patterns' if i<2 else 'colors'];start=row[4+i]*8
            if start+8>len(pool):raise ValueError('plane outside dictionary')
            p.extend(pool[start:start+8])
        for i in range(2):
            key=row[i*2:i*2+2]
            p.extend(bytes([255])*6 if key==b'\xff\xff' else key+bytes((row[8],0,row[9],0)))
        result.append(bytes(p))
    return result
