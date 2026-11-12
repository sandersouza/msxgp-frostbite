"""Compile immutable white/delta8 ice and audit its sparse SCREEN2 allocation."""

def atlas_ids():
    return tuple(range(144,160))+tuple(range(204,250))

def compile_atlas(packets):
    if len(packets)!=16:raise ValueError('all16 root phases required')
    patterns=[bytes(8)];programs=[]
    for packet in packets:
        local=packet['patterns'];names=packet['names']
        if len(names)!=30 or any(len(p)!=8 for p in local):raise ValueError('complete packet patterns and30 names required')
        for p in local:
            if p not in patterns:patterns.append(p)
        if len(patterns)>len(atlas_ids()):raise ValueError('atlas exceeds sparse VRAM allocation')
        encoded=[]
        for n in names:
            if n==129:p=bytes(8)
            elif 25<=n<25+len(local):p=local[n-25]
            else:raise ValueError('phase0 NAME outside packet namespace')
            encoded.append(atlas_ids()[patterns.index(p)])
        programs.extend(encoded+[0,0])
    return dict(patterns=b''.join(patterns),programs=bytes(programs),ids=atlas_ids()[:len(patterns)])

def audit_atlas(vram,table):
    if len(vram)!=16384 or not table or not set(table)<=set(atlas_ids()):raise ValueError('complete VRAM and declared sparse atlas required')
    for bank in (1,2):
        for identifier,tile in table.items():
            at=bank*2048+identifier*8
            if len(tile)!=16 or vram[at:at+8]+vram[0x2000+at:0x2000+at+8]!=tile:raise ValueError(f'immutable atlas differs bank{bank} id{identifier}')

def shadow_names(raw,vram,table):
    audit_atlas(vram,table)
    if len(raw)!=4110:raise ValueError('complete original owner metadata required')
    names=bytearray(raw);video=bytearray(vram)
    for offset,identifier in enumerate(raw[:1536]):
        if identifier not in table:continue
        page=offset//768;row=offset%768//32
        if row<8:continue # Bank0 uses its original independent static namespace.
        if row not in (12,15,18,21):raise ValueError('atlas reference outside an ice row')
        at=0x1800+page*0x400+offset%768
        if video[at]!=identifier:raise ValueError('physical atlas NAME differs')
        # Independently validated immutable IDs do not carry dynamic-owner keys.
        # Only the old role audit gets this shadow; actual pixels stay untouched.
        names[offset]=video[at]=128
    return bytes(names),bytes(video)
