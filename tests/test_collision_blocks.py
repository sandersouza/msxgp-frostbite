import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class CollisionBlockTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('collision_blocks'),'lossless collision blocks are missing')
        return importlib.import_module('collision_blocks')

    def test_block_boundaries_and_far_coordinate_remain_exact(self):
        api=self.api();packer=importlib.import_module('floe_tables').BankPacker()
        rows=[bytes(58)]*160
        for x,value in ((0,1),(15,2),(16,4),(159,8)):rows[x]=bytes([value])+bytes(57)
        root=api.put_row(packer,rows)
        def read(location,size):
            bank,address=location
            return bytes(packer.banks[bank-14][address-0x8000:address-0x8000+size])
        def pointer(raw):return raw[2],int.from_bytes(raw[:2],'little')
        for index,want in ((0,1),(15,2),(16,4),(42,0),(159,8)):
            block=pointer(read((root[0],root[1]+index//16*3),3))
            leaf=pointer(read((block[0],block[1]+index%16*3),3))
            self.assertEqual(read(leaf,58),bytes([want])+bytes(57))
            self.assertEqual(api.read_row(packer.banks,14,root,index,58),bytes([want])+bytes(57))

    def test_bank_crossing_never_creates_a_straddling_pointer(self):
        api=self.api();packer=importlib.import_module('floe_tables').BankPacker()
        packer.put(bytes([219])*16380)
        rows=[bytes([index%17])*58 for index in range(160)]
        root=api.put_row(packer,rows)
        for index in range(160):self.assertEqual(api.read_row(packer.banks,14,root,index,58),rows[index])
        for index in (-1,160):
            with self.assertRaises(ValueError):api.read_row(packer.banks,14,root,index,58)
        with self.assertRaises(ValueError):api.read_row(packer.banks,14,(255,0x8000),0,58)
        with self.assertRaises(ValueError):api.read_row(packer.banks,14,(root[0],0xBFFF),159,58)

    def test_incomplete_rows_cannot_be_compiled(self):
        api=self.api();packer=importlib.import_module('floe_tables').BankPacker()
        for rows in ([bytes(58)]*159,[bytes(58)]*159+[b''],[bytes(58)]*159+[bytes(57)]):
            with self.assertRaises(ValueError):api.put_row(packer,rows)
