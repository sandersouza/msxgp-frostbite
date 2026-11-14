"""Row-major representation of the guarded source write-loop summary."""


def row_data(summary):
    addresses=summary['destinations']
    if not 1<=len(addresses)<=8:raise ValueError('bounded eight-cell source summary required')
    result=bytearray()
    for row in summary['rows']:
        mask=sum(1<<i for i,a in enumerate(addresses) if a in row['writes'])
        values=bytes((mask,*[row['writes'].get(a,0) for a in addresses],row['a'],row['y']))
        result.extend(values+bytes(16-len(values)))
    return bytes(result)


def emit_summary(summary,prefix,end_label,slow_label):
    lines=['push af','ld a,b','or a',f'jr nz,{slow_label}',f'ld a,(${0xC000+summary["bound_offset"]:04X})',
           f'cp {summary["limit"]}',f'jr nc,{slow_label}','ld b,a','ld l,a','ld h,0','pop af']
    lines+=['add hl,hl']*4+[f'ld de,{prefix}_rows','add hl,de','ld d,(hl)']
    for i,address in enumerate(summary['destinations']):
        label=f'{prefix}_packed_skip{i}'
        lines+=['inc l',f'bit {i},d',f'jr z,{label}','ld a,(hl)',f'ld (${0xC000+address:04X}),a',label+':']
    lines+=['inc l','ld a,(hl)','inc l','ld c,(hl)','ld l,b','ld h,$C0','push hl','pop iy','ld e,1','cp a',f'jp {end_label}',slow_label+':','pop af']
    return lines


def emit_tables(summary,prefix):
    data=row_data(summary)
    return prefix+'_rows:\n'+'\n'.join(' DB '+','.join(map(str,data[i:i+16])) for i in range(0,len(data),16))+'\n'
