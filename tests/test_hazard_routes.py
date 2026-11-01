import copy
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


def points(patches):
    result=[]
    for index,patch in enumerate(patches):
        ram=[0]*128
        for address,value in {0xCB:4,0xCC:3,0xCD:255,0xE4:27,0xE5:69,0xE6:64,0xF2:255,**patch}.items():ram[address-128]=value
        result.append({'index':index,'ram':ram})
    return result


class HazardRouteTests(unittest.TestCase):
    def api(self):return importlib.import_module('hazard_routes')

    def test_real_console_edges_and_active_player_input_lines(self):
        api=self.api();prep=api.prepare_inputs({'select_release_intervals':2,'reset_release_intervals':3},{'warmup':2,'variation':2})
        self.assertEqual(len(prep),12);self.assertEqual([i for i,p in enumerate(prep) if p['swchb']==61],[2,5])
        self.assertEqual([i for i,p in enumerate(prep) if p['swchb']==62],[8])
        r=points([{0xE4:53,0x93:1,0xD6:100}])[0]['ram']
        self.assertEqual(api.fish_input(r)['swcha'],95)
        r[0x47]=1;self.assertEqual(api.fish_input(r)['swcha'],245)
        r[0x77]=1;self.assertEqual(api.fish_input(r)['swcha'],255)

    def test_refuge_requires_a_bear_sweep_and_continuously_safe_wait(self):
        route=points([{0xE6:9,0xE8:max(15,133-i*4)} for i in range(64)]+[{0xE6:9,0xE8:15}]*64)
        result=self.api().assess(route,'bear-refuge',approach_end=64)
        self.assertEqual((result['refuge_x'],result['bear_min'],result['bear_max']),(9,15,133))
        bad=copy.deepcopy(route);bad[-1]['ram'][0x6D]=128
        with self.assertRaises(ValueError):self.api().assess(bad,'bear-refuge',approach_end=64)
        for point in route:point['ram'][0x68]=15
        with self.assertRaises(ValueError):self.api().assess(route,'bear-refuge',approach_end=64)

    def test_bear_requires_actual_grounded_hit_push_death_and_active_recovery(self):
        route=points([{0xE8:120},{0xE8:64,0xED:128},{0xE6:63,0xED:128},
                      {0xE6:0,0xED:128,0xF1:128},{0xCC:2,0xE7:1},{0xCC:2}])
        result=self.api().assess(route,'bear-chase')
        self.assertEqual((result['contact_step'],result['push_step'],result['death_step'],result['recovery_step']),(1,2,3,5))
        for bad in (route[:4],route[:5]):
            with self.assertRaises(ValueError):self.api().assess(bad,'bear-chase')
        bad=copy.deepcopy(route);bad[1]['ram'][0x6D]=0
        with self.assertRaises(ValueError):self.api().assess(bad,'bear-chase')
        bad=copy.deepcopy(route);bad[3]['ram'][0x71]=0
        with self.assertRaises(ValueError):self.api().assess(bad,'bear-chase')

    def test_two_player_recovery_uses_both_reserve_records(self):
        route=points([{0xD2:4},{0xD2:4,0xED:128},{0xD2:4,0xE6:63,0xED:128},
                      {0xD2:4,0xE6:0,0xED:128,0xF1:128},{0xD2:3,0xC7:1}])
        result=self.api().assess(route,'bear-chase')
        self.assertEqual((result['initial_reserves_total'],result['final_reserves_total']),(7,6));self.assertTrue(result['player_changed'])

    def test_fish_requires_a_real_segment_clear_and_twenty_delayed_ten_point_awards(self):
        patches=[{0x94:1,0xDC:0,0xDF:1},{0x94:1,0xF7:1,0xF4:91,0xE7:16}];score=0
        for envelope in [*range(90,64,-1),0]:
            score+=10 if envelope&3 else 0
            patches.append({0x94:1,0xF7:1,0xF4:envelope,0xC9:(score//100)%10,0xCA:((score//10)%10)<<4})
        route=points(patches);result=self.api().assess(route,'fish-envelope')
        self.assertEqual((result['fish_row'],result['awards'],result['reward_points']),(3,20,200))
        with self.assertRaises(ValueError):self.api().assess(route[:-1],'fish-envelope')
        for index,address,value in ((1,0x5F,1),(-1,0x49,3),(1,0x74,90)):
            bad=copy.deepcopy(route);bad[index]['ram'][address]=value
            with self.assertRaises(ValueError):self.api().assess(bad,'fish-envelope')

    def test_threat_requires_attachment_real_odd_contact_and_observed_push(self):
        route=points([{0x94:2},{0x94:2,0xF2:3,0xB7:135},{0x94:2,0xF2:3,0xE6:63},
                      {0x94:2,0xF2:3,0xE6:0,0xF1:128},{0xCC:2}])
        result=self.api().assess(route,'threat-push');self.assertEqual(result['row'],3)
        bad=copy.deepcopy(route);bad[1]['ram'][0x37]=7
        with self.assertRaises(ValueError):self.api().assess(bad,'threat-push')

    def test_water_and_temperature_deaths_keep_distinct_entry_flags(self):
        for kind,entry in (('water-death',{0xE4:159,0xF1:128}),('temperature-death',{0xE5:0,0xF1:16})):
            route=points([{},entry,{0xF1:32},{0xCC:2}]);self.assertEqual(self.api().assess(route,kind)['death_step'],1)
            with self.assertRaises(ValueError):self.api().assess(route[:-1],kind)

    def test_missing_continuity_or_disabled_source_cannot_be_accepted(self):
        route=points([{},{}]);route[1]['index']=3
        with self.assertRaises(ValueError):self.api().assess(route,'bear-chase')
        policy={'ram_injections':{},'source_hazards_disabled':False,'instruction_skipping':False,'raw_input_every_interval':True}
        self.api().validate_policy(policy)
        for key,value in (('ram_injections',{'ED':0}),('source_hazards_disabled',True),('instruction_skipping',True),('raw_input_every_interval',False)):
            with self.assertRaises(ValueError):self.api().validate_policy({**policy,key:value})
