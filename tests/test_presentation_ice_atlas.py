import unittest
from presentation_ice_atlas import atlas_ids,compile_atlas,audit_atlas,shadow_names

class IceAtlasTests(unittest.TestCase):
    def test_sparse_ids_exclude_footer(self):
        ids=atlas_ids();self.assertEqual(len(ids),62);self.assertEqual(len(set(ids)),62)
        self.assertFalse(set(ids)&set(range(160,204)))
        self.assertEqual(ids,tuple(range(144,160))+tuple(range(204,250)))
    def test_programs_share_patterns_and_water(self):
        a=bytes([1])*8;b=bytes([2])*8
        packets=[dict(patterns=(a,b),names=bytes([25,26,129])*10)for _ in range(16)]
        result=compile_atlas(packets)
        self.assertEqual(result['patterns'],bytes(8)+a+b)
        self.assertEqual(len(result['programs']),16*32)
        self.assertEqual(result['programs'][:32],bytes([145,146,144])*10+bytes(2))
        with self.assertRaises(ValueError):compile_atlas(packets[:15])
    def test_atlas_checked_before_shadow_names(self):
        table={144:bytes(8)+bytes([0xf4])*8};v=bytearray(16384)
        for bank in (1,2):
            at=bank*2048+144*8;v[at:at+8]=bytes(8);v[0x2000+at:0x2000+at+8]=bytes([0xf4])*8
        names=bytearray([128])*1536;names[12*32+4]=144;names[3*32+2]=144
        for page in range(2):v[0x1800+page*0x400:0x1800+page*0x400+768]=names[page*768:(page+1)*768]
        raw=bytes(names)+bytes(4110-1536);audit_atlas(v,table)
        shadow,video=shadow_names(raw,v,table);self.assertEqual(shadow[3*32+2],144);self.assertEqual(shadow[12*32+4],128);self.assertEqual(video[0x1800+12*32+4],128)
        self.assertEqual(v[0x1800+12*32+4],144)
        v[0x2000+2048+144*8]^=1
        with self.assertRaises(ValueError):shadow_names(raw,v,table)
    def test_atlas_reference_cannot_escape_ice_rows(self):
        table={144:bytes(8)+bytes([0xf4])*8};v=bytearray(16384)
        for bank in (1,2):v[0x2000+bank*2048+144*8:0x2000+bank*2048+145*8]=bytes([0xf4])*8
        names=bytearray([128])*1536;names[22*32+4]=144
        with self.assertRaises(ValueError):shadow_names(bytes(names)+bytes(2574),v,table)
