import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import render_model as model


class HazardPacedTests(unittest.TestCase):
    def test_complete_named_route_must_cover_the_exact_source_clock_schedule(self):
        api=importlib.import_module('hazard_paced')
        for family,period in (('ntsc',59736),('pal',71364)):
            steps=1+sum(model.schedule(600,period));report={'complete':True,'source_steps':steps,'frames':600,
                'canonical_ram_injections':0,'clock_hz':3579545,'ram_bytes':65536,'min_spacing':29,
                'max_sprites_per_line':4,'stack_min':0xF340,'pal_flag':int(family=='pal'),'layout':0,'width':0}
            api.validate_report(report,steps,family)
            for changes in ({'frames':100},{'source_steps':steps-1},{'canonical_ram_injections':1},{'min_spacing':28},
                            {'max_sprites_per_line':5},{'pal_flag':1-report['pal_flag']},{'clock_hz':7159090},
                            {'layout':2},{'width':True}):
                with self.assertRaises(ValueError):api.validate_report({**report,**changes},steps,family)
