"""Artifact identity gates for runtime checks, without an emulator dependency."""
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
from xml.dom import minidom

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))


class SmokeTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('smoke'), 'smoke utility missing')
        return importlib.import_module('smoke')

    def test_wrong_artifact_cannot_borrow_another_build_identity(self):
        api=self.api()
        data=b'current ROM'
        metadata={'diagnostic':True,'rom':{'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}}
        api.validate_build_identity(data,metadata)
        with self.assertRaisesRegex(ValueError,'build identity'):
            api.validate_build_identity(b'changed ROM',metadata)

    def test_machine_profile_rejects_expanded_ram_or_vdp(self):
        api=self.api()
        xml=b'<msxconfig><devices><RAM><mem size="0x10000"/></RAM><VDP><version>TMS9918A</version><vram>16</vram></VDP></devices></msxconfig>'
        api.validate_machine_profile(xml)
        with self.assertRaisesRegex(ValueError,'64 KiB'):
            api.validate_machine_profile(xml.replace(b'0x10000',b'0x20000'))
        with self.assertRaisesRegex(ValueError,'TMS9918'):
            api.validate_machine_profile(xml.replace(b'TMS9918A',b'V9938'))

    def test_isolated_profile_resolves_bundled_firmware_without_user_cache(self):
        api=self.api()
        self.assertTrue(hasattr(api,'isolated_profile'),'firmware resolution missing')
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            (directory/'cbios.bin').write_bytes(b'fixture firmware')
            original=b'<msxconfig><ROM><rom><filename>cbios.bin</filename></rom></ROM></msxconfig>'
            path=directory/'machine.xml'
            path.write_bytes(original)
            result=api.isolated_profile(path)
            document=minidom.parseString(result)
            self.assertIsNotNone(document.doctype,'openMSX requires a hardware systemID')
            self.assertEqual(document.doctype.systemId,'msxconfig2.dtd')
            self.assertIn(str(directory/'cbios.bin').encode(),result)
            self.assertEqual(path.read_bytes(),original)

    def test_failed_attempt_removes_latest_success_summary(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            (directory/'smoke.json').write_text('{"passed":true}')
            rom=directory/'invalid.rom'
            rom.write_bytes(b'invalid')
            with mock.patch.object(api,'OUT',directory):
                with self.assertRaises(ValueError):
                    api.run_smoke(rom)
            self.assertFalse((directory/'smoke.json').exists())


if __name__=='__main__':
    unittest.main()
