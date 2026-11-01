import hashlib
import importlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class MovementEvidenceTests(unittest.TestCase):
    def test_artifact_gate_requires_exact_set_and_actual_unchanged_files(self):
        api=importlib.import_module('movement_evidence')
        with tempfile.TemporaryDirectory() as root:
            directory=Path(root);required=frozenset({'actual.bin','machine.xml'})
            for name in required:(directory/name).write_bytes(name.encode())
            hashes={n:hashlib.sha256((directory/n).read_bytes()).hexdigest() for n in required}
            api.audit_files(directory,hashes,required)
            for forged in ({},{'actual.bin':hashes['actual.bin']},{**hashes,'unexpected.bin':'0'*64}):
                with self.assertRaises(ValueError):api.audit_files(directory,forged,required)
            (directory/'actual.bin').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):api.audit_files(directory,hashes,required)
            (directory/'actual.bin').unlink()
            with self.assertRaises(ValueError):api.audit_files(directory,hashes,required)

    def test_device_scope_includes_replay_mirrors_build_receipt_and_machine(self):
        api=importlib.import_module('movement_evidence')
        self.assertTrue({'devices.omr','mirrors.bin','build.json','complete.json','native-contract.rom'}<=api.cpu_files(True))
        self.assertIn('user-data/machines/Frostbite_Native.xml',api.cpu_files(True))

    def test_failure_identity_rejects_fabricated_reason_and_wrong_stage(self):
        api=importlib.import_module('movement_evidence')
        good={'injection':'spacing','stage':'emulator','cause':'fast-io-spacing','detected':True,'detail':'MOVEMENT_FAIL fast-io-spacing'}
        api.validate_failure_identity(good)
        for patch in ({'detail':'fabricated'},{'cause':'heap-guard'},{'stage':'comparison'},{'detected':False}):
            with self.assertRaises(ValueError):api.validate_failure_identity({**good,**patch})
