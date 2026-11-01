import copy
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class HazardDeliveryTests(unittest.TestCase):
    def api(self):return importlib.import_module('hazard_delivery')

    def test_geometry_requires_every_actual_phase_and_current_clean_rom(self):
        r={'complete':True,'exploratory':False,'rom':{'sha256':'abc'},'cases':14828,'canonical_ram_injections':14828,
           'clock_hz':3579545,'ram_bytes':65536,'stack_min':0xF340,'full_original_phase_cases':14828,
           'declared_neutral_hazard_cases':[],'actual_literal_views':228}
        self.api().validate_target('geometry',r,'abc',14828)
        for patch in ({'cases':1368},{'full_original_phase_cases':14827},{'declared_neutral_hazard_cases':[1]},
                      {'exploratory':True},{'rom':{'sha256':'old'}},{'canonical_ram_injections':0}):
            with self.assertRaises(ValueError):self.api().validate_target('geometry',{**r,**patch},'abc',14828)

    def test_source_summary_rejects_partial_domain_or_unproven_copy_alias(self):
        r={'cases':50289350,'components':{k:{'cases':n} for k,n in self.api().COMPONENT_CASES.items()},
           'aliases':{'cases':3203200,'complete_geometry':True,'literal_views':228,'channels':2},
           'physical_leaf_queries':{'floe':881120,'edge':10987680,'ordinary':956160,'shore':3951520}}
        self.api().validate_source_summary(r)
        for field,value in (('cases',50289349),('aliases',{**r['aliases'],'complete_geometry':False})):
            with self.assertRaises(ValueError):self.api().validate_source_summary({**r,field:value})
        bad=copy.deepcopy(r);bad['components']['edge']['cases']=4300800
        with self.assertRaises(ValueError):self.api().validate_source_summary(bad)

    def test_observer_coverage_cannot_use_old_partial_domain_or_dirty_producer(self):
        r={'complete':True,'producer_dirty':False,**self.api().OBSERVER_COUNTS,'nusiz_values':[0,1,2,3],
           'independent_unmodified_phases':[{'case':i*7} for i in range(32)]}
        self.api().validate_observer_summary(r)
        for patch in ({'cases':9444},{'object_shapes':32},{'producer_dirty':True},{'shore_roi_comparisons':0}):
            with self.assertRaises(ValueError):self.api().validate_observer_summary({**r,**patch})

    def test_stress_catalog_requires_both_toggle_orientations_and_real_mixed_counts(self):
        api=self.api();reports={name:{'rom_sha256':'abc','canonical_nusiz_codes':[0,1,2,3] if name.startswith('mixed') else [0,3],
                  'harness_dirty':False,'build_dirty':False} for name in api.STRESS_NAMES}
        api.validate_suite_manifest(reports,'abc')
        bad=dict(reports);bad.pop('pal_transitions_inverted')
        with self.assertRaises(ValueError):api.validate_suite_manifest(bad,'abc')
        bad=copy.deepcopy(reports);bad['mixed_pal']['canonical_nusiz_codes']=[0,3]
        with self.assertRaises(ValueError):api.validate_suite_manifest(bad,'abc')

    def test_negative_manifest_rejects_wrong_cause_stale_rom_and_missing_mutation(self):
        api=self.api();reports={name:{'detected':True,'detail':needle,'rom_sha256':'abc','harness_dirty':False}
                                for name,needle in api.NEGATIVE_CAUSES.items()}
        api.validate_negative_manifest(reports,'abc')
        for key,patch in (('rng',{'rom_sha256':'old'}),('sticky',{'detail':'incomplete source'}),('cache',{'detected':False})):
            bad=copy.deepcopy(reports);bad[key].update(patch)
            with self.assertRaises(ValueError):api.validate_negative_manifest(bad,'abc')
        reports.pop('row_priority')
        with self.assertRaises(ValueError):api.validate_negative_manifest(reports,'abc')
