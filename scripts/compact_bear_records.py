"""Lossless nine-bit native bear record IDs with the original raw key map."""


def pack(records):
    if len(records) != 96*64:
        raise ValueError('complete96 original64-byte records required')
    mapping = {}
    result = bytearray()
    for start in range(0, len(records), 64):
        record = records[start:start+64]
        columns, rows = record[48:50]
        if columns not in (3, 4) or rows != 3 or record[50] != columns*6 or record[63]:
            raise ValueError('original bounded native grid metadata required')
        count = columns*rows
        if any(record[count*4:48]):
            raise ValueError('unused original cells must retain four zero bytes')
        indices = []
        for cell in range(12):
            if cell >= count:
                indices.append(0)
                continue
            at = cell*4
            raw = int.from_bytes(record[at:at+2], 'little')
            dense = int.from_bytes(record[at+2:at+4], 'little')
            index = dense & 511
            if raw >= 16384 or dense & 0x7E00 or index >= 470:
                raise ValueError('original raw ID/dense predicate grammar required')
            value = raw | (dense & 0x8000)
            if index in mapping and mapping[index] != value:
                raise ValueError('one immutable raw key per dense mask required')
            mapping[index] = value
            indices.append(index)
        for first, second in zip(indices[::2], indices[1::2]):
            result.extend((first & 255, (first >> 8) | ((second & 127) << 1), second >> 7))
        result.extend(record[48:63])
    if set(mapping) != set(range(470)):
        raise ValueError('complete470-mask bijection required')
    raw = b''.join(mapping[i].to_bytes(2, 'little') for i in range(470))
    return dict(records=bytes(result), raw=raw)


def unpack(data):
    records, raw = data['records'], data['raw']
    if len(records) != 96*33 or len(raw) != 470*2:
        raise ValueError('complete compact record domain required')
    result = bytearray()
    for start in range(0, len(records), 33):
        source = records[start:start+33]
        record = bytearray()
        for at in range(0, 18, 3):
            a, b, c = source[at:at+3]
            if c > 3:
                raise ValueError('packed index exceeds nine bits')
            for index in (a | ((b & 1) << 8), (b >> 1) | (c << 7)):
                if index >= 470:
                    raise ValueError('dense mask outside dictionary')
                value = int.from_bytes(raw[index*2:index*2+2], 'little')
                record.extend((value & 16383).to_bytes(2, 'little'))
                record.extend((index | (value & 0x8000)).to_bytes(2, 'little'))
        columns, rows = source[18:20]
        if columns not in (3, 4) or rows != 3:
            raise ValueError('bounded original grid required')
        if columns == 3:
            record[36:48] = bytes(12)
        record.extend(source[18:]+bytes(1))
        result.extend(record)
    return bytes(result)
