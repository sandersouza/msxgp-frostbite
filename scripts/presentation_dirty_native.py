"""Guard an additive extension inside the existing reserved resident kernel."""
def checked_kernel_extension(parent, offset, code, capacity):
    if offset < 0 or not code or len(code) > capacity or offset + len(code) > len(parent):
        raise ValueError('reserved kernel capacity exceeded')
    if parent[offset:offset+len(code)] != bytes([255])*len(code):
        raise ValueError('reserved kernel padding differs')
    return code

def fixed_floe_spans(table):
    """Derive native ORs only from equal coarse tables with one byte per lane."""
    if len(table)!=24 or table[:12]!=table[12:]:
        raise ValueError('coarse floe spans differ')
    result=[]
    for row in range(4):
        span=table[row*3:row*3+3];nonzero=[(i,b)for i,b in enumerate(span)if b]
        if len(nonzero)!=1:raise ValueError('single-byte floe span required')
        result.append(nonzero[0])
    return tuple(result)
