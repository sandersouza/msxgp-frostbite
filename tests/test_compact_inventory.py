"""Synthetic inputs catch misleading padding, aliasing and size accounting."""
import unittest

import compact_inventory as compact
from compact_inventory import image_inventory, physical_offset


class CompactInventoryTests(unittest.TestCase):
    def test_counts_duplicates_separately_from_padding(self):
        # Two equal banks plus an all-FF bank: duplicates are not dead bytes.
        image = b'\x01\xff\xff\x02' * 2 + b'\xff' * 4
        report = image_inventory(image, bank_size=4)
        self.assertEqual(report['size_bytes'], 12)
        self.assertEqual(report['bank_count'], 3)
        self.assertEqual(report['unique_banks'], 2)
        self.assertEqual(report['all_ff_banks'], 1)
        self.assertEqual(report['non_ff_bytes'], 4)
        self.assertEqual(report['trailing_ff_bytes'], 4)

    def test_does_not_truncate_partial_or_empty_banks(self):
        for image, size in ((b'', 4), (bytes(5), 4), (bytes(4), 0)):
            with self.subTest(image=image, size=size):
                with self.assertRaises(ValueError):
                    image_inventory(image, bank_size=size)

    def test_distinguishes_the_same_cpu_address_in_different_banks(self):
        self.assertEqual(physical_offset(0, 0x4005, 65536), 5)
        self.assertEqual(physical_offset(1, 0x8005, 65536), 16389)
        self.assertEqual(physical_offset(3, 0x8005, 65536), 49157)
        self.assertEqual(physical_offset(2, 0xBFFF, 65536), 49151)

    def test_rejects_non_rom_windows_and_outside_physical_banks(self):
        for bank, address in ((-1, 0x8000), (4, 0x8000), (0, 0x3FFF),
                              (0, 0xC000)):
            with self.subTest(bank=bank, address=address):
                with self.assertRaises(ValueError):
                    physical_offset(bank, address, 65536)

    def test_read_trace_preserves_phase_and_aliases(self):
        reader = getattr(compact, 'read_trace', None)
        self.assertIsNotNone(reader, 'phase-aware physical trace reader missing')
        phases = reader('startup,5\nruntime,16389\nruntime,5\nruntime,16389\n', 32768)
        self.assertEqual(phases, {'startup': {5}, 'runtime': {5, 16389}})

    def test_read_trace_rejects_unknown_phase_truncation_and_invalid_bank(self):
        reader = getattr(compact, 'read_trace', None)
        self.assertIsNotNone(reader, 'validated physical trace reader missing')
        for text in ('runtime,32768\n', 'runtime,-1\n', 'foo,5\n',
                     'runtime\n', 'runtime,1,2\n', 'runtime,nan\n', ''):
            with self.subTest(trace=text):
                with self.assertRaises(ValueError):
                    reader(text, 32768)


if __name__ == '__main__':
    unittest.main()
