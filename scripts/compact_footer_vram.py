"""Allocate immutable footer tiles outside every declared SCREEN2 role."""


def allocation(fixed_counts,background_counts,atlas_ids,credit_ids,count):
    if len(fixed_counts)!=3 or len(background_counts)!=3 or not isinstance(count,int) or count<=0:
        raise ValueError('three complete role/background banks and positive count required')
    if any(type(n)is not int or not 0<=n<=64 for n in fixed_counts) or any(type(n)is not int or not 0<=n<=128 for n in background_counts):
        raise ValueError('bounded fixed/background counts required')
    if any(type(n)is not int or not 0<=n<=255 for n in (*atlas_ids,*credit_ids)):
        raise ValueError('byte static tile IDs required')
    result=[]
    for bank,limit in enumerate(fixed_counts):
        used=set(range(limit))|set(range(64,64+limit))|set(range(128,128+background_counts[bank]))
        if bank in (1,2):used.update(atlas_ids)
        if bank==2:used.update(range(160,204));used.update(credit_ids)
        for tile in sorted(set(range(256))-used):
            pattern=bank*2048+tile*8
            result.append(dict(bank=bank,tile=tile,pattern=pattern,color=pattern+8192))
    if len(result)<count:raise ValueError('insufficient unallocated tile capacity')
    return result[:count]
