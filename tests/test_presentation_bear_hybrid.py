import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from presentation_bear_hybrid import cropped_mask,record_packet,row_program,pack_programs,sprite_prefix,validate_synthetic_role

class BearHybridTests(unittest.TestCase):
    def test_suffix_crop_keeps_exact_right_bits(self):
        self.assertEqual(cropped_mask(bytes((255,128,64,32,16,8,4,2)),3),bytes((31,0,0,0,16,8,4,2)))
        for cut in(-1,8,True):
            with self.assertRaises(ValueError):cropped_mask(bytes(8),cut)
        with self.assertRaises(ValueError):cropped_mask(bytes(7),0)
    def test_record_is_exact22_bytes_with_precomputed_far_programs(self):
        programs=((0,45,46),(95,322,351))
        b=record_packet(programs,4,7,1)
        self.assertEqual(len(b),22)
        self.assertEqual(b[:18],b''.join((0xb800+(i%46)*44).to_bytes(2,'little')+bytes((134+i//46,))for row in programs for i in row))
        self.assertEqual(b[18:],bytes((4,7,1,0)))
        for args in((programs[:1],4,7,1),(programs,2,7,1),(programs,4,8,1),(programs,4,7,2)):
            with self.assertRaises(ValueError):record_packet(*args)
    def test_row_program_orders_both_pgt_then_cgt_before_two_keys(self):
        tiles=(bytes(range(16)),bytes(range(16,32)))
        keys=(bytes((1,0,136,0,1,0)),bytes([255])*6)
        b=row_program(tiles,keys)
        self.assertEqual(b,bytes(range(8))+bytes(range(16,24))+bytes(range(8,16))+bytes(range(24,32))+b''.join(keys))
        with self.assertRaises(ValueError):row_program((tiles[0][:-1],tiles[1]),keys)
        rows=[bytes((i%256,))*44 for i in range(352)];packed=pack_programs(rows)
        self.assertEqual(len(packed),16384)
        for i in(0,45,46,91,321,322,351):
            at=(i//46)*2048+(i%46)*44
            self.assertEqual(packed[at:at+44],rows[i])
        for bank in range(8):
            count=min(46,352-bank*46)
            self.assertEqual(packed[bank*2048+count*44:(bank+1)*2048],bytes([255])*(2048-count*44))
        with self.assertRaises(ValueError):pack_programs([bytes(43)])
    def test_sprite_prefix_uses_nonoverlapping_bands_and_exact_hscale(self):
        pixels=bytearray(320);pixels[0]=1;pixels[10]=1;pixels[11]=1;pixels[16*16]=1
        b=sprite_prefix(pixels);self.assertEqual(len(b),64)
        self.assertEqual(b[8],128);self.assertEqual(b[24],1);self.assertEqual(b[40],128)
        self.assertEqual(sum(v.bit_count()for v in b),3)
    def test_synthetic_owner_namespace_is_bounded_to_crop_boundary_roles(self):
        registry={13539:(12,3)};key=(13539).to_bytes(2,'little')+bytes((136,0,15,0))
        for slot in(2,6,66,70):self.assertTrue(validate_synthetic_role(0,slot,key,registry))
        self.assertTrue(validate_synthetic_role(1,2,key[:2]+bytes((132,0,1,0)),registry))
        for bank,slot,bad in((0,3,key),(1,6,key),(2,2,key),(0,2,(13540).to_bytes(2,'little')+key[2:]),(0,2,key[:3]+bytes((1,15,0)))):
            with self.assertRaises(ValueError):validate_synthetic_role(bank,slot,bad,registry)
        self.assertFalse(validate_synthetic_role(2,3,bytes((12,0,129,0,15,0)),registry))

if __name__=='__main__':unittest.main()
