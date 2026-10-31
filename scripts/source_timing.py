#!/usr/bin/env python3
"""Measure the validated original in isolated, bounded Stella debugger runs."""
import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile

from reference_inventory import ROOT, MANIFEST, verified_input

STATE_HEADER = b"07000000state"
SOURCE_COMMIT = "d55b1aec0d067a4c901a6dcdf81cb8f579685659"
PHASES = [
    ("cold_reset", 0, None),
    ("first_update", 1, None),
    ("second_update", 1, None),
    ("steady", 600, None),
    ("reset_pressed", 1, 0x3E),
    ("reset_released", 600, 0x3F),
    ("select_1_pressed", 1, 0x3D),
    ("select_2_pressed", 1, 0x3D),
    ("select_3_pressed", 1, 0x3D),
    ("advanced_reset_pressed", 1, 0x3E),
]


class Reader:
    def __init__(self, data):
        self.data = data
        self.position = 0

    def take(self, size):
        end = self.position + size
        if end > len(self.data):
            raise ValueError(f"truncated Stella state at byte {self.position}")
        result = self.data[self.position:end]
        self.position = end
        return result

    def number(self, size):
        return int.from_bytes(self.take(size), "little")

    def boolean(self):
        value = self.number(1)
        if value not in (0x01, 0xFE):
            raise ValueError("invalid Stella serialized boolean")
        return value == 0xFE


def read_stella_state(data: bytes) -> dict:
    """Decode the source-reviewed 7.0 DEBUGGER_SUPPORT prefix, never search values."""
    if sys.byteorder != "little":
        raise ValueError("Stella state decoder supports little-endian hosts only")
    r = Reader(data)
    if r.number(4) != len(STATE_HEADER) or r.take(len(STATE_HEADER)) != STATE_HEADER:
        raise ValueError("unsupported Stella state header (requires 7.0)")
    cycles = r.number(8)
    r.take(1)  # System data bus.
    r.take(5)  # CPU A/X/Y/SP/IR.
    r.number(2)  # PC.
    for _ in range(7):
        r.boolean()
    r.take(1)
    r.number(4)
    r.take(8 + 16 + 1)  # Access/source addresses and flags.
    r.boolean()
    r.number(8)
    ram = r.take(128)
    r.take(12)  # RIOT timer/subtimer/divider.
    r.boolean()
    r.take(16 + 4)  # Cycle counters and DEBUGGER_SUPPORT timReadCycles.
    r.take(5)  # DDRA/DDRB/outA/outB/interruptFlag.
    r.boolean()
    r.take(4)  # outTimer.
    if r.number(4) != 16:
        raise ValueError("unsupported Stella debugger state delay queue layout")
    for _ in range(16):
        size = r.number(1)
        if size > 16:
            raise ValueError("invalid Stella delay queue member size")
        r.take(2 * size)
    if r.number(1) >= 16:
        raise ValueError("invalid Stella delay queue index")
    if any(index >= 16 and index != 255 for index in r.take(255)):
        raise ValueError("invalid Stella delay queue address index")
    for _ in range(3):
        r.boolean()
    current, last, previous, frames, layout = [r.number(4) for _ in range(5)]
    if layout not in (0, 1):
        raise ValueError("unsupported Stella frame layout")
    return {"cycles": cycles, "current_lines": current, "last_lines": last,
            "previous_lines": previous, "frames": frames, "layout": layout,
            "ram_80": ram[0], "ram_sha256": hashlib.sha256(ram).hexdigest()}


