import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compact_footer_vram import allocation

ATLAS=tuple(range(144,160))+tuple(range(204,250))
CREDIT=tuple(range(134,144))+tuple(range(250,254))


class FooterVramAllocation(unittest.TestCase):
    def test_unused_tile_pairs_are_bounded_and_disjoint(self):
        rows=allocation((56,60,50),(27,5,6),ATLAS,CREDIT,188)
        self.assertEqual(len(rows),188)
        self.assertEqual((rows[0]['bank'],rows[0]['tile']),(0,56))
        self.assertEqual((rows[-1]['bank'],rows[-1]['tile']),(2,51))
        occupied=set()
        for r in rows:
            bank=r['bank'];tile=r['tile'];count=(56,60,50)[bank]
            self.assertNotIn(tile,range(count))
            self.assertNotIn(tile,range(64,64+count))
            self.assertNotIn(tile,range(128,128+(27,5,6)[bank]))
            if bank in (1,2):self.assertNotIn(tile,ATLAS)
            if bank==2:
                self.assertNotIn(tile,range(160,204))
                self.assertNotIn(tile,CREDIT)
            self.assertEqual(r['pattern'],bank*2048+tile*8)
            self.assertEqual(r['color'],r['pattern']+8192)
            for start in (r['pattern'],r['color']):
                addresses=set(range(start,start+8))
                self.assertFalse(occupied&addresses)
                self.assertTrue(addresses<=set(range(6144))|set(range(8192,14336)))
                occupied|=addresses
        self.assertEqual(len(occupied),3008)

    def test_insufficient_capacity_is_rejected(self):
        with self.assertRaises(ValueError):allocation((64,64,64),(128,128,128),ATLAS,CREDIT,1)

    def test_duplicate_reserved_ids_do_not_create_false_capacity(self):
        self.assertEqual(allocation((56,60,50),(27,5,6),ATLAS+ATLAS,CREDIT+CREDIT,188),allocation((56,60,50),(27,5,6),ATLAS,CREDIT,188))
