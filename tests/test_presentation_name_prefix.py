"""Only a warm, exact temperature update can omit the fixed header NAME prefix."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class NamePrefixTests(unittest.TestCase):
    def test_warm_temperature_skips_exactly_three_sorted_rows(self):
        from presentation_name_prefix import start
        for rest in (0,0x40,0x4000,0x400000,0xffff00):
            self.assertEqual(start(7|rest,14),3)

    def test_cold_full_blank_and_other_header_changes_keep_original_list(self):
        from presentation_name_prefix import start
        for rows in (0,1,2,3,6,0xff,0xffffff,0x4000ff):
            self.assertEqual(start(rows,14),0)
        for lower in (0,1,6,15,0x100e,0xffff):
            self.assertEqual(start(7,lower),0)
        with self.assertRaises(ValueError):start(1<<24,14)

if __name__=='__main__':unittest.main()
