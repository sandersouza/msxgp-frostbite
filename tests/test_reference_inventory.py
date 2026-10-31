import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reference_inventory import describe, load_manifest, main, validate


def synthetic_rom():
    data = bytearray(4096)
    data[-6:] = bytes.fromhex("341200f000f0")
    return bytes(data)


class InventoryTests(unittest.TestCase):
    def test_structure_preserves_raw_unused_word_without_claiming_nmi(self):
        result = describe(synthetic_rom())
        self.assertEqual(result["size"], 4096)
        self.assertEqual(result["layout"], "4K")
        self.assertEqual(result["trailing_words"], {"unused_nmi_word": 0x1234, "reset": 0xF000, "irq_word": 0xF000})

    def test_invalid_cartridge_size_is_not_silently_accepted(self):
        for data in (b"", bytes(4095), bytes(8192)):
            with self.subTest(size=len(data)), self.assertRaisesRegex(ValueError, "4096"):
                describe(data)

    def test_same_size_corruption_fails_both_digest_checks(self):
        data = synthetic_rom()
        expected = describe(data)
        altered = bytes([1]) + data[1:]
        self.assertEqual(validate(data, expected), [])
        errors = validate(altered, expected)
        self.assertIn("sha256 mismatch", errors)
        self.assertIn("md5 mismatch", errors)

    def test_reset_vector_outside_plain_4k_window_is_invalid(self):
        data = bytearray(synthetic_rom())
        data[-4:-2] = b"\x00\x20"
        with self.assertRaisesRegex(ValueError, "reset"):
            describe(bytes(data))

    def test_manifest_schema_and_required_identity_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            for manifest in ({"schema_version": 9}, {"schema_version": 1, "input": {}},
                             {"schema_version": 1, "input": {"path": "rom.bin", "size": 4096, "sha256": "x", "md5": "x"}}):
                path.write_text(json.dumps(manifest))
                with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                    load_manifest(path)

    def test_cli_missing_input_has_failure_status_and_useful_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = io.StringIO()
            with contextlib.redirect_stderr(output):
                code = main(["--rom", str(Path(tmp) / "missing.bin")])
            self.assertEqual(code, 1)
            self.assertIn("Reference inventory failed", output.getvalue())

    def test_cli_mismatch_never_rewrites_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = synthetic_rom()
            expected = describe(data)
            expected["path"] = "rom.bin"
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "input": expected}))
            original_manifest = manifest.read_bytes()
            rom = root / "rom.bin"
            rom.write_bytes(bytes([1]) + data[1:])
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--rom", str(rom), "--manifest", str(manifest)]), 1)
            self.assertEqual(manifest.read_bytes(), original_manifest)


if __name__ == "__main__":
    unittest.main()
