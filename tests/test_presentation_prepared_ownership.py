import unittest

from presentation_prepared_ownership import decorate_owners


class PreparedOwnershipTests(unittest.TestCase):
    def test_zero_raw_key_and_strict_owner_record(self):
        rom = bytearray(4*1024*1024)
        pointer = b'\x00\x90\x03\x01'
        rom[35*16384+0x3870:35*16384+0x3874] = pointer
        records = bytearray(32);records[:4] = pointer
        tuples = bytearray([255])*32;tuples[:4] = bytes([0,0,0,15])
        colors = bytearray([255])*8;colors[0] = 15
        raw = bytearray(4110);raw[1536:3840] = b'\xff'*2304
        result = decorate_owners(raw,records,tuples,colors,rom,list(range(10)))
        at = 1536+(2*64+25)*6
        self.assertEqual(result[at:at+6],bytes([0,0,129,0,15,9]))
        badrecords = bytearray(records);badrecords[0] = 1
        with self.assertRaises(ValueError):decorate_owners(raw,badrecords,tuples,colors,rom,list(range(10)))
        badcolors = bytearray(colors);badcolors[0] = 5
        with self.assertRaises(ValueError):decorate_owners(raw,records,tuples,badcolors,rom,list(range(10)))
        raw[at] = 0
        with self.assertRaises(ValueError):decorate_owners(raw,records,tuples,colors,rom,list(range(10)))


if __name__=='__main__':unittest.main()
