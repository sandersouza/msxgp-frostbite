"""An oscillator-period witness must be complete and have the claimed minimum."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class AudioModeTests(unittest.TestCase):
    def test_dc_and_six_tick_waveforms_have_their_actual_minimum_period(self):
        api=importlib.import_module('presentation_audio_modes_check')
        self.assertEqual(api.validate_mode(bytes([1])*36864,0,31),1)
        self.assertEqual(api.validate_mode(bytes((0,0,0,1,1,1))*6144,12,0),6)
        for data,control in ((bytes(36864),0),(bytes([1])*36864,12),(bytes(36863),12)):
            with self.assertRaises(ValueError):api.validate_mode(data,control,0)
        data=bytearray(bytes((0,0,0,1,1,1))*6144);data[8192]^=1
        with self.assertRaises(ValueError):api.validate_mode(bytes(data),12,0)
