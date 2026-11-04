import unittest
from presentation_residency import Residency
from presentation_residency_probe import capture_records


class ResidencyTests(unittest.TestCase):
    def test_capture_format_and_display_page_are_validated(self):
        record = bytearray(49304)
        record[49298] = 6
        self.assertEqual(list(capture_records(record)), [(record[:128], 0)])
        record[49298] = 7
        self.assertEqual(list(capture_records(record))[0][1], 1)
        for invalid in (b'', record[:-1], record + b'x'):
            with self.assertRaises(ValueError):
                list(capture_records(invalid))
        record[49298] = 8
        with self.assertRaises(ValueError):
            list(capture_records(record))

    def test_preserves_displayed_slots_and_reuses_older_content(self):
        cache = Residency(3)
        first, misses = cache.prepare(['a', 'b'], set())
        second, misses = cache.prepare(['b', 'c'], {'a', 'b'})
        self.assertEqual(misses, 1)
        self.assertEqual(first['b'], second['b'])
        third, misses = cache.prepare(['a', 'c'], {'b', 'c'})
        self.assertEqual(misses, 0)
        self.assertEqual(first['a'], third['a'])

    def test_capacity_failure_is_atomic_and_never_evicts_active_tile(self):
        cache = Residency(2)
        cache.prepare(['a', 'b'], set())
        before = dict(cache.slots)
        with self.assertRaises(ValueError):
            cache.prepare(['c'], {'a', 'b'})
        self.assertEqual(cache.slots, before)

    def test_identical_masks_with_different_colors_are_distinct(self):
        white = (b'\x81' * 8, 15)
        blue = (b'\x81' * 8, 5)
        cache = Residency(2)
        names, misses = cache.prepare([white, blue, white], set())
        self.assertEqual(misses, 2)
        self.assertNotEqual(names[white], names[blue])


if __name__ == '__main__':
    unittest.main()
