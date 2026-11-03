"""Independently count every live name on both native cache generations."""

ROW_BYTES=1926


def audit_names(names,refs,counts):
    if len(names)!=1536 or len(refs)!=384 or len(counts)!=6 or any(count>64 for count in counts):
        raise ValueError('whole two-page names, six64-slot reference banks and counts required')
    wanted=[0]*384
    for index,identifier in enumerate(names):
        if identifier>=128:continue
        page=index//768;bank=(index%768)//256;slot=identifier&63
        if (identifier>>6)!=page:raise ValueError('name references the other generation')
        group=page*3+bank
        if slot>=counts[group]:raise ValueError('name references an unallocated constructor slot')
        at=group*64+slot;wanted[at]+=1
        if wanted[at]>255:raise ValueError('live name references exceed byte capacity')
    if bytes(wanted)!=bytes(refs):raise ValueError('live name histogram and native reference counts differ')
    return {'dynamic_cells':sum(wanted),'referenced_slots':sum(value>0 for value in wanted)}


def audit_row(raw):
    if len(raw)!=ROW_BYTES:raise ValueError('incomplete live cache ownership capture')
    return audit_names(raw[:1536],raw[1536:1920],raw[1920:])
