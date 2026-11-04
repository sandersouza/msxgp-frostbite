import unittest

from presentation_shared_ice import SharedIce


class SharedIceTests(unittest.TestCase):
    def test_changed_inactive_row_preserves_both_other_pages_and_rows(self):
        pool = SharedIce()
        a = pool.replace(0, 0, [(i, 15) for i in range(1, 15)])
        b = pool.replace(1, 1, [(i, 5) for i in range(20, 34)])
        for step in range(10):
            pool.replace(1, 0, [(100 + step * 14 + i, 15) for i in range(14)])
        self.assertEqual(pool.rows[0, 0], a)
        self.assertEqual(pool.rows[1, 1], b)
        self.assertEqual([pool.keys[2][i] for i in a], [(i, 15) for i in range(1, 15)])
        pool.audit()

    def test_shared_key_reuses_physical_slot_and_colors_stay_distinct(self):
        pool = SharedIce()
        white = pool.replace(0, 2, [(0, 15)])
        blue = pool.replace(1, 3, [(7, 5)])
        shared = pool.replace(1, 2, [(0, 15)])
        self.assertEqual(white, shared)
        self.assertNotEqual(white, blue)
        self.assertEqual(pool.refs[1][white[0]], 2)
        pool.audit()

    def test_full_capacity_churn_and_invalid_grammar(self):
        pool = SharedIce()
        for frame in range(100):
            for row in range(4):
                pool.replace(frame % 2, row, [((frame * 100 + row * 14 + i) % 2049, 5 + frame % 2) for i in range(14)])
            pool.audit()
        for keys in ([], [(-1, 5)], [(2049, 5)], [(1, 0)], [(1, 16)], [(1, 5)] * 2, [(i, 5) for i in range(1, 16)]):
            with self.assertRaises(ValueError):
                pool.replace(0, 0, keys)


if __name__ == '__main__':
    unittest.main()
