"""Shoreline translation is safe only outside both source color races."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PlayerShoreTests(unittest.TestCase):
    def test_all_masks_and_reflections_are_safe_at_the_proved_bounds(self):
        api=importlib.import_module('presentation_player_shore_check')
        self.assertEqual(api.symbolic(),30720)

    def test_neighboring_race_positions_do_not_satisfy_the_same_invariant(self):
        api=importlib.import_module('presentation_player_shore_check')
        row={'pattern':255,'prefix_pattern':0,'color':1,'prefix_color':2,'suffix_color':3,
             'update_x':22,'color_update_x':22,'suffix_x':91}
        whole=((True,1),)*8
        self.assertEqual(api.row_pixels(row,24,False),whole);self.assertEqual(api.row_pixels(row,83,False),whole)
        self.assertNotEqual(api.row_pixels(row,21,False),whole);self.assertNotEqual(api.row_pixels(row,84,False),whole)
