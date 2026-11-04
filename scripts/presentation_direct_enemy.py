"""Physical actor transactions and independent geometry normalization."""


def segments(page,lane):
    if page not in (0,1) or lane not in range(4):raise ValueError('valid page/lane required')
    roles=(((2,3),(2,6)),((1,16),(2,0)),((1,10),(1,13)),((1,4),(1,7)))
    return [dict(bank=b,tile=t+page*64,pgt=0x4000+b*2048+(t+page*64)*8,
                 key=0xd000+(page*3+b)*384+t*6,water=130 if b==1 else 129)
            for b,t in roles[lane]]


def normalized_keys(ids,columns,rows,lane,coarse):
    if (columns not in (1,2,3) or rows not in (1,2) or len(ids)!=columns*rows
            or lane not in range(4) or coarse not in (0,1)
            or any(type(i)is not int or not 0<=i<16384 for i in ids)):
        raise ValueError('bounded complete descriptor grid required')
    result=[ids[r*columns+c] if r<rows and c<columns else 0 for r in range(2) for c in range(3)]
    if lane==1 and coarse:
        if rows!=1:raise ValueError('Y128 actor has exactly one source tile row')
        result=[0,0,0]+result[:3]
    return result
