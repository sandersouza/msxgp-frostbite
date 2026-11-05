"""Instruction-only mapper and source-snapshot inventory for sealed Q-E.

sjasmplus listings retain nested source names and emitted instruction bytes; data
pseudo-ops and inactive branches never become patch candidates. F's movement.asm
owns the first three active ORGs: resident bank0, boot bank1, native bank2. I/J/K
and contact14 are resident; L is bank2; Q is resident followed by bank7. P is a
sibling control build, not an ancestor of Q, and is deliberately not overlaid.

Every listed instruction must match final Q, unless differing bytes are covered
by a documented patch from a *later* producer. Snapshot candidates redirect only
C000..C07F address operands in presentation*.asm (excluding audio), and explicit
LD H,$C0 source-pointer construction. Colour immediates and C080+ stay intact.
"""
import json
from pathlib import Path
import re

from presentation_band_spike import sha
from presentation_inherited_build import EXPECTED

Q_SHA = '2654da3abdb2fc2624f6485a9104327447e0493f64a864feb56b41212dc5ada9'
MNEMONICS = set('ADC ADD AND BIT CALL CCF CP CPD CPDR CPI CPIR CPL DAA DEC DI DJNZ EI EX EXX HALT IM IN INC IND INDR INI INIR JP JR LD LDD LDDR LDI LDIR NEG NOP OR OTDR OTIR OUT OUTD OUTI POP PUSH RES RET RETI RETN RL RLA RLC RLCA RLD RR RRA RRC RRCA RRD RST SBC SCF SET SLA SLL SRA SRL SUB XOR'.split())
LINE = re.compile(r'^\s*(\d+)\+*\s*([0-9A-Fa-f]{4})\s+(.*)$')
EMITTED = re.compile(r'^((?:[0-9A-Fa-f]{2} )*[0-9A-Fa-f]{2})\s{2,}(.*)$')


def parse_listing(text, *, layout):
    """Return real emitted instructions with source and physical bank provenance."""
    stack, result, f_orgs = [], [], 0
    for text_line in text.splitlines():
        if text_line.startswith('# file opened: '):
            stack.append(Path(text_line.removeprefix('# file opened: ')).name)
            continue
        if text_line.startswith('# file closed: '):
            name = Path(text_line.removeprefix('# file closed: ')).name
            if not stack or stack.pop() != name:
                raise ValueError(f'unbalanced listing source stack: {name}')
            continue
        matched = LINE.match(text_line)
        if not matched:
            continue
        line, address, rest = matched.groups()
        address = int(address, 16)
        rest = rest.strip()
        if rest.startswith('~'):
            continue
        if stack and stack[-1] == 'movement.asm' and re.match(r'ORG\s+\$', rest, re.I):
            f_orgs += 1
        emitted = EMITTED.match(rest)
        if not emitted:
            continue
        raw, assembly = emitted.groups()
        assembly = assembly.lstrip('> ').strip()
        if not assembly or assembly.split()[0].upper() not in MNEMONICS:
            continue
        if not stack:
            raise ValueError('emitted instruction has no source provenance')
        if layout == 'f':
            if f_orgs not in (1, 2, 3):
                raise ValueError('F executable instruction outside documented first three ORGs')
            bank = f_orgs-1
        elif layout in ('i', 'j', 'k', 'contact14'):
            bank = 0
        elif layout == 'l':
            bank = 2
        elif layout in ('p', 'q'):
            bank = 0 if address < 0x8000 else 7
        else:
            raise ValueError(f'unsupported listing layout: {layout}')
        origin = 0x4000 if bank == 0 else 0x8000
        if not origin <= address < origin+16384:
            raise ValueError(f'instruction outside physical bank{bank}: {address:04X}')
        result.append(dict(bank=bank, address=address, offset=bank*16384+address-origin,
                           source=stack[-1], line=int(line), before=bytes.fromhex(raw).hex(), assembly=assembly))
    if stack:
        raise ValueError(f'unclosed listing source stack: {stack}')
    return result


