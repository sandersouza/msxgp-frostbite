"""PSG evidence retains all fields and independent physical peripheral state."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class AudioNativeTests(unittest.TestCase):
    def test_complete_psg_work_and_peripheral_bytes_are_required(self):
        api=importlib.import_module('presentation_audio_native_check');row=bytes(api.ROW_BYTES)
        api.verify_row(row,row,bytes(5))
        for offset in (0,1,6,7,8,9,10,11,14,15,16,21,32,47):
            bad=bytearray(row);bad[offset]=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row,bytes(5))
        for actual,peripherals in ((row[:-1],bytes(5)),(row,bytes(4))):
            with self.assertRaises(ValueError):api.verify_row(actual,row,peripherals)

    def test_every_raw_register_byte_is_present_in_all_four_gpio_groups(self):
        api=importlib.import_module('presentation_audio_native_check');inputs,expected,writes,groups=api.fixtures();seen={}
        for offset in range(0,len(inputs),5):
            group,method,lo,hi,value=inputs[offset:offset+5]
            if 0xC715<=hi*256+lo<=0xC71A:seen.setdefault((group,lo),set()).add(value)
        self.assertEqual(len(seen),24)
        for values in seen.values():self.assertEqual(values,set(range(256)))
        self.assertEqual(len(expected),len(groups)*api.ROW_BYTES)
        self.assertEqual(len(inputs),len(groups)*5)
        self.assertTrue(all(reg in (0,1,2,3,6,7,8,9,10) for _,reg,_ in writes))
