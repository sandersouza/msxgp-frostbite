"""The left sea edge must close below the last water raster."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class BorderClosureTests(unittest.TestCase):
    def test_names_extend_one_row_and_keep_every_other_cell(self):
        from presentation_border_closure import border_names
        from presentation_border import border_names as parent
        raw=bytes(range(256))*3;expected=bytearray(parent(raw));expected[22*32+2]=128
        self.assertEqual(border_names(raw),bytes(expected))
        self.assertEqual(border_names(raw)[23*32:],raw[23*32:])

    def test_background_closes_the_lower_notch_only(self):
        from presentation_border_closure import close_background
        from graphics_mapping import map_y
        raw=bytes([4])*(256*192);expected=bytearray(raw)
        for y in range(176,184):expected[y*256+16:y*256+24]=bytes([1])*8
        self.assertEqual(close_background(raw),bytes(expected))
        self.assertLess(map_y(184),184)
        self.assertEqual(raw,bytes([4])*(256*192))
        with self.assertRaises(ValueError):close_background(raw[:-1])

if __name__=='__main__':unittest.main()