def classify_instruction(row):
    """Produce a complete snapshot replacement or a mapper relocation candidate."""
    raw = bytes.fromhex(row['before'])
    if row['assembly'].split()[0].upper() != 'LD':
        return None
    if raw == bytes.fromhex('320070'):
        return dict(row, kind='mapper')
    source = row['source']
    if not (source.startswith('presentation') and source.endswith('.asm')) or source.startswith('presentation_audio'):
        return None
    high = None
    if raw == bytes.fromhex('26c0'):
        high = 1
    elif len(raw) == 3 and raw[0] in (0x01, 0x11, 0x21, 0x31, 0x2A, 0x3A):
        if 0xC000 <= int.from_bytes(raw[1:3], 'little') <= 0xC07F:
            high = 2
    elif len(raw) == 4 and ((raw[0] == 0xED and raw[1] in (0x4B, 0x5B, 0x6B, 0x7B)) or
                            (raw[0] in (0xDD, 0xFD) and raw[1] in (0x21, 0x2A))):
        if 0xC000 <= int.from_bytes(raw[2:4], 'little') <= 0xC07F:
            high = 3
    if high is None:
        return None
    changed = bytearray(raw)
    changed[high] = 0xF0
    return dict(row, kind='snapshot', after=changed.hex())


def _patch_ranges(meta, stage):
    if stage in 'ijklm' and len(stage) == 1:
        patches = meta[f'inherited_{stage}']['patches']
    elif stage == 'contact14':
        patches = meta['contact14']['resident_patches']
    else:
        patches = meta['prepared_ice']['patches']
    return [(patch['offset'], patch['offset']+len(bytes.fromhex(patch['after']))) for patch in patches]


def validate_instructions(rows, rom, later_ranges, *, stage):
    """Validate all bytes, then retain only instructions not replaced later."""
    active = []
    for row in rows:
        raw = bytes.fromhex(row['before'])
        offset = row['offset']
        actual = rom[offset:offset+len(raw)]
        if len(actual) != len(raw):
            raise ValueError(f'instruction outside ROM: {row}')
        differences = [offset+i for i, (old, new) in enumerate(zip(raw, actual)) if old != new]
        if any(not any(start <= at < end for start, end in later_ranges) for at in differences):
            raise ValueError(f'unexplained {stage} instruction mismatch at bank{row["bank"]}:${row["address"]:04X} '
                             f'{row["source"]}:{row["line"]}: listed {raw.hex()}, Q {actual.hex()}')
        # Coincidentally equal bytes within newer code do not establish an old
        # instruction boundary. The newer producer owns that whole patch span.
        if any(start < offset+len(raw) and offset < end for start, end in later_ranges):
            continue
        active.append(row)
    return active


def inventory(base_f: Path, chain_root: Path, rom: bytes) -> list[dict]:
    """Validate exact F/Q and return unique final-code mapper/snapshot patches.

    Raises ValueError on missing provenance, unsupported producer layout or any
    unexplained instruction mismatch. The returned mapper records intentionally
    omit ``after``: the interrupt kernel chooses their replacement entry point.
    """
    base_f, chain_root = Path(base_f), Path(chain_root)
    f_meta = json.loads((base_f / 'build.json').read_text())
    if sha((base_f / f_meta['rom']['filename']).read_bytes()) != EXPECTED['f'] or sha(rom) != Q_SHA:
        raise ValueError('clock inventory requires exact canonical F and sealed Q-E ROMs')
    stages = ['f', 'i', 'j', 'k', 'l', 'm', 'contact14', 'q']
    patches, listings = {}, {}
    for stage in stages:
        if stage == 'f':
            listing = base_f / 'presentation.lst'
            patches[stage] = []
        else:
            meta = json.loads((chain_root / stage / 'build.json').read_text())
            patches[stage] = _patch_ranges(meta, stage)
            listing = chain_root / stage / 'patch.lst'
        listings[stage] = [] if stage == 'm' else parse_listing(listing.read_text(), layout=stage)
    candidates = {}
    for index, stage in enumerate(stages):
        later = [span for following in stages[index+1:] for span in patches[following]]
        for row in validate_instructions(listings[stage], rom, later, stage=stage):
            offset = row['offset']
            candidate = classify_instruction(row)
            if candidate:
                previous = candidates.get(offset)
                if previous and (previous['before'], previous['kind']) != (candidate['before'], candidate['kind']):
                    raise ValueError(f'conflicting instruction inventory at ROM offset {offset:#x}')
                candidates[offset] = dict(candidate, stage=stage)
    return [candidates[offset] for offset in sorted(candidates)]
