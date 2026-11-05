"""Finite legal world NAME programs, independent of target timing."""


def decoded_names(packed,first,water):
    if len(packed)!=30 or not 0<=first<=241 or not 128<=water<=255:
        raise ValueError('complete bounded NAME program and physical role required')
    codes=[code for byte in packed for code in (byte&15,byte>>4)]
    if any(code>14 for code in codes):raise ValueError('NAME code outside compiled grammar')
    return bytes(first+code-1 if code else water for code in codes)


def legal_programs(programs,lane):
    if len(programs)!=1280 or lane not in range(4):
        raise ValueError('complete finite packet directory and lane required')
    phases=((7,0),(5,6),(3,4),(1,2))[lane]
    return {programs[i] for i in range(1280) if i//160 in phases}


def occupancy(ids,columns,rows):
    if columns not in (2,3) or rows not in (1,2) or len(ids)!=columns*rows or any(type(i)is not int or not 0<=i<16384 for i in ids):
        raise ValueError('bounded complete enemy descriptor required')
    return (64 if columns==3 else 0)|(128 if rows==2 else 0)|sum((i!=0)<<n for n,i in enumerate(ids))
