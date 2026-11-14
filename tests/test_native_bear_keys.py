import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import native_bear_keys as bear
except ModuleNotFoundError as error:
    if error.name != 'native_bear_keys':
        raise
    bear = None


def source_image():
    image = bytearray(4096)
    image[0xD00:0xD13] = bytes([128])*19
    return bytes(image)


class NativeBearKeys(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(bear, 'native kind10 key contract is not implemented')

    def test_all_fields_round_trip(self):
        key = bear.make_key(15, 15, 1, 2, 3, 129, 1)
        self.assertEqual(key, bytes.fromhex('fb1f8100010a'))
        self.assertEqual(bear.fields(key), (15, 15, 1, 2, 3))

    def test_only_the_exact_bear_roles_accept_the_key(self):
        for row in range(3):
            for column in range(4):
                key = bear.make_key(0, 0, 0, row, column, 129, 15)
                bank = int(row == 2)
                slot = row*4+column if bank == 0 else column
                for page in (0, 1):
                    self.assertTrue(bear.validate_role(bank, slot+page*64, key))
                    with self.assertRaises(ValueError):
                        bear.validate_role(bank, ((slot+1) % 64)+page*64, key)
                    with self.assertRaises(ValueError):
                        bear.validate_role(1-bank, slot+page*64, key)

    def test_invalid_fields_and_reserved_bits_are_rejected(self):
        arguments = [0, 0, 0, 0, 0, 128, 1]
        for field, value in ((0, 16), (1, 16), (2, 2), (3, 3), (4, 4), (5, 127), (6, 0)):
            values = arguments.copy()
            values[field] = value
            with self.assertRaises(ValueError):
                bear.make_key(*values)
        key = bytearray(bear.make_key(*arguments))
        for field, value in ((1, 32), (0, 12), (3, 1), (5, 0)):
            bad = key.copy()
            bad[field] = value
            with self.assertRaises(ValueError):
                bear.fields(bytes(bad))

    def test_original_glyph_reflection_and_vertical_padding(self):
        backgrounds = {128: bytes([255])*8+bytes([238])*8}
        left = bear.make_key(0, 0, 0, 0, 0, 128, 1)
        right = bear.make_key(1, 0, 0, 0, 2, 128, 1)
        self.assertEqual(bear.construct(source_image(), 0, left, backgrounds),
                         bytes(3)+bytes([224])*5+bytes([30])*8)
        self.assertEqual(bear.construct(source_image(), 0, right, backgrounds),
                         bytes(3)+bytes([7])*5+bytes([30])*8)
        for coarse, mask in ((0, bytes([224])*7+bytes(1)), (1, bytes([224])*8)):
            key = bear.make_key(0, 0, coarse, 2, 0, 128, 1)
            self.assertEqual(bear.construct(source_image(), 1, key, backgrounds), mask+bytes([30])*8)

    def test_horizontal_partial_bytes_and_empty_fourth_column(self):
        backgrounds = {128: bytes([255])*8+bytes([68])*8}
        first = bear.make_key(0, 5, 0, 0, 0, 128, 15)
        second = bear.make_key(0, 5, 0, 0, 1, 128, 15)
        empty = bear.make_key(0, 0, 0, 0, 3, 128, 15)
        self.assertEqual(bear.construct(source_image(), 0, first, backgrounds)[:8], bytes(3)+bytes([1])*5)
        self.assertEqual(bear.construct(source_image(), 0, second, backgrounds)[:8], bytes(3)+bytes([192])*5)
        self.assertEqual(bear.construct(source_image(), 0, empty, backgrounds), bytes(8)+bytes([244])*8)

    def test_equal_foreground_and_background_retains_exact_pixel_color(self):
        backgrounds = {128: bytes([255])*8+bytes([238])*8}
        key = bear.make_key(0, 0, 0, 0, 0, 128, 14)
        tile = bear.construct(source_image(), 0, key, backgrounds)
        self.assertEqual(tile[8:], bytes([238])*8)
        self.assertEqual(tile[:8], bytes(3)+bytes([224])*5)

    def test_nonuniform_background_is_rejected(self):
        key = bear.make_key(0, 0, 0, 0, 0, 128, 1)
        for tile in (bytes([15])*8+bytes([238])*8, bytes([255])*8+bytes([225])*8):
            with self.assertRaises(ValueError):
                bear.construct(source_image(), 0, key, {128: tile})


if __name__ == '__main__':
    unittest.main()
