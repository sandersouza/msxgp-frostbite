import unittest
from presentation_direct_enemy import segments,normalized_keys,declare_ram,decorate_actor_owners
from presentation_fixed import world_slot


class DirectEnemyTests(unittest.TestCase):
    def test_segments_preserve_existing_actor_role_contract(self):
        for page in (0,1):
            for lane in range(4):
                rows=segments(page,lane)
                for line,record in enumerate(rows):
                    bank,tile=world_slot('object',lane,line,0,0)
                    self.assertEqual((record['bank'],record['tile']),(bank,tile+page*64))
                    self.assertEqual(record['pgt'],0x4000+bank*2048+(tile+page*64)*8)
                    self.assertEqual(record['key'],0xd000+(page*3+bank)*384+tile*6)

    def test_bank_split_normalizes_keys_like_exact_shifted_packet(self):
        self.assertEqual(normalized_keys([10,11,12,13],2,2,0,0),[10,11,0,12,13,0])
        self.assertEqual(normalized_keys([10,11],2,1,1,1),[0,0,0,10,11,0])
        self.assertEqual(normalized_keys([10,11,12],3,1,2,0),[10,11,12,0,0,0])
        with self.assertRaises(ValueError):normalized_keys([10,11,12,13],2,2,1,1)
        with self.assertRaises(ValueError):segments(2,0)

    def test_only_declared_scratch_is_removed_from_guard(self):
        text='debug read_block memory 0xE800 0xB40;debug write_block memory 0xE800 [string repeat [binary format c 165] 0xB40];0xB40;source-state abi'
        changed=declare_ram(text)
        self.assertIn('0xE880 0xAC0',changed)
        self.assertTrue(changed.endswith('source-state abi'))
        for invalid in (text.replace('0xE800','0xE801'),text+' 0xB40',changed):
            with self.assertRaises(ValueError):declare_ram(invalid)

    def test_lazy_actor_keys_retain_strict_generation_and_bank_split(self):
        rom=bytearray(4*16384)
        rom[0:2]=(0).to_bytes(2,'little')
        rom[3*16384:3*16384+4]=bytes([10,0,11,0])
        geometry={'roots':{'row':[[0,128,0]]},'classes':[{'columns':2,'rows':1,'stride':4,'count':1,'offset':0}],'patterns':12}
        raw=b'\xff'*4110;caches=bytearray(b'\xff'*32)
        caches[4:8]=bytes([0,128,7,255])
        result=decorate_actor_owners(raw,caches,rom,geometry)
        for segment,role in enumerate(segments(0,1)):
            at=1536+role['key']-0xd000
            ids=(0,0,0) if segment==0 else (10,11,0)
            self.assertEqual(result[at:at+18],b''.join(i.to_bytes(2,'little')+bytes([role['water'],0,7,0]) for i in ids))
        wrong=bytearray(raw);wrong[1536+segments(0,1)[0]['key']-0xd000]=0
        with self.assertRaises(ValueError):decorate_actor_owners(wrong,caches,rom,geometry)


if __name__=='__main__':unittest.main()
