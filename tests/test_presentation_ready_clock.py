import unittest

from presentation_fixed_clock_probe import clocks as legacy_clocks
from presentation_ready_clock import admit_ready, clocks


class ReadyClockTests(unittest.TestCase):
    def setUp(self):
        self.points = [{'ram': [0]*128} for _ in range(10)]
        self.irq = [[i+1, i+90, i/60, 22000, 1, 0, 0] for i in range(9)]
        self.pictures = [[i, i+1, i+1, i/60, i+90, 22000, 193, 202]
                         for i in range(3)]

    def test_ready_picture_at_next_field_is_valid_but_legacy_cap_stays_two(self):
        with self.assertRaisesRegex(ValueError, 'picture cap'):
            legacy_clocks(self.irq, self.pictures, self.points)
        report = clocks(self.irq, self.pictures, self.points)
        self.assertAlmostEqual(report['source_steps_per_second'], 60)
        self.assertAlmostEqual(report['active_pictures_per_second'], 60)

    def test_same_field_and_backwards_commits_are_rejected(self):
        for field in (90, 89):
            with self.subTest(field=field):
                rows = [r[:] for r in self.pictures]
                rows[1][4] = field
                with self.assertRaisesRegex(ValueError, 'picture cap'):
                    clocks(self.irq, rows, self.points)

    def test_missed_hardware_field_remains_an_error(self):
        self.irq[3][1] += 1
        with self.assertRaisesRegex(ValueError, 'missed hardware'):
            clocks(self.irq, self.pictures, self.points)

    def test_late_irq_remains_an_error(self):
        self.irq[3][6] = 1
        with self.assertRaisesRegex(ValueError, 'missed/partial'):
            clocks(self.irq, self.pictures, self.points)

    def test_repeated_snapshot_remains_an_error(self):
        self.pictures[1][1] = self.pictures[0][1]
        with self.assertRaisesRegex(ValueError, 'unordered picture'):
            clocks(self.irq, self.pictures, self.points)

    def test_death_crossing_does_not_inflate_active_rate(self):
        self.points[2]['ram'][0x71] = 128
        self.assertEqual(clocks(self.irq, self.pictures, self.points)
                         ['active_picture_intervals'], 0)

    def test_two_field_records_retain_identical_legacy_metrics(self):
        for row in self.pictures:
            row[4] *= 2
            row[3] *= 2
        self.assertEqual(clocks(self.irq, self.pictures, self.points),
                         legacy_clocks(self.irq, self.pictures, self.points))

    def test_admission_requires_ready_and_a_real_new_uint16_tick(self):
        for last in (0, 1, 65534, 65535):
            self.assertFalse(admit_ready(True, last, last))
            for delta in (1, 2):
                self.assertTrue(admit_ready(True, (last+delta)&65535, last))
                self.assertFalse(admit_ready(False, (last+delta)&65535, last))
        for args in ((1, 1, 0), (True, -1, 0), (True, 65536, 0)):
            with self.assertRaises(ValueError):
                admit_ready(*args)
