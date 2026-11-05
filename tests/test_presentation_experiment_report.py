import unittest
from presentation_experiment_report import measured_io_cost


class ExperimentIOTests(unittest.TestCase):
    def test_both_measured_io_paths_include_their_own_msx_setup(self):
        self.assertEqual(measured_io_cost(256,3,0),29*256+53*3)
        self.assertEqual(measured_io_cost(256,3,2),53+(33*128+55)*2)
        for values in ((127,1,1),(128,0,1),(128,1,-1)):
            with self.assertRaises(ValueError):measured_io_cost(*values)

    def test_mixed_ice_and_enemy_fill_lengths(self):
        self.assertEqual(measured_io_cost(208,4,3,176),29*32+53+33*176+55*3)
        for values in ((24,1,1,25),(48,1,2,48),(48,2,1,-1),(48,2,0,24)):
            with self.assertRaises(ValueError):measured_io_cost(*values)


if __name__=='__main__':unittest.main()
