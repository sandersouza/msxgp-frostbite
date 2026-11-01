"""Strict original-clock truth for eight row windows and the shore latch.

Each window retains 228 literal player views for each electrical high bit.
This local protocol is independent of the compiled MSX lookup representation.
"""
from floe_truth import ROW_BYTES,sample,validate_row,view_index

FULL_BYTES=674
WINDOWS=9


def full_record(data):
    if len(data)!=FULL_BYTES:raise ValueError('complete674-byte hazard record required')
    rows=[bytes(data[i*ROW_BYTES:(i+1)*ROW_BYTES]) for i in range(WINDOWS)]
    for row in rows:validate_row(row)
    ram=bytes(data[522:650])
    if any(value&63!=7 for value in ram[0x30:0x38]):
        raise ValueError('original row latches require electrical low bits07')
    return {'truth':rows,'ram':ram,
            'registers':dict(zip(('a','x','y','p','sp'),data[650:655])),
            'glyph':bytes(data[655:674])}


def contacts(record,ram):
    if len(ram)!=128 or len(record['truth'])!=WINDOWS:
        raise ValueError('complete source RAM and all nine collision windows required')
    view=view_index(ram[0x6E],ram[0x6B],bool(ram[0x6C]&8))
    return {'rows':bytes(sample(row,view) for row in record['truth'][:8]),
            'shore':sample(record['truth'][8],view)}
