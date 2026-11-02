"""Sparse world composition has exact typed unions and fixed fused rows."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class PresentationFastModelTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fast_model'),'sparse constructor model missing')
        return importlib.import_module('presentation_fast_model')
    def test_object_and_floe_shared_cell_uses_the_exact_three_row_grammar(self):
        api=self.api()
        layer=lambda role,index,row,mask,color:{'role':role,'id':index,'pattern':bytes(mask if y==row else 0 for y in range(8)),'color':color}
        key=api.combine_cell([layer('object',2,0,170,2),layer('floe',3,7,204,15)],128,row=20,column=10,coarse=False)
        self.assertEqual(key,bytes((170,204,0,47,0,1)))
        with self.assertRaises(ValueError):api.combine_cell([layer('object',2,2,170,2),layer('floe',3,7,204,15)],128,row=20,column=10,coarse=False)
    def test_separated_floe_planes_keep_both_ids_and_viewport_clipping(self):
        api=self.api();one={'role':'floe','id':7,'pattern':bytes((240,))*8,'color':15};two={'role':'floe','id':8,'pattern':bytes((15,))*8,'color':15}
        self.assertEqual(api.combine_cell([one,two],128,row=18,column=10,coarse=False),bytes((7,0,8,0,244,7)))
        self.assertEqual(api.combine_cell([one,two],128,row=18,column=2,coarse=False),bytes((8,0,128,1,15,0)))
