import unittest
from presentation_direct_enemy import segments,normalized_keys
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


if __name__=='__main__':unittest.main()
