import unittest
from scripts.presentation_shore_recipes import pack_record

class ShoreRecipeRecordTests(unittest.TestCase):
    def test_four_entries_and_one_byte_pattern_ids(self):
        got=pack_record(20,[(4,11,0),(4,10,253),(20,14,254),(20,11,7)])
        self.assertEqual(got[:2],bytes((4,20)))
        self.assertEqual(len(got),16)
        self.assertEqual(got[2:14],bytes((4,11,0,4,10,253,20,14,254,20,11,7)))
        self.assertEqual(got[14:],bytes(2))
        with self.assertRaises(ValueError):pack_record(20,[(4,11,256)])
        with self.assertRaises(ValueError):pack_record(20,[(4,11,0)]*5)
        with self.assertRaises(ValueError):pack_record(20,[(4,16,0)])

    def test_standing_right_race_free_alias_and_fallback_boundary(self):
        from scripts.presentation_shore_recipes import recipe_x
        self.assertEqual([recipe_x(x)for x in range(24)],list(range(24)))
        for x in range(84,153):self.assertEqual(recipe_x(x),22+(x&1))
        for x in (24,83,153,159,255):
            with self.assertRaises(ValueError):recipe_x(x)
