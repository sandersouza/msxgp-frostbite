import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardDomainTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('hazard_domain'),'source hazard domain is missing')
        return importlib.import_module('hazard_domain')

    def test_initial_and_animated_modes_are_not_truncated_at_256(self):
        api=self.api();rom=bytearray(4096)
        rom[0xD0A:0xD12]=bytes([1,2,16,32,48,64,80,96])
        rom[0xDC2:0xDD2]=bytes([0,1,2,3,4]+[0]*11)
        modes=api.object_modes(rom)
        self.assertEqual(len(modes),264)
        self.assertEqual(modes[0],(0,False,0))
        self.assertEqual(modes[263],(100,True,3))
        self.assertEqual(len(api.shapes(rom)),33)
        with self.assertRaises(ValueError):api.shapes(rom[:-1])

    def test_bear_animation_aliases_keep_every_source_pose(self):
        api=self.api();rom=bytearray(4096)
        rom[0xEE7:0xEEF]=bytes([16,16,32,32,48,48,32,32])
        reps,aliases=api.bear_modes(rom)
        self.assertEqual(reps,[0,2,4])
        self.assertEqual(aliases,[0,0,1,1,2,2,1,1])
        rom[0xEE7]=240
        with self.assertRaises(ValueError):api.bear_modes(rom)
