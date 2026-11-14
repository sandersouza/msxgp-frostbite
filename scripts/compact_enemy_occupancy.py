"""Exact66-group x16 horizontal x8 vertical occupancy matrix factorization."""


def pack(data):
    if len(data)!=8448:raise ValueError('complete66x16x8 matrix required')
    rows=[bytes(data[g*128+x*8+y] for x in range(16)) for g in range(66) for y in range(8)]
    unique=sorted(set(rows))
    if len(unique)>256:raise ValueError('byte directory cannot represent row domain')
    lookup={row:i for i,row in enumerate(unique)}
    return dict(directory=bytes(lookup[row] for row in rows),rows=b''.join(unique))


def unpack(data):
    directory=data['directory'];rows=data['rows']
    if len(directory)!=528 or not rows or len(rows)%16:raise ValueError('complete directory and phase rows required')
    if max(directory)*16+16>len(rows):raise ValueError('row outside dictionary')
    return bytes(rows[directory[g*8+y]*16+x] for g in range(66) for x in range(16) for y in range(8))
