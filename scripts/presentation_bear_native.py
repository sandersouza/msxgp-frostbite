"""Lossless prepared bear packets and exact uniform-background byte constructor."""

def raw_pattern(rom,banks,halves,identifier,count):
    if type(identifier)is not int or not 0<=identifier<count:raise ValueError('logical pattern outside declared namespace')
    def read(at,size):
        bank=at//16384
        if bank>=len(banks)or at%16384+size>16384:raise ValueError('cross-bank logical read')
        start=banks[bank]*16384+at%16384;data=rom[start:start+size]
        if len(data)!=size:raise ValueError('incomplete actual asset ROM')
        return data
    pair=read(identifier*4,4)
    return b''.join(read(halves+int.from_bytes(pair[i:i+2],'little')*4,4)for i in(0,2))

def prepared_packet(columns,rows,ids,indexes,strips=None):
    if columns not in(3,4)or rows!=3 or len(ids)!=columns*rows or len(indexes)!=len(ids)or any(len(x)!=9 for x in indexes):raise ValueError('complete geometry and nine context indexes required')
    data=bytearray()
    for identifier,tiles in zip(ids,indexes):
        if not 0<=identifier<16384 or any(not 0<=n<65536 for n in tiles):raise ValueError('bounded logical/tile IDs required')
        data.extend(identifier.to_bytes(2,'little'));data.extend(b''.join(n.to_bytes(2,'little')for n in tiles))
    if strips is None:strips=(65535,)*6
    if len(strips)!=6 or any(not 0<=n<65536 for n in strips):raise ValueError('six bounded row-strip indexes required')
    return bytes(data)+bytes(240-len(data))+bytes((columns,rows,columns*rows*2))+b''.join(n.to_bytes(2,'little')for n in strips)+bytes(1)


def row_strip(tiles):
    if len(tiles)!=4 or any(len(t)!=16 for t in tiles):raise ValueError('four complete PGT/CGT tiles required')
    return b''.join(t[:8]for t in tiles)+b''.join(t[8:]for t in tiles)
