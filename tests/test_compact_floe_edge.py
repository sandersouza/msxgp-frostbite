"""Synthetic clock windows and hand-derived edge masks; no source ROM needed."""
import unittest
import importlib.util
from pathlib import Path


class EdgeMaskTests(unittest.TestCase):
    def model(self):
        path=Path(__file__).resolve().parents[1]/'scripts/compact_floe_edge.py'
        self.assertTrue(path.exists(),'analytic edge compiler missing')
        spec=importlib.util.spec_from_file_location('edge_model',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

    def test_window_and_stopped_counter_hold_the_last_sample(self):
        m=self.model()
        self.assertEqual(m.rectangle_window(0),255)
        self.assertEqual(m.rectangle_window(159),510)
        self.assertEqual(m.held_window(159,0),0)
        self.assertEqual(m.held_window(159,1),0)
        self.assertEqual(m.held_window(159,2),65534)
        self.assertEqual(m.held_window(0,0),65535)
        self.assertEqual(m.rectangle_window(32),255)
        self.assertEqual(m.rectangle_window(96),0)

    def test_hidden_clock_bits_align_and_wrap_to_player_bits(self):
        m=self.model()
        self.assertEqual(m.player_mask(1,0),128)
        self.assertEqual(m.player_mask(1,159),64)
        self.assertEqual(m.player_mask(1,154),2)
        self.assertEqual(m.player_mask(255,8),0)
        self.assertEqual(m.player_mask(255,80),0)
        self.assertEqual(m.player_mask(255,1),254)

    def test_clear_line_keeps_stale_last_pixel_and_excludes_disabled_missile(self):
        m=self.model()
        # P1 counter2 samples the first filled pixel, then advances eight times.
        # Its last pixel remains latched while the next sample is already blank.
        self.assertEqual(m.edge_row_masks(2,100,8,8,1,7),(254,0,1,248))
        self.assertEqual(m.edge_row_masks(2,100,8,8,0,7),(255,0,0,252))

    def test_visible_clip_keeps_only_regular_clocks_eight_to_159(self):
        m=self.model()
        self.assertEqual(m.visible_player_mask(0),0)
        self.assertEqual(m.visible_player_mask(1),1)
        self.assertEqual(m.visible_player_mask(8),255)
        self.assertEqual(m.visible_player_mask(80),255)
        self.assertEqual(m.visible_player_mask(154),252)
        self.assertEqual(m.visible_player_mask(159),128)

    def test_rejects_outside_finite_clock_domain(self):
        m=self.model()
        for args in ((-1,0,8,8,0,0),(0,160,8,8,0,0),(0,0,16,8,0,0),(0,0,8,8,160,0),(0,0,8,8,0,8)):
            with self.assertRaises(ValueError):m.edge_row_masks(*args)


if __name__=='__main__':unittest.main()
