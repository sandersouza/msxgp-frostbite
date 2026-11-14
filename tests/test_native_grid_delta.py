import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class GridDelta(unittest.TestCase):
    def test_every_original_translation_is_preserved(self):
        from native_grid_delta import pack,lookup
        from presentation_grid24 import delta_table
        source=delta_table()
        tables=pack(source)
        self.assertEqual(sum(map(len,tables)),56)
        for coarse in range(2):
            for y in range(256):self.assertEqual(lookup(tables[coarse],y),source[coarse*256+y])
    def test_nonconstant_initial_row_is_explicit(self):
        from native_grid_delta import pack,lookup
        data=bytes([3]*256+[7]*256)
        tables=pack(data)
        self.assertEqual(tables,(b'\0\3',b'\0\7'))
        self.assertEqual(lookup(tables[1],255),7)
    def test_partial_and_unbounded_input_is_rejected(self):
        from native_grid_delta import pack,lookup
        for data in (b'',bytes(511),bytes(513)):
            with self.assertRaises(ValueError):pack(data)
        for table,y in ((b'\0',1),(b'\1\3',0),(b'\0\1\0\2',3),(b'\0\1',256)):
            with self.assertRaises(ValueError):lookup(table,y)
