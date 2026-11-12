import unittest
from presentation_bear_native import raw_pattern,prepared_packet,row_strip

class NativeBearTests(unittest.TestCase):
    def test_prepared_packet_has_exact_ids_and_nine_context_indexes(self):
        ids=list(range(12));indexes=[tuple(range(i*9,i*9+9))for i in range(12)]
        p=prepared_packet(4,3,ids,indexes)
        self.assertEqual(len(p),256);self.assertEqual(p[240:243],bytes((4,3,24)))
        self.assertEqual(p[20:22],bytes((1,0)));self.assertEqual(p[22:40],b''.join(n.to_bytes(2,'little')for n in indexes[1]))
        with self.assertRaises(ValueError):prepared_packet(4,3,ids,indexes[:11])
        p=prepared_packet(3,3,ids[:9],indexes[:9]);self.assertEqual(p[180:240],bytes(60));self.assertEqual(p[240:243],bytes((3,3,18)))
        flagged=list(indexes);flagged[0]=(0x8000,)+indexes[0][1:]
        self.assertEqual(prepared_packet(4,3,ids,flagged)[2:4],bytes((0,128)))
    def test_bulk_row_keeps_four_pgt_then_four_cgt(self):
        tiles=[bytes([i])*8+bytes([i+4])*8 for i in range(1,5)]
        self.assertEqual(row_strip(tiles),b''.join(t[:8]for t in tiles)+b''.join(t[8:]for t in tiles))
        with self.assertRaises(ValueError):row_strip(tiles[:3])
    def test_half_decoding_uses_actual_rom_namespace(self):
        rom=bytearray(32768);base=16384;rom[base+4:base+8]=bytes((0,0,1,0));rom[base+16:base+24]=b'ABCDEFGH'
        self.assertEqual(raw_pattern(rom,[1],16,1,2),b'ABCDEFGH')
        with self.assertRaises(ValueError):raw_pattern(rom,[1],16,2,2)
