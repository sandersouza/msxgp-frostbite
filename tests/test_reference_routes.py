import copy
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class RefugeRouteTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('reference_routes'), 'natural refuge route checker missing')
        return importlib.import_module('reference_routes')

    def point(self, x, bear):
        ram = [0]*128
        for address,value in {0xCB:4, 0xCC:3, 0xE4:0x1B, 0xE6:x, 0xE8:bear}.items():
            ram[address-0x80] = value
        return {'ram':ram}

    def fixtures(self):
        return ([self.point(x,100) for x in range(64,32,-1)] + [self.point(8,84) for _ in range(32)],
                [self.point(8,bear) for bear in (84,24,16,24,128,140,128)])

    def test_refuge_requires_left_plateau_grounded_no_hit_and_bear_sweep(self):
        approach, wait = self.fixtures()
        result = self.api().assess_refuge(approach,wait)
        self.assertEqual(result['refuge_x'], 8)
        self.assertEqual((result['bear_min'],result['bear_max']), (16,140))
        self.assertEqual(result['bear_direction_reversals'],2)

    def test_hit_jump_life_loss_and_partial_sweep_are_failures(self):
        for address,value in ((0xED,0x80),(0xEA,1),(0xCC,2),(0xF1,0x10)):
            approach,wait=self.fixtures();wait[3]['ram'][address-0x80]=value
            with self.subTest(address=address),self.assertRaises(ValueError):
                self.api().assess_refuge(approach,wait)
        approach,wait=self.fixtures()
        with self.assertRaises(ValueError): self.api().assess_refuge(approach,wait[:3])
