"""Literal aligned-edge and actual hardware rectangle contracts."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class BorderTests(unittest.TestCase):
    def model(self):
        import presentation_border
        return presentation_border

    def test_left_masks_include_wholly_hidden_and_unaliased_x10(self):
        m=self.model()
        self.assertEqual([m.left_mask(x)for x in(0,1,2,7,8,9,10)],
                         [0,0,0x0007,0x01ff,0x0fff,0x0fff,0x7fff])
        self.assertNotEqual(m.left_mask(2),m.left_mask(10))
        with self.assertRaises(ValueError):m.left_mask(11)

    def test_border_changes_only_column2_in_former_mask_rows(self):
        m=self.model();raw=bytes(range(256))*3
        got=m.border_names(raw)
        expected=bytearray(raw)
        for row in range(8,22):expected[row*32+2]=128
        self.assertEqual(got,bytes(expected));self.assertEqual(raw,bytes(range(256))*3)

    def test_four_rectangles_fit_without_phantom_mask(self):
        m=self.model()
        self.assertTrue(m.eligible(0,80,104,[(103,),(103,),(103,)],7))
        self.assertFalse(m.eligible(0,80,104,[(103,)]*4,8))
        self.assertTrue(m.eligible(3,80,104,[(87,)],7))
        self.assertFalse(m.eligible(0,80,104,[],31))

    def test_waiting_normalized_zero_and_multicopy_edges_do_not_emit(self):
        m=self.model()
        for raw in(0,160):self.assertFalse(m.eligible(0,raw,104,[],4))
        self.assertFalse(m.eligible(1,10,104,[],4))
        self.assertTrue(m.eligible(0,10,104,[],4))
        self.assertTrue(m.eligible(1,11,104,[],4))

if __name__=='__main__':unittest.main()
