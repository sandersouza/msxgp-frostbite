import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    from native_effect_gain import project_volume
except ImportError:
    project_volume = None


class EffectGain(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(project_volume, 'selective native gain is missing')

    def test_only_death_and_bear_store_sites_gain(self):
        selected = {0xF4D7, 0xF4D9, 0xF7F0, 0xF7F2}
        for pc in range(0xF000, 0x10000):
            self.assertEqual(project_volume(pc, 4), 5 if pc in selected else 4)

    def test_silence_and_other_levels_are_preserved(self):
        for pc in (0xF4D7, 0xF4D9, 0xF7F0, 0xF7F2):
            for raw in range(256):
                level = raw & 15
                self.assertEqual(project_volume(pc, raw), 5 if level == 4 else level)

    def test_adjacent_unrelated_effects_do_not_inherit_gain(self):
        self.assertEqual([project_volume(pc, v) for pc, v in
                          ((0xF7F0, 4), (0xF50C, 4), (0xF4D7, 0))], [5, 4, 0])

    def test_nonvolume_writes_preserve_selected_physical_level(self):
        import native_effect_gain as gain
        self.assertTrue(hasattr(gain, 'project_write'), 'ordered projection is missing')
        previous = {'psg': bytes((1,0,1,0,0,0,1,191,0,0,0,0,0,0,0,0))}
        source = bytes((12,12,7,7,4,4))
        state = gain.project_write(source, previous, 0xF4D7, 25)
        self.assertEqual(state['psg'][8], 5)
        state = gain.project_write(source, state, 0xF514, 23)
        self.assertEqual(state['psg'][8], 5)
        state = gain.project_write(source, state, 0xF50C, 25)
        self.assertEqual(state['psg'][8], 4)
