"""Original-free CRC8 bucket index; exact constructor keys remain authoritative."""
from functools import lru_cache

@lru_cache(maxsize=1)
def table():
    values=[]
    for byte in range(256):
        state=byte
        for _ in range(8):state=((state<<1)^(7 if state&128 else 0))&255
        values.append(state)
    return bytes(values)

def hash_key(key):
    if len(key)!=6:raise ValueError('exact six-byte constructor key required')
    state=0;lookup=table()
    for byte in key:state=lookup[state^byte]
    return state

def collisions(count):
    if not 1<=count<=256:raise ValueError('bounded collision matrix required')
    return [bytes(4)+bytes((n,next(last for last in range(256) if hash_key(bytes(4)+bytes((n,last)))==0))) for n in range(count)]
