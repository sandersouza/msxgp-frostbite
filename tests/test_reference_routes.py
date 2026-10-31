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
        return ([self.point(x,100) for x in range(64,32,-1)] + [self.point(7,84) for _ in range(32)],
                [self.point(7,bear) for bear in (84,24,16,15)] + [self.point(7,15) for _ in range(64)])

    def test_refuge_requires_airborne_access_then_blocked_bear_approach(self):
        approach, wait = self.fixtures()
        approach[10]['ram'][0x64]=53;approach[10]['ram'][0x6A]=15
        result = self.api().assess_refuge(approach,wait)
        self.assertEqual(result['refuge_x'], 7)
        self.assertEqual((result['bear_min'],result['bear_max']), (15,100))
        self.assertTrue(result['bear_blocked_at_edge'])

    def test_refuge_approach_uses_down_and_up_jumps(self):
        api=self.api();self.assertTrue(hasattr(api,'refuge_approach'),'natural jumping approach missing')
        steps=api.refuge_approach()
        self.assertEqual(len(steps),288)
        self.assertEqual(steps[196]['swcha'],0x9F)
        self.assertEqual(steps[226]['swcha'],0xAF)

    def test_hit_jump_life_loss_and_partial_sweep_are_failures(self):
        for address,value in ((0xED,0x80),(0xEA,1),(0xCC,2),(0xF1,0x10)):
            approach,wait=self.fixtures();wait[3]['ram'][address-0x80]=value
            with self.subTest(address=address),self.assertRaises(ValueError):
                self.api().assess_refuge(approach,wait)
        approach,wait=self.fixtures()
        with self.assertRaises(ValueError): self.api().assess_refuge(approach,wait[:3])
