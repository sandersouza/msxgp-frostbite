"""The large-player negative must exercise eight visible full rectangles."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PlayerLargeTests(unittest.TestCase):
    def test_fixture_has_eight_visible_patterns_and_four_full_rectangles_per_line(self):
        api=importlib.import_module('presentation_player_large_check')
        from presentation_assets import check_rectangles
        for page in (0,1):
            row=api.expected(page);sat=row[32768+256:32768+256+32];boxes=[]
            self.assertEqual(len(sat),32)
            for index in range(8):
                y,x,pattern,color=sat[index*4:index*4+4]
                self.assertIn(y+1,(32,48));self.assertEqual(pattern,(page*24+index)*4)
                self.assertTrue(any(row[16384+0x3800+pattern*8:16384+0x3820+pattern*8]))
                boxes.append({'x':x,'y':y+1,'width':16,'height':16})
            self.assertEqual(check_rectangles(boxes)['max_per_line'],4)
            if not page:
                old_slots=set(range(18,26));active_slots={row[0x1B02+i*4]//4 for i in range(4)}
                self.assertEqual(old_slots&active_slots,{24,25})

    def test_active_pattern_corruption_and_fallback_field_corruption_fail(self):
        api=importlib.import_module('presentation_player_large_check')
        for page in (0,1):
            row=api.expected(page);api.verify_case(row,row,page)
            bad=bytearray(row);active_slot=(1-page)*24;bad[16384+0x3800+active_slot*32]^=1
            with self.assertRaisesRegex(ValueError,'active'):api.verify_case(bytes(bad),row,page)
            bad=bytearray(row);bad[-6]^=1
            with self.assertRaisesRegex(ValueError,'fields differ'):api.verify_case(bytes(bad),row,page)
            with self.assertRaises(ValueError):api.verify_case(row[:-1],row,page)
