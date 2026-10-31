import contextlib
import io
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from source_timing import assess_repeatability, capture, main, read_stella_state, summarize, validate_controls


def fixture(lines=262, events=(), frames=40, cycles=800000):
    # Independent Stella 7.0 wire-format fixture; no Atari ROM/state bytes.
    header = struct.pack("<I", 13) + b"07000000state"
    system = struct.pack("<QB", cycles, 0)
    cpu = bytes(5) + struct.pack("<H", 0xF000) + b"\x01" * 7
    cpu += bytes(1 + 4 + 8 + 16 + 1) + b"\x01" + bytes(8)
    riot = bytes(128 + 12) + b"\x01" + bytes(16 + 4 + 4 + 1) + b"\x01" + bytes(4)
    queue = struct.pack("<I", 16) + bytes([len(events)])
    queue += bytes(value for pair in events for value in pair) + bytes(15)
    queue += bytes(1) + b"\xff" * 255
    frame = b"\x01" * 3 + struct.pack("<5I", 0, lines, lines, frames, 0)
    return header + system + cpu + riot + queue + frame + struct.pack("<I", 262)


class TimingTests(unittest.TestCase):
    def test_relative_backend_path_survives_the_isolated_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / "stella-test"
            executable.write_text("#!/bin/sh\nexit 0\n")
            executable.chmod(0o755)
            rom = root / "fixture.bin"
            rom.write_bytes(bytes(4096))
            relative = os.path.relpath(executable, Path.cwd())
            with (
                patch("source_timing.verified_input", return_value={}),
                patch("source_timing.subprocess.run", side_effect=RuntimeError("intercepted launch")) as launch,
                self.assertRaisesRegex(RuntimeError, "intercepted launch"),
            ):
                capture(rom, relative, root / "capture")
            self.assertEqual(Path(launch.call_args.args[0][0]), executable.resolve())

    def test_console_buttons_have_the_observed_effect_and_reset_preserves_mode(self):
        points = [{"phase": phase, "ram_80": value} for phase, value in (
            ("cold_reset", 0), ("steady", 0), ("reset_pressed", 0), ("reset_released", 0),
            ("select_1_pressed", 1), ("select_2_pressed", 2), ("select_3_pressed", 3),
            ("advanced_reset_pressed", 3))]
        validate_controls(points)
        points[-1]["ram_80"] = 0
        with self.assertRaisesRegex(ValueError, "console"):
            validate_controls(points)

    def test_timing_repeatability_does_not_claim_identical_game_state(self):
        a = {"backend": {"version": "7.0"}, "policy": {"reset": "explicit"},
             "summary": {"cycles_per_frame": 19912},
             "checkpoints": [{"phase": "steady", "layout": 0, "ram_80": 0,
                              "cycles": 100000, "ram_sha256": "a", "state_sha256": "one"}]}
        b = {**a, "checkpoints": [{**a["checkpoints"][0], "cycles": 119912,
                                  "ram_sha256": "b", "state_sha256": "two"}]}
        result = assess_repeatability([a, b])
        self.assertTrue(result["stable_timing_equal"])
        self.assertFalse(result["checkpoint_state_equal"])
        self.assertFalse(result["serialized_bytes_equal"])

    def test_changed_timing_or_console_mode_is_rejected(self):
        a = {"backend": {}, "policy": {}, "summary": {"cycles": 19912},
             "checkpoints": [{"phase": "select", "layout": 0, "ram_80": 1, "state_sha256": "a"}]}
        for b in ({**a, "summary": {"cycles": 20000}},
                  {**a, "checkpoints": [{**a["checkpoints"][0], "ram_80": 2}]}):
            with self.assertRaises(ValueError):
                assess_repeatability([a, b])

    def test_counts_are_read_structurally_and_not_assumed_ntsc(self):
        for lines in (262, 313):
            with self.subTest(lines=lines):
                result = read_stella_state(fixture(lines=lines))
                self.assertEqual(result["last_lines"], lines)
                self.assertEqual(result["frames"], 40)
                self.assertEqual(result["cycles"], 800000)

    def test_variable_delay_queue_does_not_shift_frame_fields(self):
        self.assertEqual(read_stella_state(fixture(lines=313, events=((3, 5), (9, 11))))["last_lines"], 313)

    def test_unknown_header_and_truncated_fields_fail(self):
        state = fixture()
        for bad in (b"", state[:16], state[:250], state[:-30], state.replace(b"07000000state", b"09000000state")):
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                read_stella_state(bad)

    def test_invalid_boolean_queue_shape_index_and_layout_fail(self):
        state = fixture()
        # Offsets follow the independent fixture's explicit component sizes.
        for offset, value in ((33, 0), (250, 15), (254, 17), (270, 16), (525, 16), (545, 2)):
            bad = bytearray(state)
            bad[offset] = value
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                read_stella_state(bytes(bad))

    def test_aligned_steady_interval_uses_observed_frames_and_cycles(self):
        points = [
            {"phase": "cold", "cycles": 7, "frames": 0, "current_lines": 0, "last_lines": 0, "previous_lines": 0},
            {"phase": "steady", "cycles": 100000, "frames": 5, "current_lines": 0, "last_lines": 262, "previous_lines": 262},
            {"phase": "reset_released", "cycles": 100000 + 600 * 19912, "frames": 605, "current_lines": 0, "last_lines": 262, "previous_lines": 262},
        ]
        result = summarize(points)
        self.assertEqual(result["steady_cpu_cycles_per_frame"], {"numerator": 19912, "denominator": 1})
        self.assertEqual(result["steady_scanlines"], [262])

    def test_partial_frame_or_inconsistent_interval_is_not_accepted(self):
        a = {"phase": "steady", "cycles": 100, "frames": 5, "current_lines": 1, "last_lines": 262, "previous_lines": 262}
        b = {**a, "phase": "reset_released", "cycles": 20012, "frames": 6, "current_lines": 0}
        with self.assertRaisesRegex(ValueError, "aligned"):
            summarize([a, b])
        a["current_lines"] = 0
        b["cycles"] += 3
        with self.assertRaisesRegex(ValueError, "cycles"):
            summarize([a, b])

    def test_wrong_rom_is_rejected_before_any_backend_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = Path(tmp) / "wrong.bin"
            bad = bytearray(4096)
            bad[-4:] = b"\x00\xf0\x00\xf0"
            rom.write_bytes(bad)
            with patch("source_timing.subprocess.run") as backend, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--rom", str(rom)]), 1)
                backend.assert_not_called()

    def test_public_report_destination_never_receives_raw_rom_captures(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            output = Path(tmp) / "public/report.json"
            run = {"backend": {}, "policy": {}, "summary": {}, "checkpoints": []}
            with (
                patch("source_timing.ROOT", repo),
                patch("source_timing.verified_input", return_value={}),
                patch("source_timing.capture", return_value=run) as capture,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(main(["--output", str(output)]), 0)
            for call in capture.call_args_list:
                self.assertTrue(call.args[2].is_relative_to(repo / "outputs/reference-inventory"))
                self.assertFalse(call.args[2].is_relative_to(output.parent))


if __name__ == "__main__":
    unittest.main()
