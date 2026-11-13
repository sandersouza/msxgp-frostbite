"""Independent source-packet ownership reconstruction for fixed ice roles."""


def decorate_owners(raw,records,tuples,colors,rom,deltas):
    if len(raw)!=4110 or len(records)!=32 or len(tuples)!=32 or len(colors)!=8 or len(deltas)!=10:
        raise ValueError('complete physical ownership and saved band identities required')
    result=bytearray(raw)
    for page in range(2):
        for row,(bank,base) in enumerate(((2,25),(2,9),(1,35),(1,19))):
            group=page*3+bank
            for slot in range(base,base+16):
                at=1536+(group*64+slot)*6
                if raw[at:at+6]!=b'\xff'*6:
                    raise ValueError('obsolete per-tile ice metadata was published')
            owner=page*4+row
            record=records[owner*4:owner*4+4]
            count=record[3]
            if not count:continue
            root,delta,phase,color=tuples[owner*4:owner*4+4]
            if not 1<=count<=14 or not 0<=root<16 or phase>=8 or delta not in deltas or not 1<=color<=15 or colors[owner]!=color:
                raise ValueError('invalid saved owner/count/tuple/color identity')
            index=(phase*10+deltas.index(delta))*16+root
            packet_bank=35+index//16;packet=packet_bank*16384+0x3800+index%16*128
            if bytes(record)!=rom[packet+112:packet+116]:
                raise ValueError('owner record differs from its exact source-derived packet')
            address=int.from_bytes(record[:2],'little');keybank=record[2]
            if not 0x8000<=address or address+count*2>0xC000 or keybank*16384+address-0x8000+count*2>len(rom):
                raise ValueError('invalid bank-local immutable raw-key pointer')
            data=rom[keybank*16384+address-0x8000:keybank*16384+address-0x8000+count*2]
            for slot in range(count):
                identifier=int.from_bytes(data[slot*2:slot*2+2],'little')
                if identifier>=2049:raise ValueError('raw key outside finite floe namespace')
                at=1536+(group*64+base+slot)*6
                result[at:at+6]=data[slot*2:slot*2+2]+bytes([130 if bank==1 else 129,0,color,9])
    return bytes(result)
