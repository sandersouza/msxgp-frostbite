import unittest
from presentation_experiment_report import measured_io_cost


class ExperimentIOTests(unittest.TestCase):
    def test_both_measured_io_paths_include_their_own_msx_setup(self):
        self.assertEqual(measured_io_cost(256,3,0),29*256+53*3)
        self.assertEqual(measured_io_cost(256,3,2),53+(33*128+55)*2)
        for values in ((127,1,1),(128,0,1),(128,1,-1)):
            with self.assertRaises(ValueError):measured_io_cost(*values)


if __name__=='__main__':unittest.main()
