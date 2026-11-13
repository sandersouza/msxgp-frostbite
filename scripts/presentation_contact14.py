"""Lossless 14-bit contact-record indices; no collision semantics change."""


def pack_block(values):
    if len(values) != 16 or any(type(v) is not int or not 0 <= v < 16384 for v in values):
        raise ValueError('sixteen uint14 record indices required')
    return sum(v << (14*i) for i,v in enumerate(values)).to_bytes(28,'little')


def read_field(raw, index):
    if len(raw) != 28 or type(index) is not int or not 0 <= index < 16:
        raise ValueError('complete uint14 block and field required')
    return int.from_bytes(raw,'little') >> (14*index) & 16383


def repack_bank(data,count,record_count):
    if len(data)!=16384 or type(count)is not int or not 1<=count<=512 or not 1<=record_count<=16384:
        raise ValueError('complete bank and bounded live block/record counts required')
    result=bytearray(data)
    result[:count*32]=b'\xff'*(count*32)
    for slot in range(count):
        raw=data[slot*32:slot*32+32]
        values=[int.from_bytes(raw[i:i+2],'little') for i in range(0,32,2)]
        if any(v>=record_count for v in values):raise ValueError('invalid original record index')
        result[slot*28:slot*28+28]=pack_block(values)
    return bytes(result)
