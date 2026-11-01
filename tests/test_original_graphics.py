import importlib
import importlib.util
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class OriginalGraphicsTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('original_graphics'),'source extractor missing')
        return importlib.import_module('original_graphics')

    def test_table_view_reverses_rows_reflects_and_doubles_each_pixel(self):
        data=bytearray(4096);data[0x100:0x102]=b'\x80\x03'
        view=self.api().view(bytes(data),0xF100,2,reflect=True,scale=2)
        self.assertEqual(view['width'],16)
        self.assertEqual(view['pixels'],[1,1,1,1]+[0]*12+[0]*14+[1,1])
        self.assertEqual(view['range'],[0xF100,0xF101])

    def test_wrong_rom_and_outside_table_reads_fail(self):
        api=self.api()
        with self.assertRaisesRegex(ValueError,'identity'):api.catalog(bytes(4096))
        for address,height in [(0xEFFF,1),(0xFFFF,2),(0xF000,0)]:
            with self.assertRaises(ValueError):api.view(bytes(4096),address,height)
        with self.assertRaises(ValueError):api.view(bytes(4096),0xF000,1,scale=3)
