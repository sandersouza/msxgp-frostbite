"""Lossless start-threshold grammar for the complete two-page grid translation."""

def pack(data):
    if len(data)!=512:raise ValueError('complete two-coarse256-row translation required')
    return tuple(bytes(v for i,value in enumerate(data[c*256:(c+1)*256])
                       if i==0 or value!=data[c*256+i-1] for v in (i,value)) for c in range(2))


def lookup(table,y):
    if (not table or len(table)%2 or table[0]!=0 or type(y) is not int or not 0<=y<256
            or any(table[i]<=table[i-2] for i in range(2,len(table),2))):
        raise ValueError('strict ordered start thresholds and byte row required')
    result=table[1]
    for at in range(2,len(table),2):
        if y<table[at]:break
        result=table[at+1]
    return result
