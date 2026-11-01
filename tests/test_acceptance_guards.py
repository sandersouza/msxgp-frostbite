"""Execute real Tcl finish procedures when openMSX exit only queues shutdown."""
import importlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class AcceptanceGuardTests(unittest.TestCase):
    def finish(self, name, fault):
        tclsh = shutil.which('tclsh')
        if not tclsh: self.skipTest('Tcl interpreter unavailable')
        source = (ROOT / 'scripts' / name).read_text()
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            for filename in ('cases.bin', 'inputs.bin'): (out / filename).write_bytes(b'')
            script = f'''set floe_dir {{{out}}}
set paced_dir {{{out}}}
set natural 0
set slot 0
set initial_layout 0
set initial_width 0
set fault {fault}
set exits {{}}
array set symbols {{{' '.join(n+' 0' for n in sorted(set(re.findall(r'\$symbols\((\w+)\)', source))))}}}
proc exit args {{lappend ::exits [expr {{[llength $args] ? [lindex $args 0] : 0}}];return}}
proc after args {{return}}
proc reg args {{return [expr {{$::fault eq "iff" && [lindex $args 0] eq "IFF" ? 1 : 0}}]}}
proc machine_info args {{return 3579545}}
proc debug args {{
    switch [lindex $args 0] {{
        set_bp - set_watchpoint {{return 1}}
        size {{return 65536}}
        read {{return [expr {{$::fault eq "slot" && [lindex $args 1] eq "ioports" ? 1 : 0}}]}}
        read_block {{
            set address [lindex $args 2]
            if {{$address==0xF300 && $::fault ne "stack"}} {{
                return [string repeat [binary format c 165] 112][string repeat [binary format c 0] 16]
            }}
            set value [expr {{($::fault eq "heap" && $address==0xD000) || ($::fault eq "stack" && $address==0xF300) ? 0 : 165}}]
            return [string repeat [binary format c $value] [lindex $args 3]]
        }}
        default {{return}}
    }}
}}
'''
            script += source
            finish = 'finish_paced' if name == 'hazard_paced.tcl' else 'finish_floe'
            script += f'\nputs "RESULT [catch {{{finish}}} detail] $::exits"\n'
            result = subprocess.run([tclsh], input=script, text=True, capture_output=True)
            lines = [line for line in result.stdout.splitlines() if line.startswith('RESULT ')]
            self.assertEqual(len(lines), 1, result.stderr)
            receipt = json.loads((out / 'complete.json').read_text()) if (out / 'complete.json').exists() else None
            return lines[0], receipt, result.stderr

    def test_native_failed_final_guards_cannot_write_success_or_reset_exit_code(self):
        for name in ('hazard_native.tcl', 'floe_native.tcl'):
            for fault in ('heap', 'slot', 'iff', 'stack'):
                with self.subTest(name=name, fault=fault):
                    line, receipt, stderr = self.finish(name, fault)
                    self.assertEqual(line, 'RESULT 1 1', stderr)
                    self.assertIsNone(receipt)

    def test_paced_failed_final_guards_cannot_write_success_or_reset_exit_code(self):
        for fault in ('heap', 'stack'):
            with self.subTest(fault=fault):
                line, receipt, stderr = self.finish('hazard_paced.tcl', fault)
                self.assertEqual(line, 'RESULT 1 1', stderr)
                self.assertIsNone(receipt)

    def test_clean_actual_finish_procedures_still_write_exact_success(self):
        for name in ('hazard_native.tcl', 'floe_native.tcl', 'hazard_paced.tcl'):
            with self.subTest(name=name):
                line, receipt, stderr = self.finish(name, 'none')
                self.assertEqual(line, 'RESULT 0 0', stderr)
                self.assertIs(receipt['complete'], True)

    def test_positive_audit_rejects_fatal_logs_even_with_success_receipt(self):
        api = importlib.import_module('progression_delivery')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory); log = out / 'emulator.log'
            (out / 'complete.json').write_text('{"complete":true}')
            for marker in ('FLOE_NATIVE_FAIL', 'FLOE_PACED_FAIL', 'FLOE_FAIL', 'SHIFT_FAIL', 'WRITE_LOOP_FAIL', 'NATIVE_FAIL'):
                log.write_text(f'{marker} heap-guard\n')
                with self.subTest(marker=marker), self.assertRaises(ValueError): api.positive_log(out)
            log.write_text(''); api.positive_log(out)
            log.write_text('ordinary emulator warning\n'); api.positive_log(out)
