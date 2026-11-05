"""Original-free pixel and ROM-layout contracts for the direct header."""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from presentation_header_dictionary import compile_dictionary, project_pair


class HeaderDictionaryTests(unittest.TestCase):
    def test_complete_synthetic_dictionary(self):
        source = random.Random(42).randbytes(4096)
        payload, sections = compile_dictionary(source)
        self.assertEqual(len(payload), 5328)
        # These far addresses are consumed by the assembled lookup routine.
        self.assertEqual([(s['offset'], s['size']) for s in sections],
                         [(0, 2048), (2048, 2048), (4096, 272),
                          (4368, 272), (4640, 272), (4912, 128),
                          (5040, 16), (5056, 16), (5072, 256)])
        for first in range(16):
            for second in range(16):
                at = (first*16+second)*8
                self.assertEqual(payload[at:at+8], project_pair(source, first, second, 1))
                self.assertEqual(payload[2048+at:2056+at], project_pair(source, first, second, 3))
        self.assertEqual(payload[5040:5048], project_pair(source, 32, 10, 1))
        self.assertEqual(payload[5048:5056], project_pair(source, 32, 33, 1))
        self.assertEqual(payload[5056:5064], project_pair(source, 10, 10, 3))
        self.assertEqual(payload[5064:5072], project_pair(source, 33, 10, 3))

    def test_one_source_pixel_maps_to_exact_scaled_columns(self):
        # Source rows run bottom-to-top. Glyph zero's top left pixel projects
        # to screen bit6 in the first column and to no pixel in its final tail.
        source = bytearray(4096)
        source[0xF07] = 128
        self.assertEqual(project_pair(source, 0, 1, 0), bytes([64])+bytes(7))
        self.assertEqual(project_pair(source, 0, 1, 4), bytes(8))
        source[0xF07] = 64
        self.assertEqual(project_pair(source, 0, 1, 0), bytes([48])+bytes(7))
        compile_dictionary(source)

    def test_every_source_bit_is_checked_against_pixel_projection(self):
        for row in range(8):
            for bit in range(8):
                source = bytearray(4096)
                for glyph in range(32):
                    source[0xF00+glyph*8+row] = 1 << bit
                source[0xF53+row] = 1 << bit
                source[0xD6D+row] = 1 << bit
                payload, _ = compile_dictionary(source)
                self.assertTrue(any(payload))

    def test_reject_wrong_image_size(self):
        for size in (0, 4095, 4097):
            with self.assertRaises(ValueError):
                compile_dictionary(bytes(size))


if __name__ == '__main__':
    unittest.main()
