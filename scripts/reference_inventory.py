#!/usr/bin/env python3
"""Identify and verify the supplied local Frostbite reference without changing it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "references/manifest.json"


def describe(data: bytes) -> dict:
    if len(data) != 4096:
        raise ValueError("expected a plain 4096-byte Atari 2600 image")
    words = [int.from_bytes(data[offset:offset + 2], "little") for offset in (-6, -4)]
    words.append(int.from_bytes(data[-2:], "little"))
    if not words[1] & 0x1000:
        raise ValueError("reset vector does not select the 6507 cartridge window")
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "md5": hashlib.md5(data).hexdigest(),
        "layout": "4K",
        "trailing_words": {"unused_nmi_word": words[0], "reset": words[1], "irq_word": words[2]},
    }


def validate(data: bytes, expected: dict) -> list[str]:
    actual = describe(data)
    return [f"{key} mismatch" for key in ("size", "sha256", "md5", "layout", "trailing_words")
            if actual[key] != expected[key]]


def load_manifest(path: Path = MANIFEST) -> dict:
    manifest = json.loads(path.read_text())
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("unsupported reference manifest schema")
    expected = manifest.get("input")
    if not isinstance(expected, dict):
        raise ValueError("manifest requires one input identity")
    if not isinstance(expected.get("path"), str) or not expected["path"]:
        raise ValueError("manifest requires an input path")
    if type(expected.get("size")) is not int or expected["size"] != 4096:
        raise ValueError("manifest requires size 4096")
    for key, length in (("sha256", 64), ("md5", 32)):
        if not isinstance(expected.get(key), str) or not re.fullmatch(f"[0-9a-f]{{{length}}}", expected[key]):
            raise ValueError(f"manifest requires a lowercase {key} digest")
    if expected.get("layout") != "4K":
        raise ValueError("manifest requires 4K layout")
    words = expected.get("trailing_words")
    if not isinstance(words, dict) or set(words) != {"unused_nmi_word", "reset", "irq_word"}:
        raise ValueError("manifest requires three trailing words")
    if any(type(value) is not int or not 0 <= value <= 65535 for value in words.values()):
        raise ValueError("manifest trailing words must be 16-bit integers")
    return manifest


def verified_input(rom: Path, manifest_path: Path = MANIFEST) -> dict:
    expected = load_manifest(manifest_path)["input"]
    data = rom.read_bytes()
    errors = validate(data, expected)
    if errors:
        raise ValueError("; ".join(errors))
    return describe(data)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--describe", action="store_true",
                        help="inspect the explicit/default image without rewriting authority")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        rom = args.rom or ROOT / manifest["input"]["path"]
        if args.describe:
            print(json.dumps({"verification": "inspection only", **describe(rom.read_bytes())}, indent=2))
        else:
            actual = verified_input(rom, args.manifest)
            print(f"Verified Frostbite reference: {actual['size']} bytes, SHA-256 {actual['sha256']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Reference inventory failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
