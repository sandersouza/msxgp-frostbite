"""Exact two-channel contacts in typed slots and sparse coordinate blocks.

Only a proven uniform bit6 channel is scalarized, separately in each record.
No vertical/horizontal or glyph equivalence is assumed. Both channels are
reconstructed byte-exactly by the independent packed-image reader below.
"""
from floe_tables import BankPacker
from floe_truth import validate_row

SHADOW_ON=bytes([255])*28+b'\x0f'


def encode_record(row):
    validate_row(row);shadow=bytes(row[29:])
    if shadow not in (bytes(29),SHADOW_ON):raise ValueError('view-dependent shadow cannot use uniform record encoding')
    return bytes(row[:29])+bytes([64 if shadow==SHADOW_ON else 0])


def decode_record(data):
    if len(data)!=30 or data[29] not in (0,64):raise ValueError('complete exact compact contact record required')
    result=bytes(data[:29])+(SHADOW_ON if data[29] else bytes(29));validate_row(result)
    return result


class CompactRows:
    def __init__(self):
        self.records=[bytes(30)];self.record_ids={bytes(30):0}
        self.blocks=[];self.block_ids={};self.rows=[];self.row_ids={}

    def intern_row(self,records):
        if len(records)!=160 or any(not isinstance(row,(bytes,bytearray,memoryview)) for row in records):
            raise ValueError('complete160-coordinate original contact row required')
        return self.intern_indices([self.intern_record(row) for row in records])

    def intern_record(self,row):
        data=encode_record(row)
        if data not in self.record_ids:
            if len(self.records)>=65536:raise ValueError('compact record index overflow')
            self.record_ids[data]=len(self.records);self.records.append(data)
        return self.record_ids[data]

    def intern_indices(self,ids):
        if len(ids)!=160 or any(type(value) is not int or not 0<=value<len(self.records) for value in ids):
            raise ValueError('complete160-coordinate row of existing exact record IDs required')
        bitmap=0;references=bytearray()
        for index in range(10):
            values=ids[index*16:(index+1)*16]
            if not any(values):continue
            data=b''.join(value.to_bytes(2,'little') for value in values)
            if data not in self.block_ids:
                if len(self.blocks)>=65536:raise ValueError('compact block index overflow')
                self.block_ids[data]=len(self.blocks);self.blocks.append(data)
            bitmap|=1<<index;references.extend(self.block_ids[data].to_bytes(2,'little'))
        node=bitmap.to_bytes(2,'little')+references
        if node not in self.row_ids:self.row_ids[node]=len(self.rows);self.rows.append(node)
        return self.row_ids[node]

    def emit(self,first_bank=14):
        if not self.rows or type(first_bank) is not int or not 0<=first_bank<=255:
            raise ValueError('nonempty compact table and physical first bank required')
        return PackedRows(first_bank,self.records,self.blocks,self.rows)


class PackedRows:
    def __init__(self,first_bank,records,blocks,rows):
        self.pools=[]
        def slots(values):
            for offset in range(0,len(values),512):
                bank=bytearray([255])*16384
                for index,data in enumerate(values[offset:offset+512]):bank[index*32:index*32+len(data)]=data
                self.pools.append(bank)
        slots(records);block_bank=first_bank+len(self.pools);slots(blocks)
        tree_bank=first_bank+len(self.pools)
        if tree_bank>255:raise ValueError('compact pools exceed ASCII16 bank range')
        self.tree=BankPacker(tree_bank);self.rows=[self.tree.put(row) for row in rows]
        self.metadata={'first_bank':first_bank,'record_bank':first_bank,'record_count':len(records),
                       'block_bank':block_bank,'block_count':len(blocks),'tree_bank':tree_bank}

    @property
    def banks(self):
        return [*self.pools,*self.tree.banks]

    def put(self,data):
        return self.tree.put(data)


def read_row(banks,metadata,root,index):
    """Read actual bank bytes, without consulting compiler dictionaries."""
    if type(index) is not int or not 0<=index<160:raise ValueError('source coordinate outside0..159')
    first=metadata['first_bank']
    def read(location,size):
        bank,address=location
        if not first<=bank<first+len(banks) or not 0x8000<=address or address+size>0xC000:
            raise ValueError('compact pointer outside bank-local cartridge bytes')
        offset=address-0x8000;data=banks[bank-first]
        if offset+size>len(data):raise ValueError('compact pointer exceeds emitted bank data')
        return bytes(data[offset:offset+size])
    def slot(kind,number):
        if not 0<=number<metadata[kind+'_count']:raise ValueError('compact slot index outside emitted pool')
        return read((metadata[kind+'_bank']+number//512,0x8000+(number%512)*32),32)
    if root[0]<metadata['tree_bank']:raise ValueError('compact row pointer is not in the tree pool')
    bitmap=int.from_bytes(read(root,2),'little')
    if bitmap&~1023:raise ValueError('compact row bitmap has undefined coordinates')
    bit=index//16
    if not bitmap&(1<<bit):return bytes(58)
    node=read(root,2+2*bitmap.bit_count());rank=(bitmap&((1<<bit)-1)).bit_count()
    block=int.from_bytes(node[2+rank*2:4+rank*2],'little')
    references=slot('block',block);offset=index%16*2
    record=int.from_bytes(references[offset:offset+2],'little')
    return decode_record(slot('record',record)[:30])
