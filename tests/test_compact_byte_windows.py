import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compact_byte_windows import pack_windows,restore_windows


class ByteWindows(unittest.TestCase):
    def test_exact_order_duplicates_and_shared_suffixes(self):
        values=[b'abcd',b'cdef',b'abcd',b'efab']
        result=pack_windows(values)
        self.assertEqual(restore_windows(result),values)
        self.assertLessEqual(len(result['pool']),8)
        self.assertEqual(len(result['offsets']),8)

    def test_identical_values_cannot_form_a_cycle(self):
        result=pack_windows([bytes(8)]*5)
        self.assertEqual(result['pool'],bytes(8))
        self.assertEqual(restore_windows(result),[bytes(8)]*5)

    def test_nonoverlapping_records_are_preserved(self):
        values=[bytes([1])*8,bytes([2])*8,bytes([3])*8]
        self.assertEqual(restore_windows(pack_windows(values)),values)

    def test_invalid_inputs_and_corrupt_offsets_rejected(self):
        for values in ([],[b'a',b'bc'],[b'']):
            with self.assertRaises(ValueError):pack_windows(values)
        data=pack_windows([b'ab'])
        with self.assertRaises(ValueError):restore_windows({**data,'offsets':b'\xff\xff'})
