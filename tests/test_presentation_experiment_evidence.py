import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from presentation_experiment_evidence import validate_scene_receipt,validate_owner_receipt


class EvidenceBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name);self.rom='a'*64
        self.artifacts={}
        for name in ('cases.bin','captures.bin','timing.tsv','ownership.bin','band-records.bin','expected.tms','scenes.bin','fill-events.tsv'):
            data=name.encode();(self.path/name).write_bytes(data)
            self.artifacts[name]=hashlib.sha256(data).hexdigest()

    def scene(self):
        return dict(complete=True,cases=2115,different_frames=0,rom_sha256=self.rom,
            full_source_pixels_accepted=True,fixed_role_ownership_accepted=True,
            physical_name_pages_accepted=True,integrated_dirty_states_accepted=True,
            dirty_row_list_accepted=True,prepared_band_ownership_accepted=True,artifacts=self.artifacts)

    def test_scene_receipt_rejects_other_rom_and_changed_timing_or_ownership(self):
        receipt=self.scene();(self.path/'check.json').write_text(json.dumps(receipt))
        validate_scene_receipt(self.path,self.rom,2115,'prepared')
        with self.assertRaises(ValueError):validate_scene_receipt(self.path,'b'*64,2115,'prepared')
        for name in ('timing.tsv','ownership.bin','band-records.bin'):
            saved=(self.path/name).read_bytes();(self.path/name).write_bytes(b'changed')
            with self.assertRaises(ValueError):validate_scene_receipt(self.path,self.rom,2115,'prepared')
            (self.path/name).write_bytes(saved)
        receipt['prepared_band_ownership_accepted']=False
        (self.path/'check.json').write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):validate_scene_receipt(self.path,self.rom,2115,'prepared')

    def test_owner_receipt_binds_rom_probe_and_all_audited_buffers(self):
        (self.path/'check.json').write_bytes(b'original probe')
        receipt=dict(complete=True,frames=2253,rom_sha256=self.rom,
            probe_receipt_sha256=hashlib.sha256(b'original probe').hexdigest(),
            physical_owner_audits=True,active_full_page_protection=True,
            direct_fill_io_instrumented=True,artifacts=self.artifacts)
        (self.path/'prepared-check-v2.json').write_text(json.dumps(receipt))
        validate_owner_receipt(self.path,self.rom,2253,'prepared')
        for key,value in [('rom_sha256','b'*64),('probe_receipt_sha256','c'*64),('physical_owner_audits',False)]:
            invalid={**receipt,key:value};(self.path/'prepared-check-v2.json').write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):validate_owner_receipt(self.path,self.rom,2253,'prepared')
        (self.path/'prepared-check-v2.json').write_text(json.dumps(receipt))
        (self.path/'fill-events.tsv').write_bytes(b'changed')
        with self.assertRaises(ValueError):validate_owner_receipt(self.path,self.rom,2253,'prepared')
