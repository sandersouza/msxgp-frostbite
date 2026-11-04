"""Original-free build guards for the private native band experiment."""
import unittest
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from presentation_band_spike import apply_patch, column_table, verified_bytes


class BandSpikeTests(unittest.TestCase):
    def test_companion_identity_is_checked_before_use(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'symbols'
            data = b'helper: EQU 0x4000\n'
            expected = hashlib.sha256(data).hexdigest()
            path.write_bytes(data)
            self.assertEqual(verified_bytes(path, expected), data)
            path.write_bytes(b'helper: EQU 0x4100\n')
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                verified_bytes(path, expected)

    def test_rejects_wrong_parent_and_out_of_bounds_without_mutation(self):
        rom = bytearray(b'\x11\x22\x33\x44')
        for offset, old, new in [(1, b'\x99', b'\x00'),
                                 (4, b'\x00', b'\x01'),
                                 (-1, b'\x44', b'\x00'),
                                 (1, b'\x22', b'\x00\x01')]:
            with self.assertRaises(ValueError):
                apply_patch(rom, offset, old, new)
            self.assertEqual(rom, b'\x11\x22\x33\x44')

    def test_patch_changes_only_the_authorized_range(self):
        rom = bytearray(b'\x11\x22\x33\x44')
        record = apply_patch(rom, 1, b'\x22\x33', b'\xaa\xbb')
        self.assertEqual(rom, b'\x11\xaa\xbb\x44')
        self.assertEqual(record, dict(offset=1, before='2233', after='aabb'))

    def test_all_source_positions_match_pixel_projection(self):
        columns = column_table()
        self.assertEqual(len(columns), 160)
        self.assertEqual((min(columns), max(columns)), (1, 30))
        for x, column in enumerate(columns):
            self.assertEqual(column, (8 + x + x // 2) // 8)


if __name__ == '__main__':
    unittest.main()
