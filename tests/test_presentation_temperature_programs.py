import unittest
from scripts.presentation_temperature_programs import pack_program, lower_key

class TemperatureProgramTests(unittest.TestCase):
    def test_exact_three_streams_and_key_vectors(self):
        data=pack_program(bytes(range(24)),3,9)
        self.assertEqual(len(data),32)
        self.assertEqual(data[:24],bytes(range(24)))
        self.assertEqual(data[24:30],bytes((0x30,36,0x90,0,0x90,128)))
        self.assertEqual(data[30:],bytes(2))
        for bad in(-1,16,255):
            with self.assertRaises(ValueError):pack_program(bytes(24),bad,0)
            with self.assertRaises(ValueError):pack_program(bytes(24),0,bad)
        with self.assertRaises(ValueError):pack_program(bytes(23),0,0)

    def test_middle_upper_nibble_is_preserved_for_every_font_pair(self):
        for old in range(256):
            for a in range(16):
                for b in(0,1,9,15,32):
                    middle,tail,bottom,repeat=lower_key(old,a,b)
                    self.assertEqual(middle&15,old&15)
                    self.assertEqual(middle&240,a<<4)
                    self.assertEqual(tail,(b<<2)|(a>>4))
                    self.assertEqual(bottom,a<<4)
                    self.assertEqual(repeat,tail)
