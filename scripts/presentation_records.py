"""Strict local source-raster/audio stream; no original pixels in public source."""
import struct

from graphics_mapping import map_y

HEADER = struct.Struct('<8sIII')
RECORD = struct.Struct('<IHHHIIIH')
RECORD_V2 = struct.Struct('<IHHHIIIIIHH')
VIDEO = struct.Struct('<IHHHH')
EVENT = struct.Struct('<IBB')
MAGIC = b'FBPR0001'
RASTER_BYTES = 160 * 210
SNAPSHOT_BYTES = 133
MAX_INTERVAL_CYCLES = 1 << 19  # Includes seeded8-bit/1024-divider RIOT startup.


def normalize_frame(frame):
    """Measured Stella start23 -> original/ALE start34; never accept lost pixels."""
    if (type(frame.get('frame')) is not int or frame['frame'] < 1
            or (frame.get('width'), frame.get('height'), frame.get('start_line')) != (160, 228, 23)
            or frame.get('scanlines') not in (262, 263)
            or not isinstance(frame.get('pixels'), bytes) or len(frame['pixels']) != 160 * 228):
        raise ValueError('completed regular measured native viewport required')
    pixels = frame['pixels']
    if any(pixels[:11 * 160]) or any(pixels[221 * 160:]):
        raise ValueError('nonblack content outside measured original viewport')
    raster = pixels[11 * 160:221 * 160]
    if any(any(raster[y * 160:(y + 1) * 160]) for y in range(210) if map_y(y) is None):
        raise ValueError('nonblack source pixel in omitted presentation rows')
    return raster


def parse_records(data):
    if not isinstance(data, bytes): raise ValueError('immutable source observation bytes required')
    position = 0

    def take(size):
        nonlocal position
        if position + size > len(data): raise ValueError('truncated presentation observation')
        part = data[position:position + size]; position += size
        return part

    def video(cycle_limit):
        cycle, width, height, start, lines = VIDEO.unpack(take(VIDEO.size))
        if not 0 < cycle <= cycle_limit or width != 160 or not 1 <= height <= 320 or not 0 <= start <= 320 or not 1 <= lines <= 1024:
            raise ValueError('bounded complete native source viewport required')
        return {'cycle': cycle, 'width': width, 'height': height, 'start_line': start,
                'scanlines': lines, 'pixels': take(width * height)}

    magic, count, clock, divisor = HEADER.unpack(take(HEADER.size))
    if magic not in (MAGIC, b'FBPR0002') or not 1 <= count <= 5000 or (clock, divisor) != (3579545, 3):
        raise ValueError('bounded versioned original-clock stream required')
    records = []
    for index in range(count):
        if magic == MAGIC:
            ordinal, before_pc, visible_pc, after_pc, frame, visible_cycles, cycles, event_count = RECORD.unpack(take(RECORD.size))
        else:
            ordinal, before_pc, visible_pc, after_pc, frame, visible_frame, after_frame, visible_cycles, cycles, event_count, frame_count = RECORD_V2.unpack(take(RECORD_V2.size))
            if not frame <= visible_frame <= after_frame or after_frame - frame != frame_count or not 1 <= frame_count <= 64:
                raise ValueError('every physical source frame must be retained')
        if ordinal != index or (before_pc, visible_pc, after_pc) != (0xF019, 0xF476, 0xF019):
            raise ValueError('complete ordered source drawing phases required')
        if not 0 < visible_cycles < cycles <= MAX_INTERVAL_CYCLES:
            raise ValueError('bounded positive visible/post-visible source timing required')
        point = {'index': index, 'source_frame': frame,
                 'phases': [before_pc, visible_pc, after_pc], 'visible_cycles': visible_cycles, 'cycles': cycles}
        for name in ('before', 'visible', 'after'):
            raw = take(SNAPSHOT_BYTES)
            if not raw[3] & 32: raise ValueError('complete normalized original CPU flags required')
            point[name] = {'registers': dict(zip(('a', 'x', 'y', 'p', 'sp'), raw[:5])), 'ram': list(raw[5:])}
        if magic == MAGIC:
            raster = take(RASTER_BYTES)
            if any(any(raster[y * 160:(y + 1) * 160]) for y in range(210) if map_y(y) is None):
                raise ValueError('nonblack source pixel in omitted presentation rows')
            point['raster'] = raster
        else:
            point['visible_frame'] = visible_frame; point['after_frame'] = after_frame
            point['visible_raster'] = video(cycles)
            if point['visible_raster']['cycle'] != visible_cycles:
                raise ValueError('visible buffer must match its phase timestamp')
            point['frames'] = [{**video(cycles), 'frame': frame + i + 1} for i in range(frame_count)]
            completed = point['frames']
            if (any(a['cycle'] >= b['cycle'] for a, b in zip(completed, completed[1:]))
                    or sum(p['cycle'] <= visible_cycles for p in completed) != visible_frame - frame):
                raise ValueError('physical frame completion order differs from source phases')
        audio = [EVENT.unpack(take(EVENT.size)) for _ in range(event_count)]
        if (any(not 0 <= cycle <= cycles or not 0x15 <= address <= 0x1A for cycle, address, _ in audio)
                or any(a[0] > b[0] for a, b in zip(audio, audio[1:]))):
            raise ValueError('ordered in-phase original audio writes required')
        point['audio'] = audio; records.append(point)
    if take(12) != b'FBPRDONE' + struct.pack('<I', count) or position != len(data):
        raise ValueError('unique complete source observation terminator required')
    return records
