import unittest

from presentation_contact14 import pack_block, read_field, repack_bank


class Contact14Tests(unittest.TestCase):
    def test_partial_bank_retains_other_live_tail_allocations(self):
        bank=bytearray([165])*16384
        for slot in range(3):
            bank[slot*32:slot*32+32]=b''.join((slot*16+i).to_bytes(2,'little') for i in range(16))
        packed=repack_bank(bank,3,100)
        self.assertEqual(packed[3*32:],bank[3*32:])
        self.assertEqual(packed[3*28:3*32],b'\xff'*12)
        for slot in range(3):
            self.assertEqual([read_field(packed[slot*28:slot*28+28],i) for i in range(16)],list(range(slot*16,slot*16+16)))

    def test_all_fields_preserve_high_bits_and_neighbours(self):
        values = [0, 1, 16383, 2, 8192, 255, 256, 1023, 4096, 7, 127, 128, 8191, 16382, 3, 16383]
        packed = pack_block(values)
        self.assertEqual(len(packed), 28)
        self.assertEqual([read_field(packed,i) for i in range(16)], values)
        for i in range(16):
            changed = list(values);changed[i] ^= 16383
            self.assertEqual([read_field(pack_block(changed),j) for j in range(16)], changed)

    def test_rejects_truncation_invalid_fields_and_incomplete_blocks(self):
        for values in ([0]*15, [0]*17, [-1]+[0]*15, [16384]+[0]*15):
            with self.assertRaises(ValueError):pack_block(values)
        for raw,index in ((bytes(27),0),(bytes(29),0),(bytes(28),-1),(bytes(28),16)):
            with self.assertRaises(ValueError):read_field(raw,index)


if __name__ == '__main__':unittest.main()
