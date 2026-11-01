"""Lossless bank-local indirection for complete 160-coordinate contact rows."""
from floe_tables import pointer


def put_row(packer,records):
    if (len(records)!=160 or any(not isinstance(row,(bytes,bytearray,memoryview)) or not row for row in records)
            or len({len(row) for row in records})!=1):
        raise ValueError('complete160-coordinate equal-sized nonempty records required')
    leaves=b''.join(pointer(packer.put(bytes(row))) for row in records)
    blocks=b''.join(pointer(packer.put(leaves[start:start+48])) for start in range(0,480,48))
    return packer.put(blocks)


def read_row(banks,first_bank,root,index,record_size):
    if type(index) is not int or not 0<=index<160 or type(record_size) is not int or not 1<=record_size<=16384:
        raise ValueError('declared source coordinate and bounded record size required')
    def read(location,size):
        bank,address=location
        if not first_bank<=bank<first_bank+len(banks) or not 0x8000<=address or address+size>0xC000:
            raise ValueError('bank-local collision pointer outside cartridge')
        offset=address-0x8000;data=banks[bank-first_bank]
        if offset+size>len(data):raise ValueError('collision pointer exceeds emitted bank bytes')
        return bytes(data[offset:offset+size])
    def decode(raw):return raw[2],int.from_bytes(raw[:2],'little')
    nodes=read(root,30);offset=index//16*3
    leaves=read(decode(nodes[offset:offset+3]),48);offset=index%16*3
    return read(decode(leaves[offset:offset+3]),record_size)
