import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from artifact_hash import digest
from release_check import PAYLOADS, verify_delivery


class ReleaseCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        files = {}
        for name in PAYLOADS:
            path = self.root/name
            path.parent.mkdir(exist_ok=True)
            data = name.encode()
            path.write_bytes(data)
            files[name] = dict(size=len(data), sha256=digest(data))
        self.baseline = dict(files=files)
        self.metadata = dict(native_formats_built=True, files=files.copy())
        self.write_receipt()

    def write_receipt(self):
        (self.root/'native-delivery-build.json').write_text(json.dumps(self.metadata))

    def test_complete_delivery_matches_the_reviewed_baseline(self):
        self.assertEqual(verify_delivery(self.root, self.baseline), self.baseline['files'])

    def test_each_payload_is_checked_for_changed_or_missing_bytes(self):
        for name in PAYLOADS:
            path = self.root/name
            saved = path.read_bytes()
            path.write_bytes(saved+b'changed')
            with self.assertRaises(ValueError):
                verify_delivery(self.root, self.baseline)
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                verify_delivery(self.root, self.baseline)
            path.write_bytes(saved)

    def test_incomplete_or_mismatched_build_receipt_is_rejected(self):
        self.metadata['native_formats_built'] = False
        self.write_receipt()
        with self.assertRaises(ValueError):
            verify_delivery(self.root, self.baseline)
        self.metadata['native_formats_built'] = True
        self.metadata['files'].pop(PAYLOADS[-1])
        self.write_receipt()
        with self.assertRaises(ValueError):
            verify_delivery(self.root, self.baseline)
