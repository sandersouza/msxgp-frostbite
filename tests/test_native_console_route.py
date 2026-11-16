import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from native_console_route import samples, assess


class ConsoleContractTests(unittest.TestCase):
    def test_explicit_raw_opposite_directions_and_reset_select(self):
        inputs, marks = samples()
        self.assertEqual(inputs[marks['wake']]['swchb'], 60)
        self.assertIn(207, [s['swcha'] for s in inputs])
        self.assertIn(63, [s['swcha'] for s in inputs])
        self.assertGreater(marks['wake'], 2040)

    def test_boot_alone_never_satisfies_attract_reentry(self):
        inputs, marks = samples()
        points = [dict(index=i, ram=[0]*128) for i in range(len(inputs))]
        with self.assertRaisesRegex(ValueError, 'attract'):
            assess(points, marks)