def summarize(checkpoints: list[dict]) -> dict:
    phases = {point["phase"]: point for point in checkpoints}
    a, b = phases["steady"], phases["reset_released"]
    if any(p["current_lines"] != 0 or p["last_lines"] != p["previous_lines"]
           or p["last_lines"] <= 0 for p in (a, b)):
        raise ValueError("steady interval endpoints are not aligned/stable")
    if a["last_lines"] != b["last_lines"]:
        raise ValueError("steady scanline counts disagree")
    frames, cycles = b["frames"] - a["frames"], b["cycles"] - a["cycles"]
    if frames <= 0 or cycles <= 0:
        raise ValueError("non-increasing measured frame/cycle counters")
    ratio = Fraction(cycles, frames)
    if ratio != a["last_lines"] * 76:
        raise ValueError("measured cycles do not match complete 76-cycle scanlines")
    return {"steady_scanlines": sorted({a["last_lines"], b["last_lines"]}),
            "interval_observed_frames": frames, "interval_cpu_cycles": cycles,
            "steady_cpu_cycles_per_frame": {"numerator": ratio.numerator, "denominator": ratio.denominator},
            "scope": "observed aligned steady/Reset interval, not full-game acceptance"}


def debugger_script() -> str:
    commands = ["base dec", "reset", "swchb $3f"]
    for slot, (phase, steps, switches) in enumerate(PHASES):
        if phase in ("select_2_pressed", "select_3_pressed", "advanced_reset_pressed"):
            commands += ["swchb $3f", "frame 30"]
        if switches is not None:
            commands.append(f"swchb ${switches:02x}")
        if steps:
            commands.append(f"frame {steps}")
        commands.append(f"saveState {slot}")
    return "\n".join(commands + ["exitRom", ""])


def assess_repeatability(runs: list[dict]) -> dict:
    a, b = runs
    if any(a[key] != b[key] for key in ("backend", "policy", "summary")):
        raise ValueError("repeated source captures disagree on backend/policy/stable timing")
    control = lambda run: [(p["phase"], p["layout"], p["ram_80"]) for p in run["checkpoints"]]
    if control(a) != control(b):
        raise ValueError("repeated source captures disagree on console-mode checkpoints")
    observations = lambda run: [{k: v for k, v in p.items() if k != "state_sha256"}
                                for p in run["checkpoints"]]
    return {"isolated_runs": 2, "stable_timing_equal": True,
            "checkpoint_state_equal": observations(a) == observations(b),
            "serialized_bytes_equal": [p["state_sha256"] for p in a["checkpoints"]]
                                      == [p["state_sha256"] for p in b["checkpoints"]],
            "scope": "stable interval and mode checkpoints; full state/RNG replay is issue #7"}


def validate_controls(checkpoints: list[dict]) -> None:
    values = {point["phase"]: point["ram_80"] for point in checkpoints}
    expected = {"cold_reset": 0, "steady": 0, "reset_pressed": 0, "reset_released": 0,
                "select_1_pressed": 1, "select_2_pressed": 2, "select_3_pressed": 3,
                "advanced_reset_pressed": 3}
    if any(values.get(phase) != mode for phase, mode in expected.items()):
        raise ValueError("console input checkpoints did not produce the expected reference observations")


