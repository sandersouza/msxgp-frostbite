"""Pure declared-view contracts; no original ROM or private artifacts."""
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class Grid24Tests(unittest.TestCase):
    def model(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_grid24'),'grid24 model is missing')
        import presentation_grid24
        return presentation_grid24

    def test_anchors_are_separate_single_tile_rows(self):
        m=self.model()
        self.assertEqual([m.anchor('enemy',i)for i in range(4)],[152,128,104,80])
        self.assertEqual([m.anchor('floe',i)for i in range(4)],[168,144,120,96])
        rows=[m.anchor(k,i)//8 for k in('enemy','floe')for i in range(4)]
        self.assertEqual(len(set(rows)),8)
        self.assertTrue(all(m.anchor(k,i)%8==0 for k in('enemy','floe')for i in range(4)))

    def test_contact_mapping_preserves_landings_and_is_monotone(self):
        m=self.model()
        for coarse in range(2):
            values=[m.contact_y(y,coarse)for y in range(256)]
            self.assertEqual(values,sorted(values))
            self.assertTrue(all(0<=b-a<=7 for a,b in enumerate(values)))
            for y,want in zip((89,115,141,167),(96,120,144,168)):
                self.assertEqual(m.contact_y(y+coarse,coarse),want)
            for y in(0,42,63+coarse,185+coarse,255):self.assertEqual(m.contact_y(y,coarse),y)
            for lane,origin in enumerate((131,105,79,53)):
                delta=m.player_delta(origin,coarse)
                self.assertEqual(origin+39+coarse+delta,m.anchor('floe',lane)+3)

    def test_name_translation_reuses_exact_pattern_ordinals(self):
        m=self.model()
        bases=(25,9,35,19)
        for page in range(2):
            for lane,base in enumerate(bases):
                raw=bytes([129,25+page*64,26+page*64,129,38+page*64]+[129]*25)
                for rotation in range(0,30,3):
                    got=m.names(raw,lane,page,rotation)
                    ordered=raw[-rotation:]+raw[:-rotation]if rotation else raw
                    want=bytes((129 if lane<2 else 130)if x>=128 else x-25+base for x in ordered)
                    self.assertEqual(got,want)
        with self.assertRaises(ValueError):m.names(bytes([24])*30,0,0,0)

    def test_phase_zero_water_uses_destination_bank_background(self):
        m=self.model()
        self.assertEqual(m.names(bytes([129])*30,0,0,0),bytes([129])*30)
        self.assertEqual(m.names(bytes([129])*30,3,1,3),bytes([130])*30)

    def test_positive_world_motion_rotates_name_program_right(self):
        m=self.model()
        raw=bytes([25,26,27]+[129]*27)
        self.assertEqual(m.names(raw,0,0,3),bytes([129]*3+[25,26,27]+[129]*24))

    def test_dirty_masks_cover_each_new_complete_band(self):
        m=self.model()
        for kind in('enemy','floe'):
            for lane in range(4):
                flags=m.span(kind,lane)
                rows=[i for i in range(24)if flags[i//8]&(1<<(i%8))]
                self.assertEqual(rows,[m.anchor(kind,lane)//8])
        for page in range(2):
            self.assertEqual(m.actor_segments(page,1)[0],(2,64*page))

if __name__=='__main__':unittest.main()
