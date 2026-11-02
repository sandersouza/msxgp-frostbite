"""Variant evidence must check every retained way and every key bit."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PlayerVariantsTests(unittest.TestCase):
    def test_uncacheable_fallback_invalidates_only_its_own_generation(self):
        api=importlib.import_module('presentation_player_variants_check');inputs,expected=api.fixtures();checked=set()
        for index in range(1,len(inputs)//api.INPUT_BYTES):
            data=inputs[index*api.INPUT_BYTES:(index+1)*api.INPUT_BYTES]
            if data[0]!=2 or data[1]>1:continue
            page=data[1];before=bytearray(expected[(index-1)*api.ROW_BYTES:index*api.ROW_BYTES]);row=expected[index*api.ROW_BYTES:(index+1)*api.ROW_BYTES]
            for way in range(4):before[page*128+way*32]=0
            self.assertEqual(row[:258],before[:258]);self.assertEqual(row[-2],0);checked.add(page)
        self.assertEqual(checked,{0,1})

    def test_stateful_domain_visits_every_way_and_preserves_invalid_bounds(self):
        api=importlib.import_module('presentation_player_variants_check');inputs,expected=api.fixtures();seen=set();keys=set()
        for index in range(len(inputs)//api.INPUT_BYTES):
            data=inputs[index*api.INPUT_BYTES:(index+1)*api.INPUT_BYTES];row=expected[index*api.ROW_BYTES:(index+1)*api.ROW_BYTES]
            page=data[1];keys.add(data[-7:])
            if page<2:
                way=row[-2];seen.add((page,way));pointer=int.from_bytes(row[259:261],'little')
                self.assertEqual(pointer,0xC080+page*128+way*32)
                self.assertEqual(row[258],page*96+way*24);self.assertLessEqual(row[258]+5*4,188)
            else:
                before=expected[(index-1)*api.ROW_BYTES:index*api.ROW_BYTES]
                self.assertEqual(row[:-1],before[:-1]);self.assertEqual(row[-1],1)
        self.assertEqual(seen,{(page,way) for page in (0,1) for way in range(4)})
        for field in range(7):
            for bit in range(8):self.assertIn(bytes(1<<bit if i==field else 0 for i in range(7)),keys)

    def test_whole_capture_rejects_metadata_cursor_pointer_way_and_carry(self):
        api=importlib.import_module('presentation_player_variants_check');row=bytes(api.ROW_BYTES)
        api.verify_row(row,row)
        for at in (0,31,127,128,255,256,257,258,259,260,261,262):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
