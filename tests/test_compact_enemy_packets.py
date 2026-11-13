import unittest

from compact_enemy_packets import packet, scatter


class PacketTests(unittest.TestCase):
    def test_msb_expansion_and_reflection(self):
        self.assertEqual(packet(bytes([128])*8,0,False), bytes([128])*8+bytes(16))
        self.assertEqual(packet(bytes([1])*8,0,True), bytes([128])*8+bytes(16))

    def test_odd_phase_and_third_column(self):
        p=packet(bytes([255])*8,9,False)
        self.assertEqual(p,bytes([7])*8+bytes([255])*8+bytes([128])*8)

    def test_vertical_split(self):
        out=scatter(bytes(range(24)),7)
        self.assertEqual(out[7],0)
        self.assertEqual(out[24:31],bytes(range(1,8)))
        self.assertEqual(out[39],0)
        self.assertEqual(out[40:47],bytes(range(17,24)))

    def test_input_validation(self):
        for args in ((bytes(7),0,False),(bytes(8),16,False),(bytes(8),0,2)):
            with self.assertRaises(ValueError):packet(*args)
        with self.assertRaises(ValueError):scatter(bytes(24),8)


if __name__=='__main__':unittest.main()
