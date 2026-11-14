import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compact_enemy_occupancy import pack,unpack


class OccupancyDictionary(unittest.TestCase):
    def test_all_group_x_y_coordinates_are_preserved(self):
        data=bytes((g//3+x//4*16+y)&255 for g in range(66) for x in range(16) for y in range(8))
        result=pack(data)
        self.assertEqual(len(result['directory']),528)
        self.assertEqual(unpack(result),data)
        self.assertLess(len(result['rows']),len(data))

    def test_aliases_share_rows_without_changing_groups(self):
        result=pack(bytes([19])*8448)
        self.assertEqual(result['directory'],bytes(528))
        self.assertEqual(result['rows'],bytes([19])*16)

    def test_partial_matrix_rejected(self):
        with self.assertRaises(ValueError):pack(bytes(8447))
