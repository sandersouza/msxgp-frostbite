import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardQueryTests(unittest.TestCase):
    def test_all_four_odd_rows_and_shore_use_the_actual_view_and_keep_count_zero(self):
        api=importlib.import_module('hazard_query');query=api.RawContacts.__new__(api.RawContacts)
        class Floes:
            def contacts(self,ram):return {'rows':bytes([71,7,7,7,135,7,7,7]),'shore':7}
        query.floes=Floes();seen=[]
        def row(ram,index):
            seen.append((index,ram[0x58+index]));data=bytearray(58);data[28]=8;return bytes(data)
        query.row_record=row;query.shore_record=lambda ram:bytes(28)+b'\x08'+bytes(29)
        ram=bytearray(128);ram[0x6E]=5;ram[0x6B]=18;ram[0x6C]=8;ram[0x6D]=199
        got=query.contacts(ram)
        self.assertEqual(got,{'rows':bytes([71,135,7,135,135,135,7,135]),'shore':135})
        self.assertEqual(seen,[(0,0),(1,0),(2,0),(3,0)])
        self.assertEqual(ram[0x6D],199)
        ram[0x3F]=128;self.assertEqual(query.contacts(ram),{'rows':bytes([7])*8,'shore':7})
        self.assertEqual(len(seen),4)

    def test_only_the_source_normalized_vertical_domains_are_sampled(self):
        api=importlib.import_module('hazard_query')
        self.assertEqual([api.row_y(y,row) for row,y in enumerate((131,105,79,53))],[53]*4)
        for row in range(4):
            shift=(3-row)*26
            self.assertEqual(api.row_y(31+shift,row),0);self.assertEqual(api.row_y(66+shift,row),0)
        for y in (0,3,57,255):self.assertEqual(api.shore_y(y),0)
        self.assertEqual(api.shore_y(4),4);self.assertEqual(api.shore_y(56),56)
