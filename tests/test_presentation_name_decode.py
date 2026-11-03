"""Nibble expansion evidence preserves all owners, including clipped masks."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class NameDecodeTests(unittest.TestCase):
    def test_fixed_role_microbudget_rejects_the_old_generic_timing(self):
        api=importlib.import_module('presentation_name_decode_check');inputs,_=api.fixtures()
        times=[(index,3721) for index in range(len(inputs)//34)]
        with self.assertRaises(ValueError):api.fast_timing(inputs,times)
        times=[(index,2735) for index in range(len(inputs)//34)]
        self.assertEqual(api.fast_timing(inputs,times)['fixed_role_cases'],2048)
        with self.assertRaises(ValueError):api.fast_timing(inputs,times[:100])

    def test_complete_cross_product_and_invalid_destinations(self):
        api=importlib.import_module('presentation_name_decode_check');inputs,expected=api.fixtures();seen={}
        for index in range(40960):
            data=inputs[index*34:index*34+34];key=(data[0],data[1],int.from_bytes(data[2:4],'little'))
            seen.setdefault(key,set()).add(data[4])
        self.assertEqual(len(seen),160)
        for phases in seen.values():self.assertEqual(phases,set(range(256)))
        self.assertEqual(len(inputs),40967*34);self.assertEqual(len(expected),40967*api.ROW_BYTES)
        retained=expected[40959*api.ROW_BYTES:40960*api.ROW_BYTES-1]
        for index in range(40960,40967):
            row=expected[index*api.ROW_BYTES:(index+1)*api.ROW_BYTES]
            self.assertEqual(row[:-1],retained);self.assertEqual(row[-1],1)

    def test_whole_capture_rejects_cache_code_table_carry_and_truncation(self):
        api=importlib.import_module('presentation_name_decode_check');row=bytes(api.ROW_BYTES)
        api.verify_row(row,row)
        for at in (0,59,63,256,511,512,527,528):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
