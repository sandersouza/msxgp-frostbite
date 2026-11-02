"""Finite geometry tables for native dirty-band rendering, never frame playback."""


class BankImage:
    """Pack small records within bank windows; streams use logical bank order."""
    def __init__(self, banks):
        if not banks or len(set(banks)) != len(banks) or any(type(bank) is not int or not 0 <= bank <= 255 for bank in banks):
            raise ValueError('nonempty unique physical bank list required')
        self.banks = list(banks); self.data = bytearray()

    @property
    def used_bytes(self): return len(self.data)

    def store(self, data, *, record=True, alignment=1):
        if (not isinstance(data, (bytes, bytearray)) or not data or type(alignment) is not int
                or not 1 <= alignment <= 16384 or alignment & (alignment - 1)
                or record and len(data) > 16384):
            raise ValueError('bounded nonempty binary record and power-of-two alignment required')
        start = (len(self.data) + alignment - 1) & -alignment
        if record and start % 16384 + len(data) > 16384: start = (start + 16383) & -16384
        if start + len(data) > len(self.banks) * 16384: raise ValueError('finite geometry exceeds available cartridge banks')
        pointer = (0x8000 + start % 16384).to_bytes(2, 'little') + bytes((self.banks[start // 16384],))
        self.data.extend(bytes([255]) * (start - len(self.data))); self.data.extend(data)
        return pointer

    def images(self):
        return [bytes(self.data[start:start + 16384]).ljust(16384, b'\xff') for start in range(0, len(self.data), 16384)]


def mask_tiles(bitmap, width, height, phase_x, phase_y):
    """Expand a source mask into reusable eight-row SCREEN2 pattern fragments."""
    if (type(width) is not int or type(height) is not int or not 1 <= width <= 32 or not 1 <= height <= 32
            or type(phase_x) is not int or not 0 <= phase_x < 16 or type(phase_y) is not int or not 0 <= phase_y < 8
            or len(bitmap) != width * height or any(value not in (0, 1) for value in bitmap)):
        raise ValueError('bounded binary source mask and explicit horizontal/vertical phase required')
    start = 8 + phase_x * 3 // 2; origin = start & ~7
    columns = (8 + (phase_x + width) * 3 // 2 - origin + 7) // 8
    rows = (phase_y + height + 7) // 8; patterns = [bytearray(8) for _ in range(columns * rows)]
    for y in range(height):
        target_y = phase_y + y
        for x in range(width):
            if bitmap[y * width + x]:
                for target_x in range(8 + (phase_x + x) * 3 // 2 - origin, 8 + (phase_x + x + 1) * 3 // 2 - origin):
                    patterns[(target_y // 8) * columns + target_x // 8][target_y % 8] |= 128 >> (target_x % 8)
    return {'columns': columns, 'rows': rows, 'patterns': [bytes(pattern) for pattern in patterns]}
