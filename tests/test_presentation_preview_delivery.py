"""A preview must never promote failed timing to game acceptance."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PreviewDeliveryTests(unittest.TestCase):
    def test_independent_contrast_receipt_is_bound_to_the_same_rom_and_pixels(self):
        api=importlib.import_module('presentation_preview_delivery')
        report={'complete':True,'cases':2115,'touched_ice_source_pixels':1,'sea_source_pixels':2,
            'colors':{'sea':{'source':144,'tms':4},'touched_ice':{'source':152,'tms':5}},
            'rom_sha256':'rom','matrix_sha256':'matrix','captures_sha256':'captures'}
        api.validate_contrast(report,'rom','matrix','captures')
        for field,value in (('complete',False),('cases',2114),('touched_ice_source_pixels',0),('rom_sha256','old'),('captures_sha256','old'),('matrix_sha256','old')):
            with self.assertRaises(ValueError):api.validate_contrast({**report,field:value},'rom','matrix','captures')
        with self.assertRaises(ValueError):api.validate_contrast({**report,'colors':{'sea':{'source':144,'tms':4},'touched_ice':{'source':152,'tms':4}}},'rom','matrix','captures')

    def test_preview_retains_failed_timing_and_distinct_human_evidence(self):
        api=importlib.import_module('presentation_preview_delivery')
        value=api.preview_scope()
        api.validate_scope(value)
        for field in ('runtime_qualified','frame_deadline_accepted','manual_emulator_accepted','physical_hardware_accepted'):
            wrong={**value,field:True}
            with self.assertRaises(ValueError):api.validate_scope(wrong)
        with self.assertRaises(ValueError):api.validate_scope({**value,'purpose':'complete-game'})

    def test_fatal_positive_logs_cannot_be_hidden_by_success_receipts(self):
        api=importlib.import_module('presentation_preview_delivery')
        api.check_log('MATRIX_CAPTURED 2115\n')
        for marker in ('MATRIX_FAIL guard','GAME_AUDIO_FAIL gpio','FLOE_NATIVE_FAIL heap','PACE_PROBE_FAIL vram','Error executing delayed command'):
            with self.assertRaises(ValueError):api.check_log('complete true\n'+marker)

    def test_measured_pace_must_be_recomputed_without_acceptance(self):
        api=importlib.import_module('presentation_preview_delivery')
        from presentation_pace_probe import verify_rows
        rows='0 10 100 70000 100 70200 0 1 200 210\n1 12 100 70000 100 70200 119472 1 200 210\n'
        report=verify_rows(rows,2,'ntsc')
        api.audit_timing(report,rows,'ntsc')
        for field in ('max_busy_cycles','skipped_vdp_frames','over_budget_frames'):
            with self.assertRaises(ValueError):api.audit_timing({**report,field:0},rows,'ntsc')
