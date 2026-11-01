import importlib
from pathlib import Path
import struct
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class NativeWriteLoopCheckTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('native_write_loop_check'), 'actual-Z80 loop checker missing')
        return importlib.import_module('native_write_loop_check')

    def test_complete_cpu_flags_unwritten_ram_and_target_guards_are_required(self):
        api = self.api(); ram = bytes([165]) * 128
        expected = {'a': 51, 'x': 2, 'y': 0, 'p': 123, 'ram': ram, 'fast': True, 'iy': 0xC002}
        row = bytes((51, 2, 0, 0x42, 1, 64, 56, 1)) + struct.pack('<4H', 0xC07F, 0xC002, 0xF380, 0) + ram + struct.pack('<I', 500)
        self.assertEqual(api.verify_case(row, expected), 500)
        for offset, value in ((3, 0xC2), (5, 0), (8, 0), (10, 0), (14, 1), (20, 0)):
            bad = bytearray(row); bad[offset] = value
            with self.assertRaises(ValueError): api.verify_case(bytes(bad), expected)
        with self.assertRaises(ValueError): api.verify_case(row[:-1], expected)

    def test_a_rejected_guard_must_preserve_input_before_the_original_body(self):
        api = self.api(); ram = bytes(range(128))
        expected = {'a': 165, 'x': 7, 'y': 90, 'p': 249, 'ram': ram, 'fast': False, 'iy': 0xC007}
        row = bytes((165, 7, 90, 128, 1, 64, 56, 0)) + struct.pack('<4H', 0xC07F, 0xC007, 0xF380, 0) + ram + struct.pack('<I', 100)
        self.assertEqual(api.verify_case(row, expected), 100)
        bad = bytearray(row); bad[7] = 1
        with self.assertRaises(ValueError): api.verify_case(bytes(bad), expected)

    def test_eof_finishes_without_falling_through_after_emulator_exit_request(self):
        api = self.api(); tclsh = shutil.which('tclsh')
        if not tclsh: self.skipTest('Tcl interpreter unavailable')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory); (out / 'cases.bin').write_bytes(b'')
            # openMSX exit schedules shutdown and returns to Tcl. Execute the
            # real generated handler with that observed behavior.
            shim = '''proc exit args {return}
proc after args {return}
proc machine_info args {return 3579545}
proc debug args {
    switch [lindex $args 0] {
        set_bp {return 1}
        size {return 65536}
        read_block {return [string repeat [binary format c 165] [lindex $args 3]]}
        default {return}
    }
}
'''
            script = shim + api.launch_script(out, {'ready': 16400, 'run_loop': 16416}, 5)
            script += '\nset count 5\nputs [catch {dispatch_loop} error]\n'
            result = subprocess.run([tclsh], input=script, capture_output=True, text=True)
            self.assertEqual(result.stdout.strip(), '0', result.stderr)
            self.assertEqual(json.loads((out / 'complete.json').read_text())['cases'], 5)

    def test_failed_heap_guard_cannot_write_a_success_receipt_after_exit_returns(self):
        api = self.api(); tclsh = shutil.which('tclsh')
        if not tclsh: self.skipTest('Tcl interpreter unavailable')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory); (out / 'cases.bin').write_bytes(b'')
            shim = '''proc exit args {return}
proc after args {return}
proc machine_info args {return 3579545}
proc debug args {
    switch [lindex $args 0] {
        set_bp {return 1}
        size {return 65536}
        read_block {return [string repeat [binary format c 0] [lindex $args 3]]}
        default {return}
    }
}
'''
            script = shim + api.launch_script(out, {'ready': 16400, 'run_loop': 16416}, 5)
            script += '\nset count 5\nputs [catch {dispatch_loop} error]\n'
            subprocess.run([tclsh], input=script, capture_output=True, text=True)
            self.assertFalse((out / 'complete.json').exists(), 'failed heap guard wrote success')
