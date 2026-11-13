import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from presentation_temperature_burst import burst_program,burst_table
from presentation_temperature_programs import pack_program

class TemperatureBurstTests(unittest.TestCase):
 def test_same32_bytes_pack_three_midpoints_one_padded_bottom_stream_and_pair(self):
  old=pack_program(bytes(range(24)),3,5);new=burst_program(old,0x35)
  self.assertEqual(len(new),32);self.assertEqual(new[:3],bytes((0,8,16)));self.assertEqual(new[3:27],bytes(range(1,8))+bytes(1)+bytes(range(9,16))+bytes(1)+bytes(range(17,24))+bytes(1));self.assertEqual(new[27:],bytes((0x35,0,0,0,0)))
 def test_all_font_pairs_preserve_layout_capacity_and_reject_bad_metadata(self):
  old=b''.join(pack_program(bytes((i,))*24,i//16,i%16)for i in range(256));new=burst_table(old);self.assertEqual(len(new),8192)
  for i in range(256):self.assertEqual(new[i*32+27],i);self.assertEqual(new[i*32+10],0);self.assertEqual(new[i*32+18],0);self.assertEqual(new[i*32+26],0)
  bad=bytearray(old[:32]);bad[24]^=1
  with self.assertRaises(ValueError):burst_program(bad,0)
  with self.assertRaises(ValueError):burst_table(old[:-1])

if __name__=='__main__':unittest.main()
