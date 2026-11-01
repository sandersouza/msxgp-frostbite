import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class CompactCollisionTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('collision_compact'),'compact exact collision storage is missing')
        return importlib.import_module('collision_compact')

    def test_each_record_keeps_its_own_uniform_shadow_without_y_factoring(self):
        api=self.api();zero=bytes(58);shadow=bytes([255])*28+b'\x0f'
        raw=b'\x01'+bytes(28)+shadow
        self.assertEqual(api.encode_record(raw),b'\x01'+bytes(28)+b'\x40')
        self.assertEqual(api.decode_record(b'\x01'+bytes(28)+b'\x40'),raw)
        self.assertEqual(api.encode_record(zero),bytes(30))
        with self.assertRaises(ValueError):api.encode_record(bytes(29)+b'\x01'+bytes(28))
        with self.assertRaises(ValueError):api.decode_record(bytes(29)+b'\x01')
        with self.assertRaises(ValueError):api.encode_record(bytes(28)+b'\x10'+bytes(29))

    def test_sparse_row_boundaries_keep_zero_and_shadow_only_cells(self):
        api=self.api();table=api.CompactRows();rows=[bytes(58)]*160
        for x,value in ((0,1),(15,2),(16,4),(159,8)):rows[x]=bytes([value])+bytes(57)
        rows[42]=bytes(29)+bytes([255])*28+b'\x0f'
        row=table.intern_row(rows);packed=table.emit(14)
        for index in (0,15,16,31,42,47,48,159):
            self.assertEqual(api.read_row(packed.banks,packed.metadata,packed.rows[row],index),rows[index])
        for index in (-1,160):
            with self.assertRaises(ValueError):api.read_row(packed.banks,packed.metadata,packed.rows[row],index)
        with self.assertRaises(ValueError):table.intern_row(rows[:-1])

    def test_slot_bank_crossing_and_corrupt_ids_are_not_silently_truncated(self):
        api=self.api();table=api.CompactRows();ids=[]
        for n in range(520):
            raw=(n+1).to_bytes(2,'little')+bytes(56)
            ids.append(table.intern_row([raw]+[bytes(58)]*159))
        packed=table.emit(14)
        for n in (0,510,511,512,519):
            self.assertEqual(api.read_row(packed.banks,packed.metadata,packed.rows[ids[n]],0),
                             (n+1).to_bytes(2,'little')+bytes(56))
        with self.assertRaises(ValueError):table.emit(255)
        bad=[bytearray(bank) for bank in packed.banks]
        bad[packed.metadata['block_bank']-14][:2]=b'\xff\xff'
        with self.assertRaises(ValueError):api.read_row(bad,packed.metadata,packed.rows[ids[0]],0)

    def test_preinterned_zero_tail_is_byte_exact_and_rejects_unknown_ids(self):
        api=self.api();table=api.CompactRows();raw=b'\x05'+bytes(57)
        record=table.intern_record(raw)
        root=table.intern_indices([record]+[0]*159)
        self.assertEqual(root,table.intern_row([raw]+[bytes(58)]*159))
        with self.assertRaises(ValueError):table.intern_indices([record+1]+[0]*159)
        with self.assertRaises(ValueError):table.intern_indices([record]*159)

    def test_nibble_rank_roots_retain_all_ten_blocks_without_a_scan(self):
        api=self.api();table=api.CompactRows(row_format='nibble');rows=[bytes(58)]*160
        for block in (0,1,4,8,9):rows[block*16+15]=bytes([block+1])+bytes(57)
        root=table.intern_row(rows);packed=table.emit()
        self.assertEqual(packed.metadata['row_format'],'nibble')
        for x in range(160):self.assertEqual(api.read_row(packed.banks,packed.metadata,packed.rows[root],x),rows[x])
        bank,address=packed.rows[root];offset=address-0x8000
        self.assertEqual(bytes(packed.banks[bank-14][offset:offset+5]),bytes([0x21,0,3,0,0x54]))
        bad=[bytearray(bank) for bank in packed.banks];bad[bank-14][offset]=0x31
        with self.assertRaises(ValueError):api.read_row(bad,packed.metadata,packed.rows[root],15)
        with self.assertRaises(ValueError):api.CompactRows(row_format='unknown')
