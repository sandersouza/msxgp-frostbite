"""Exact fixed-region transactions and bounded ROM/RAM layout."""
from presentation_constructors import merge


def changed_columns(columns,colors,saved):
    if len(columns)!=40 or len(colors)!=3 or len(saved)!=48:raise ValueError('complete two-row column identities required')
    if colors!=saved[40:43]:return 1023
    return sum(1<<c for c in range(10) if columns[c*4:c*4+4]!=saved[c*4:c*4+4])


def igloo_records(backgrounds,reachable=None):
    records=bytearray();mapping=bytearray()
    for index,background in enumerate(backgrounds):
        if len(background)!=16:raise ValueError('complete PGT/CGT background required')
        uniform=all(background[y]in(0,255) or background[y+8]>>4==background[y+8]&15 for y in range(8))
        if reachable is not None and index not in reachable:
            mapping.append(255);continue
        if not uniform:
            if reachable is not None:raise ValueError('reachable igloo background is not uniform per scanline')
            mapping.append(255);continue
        mapping.append(len(records)//768)
        for first in (252,240,192):
            for pair in range(16):
                masks=[(first if p&1 else 0)|((first^255) if p&2 else 0) for p in (pair&3,pair>>2)]
                records.extend(merge(background,bytes([masks[0]])*4+bytes([masks[1]])*4,14))
    return bytes(records),bytes(mapping)


def record_address(index):
    if type(index)is not int or not 0<=index<34*128:raise ValueError('record outside reclaimed full-bank tails')
    return 116+index//128,0xb800+(index%128)*16


def declare_ram(text,code,fail):
    read='debug read_block memory 0xE880 0xAC0'
    write='debug write_block memory 0xE880 [string repeat [binary format c 165] 0xAC0]'
    if text.count(read)!=1 or text.count(write)!=1 or text.count('0xAC0')!=3 or not 0<len(code)<=1792:
        raise ValueError('unrecognized Q guard or oversized RAM code')
    check=f'if {{[debug read_block memory 0xE900 {len(code)}] ne [binary format H* {code.hex()}]}} {{{fail} ram-code}}\n    '
    text=text.replace('if {['+read,check+'if {['+read,1)
    return text.replace(read,'debug read_block memory 0xF000 0x340').replace(write,
        'debug write_block memory 0xF000 [string repeat [binary format c 165] 0x340]').replace('0xAC0','0x340')


def ram_code(meta,rom):
    import hashlib
    record=meta['region_pipeline'];size=record['ram_code_bytes']
    at=record['ram_code_bank']*16384+record['ram_code_address']-32768
    code=rom[at:at+size]
    if not 0<size<=1792 or hashlib.sha256(code).hexdigest()!=record['ram_code_sha256']:
        raise ValueError('RAM driver image differs')
    return code
