import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    from native_flat_layout import Layout
except ImportError:
    Layout=None


class Allocation(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Layout,'native fixed-address allocator is missing')

    def test_best_fit_retains_large_object_extent(self):
        q=Layout(((0x100,0x200),(0x300,0x310)))
        self.assertEqual(q.add('small',bytes(8)),0x300)
        self.assertEqual(q.add('large',bytes(200)),0x100)

    def test_alignment_preserves_prefix_and_suffix_holes(self):
        q=Layout(((0x101,0x130),))
        self.assertEqual(q.add('aligned',b'AB',16),0x110)
        self.assertEqual(q.free,[(0x101,0x110),(0x112,0x130)])

    def test_scatter_table_preserves_record_boundaries(self):
        q=Layout(((0x100,0x104),(0x200,0x208),(0x300,0x304)))
        pointers=q.records('rows',b'AAAABBBBCCCC',4)
        self.assertEqual(len(pointers),6)
        for i in range(3):
            a=int.from_bytes(pointers[i*2:i*2+2],'little')
            self.assertEqual(q.image[a:a+4],bytes((65+i,))*4)

    def test_no_fit_is_explicit(self):
        q=Layout(((0x100,0x104),))
        with self.assertRaisesRegex(ValueError,'cannot fit'):
            q.add('large',bytes(5))
        self.assertEqual(q.free,[(0x100,0x104)])

    def test_overlapping_domains_are_rejected(self):
        with self.assertRaises(ValueError):Layout(((0x100,0x200),(0x180,0x300)))

    def test_wrapping_addresses_are_rejected(self):
        for spans in (((-1,4),),((65530,65537),),((10,10),)):
            with self.assertRaises(ValueError):Layout(spans)

    def test_duplicate_owner_and_bad_alignment_are_rejected(self):
        q=Layout(((0x100,0x200),));q.add('same',b'A')
        with self.assertRaises(ValueError):q.add('same',b'B')
        with self.assertRaises(ValueError):q.add('odd',b'C',3)

    def test_complete_row_count_is_required(self):
        q=Layout(((0x100,0x200),))
        with self.assertRaises(ValueError):q.records('partial',b'ABC',2)

    def test_overlapping_windows_remain_whole_across_scattered_chunks(self):
        q=Layout(((0x100,0x108),(0x200,0x208),(0x300,0x308)))
        pool=b'abcdefghijklmnop'
        offsets=b''.join(i.to_bytes(2,'little') for i in range(13))
        pointers=q.windows('windows',pool,offsets,4,8)
        for i in range(13):
            at=int.from_bytes(pointers[i*2:i*2+2],'little')
            self.assertEqual(q.image[at:at+4],pool[i:i+4])

    def test_out_of_bounds_window_is_rejected_before_mutation(self):
        q=Layout(((0x100,0x200),))
        with self.assertRaises(ValueError):q.windows('bad',b'abcdef',b'\x04\0',4,8)
        self.assertEqual(q.objects,{})