def capture(rom: Path, stella: str, output_dir: Path) -> dict:
    verified_input(rom)
    executable = shutil.which(stella)
    if not executable:
        raise ValueError(f"missing Stella executable: {stella}")
    executable = str(Path(executable).resolve())
    output_dir.mkdir(parents=True, exist_ok=False)
    settings = output_dir / "settings"
    settings.mkdir()
    local_rom = output_dir / "frostbite.bin"
    shutil.copyfile(rom, local_rom)
    script = debugger_script()
    (settings / "autoexec.script").write_text(script)
    options = ["-basedir", str(settings.resolve()), "-video", "software",
               "-audio.enabled", "0", "-logtoconsole", "1", "-loglevel", "2",
               "-format", "AUTO", "-dev.settings", "1",
               "-dev.ramrandom", "0", "-dev.tiarandom", "0", "-dev.cpurandom", "0",
               "-dev.bankrandom", "0", "-dev.tv.jitter", "0", "-dev.tiadriven", "0",
               "-dev.hsrandom", "0", "-dbg.autosave", "0",
               "-debug", "-exitlauncher", "0"]
    environment = {**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}
    process = subprocess.run([executable, *options, str(local_rom.resolve())],
                             cwd=output_dir, env=environment, capture_output=True,
                             text=True, timeout=30, check=True)
    log = process.stdout + process.stderr
    (output_dir / "stella.log").write_text(log)
    if not re.search(r"^Stella 7\.0$", log, re.MULTILINE) or "Debugger" not in log:
        raise ValueError("unsupported Stella build; requires 7.0 with Debugger")
    states = output_dir / "settings/state"
    checkpoints = []
    for slot, (phase, steps, switches) in enumerate(PHASES):
        candidates = list(states.glob(f"*.st{slot}"))
        if len(candidates) != 1:
            raise ValueError(f"missing or ambiguous checkpoint {slot}")
        raw = candidates[0].read_bytes()
        point = read_stella_state(raw)
        point.update(phase=phase, requested_update_calls=steps,
                     release_update_calls_before=30 if slot >= 7 else 0,
                     swchb_command=switches, state_sha256=hashlib.sha256(raw).hexdigest())
        checkpoints.append(point)
    validate_controls(checkpoints)
    if not re.search(r"Display Format:\s+NTSC\*", log):
        raise ValueError("unexpected source display autodetection; inspect raw log")
    return {"backend": {"name": "Stella", "version": "7.0",
                        "binary_sha256": hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
                        "source_contract_commit": SOURCE_COMMIT,
                        "state_header": STATE_HEADER.decode(), "byteorder": sys.byteorder,
                        "features": next(line.strip() for line in log.splitlines() if "Features:" in line),
                        "build": next(line.strip() for line in log.splitlines() if "Build " in line),
                        "host": {"system": platform.system(), "machine": platform.machine()}},
            "policy": {"format": "AUTO (observed NTSC*)", "ram_cpu_tia_randomization": False,
                       "random_unused_tia_pins": False, "random_hotspot_peeks": False,
                       "initialization": "debugger reset (System reset), SWCHB=3f; not console Game Reset",
                       "console_switches": {"released": "3f", "reset_pressed": "3e", "select_pressed": "3d"},
                       "inputs": "both joysticks neutral, difficulty B/B, color",
                       "sound": False, "script_sha256": hashlib.sha256(script.encode()).hexdigest(),
                       "boundary": "after each requested debugger update batch; partial startup frames retained"},
            "checkpoints": checkpoints, "summary": summarize(checkpoints)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=ROOT / "references/roms/frostbite.bin")
    parser.add_argument("--stella", default="stella")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/reference-inventory/timing.json")
    args = parser.parse_args(argv)
    try:
        identity = verified_input(args.rom)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        raw_root = ROOT / "outputs/reference-inventory"
        raw_root.mkdir(parents=True, exist_ok=True)
        runs = []
        raw_paths = []
        for _ in range(2):
            parent = Path(tempfile.mkdtemp(prefix="capture-", dir=raw_root))
            run_dir = parent / "run"
            runs.append(capture(args.rom.resolve(), args.stella, run_dir))
            raw_paths.append(str(run_dir))
        repeatability = assess_repeatability(runs)
        report = {"schema_version": 1, "rom": identity, "runs": runs,
                  "repeatability": repeatability,
                  "limitations": ["Commercial revision/dump provenance not independently established",
                                  "Emulator counters, not physical-machine or wall-clock measurements",
                                  "Checkpoint inventory, not frame-by-frame full-game timing coverage",
                                  "Full serialized/game-state repeatability is not established by stable cadence"]}
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Verified repeated stable timing; {runs[0]['summary']}; report={args.output}")
        print(f"State repeatability: {repeatability}")
        print("Raw local captures: " + ", ".join(raw_paths))
        return 0
    except (OSError, ValueError, KeyError, TypeError, StopIteration, subprocess.SubprocessError) as error:
        print(f"Source timing failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
