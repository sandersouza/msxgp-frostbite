"""Physical actor transactions and independent geometry normalization."""


def declare_ram(text):
    """Only the declared 128-byte Q region is removed from the inherited guard."""
    read='debug read_block memory 0xE800 0xB40'
    write='debug write_block memory 0xE800 [string repeat [binary format c 165] 0xB40]'
    if text.count(read)!=1 or text.count(write)!=1 or text.count('0xB40')!=3:
        raise ValueError('unrecognized inherited heap guard')
    return text.replace(read,'debug read_block memory 0xE880 0xAC0').replace(write,
        'debug write_block memory 0xE880 [string repeat [binary format c 165] 0xAC0]').replace('0xB40','0xAC0')


def segments(page,lane):
    if page not in (0,1) or lane not in range(4):raise ValueError('valid page/lane required')
    roles=(((2,3),(2,6)),((1,16),(2,0)),((1,10),(1,13)),((1,4),(1,7)))
    return [dict(bank=b,tile=t+page*64,pgt=0x4000+b*2048+(t+page*64)*8,
                 key=0xd000+(page*3+b)*384+t*6,water=130 if b==1 else 129)
            for b,t in roles[lane]]


def normalized_keys(ids,columns,rows,lane,coarse):
    if (columns not in (1,2,3) or rows not in (1,2) or len(ids)!=columns*rows
            or lane not in range(4) or coarse not in (0,1)
            or any(type(i)is not int or not 0<=i<16384 for i in ids)):
        raise ValueError('bounded complete descriptor grid required')
    result=[ids[r*columns+c] if r<rows and c<columns else 0 for r in range(2) for c in range(3)]
    if lane==1 and coarse:
        if rows!=1:raise ValueError('Y128 actor has exactly one source tile row')
        result=[0,0,0]+result[:3]
    return result


def resident_geometry(rom,symbols):
    """Use the live compact ROM directory; the archived pool has older offsets."""
    def directory(address,size):
        if not 0x8000<=address<address+size<=0xc000:raise ValueError('invalid bank1 directory')
        at=16384+address-0x8000
        return rom[at:at+size]
    roots=directory(symbols['p_geo_row_roots_data'],66*3)
    data=directory(symbols['p_geo_classes_data'],symbols['p_geo_class_count']*8)
    classes=[]
    for i in range(0,len(data),8):
        c=data[i:i+8]
        classes.append(dict(columns=c[0],rows=c[1],stride=c[2],count=int.from_bytes(c[3:5],'little'),offset=int.from_bytes(c[5:8],'little')))
    return dict(roots={'row':[list(roots[i:i+3]) for i in range(0,len(roots),3)]},classes=classes,patterns=symbols['p_geo_pattern_count'])


def decorate_actor_owners(raw,caches,rom,geometry):
    """Rebuild typed actor keys independently from immutable source descriptors."""
    if len(raw)!=4110 or len(caches)!=32:raise ValueError('complete ownership and eight actor identities required')
    def physical(bank,address,size):
        if not 0x8000<=address<address+size<=0xc000 or (bank+1)*16384>len(rom):raise ValueError('invalid bank-local descriptor')
        at=bank*16384+address-0x8000
        return rom[at:at+size]
    result=bytearray(raw)
    for page in range(2):
        for lane in range(4):
            owner=page*4+lane;cache=bytes(caches[owner*4:owner*4+4]);roles=segments(page,lane)
            for role in roles:
                at=1536+role['key']-0xd000
                if raw[at:at+18]!=b'\xff'*18:raise ValueError('obsolete actor per-tile metadata published')
            if cache==b'\xff'*4:continue
            group,encoded,color,pad=cache;variant=encoded&127;coarse=encoded>>7
            if group>=66 or not 1<=color<=15 or pad!=255:raise ValueError('invalid actor owner identity')
            lo,hi,bank=geometry['roots']['row'][group]
            code=int.from_bytes(physical(bank,lo+hi*256+variant*2,2),'little')
            cls=geometry['classes'][code>>12];index=code&4095
            if index>=cls['count']:raise ValueError('invalid finite descriptor index')
            address=cls['offset']+index*cls['stride'];logical=address//16384
            bank=logical+3 if logical<11 else logical+242
            data=physical(bank,0x8000+address%16384,cls['stride'])
            ids=[int.from_bytes(data[i:i+2],'little') for i in range(0,len(data),2)]
            if any(i>=geometry['patterns'] for i in ids):raise ValueError('actor geometry key outside finite namespace')
            ids=normalized_keys(ids,cls['columns'],cls['rows'],lane,coarse)
            for segment,role in enumerate(roles):
                at=1536+role['key']-0xd000
                result[at:at+18]=b''.join(i.to_bytes(2,'little')+bytes([role['water'],0,color,0]) for i in ids[segment*3:segment*3+3])
    return bytes(result)
