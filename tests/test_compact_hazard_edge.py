"""Hand-derived hidden-clock cases independent of copyrighted source assets."""
import unittest
import importlib.util
from pathlib import Path


class HazardEdgeTests(unittest.TestCase):
    def model(self):
        p=Path(__file__).resolve().parents[1]/'scripts/compact_hazard_edge.py'
        self.assertTrue(p.exists(),'compact hazard edge compiler missing')
        s=importlib.util.spec_from_file_location('hazard_edge_model',p)
        m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

    def test_copy_at_eight_can_be_next_copy_without_hidden_pixels(self):
        m=self.model()
        self.assertEqual(m.ordinary_context(0,152,1),(255,255,0,0))
        self.assertEqual(m.ordinary_context(1,0,0),(8,7,255,1))
        self.assertEqual(m.ordinary_context(0,159,0),(8,8,255,0))

    def test_new_copy_samples_stopped_player_and_keeps_byte_equality(self):
        m=self.model();glyph=bytes([0]*7+[128])
        self.assertEqual(m.ordinary_program(glyph,m.ordinary_context(0,8,0))[0],(1,0,0,0,0))
        self.assertEqual(m.ordinary_program(glyph,m.ordinary_context(1,8,0))[0],(0,2,1,0,1))

    def test_eighth_visual_row_is_clipped_at_source_latch_read(self):
        m=self.model();glyph=bytes([128]+[0]*7)
        self.assertEqual(m.ordinary_program(glyph,m.ordinary_context(24,24,0))[7],(0,0,0,0,128))
        self.assertEqual(m.ordinary_program(glyph,m.ordinary_context(25,25,0))[7],(0,0,0,0,0))

    def test_wide_pixels_wrap_without_rotation_artifacts(self):
        m=self.model()
        self.assertEqual(m.expanded_bear_byte(128),49152)
        self.assertEqual(m.expanded_bear_byte(1),3)
        self.assertEqual(m.wide_mask(128,0,0),192)
        self.assertEqual(m.wide_mask(128,1,0),128)
        self.assertEqual(m.wide_mask(1,9,159),12)

    def test_first_bear_row_keeps_fine_motion_and_delayed_sample(self):
        m=self.model()
        self.assertEqual(m.bear_position(0),(6,14,12))
        self.assertEqual(m.bear_position(14),(20,0,12))
        self.assertEqual(m.bear_position(15),(16,14,22))
        self.assertEqual(m.bear_position(159),(0,5,157))
        glyph=bytes([0]*18+[128])
        self.assertEqual(m.shore_program(glyph,0,0)[0],(1,0,0,0,0))
        self.assertEqual(m.shore_program(glyph,8,0)[0],(0,0,128,0,0))

    def test_rejects_partial_or_unqualified_source_shapes(self):
        m=self.model()
        with self.assertRaises(ValueError):m.ordinary_program(bytes(7),(0,0,0,0))
        with self.assertRaises(ValueError):m.ordinary_program([999]*8,(255,255,255,80))
        with self.assertRaises(ValueError):m.shore_program(bytes([128]+[0]*18),0,0)
        with self.assertRaises(ValueError):m.ordinary_context(160,0,0)


if __name__=='__main__':unittest.main()
