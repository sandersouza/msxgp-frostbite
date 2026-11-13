import unittest
from scripts.presentation_dirty_native import checked_kernel_extension

class DirtyNativeAllocationTests(unittest.TestCase):
    def test_exact_reserved_padding_and_capacity(self):
        rom=bytes(0x100)+bytes([255])*63
        self.assertEqual(checked_kernel_extension(rom,0x100,b'abc',63),b'abc')
        with self.assertRaises(ValueError):checked_kernel_extension(rom,0x100,b'x'*64,63)
        with self.assertRaises(ValueError):checked_kernel_extension(rom[:0x101]+b'\x00'+rom[0x102:],0x100,b'abc',63)
        with self.assertRaises(ValueError):checked_kernel_extension(rom,0x130,b'x'*30,63)

    def test_no_zero_length_or_negative_region(self):
        with self.assertRaises(ValueError):checked_kernel_extension(bytes([255])*20,0,b'',20)
        with self.assertRaises(ValueError):checked_kernel_extension(bytes([255])*20,-1,b'a',20)

class DirtyNativeSpanTests(unittest.TestCase):
    def test_exact_effective_grid24_spans_and_nonuniform_rejection(self):
        from scripts.presentation_dirty_native import fixed_floe_spans
        rows=bytes.fromhex('000020000004008000001000')
        self.assertEqual(fixed_floe_spans(rows*2),((2,32),(2,4),(1,128),(1,16)))
        with self.assertRaises(ValueError):fixed_floe_spans(rows+bytes(12))
        with self.assertRaises(ValueError):fixed_floe_spans(bytes.fromhex('000120')+rows[3:]+bytes.fromhex('000120')+rows[3:])
