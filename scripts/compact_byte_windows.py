"""Deterministic lossless overlap packing of immutable fixed-width byte windows.

This is an offline layout operation. Runtime reads literal bytes at an offset;
no decompression loop or route-based pruning is involved.
"""
from collections import defaultdict


def pack_windows(values):
    if not values or any(not isinstance(v,bytes) or not v for v in values):
        raise ValueError('nonempty byte windows required')
    width=len(values[0])
    if width>65536 or any(len(v)!=width for v in values):raise ValueError('one bounded fixed width required')
    unique=sorted(set(values));count=len(unique);parent=list(range(count));successor={};previous={};overlaps={}
    def root(index):
        while parent[index]!=index:
            parent[index]=parent[parent[index]];index=parent[index]
        return index
    # Each unique record gets at most one predecessor/successor. A union check
    # prevents cycles, so every chosen edge becomes a real retained substring.
    for length in range(width-1,0,-1):
        prefixes=defaultdict(list)
        for j,v in enumerate(unique):
            if j not in previous:prefixes[v[:length]].append(j)
        for i,v in enumerate(unique):
            if i in successor:continue
            for j in prefixes[v[-length:]]:
                if j in previous or root(i)==root(j):continue
                successor[i]=j;previous[j]=i;overlaps[i]=length;parent[root(j)]=root(i);break
    pool=bytearray()
    for i in range(count):
        if i in previous:continue
        pool.extend(unique[i])
        while i in successor:
            length=overlaps[i];i=successor[i];pool.extend(unique[i][length:])
    if len(pool)>65536:raise ValueError('pool exceeds16-bit offsets')
    offsets=bytearray()
    for value in values:
        at=pool.find(value)
        if not 0<=at<=65535:raise ValueError('packed window missing or unaddressable')
        offsets.extend(at.to_bytes(2,'little'))
    return dict(width=width,pool=bytes(pool),offsets=bytes(offsets))


def restore_windows(data):
    width=data['width'];pool=data['pool'];offsets=data['offsets']
    if not isinstance(width,int) or not 1<=width<=65536 or len(offsets)%2:raise ValueError('whole offsets and width required')
    result=[]
    for i in range(0,len(offsets),2):
        at=int.from_bytes(offsets[i:i+2],'little')
        if at+width>len(pool):raise ValueError('window outside packed pool')
        result.append(pool[at:at+width])
    return result


def bear_lookup(source):
    old='''    DUP 3
    ADD HL,HL
    EDUP
    LD DE,cb_patterns
    ADD HL,DE
'''
    new='''    ADD HL,HL
    LD BC,cw_directory
    ADD HL,BC
    LD C,(HL)
    INC HL
    LD B,(HL)
    LD HL,cw_pool
    ADD HL,BC
'''
    if source.count(old)!=1:raise ValueError('unique native bear mask lookup required')
    return source.replace(old,new,1)


def strip_lookup(source):
    old='''    DUP 3
    ADD HL,HL
    EDUP
    LD BC,cb_patterns
    ADD HL,BC
'''
    new='''    ADD HL,HL
    LD BC,cw_directory
    ADD HL,BC
    LD C,(HL)
    INC HL
    LD B,(HL)
    LD HL,cw_pool
    ADD HL,BC
'''
    if source.count(old)!=1:raise ValueError('unique native strip mask lookup required')
    return source.replace(old,new,1)
