import copy
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


def points(patches, variation=0):
    result = []
    for i, patch in enumerate(patches):
        ram = [0] * 128
        defaults = {0x80: variation, 0xCB: 4 if variation & 2 else 0,
                    0xCC: 3, 0xCD: 255, 0xD1: 4 if variation & 2 else 0,
                    0xD2: 4 if variation & 1 else 0, 0xD3: 255,
                    0xE4: 27, 0xE5: 0x45, 0xE6: 64, 0xF2: 255}
        for address, value in {**defaults, **patch}.items():
            ram[address - 128] = value
        result.append({'index': i, 'ram': ram})
    return result


class ProgressionRouteTests(unittest.TestCase):
    def api(self): return importlib.import_module('progression_routes')

    def test_progression_requires_construction_entry_bonus_and_active_next_level_in_every_mode(self):
        for variation in range(4):
            level = 4 if variation & 2 else 0
            route = points([{}, {0xCD: 15}, {0xCD: 15, 0xF1: 64, 0xE4: 0, 0xE9: 0},
                            {0xCD: 255, 0xF1: 8, 0xE5: 0}, {0xCB: level + 1}], variation)
            result = self.api().assess(route, 'progression', 0)
            self.assertEqual(result['variation'], variation)
            self.assertEqual(result['next_level_step'], 4)
            for bad in (route[:-1], route[:2] + route[3:]):
                with self.assertRaises(ValueError): self.api().assess(bad, 'progression', 0)

    def test_exhaustion_must_follow_real_death_then_terminal_then_reset(self):
        route = points([{}, {0xF1: 128}, {0xCC: 0, 0xF1: 32},
                        {0xCC: 0, 0xC6: 255}, {}])
        result = self.api().assess(route, 'exhaustion-restart', 0)
        self.assertEqual((result['terminal_step'], result['restart_step']), (3, 4))
        for bad in (route[:-1], points([{}, {0xCC: 0, 0xC6: 255}, {}])):
            with self.assertRaises(ValueError): self.api().assess(bad, 'exhaustion-restart', 0)

    def test_alternation_requires_both_directions_and_preserves_exact_records(self):
        api = self.api()
        route = points([{}, {0xC7: 1, 0xCC: 3, 0xD2: 3},
                        {0xC7: 0, 0xCC: 2, 0xD2: 3}, {0xF1: 128},
                        {0xCC: 0, 0xD2: 0, 0xF1: 32},
                        {0xCC: 0, 0xD2: 0, 0xC6: 255}, {}], 1)
        self.assertEqual(api.assess(route, 'exhaustion-restart')['turn_players'], [1, 0])
        bad = copy.deepcopy(route); bad[1]['ram'][0x4E] = 1
        with self.assertRaises(ValueError): api.assess(bad, 'exhaustion-restart')
        with self.assertRaises(ValueError): api.assess(points([{}, {0xF1: 128},
            {0xCC: 0, 0xD2: 0, 0xC6: 255}, {}], 1), 'exhaustion-restart')

    def test_initial_mode_continuity_and_active_controller_are_checked(self):
        api = self.api()
        route = points([{}, {}], 2)
        route[0]['ram'][0x4B] = 0
        with self.assertRaises(ValueError): api.assess(route, 'progression')
        self.assertEqual(api.controller(0xDF, 0), 0xDF)
        self.assertEqual(api.controller(0xDF, 1), 0xFD)
        with self.assertRaises(ValueError): api.controller(0xDF, 2)
        with self.assertRaises(ValueError): api.controller(0, 0)

    def test_reset_from_player_one_is_not_a_natural_record_swap(self):
        route = points([{}, {0xC7: 1, 0xCC: 3, 0xD2: 3},
                        {0xC7: 0, 0xCC: 2, 0xD2: 3},
                        {0xC7: 1, 0xCC: 2, 0xD2: 2}, {0xC7: 1, 0xF1: 128},
                        {0xC7: 1, 0xCC: 0, 0xD2: 0, 0xC6: 255}, {}], 1)
        self.assertEqual(self.api().assess(route, 'exhaustion-restart')['restart_step'], 6)


if __name__ == '__main__': unittest.main()
