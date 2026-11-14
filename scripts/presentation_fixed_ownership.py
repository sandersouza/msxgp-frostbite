"""Audit permanent roles against both NAME pages and real PGT/CGT bytes."""
from presentation_fixed import COUNTS
from presentation_dirty_audit import audit_physical_names

ROW_BYTES=4110


def audit_active(before,prepared,registers):
    if len(before)!=16384 or len(prepared)!=16384 or len(registers)!=8 or registers[2]not in (6,7):raise ValueError('whole before/prepare VRAM and active page registers required')
    page=registers[2]-6;spans=[(registers[2]*1024,768),(0x1B00,128)]
    for bank in range(3):
        for table in (0,0x2000):
            spans.extend(((table+bank*2048+page*64*8,512),(table+bank*2048+128*8,32*8)))
    for table in (0,0x2000):spans.append((table+4096+(160+page*22)*8,22*8))
    for offset in range(0x1B00,0x1B80,4):
        if before[offset]==208:break
        spans.append((0x3800+(before[offset+2]&252)*8,32))
    if any(before[start:start+size]!=prepared[start:start+size] for start,size in spans):raise ValueError('active NAME/PGT/CGT/SAT/full SGT bytes changed during prepare')


def kinds(bank,slot,templates=False):
    if bank==0:
        if slot<8:return (0,)
        if slot<38:return (16+(slot-8)//10,)
        return (5,)
    if bank==1:return (0,) if slot<19 else ((9,) if templates else (0,7)) if slot<51 else (2,3)
    return (0,) if slot<9 else ((9,) if templates else (0,7)) if slot<41 else (1,)


def audit_row(raw,vram,tile,*,templates=False,shared_ice=False,native_bear=False):
    if type(native_bear) is not bool:raise ValueError('explicit native bear feature selection required')
    if type(templates)is not bool:raise ValueError('explicit fixed/template role selection required')
    if len(raw)!=ROW_BYTES or len(vram)!=16384:raise ValueError('complete fixed metadata, both NAME pages and16KiB VRAM required')
    names=raw[:1536];keys=raw[1536:3840];footer=raw[3840:4104];counts=raw[4104:]
    if counts!=bytes(COUNTS*2):raise ValueError('fixed role capacities changed')
    audit_physical_names(vram,names)
    valid={};published=0
    def check_tile(bank,identifier,key):
        nonlocal published
        expected=tile(bank,key)
        if len(expected)!=16:raise ValueError('constructor must return all16 bytes')
        at=bank*2048+identifier*8
        if vram[at:at+8]+vram[0x2000+at:0x2000+at+8]!=expected:
            raise ValueError(f'published fixed key differs from real tile bank{bank} id{identifier}')
        published+=1
    for group in range(6):
        bank=group%3;page=group//3
        for slot in range(64):
            key=keys[(group*64+slot)*6:(group*64+slot+1)*6]
            if key==bytes([255])*6:continue
            if key[5]==10 and native_bear:
                from native_bear_keys import validate_role
                validate_role(bank,slot+page*64,key)
            elif slot>=COUNTS[bank] or key[5] not in kinds(bank,slot,templates):raise ValueError('key belongs to another fixed primitive role')
            identifier=slot+page*64;check_tile(bank,identifier,key);valid[page,bank,identifier]=key
    for index in range(44):
        key=footer[index*6:(index+1)*6]
        if key==bytes([255])*6:continue
        if key[5]!=6:raise ValueError('footer metadata has a non-footer constructor')
        identifier=160+index;page=index//22;check_tile(2,identifier,key);valid[page,2,identifier]=key
    dynamic=0;referenced=set()
    for offset,identifier in enumerate(names):
        page=offset//768;row=offset%768//32;bank=row//8;column=offset%32
        if identifier<128:
            physical_page=identifier//64
            physical_key=valid.get((physical_page,bank,identifier))
            cross_ice=(shared_ice and templates and bank in (1,2)
                       and physical_key is not None and physical_key[5]==9
                       and (19 if bank==1 else 9)<=identifier%64<(51 if bank==1 else 41))
            if physical_key is None or physical_page!=page and not cross_ice:raise ValueError('NAME references another generation or an unpublished fixed role')
            slot=identifier&63
            if physical_key[5]==10 and native_bear:
                from native_bear_keys import fields
                if row!=6+fields(physical_key)[3]:raise ValueError('native bear NAME escaped its exact row')
            if bank==0:
                if slot<8 and row not in (6,7) or 8<=slot<38 and (row!=(slot-8)//10 or column!=5+(slot-8)%10) or slot>=38 and (row!=3+(slot-38)//6 or column!=22+(slot-38)%6):
                    raise ValueError('NAME position differs from its bank0 role')
            if bank==1 and slot>=51 and row not in (12,15) or bank==2 and slot>=41 and row!=20:raise ValueError('fused NAME escaped its shared row')
            dynamic+=1;referenced.add((page,bank,identifier))
        elif identifier>=160:
            expected=160+page*22+(row-22)*11+column-4
            if bank!=2 or row not in (22,23) or not 4<=column<15 or identifier!=expected or (page,2,identifier)not in valid:
                raise ValueError('footer NAME position/generation/metadata differs')
    return {'dynamic_cells':dynamic,'referenced_slots':len(referenced),'published_slots':published}
