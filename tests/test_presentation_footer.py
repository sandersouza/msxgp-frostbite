"""Footer publication must retain zero cells and define every emitted byte."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class FooterTests(unittest.TestCase):
    def test_fixture_domain_and_zero_descriptor_background_retention(self):
        api=importlib.import_module('presentation_footer_check')
        programs=b''.join(((state+cell)%3).to_bytes(2,'little') for state in range(16) for cell in range(22))
        inputs,expected=api.fixtures(programs,bytes(16)+bytes([23])*16+bytes([179])*16)
        self.assertEqual(len(inputs),78*4);self.assertEqual(len(expected),78*api.ROW_BYTES)
        first=expected[:api.ROW_BYTES]
        self.assertEqual(first[:6],bytes([255])*6)
        self.assertEqual(first[264+22*32+4],165)
        self.assertEqual(first[264+22*32+5],161)
        for index in range(72,78):
            before=expected[(index-1)*api.ROW_BYTES:index*api.ROW_BYTES]
            after=expected[index*api.ROW_BYTES:(index+1)*api.ROW_BYTES]
            self.assertEqual(after[:-2],before[:-2]);self.assertEqual(after[-2:],bytes((1,1)))

    def test_whole_capture_rejects_keys_names_tables_flags_and_truncation(self):
        api=importlib.import_module('presentation_footer_check');row=bytes(api.ROW_BYTES)
        api.verify_row(row,row)
        for at in (0,263,264,1031,1032,1799,1800,api.ROW_BYTES-3,api.ROW_BYTES-2,api.ROW_BYTES-1):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
