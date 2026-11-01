import importlib
import gzip
from pathlib import Path
import sys
import unittest
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class NativeInputTests(unittest.TestCase):
    def test_raw_opposing_keyboard_directions_join_only_selected_port(self):
        hardware=importlib.import_module('native_input_check').hardware
        # All opposing directions, SPACE, F1 and F2 held simultaneously.
        self.assertEqual(hardware((96,241,0,0),0),(15,60,0,128))
        self.assertEqual(hardware((96,241,0,0),1),(240,60,128,0))
        self.assertEqual(hardware((0,0,5,26),0),(165,63,128,0))

    def test_sixteen_raw_joystick_combinations_are_not_normalized(self):
        hardware=importlib.import_module('native_input_check').hardware
        for bits in range(16):
            self.assertEqual(hardware((0,0,bits,15^bits),0)[0],((15^bits)<<4)|bits)

    def test_input_events_target_emulated_matrix_and_both_standard_devices(self):
        events=importlib.import_module('device_replay').device_events(6,(32,17,4,24))
        self.assertEqual([e[1] for e in events],['KeyMatrixState']*2+['MSXJoyState']*2)
        self.assertEqual(events[-1][2],{'id':2,'press':24,'release':39})

    def test_replay_serializes_bytearray_as_device_bytes_not_python_repr(self):
        replay=importlib.import_module('device_replay').replay
        with tempfile.TemporaryDirectory() as folder:
            seed=Path(folder)/'seed.omr';target=Path(folder)/'target.omr'
            seed.write_bytes(gzip.compress(b'<root><replay><snapshots><snapshot id="1"/></snapshots><events/><currentTime><time>0</time></currentTime></replay></root>'))
            replay(seed,[(6,'MSXCommandEvent',{'tokens':['debug','write_block',bytearray((0,130))]})],7,target)
            xml=gzip.decompress(target.read_bytes())
            self.assertIn(b'<item>\xc0\x80\xc2\x82</item>',xml)
            self.assertNotIn(b'bytearray',xml)
