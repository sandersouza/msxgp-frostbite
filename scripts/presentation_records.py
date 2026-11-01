"""Strict local source-raster/audio stream; no original pixels in public source."""
import struct

from graphics_mapping import map_y

HEADER = struct.Struct('<8sIII')
RECORD = struct.Struct('<IHHHIIIH')
EVENT = struct.Struct('<IBB')
MAGIC = b'FBPR0001'
RASTER_BYTES = 160 * 210
SNAPSHOT_BYTES = 133


def parse_records(data):
    if not isinstance(data, bytes): raise ValueError('immutable source observation bytes required')
    position = 0

    def take(size):
        nonlocal position
        if position + size > len(data): raise ValueError('truncated presentation observation')
        part = data[position:position + size]; position += size
        return part

    magic, count, clock, divisor = HEADER.unpack(take(HEADER.size))
    if magic != MAGIC or not 1 <= count <= 5000 or (clock, divisor) != (3579545, 3):
        raise ValueError('bounded versioned original-clock stream required')
    records = []
    for index in range(count):
        ordinal, before_pc, visible_pc, after_pc, frame, visible_cycles, cycles, event_count = RECORD.unpack(take(RECORD.size))
        if ordinal != index or (before_pc, visible_pc, after_pc) != (0xF019, 0xF476, 0xF019):
            raise ValueError('complete ordered source drawing phases required')
        if not 0 < visible_cycles < cycles <= 131072:
            raise ValueError('bounded positive visible/post-visible source timing required')
        point = {'index': index, 'source_frame': frame,
                 'phases': [before_pc, visible_pc, after_pc], 'visible_cycles': visible_cycles, 'cycles': cycles}
        for name in ('before', 'visible', 'after'):
            raw = take(SNAPSHOT_BYTES)
            if not raw[3] & 32: raise ValueError('complete normalized original CPU flags required')
            point[name] = {'registers': dict(zip(('a', 'x', 'y', 'p', 'sp'), raw[:5])), 'ram': list(raw[5:])}
        raster = take(RASTER_BYTES)
        if any(any(raster[y * 160:(y + 1) * 160]) for y in range(210) if map_y(y) is None):
            raise ValueError('nonblack source pixel in omitted presentation rows')
        point['raster'] = raster
        audio = [EVENT.unpack(take(EVENT.size)) for _ in range(event_count)]
        if (any(not 0 <= cycle <= cycles or not 0x15 <= address <= 0x1A for cycle, address, _ in audio)
                or any(a[0] > b[0] for a, b in zip(audio, audio[1:]))):
            raise ValueError('ordered in-phase original audio writes required')
        point['audio'] = audio; records.append(point)
    if take(12) != b'FBPRDONE' + struct.pack('<I', count) or position != len(data):
        raise ValueError('unique complete source observation terminator required')
    return records
