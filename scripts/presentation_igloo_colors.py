"""Finite CGT records for igloo shapes over certified uniform backgrounds."""

def uniform_background(tile):
    if not isinstance(tile,bytes) or len(tile)!=16:
        raise ValueError('whole sixteen-byte background required')
    return tile[:8]==bytes([255])*8 and all(c>>4==c&15 and c&15!=14 for c in tile[8:])


def can_reuse_pattern(previous,current,backgrounds):
    if any(not isinstance(k,bytes) or len(k)!=6 for k in (previous,current)):
        raise ValueError('whole previous/current six-byte keys required')
    return (previous[:2]==current[:2] and previous[3:]==current[3:]==bytes((14,0,5))
        and previous[2] in backgrounds and current[2] in backgrounds
        and uniform_background(backgrounds[previous[2]])
        and uniform_background(backgrounds[current[2]]))


def compile_colors(backgrounds):
    if set(backgrounds)!=set(range(128,155)):
        raise ValueError('complete bank0 background domain128..154 required')
    flags=bytearray();records=bytearray()
    for identifier in range(128,155):
        tile=backgrounds[identifier];valid=uniform_background(tile);flags.append(int(valid))
        for mode in range(4):
            colors=bytearray(tile[8:] if valid else bytes(8))
            if valid:
                for y in range(8):
                    if mode&(1 if y<4 else 2):colors[y]=0xe0|(colors[y]&15)
            records.extend(colors)
    return bytes(flags).ljust(32,b'\0'),bytes(records)
