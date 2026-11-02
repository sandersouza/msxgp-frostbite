"""Finite mask fragments must preserve every source bit at every phase."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationFragmentsTests(unittest.TestCase):
    def test_bit_masks_at_all_horizontal_and_vertical_phases_decode_exactly(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fragments'), 'finite geometry compiler missing')
        api = importlib.import_module('presentation_fragments')
        for width, height in ((8, 1), (8, 8), (16, 19), (24, 7)):
            bitmap = bytes(int((x * 7 + y * 3) % 11 < 4) for y in range(height) for x in range(width))
            for phase_x in range(16):
                for phase_y in range(8):
                    result = api.mask_tiles(bitmap, width, height, phase_x, phase_y)
                    origin = (8 + phase_x * 3 // 2) & ~7; decoded = set()
                    self.assertEqual(len(result['patterns']), result['columns'] * result['rows'])
                    for tile, pattern in enumerate(result['patterns']):
                        self.assertEqual(len(pattern), 8)
                        for y, row in enumerate(pattern):
                            for x in range(8):
                                if row & (128 >> x): decoded.add((origin + (tile % result['columns']) * 8 + x, (tile // result['columns']) * 8 + y))
                    expected = set()
                    for y in range(height):
                        for x in range(width):
                            if bitmap[y * width + x]:
                                for target in range(8 + (phase_x + x) * 3 // 2, 8 + (phase_x + x + 1) * 3 // 2): expected.add((target, phase_y + y))
                    self.assertEqual(decoded, expected)
        for values in ((bytes(64), 8, 8, -1, 0), (bytes(63), 8, 8, 0, 0), (bytes([2]) * 64, 8, 8, 0, 0)):
            with self.assertRaises(ValueError): api.mask_tiles(*values)

    def test_bank_records_never_cross_mapper_windows_or_mutate_state_after_overflow(self):
        api = importlib.import_module('presentation_fragments'); packed = api.BankImage([3, 253])
        self.assertEqual(packed.store(b'A' * 16383), bytes((0, 128, 3)))
        self.assertEqual(packed.store(b'BC'), bytes((0, 128, 253)))
        images = packed.images()
        self.assertEqual([len(image) for image in images], [16384, 16384])
        self.assertEqual(images[0][-1], 255); self.assertEqual(images[1][:3], b'BC\xff')
        before = packed.images()
        with self.assertRaises(ValueError): packed.store(bytes(16385))
        with self.assertRaises(ValueError): packed.store(bytes(16384))
        self.assertEqual(packed.images(), before)
        for banks in ([3, 3], [], [256], [True]):
            with self.assertRaises(ValueError): api.BankImage(banks)
        stream = api.BankImage([3, 253])
        self.assertEqual(stream.store(bytes(range(256)) * 80, record=False, alignment=8), bytes((0, 128, 3)))
        self.assertEqual(stream.used_bytes, 20480)
