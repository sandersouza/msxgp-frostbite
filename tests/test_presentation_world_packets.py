import unittest
from presentation_world_packets import decoded_names, legal_programs

class WorldPacketsTests(unittest.TestCase):
    def test_ready_names_preserve_water_and_physical_role(self):
        packed=bytes([0x10,0x32,0x04]*10)
        self.assertEqual(decoded_names(packed,25,129),bytes([129,25,26,27,28,129]*10))
        self.assertEqual(decoded_names(packed,89,129),bytes([129,89,90,91,92,129]*10))
        with self.assertRaises(ValueError):decoded_names(bytes([0xf0])*30,25,129)
    def test_only_legal_vertical_phases_are_selected_for_each_lane(self):
        programs=[i//160 for i in range(1280)]
        self.assertEqual(legal_programs(programs,0),{7,0})
        self.assertEqual(legal_programs(programs,1),{5,6})
        self.assertEqual(legal_programs(programs,2),{3,4})
        self.assertEqual(legal_programs(programs,3),{1,2})
        with self.assertRaises(ValueError):legal_programs(programs,4)
    def test_occupancy_is_exact_for_blank_ids_and_both_grid_dimensions(self):
        from presentation_world_packets import occupancy
        self.assertEqual(occupancy([1,0,0,3],2,2),128+9)
        self.assertEqual(occupancy([0,2,3],3,1),64+6)
        self.assertEqual(occupancy([1,2],2,1),3)
        with self.assertRaises(ValueError):occupancy([1],1,1)
