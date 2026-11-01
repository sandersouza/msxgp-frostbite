import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardDeviceRouteTests(unittest.TestCase):
    def test_inputs_use_the_active_controller_before_a_turn_swap(self):
        api=importlib.import_module('hazard_play')
        neutral={'swcha':255,'swchb':63,'fire':[False,False]};active={'swcha':239,'swchb':63,'fire':[True,False]}
        first=[0]*128;second=[0]*128;second[0x47]=1
        points=[{'ram':first,'input':neutral},{'ram':second,'input':active}]
        self.assertEqual(api.input_records([neutral,active],points),bytes([255,63,0,0,239,63,1,0]))

    def test_missing_or_inactive_device_inputs_cannot_pass(self):
        api=importlib.import_module('hazard_play');ram=[0]*128
        sample={'swcha':255,'swchb':63,'fire':[False,True]}
        with self.assertRaises(ValueError):api.input_records([sample],[{'ram':ram,'input':sample}])
        with self.assertRaises(ValueError):api.input_records([], [{'ram':ram,'input':sample}])
