"""Rebuild the hand-written I/J/K/L/M presentation patches from canonical F.

These producers read only their explicitly supplied generated parent directory.
All ROM-derived packet tables/includes stay in fresh ignored build outputs.
"""
import json
from pathlib import Path
import subprocess

from environment import ROOT, verified_tool
from presentation_band_spike import apply_patch, sha, verified_bytes
from presentation_inherited_tables import generate
from render_build import symbols

EXPECTED = {
    'f': '838b67ae6ba4c7cbed72f643f64f78b45bb404a1e43b395f36331343f6656ae6',
    'i': '7a9d4eae3cf0e3c4d8f5c4828065131055ea28a0dad7153ee5dcf24d15ca9c91',
    'j': '0c59256373e910392fd71012f4357b4e2737f410541e2a2b1ae2a1e76b0f5c01',
    'k': '4a59e59c6033fc3a8ef0c7898ac0f42739efed9193d96b5299ed2acb482a5d9e',
    'l': '6ed90b73c46928e77ee3af3c8a029c560cacd97dd6dbfb615c9edb1dd8b1f0c2',
    'm': '0e43bd16a5219a2d2548580e581ee5e26c7f440e715c18d96e07dbe033351ad0',
}


def build(stage, base, out, *, i_symbols=None):
    if out.exists():
        raise ValueError('immutable output already exists')
    predecessor = {'i': 'f', 'j': 'i', 'k': 'j', 'l': 'k', 'm': 'l'}[stage]
    meta = json.loads((base / 'build.json').read_text())
    before = verified_bytes(base / meta['rom']['filename'], EXPECTED[predecessor])
    raw_symbols = (base / 'presentation.sym').read_bytes()
    s = symbols(base / 'presentation.sym')
    out.mkdir(parents=True)
    (out / 'symbols.inc').write_text('\n'.join(f'{k} EQU ${v:04X}' for k, v in s.items())+'\n')
    rom = bytearray(before)
    allocation = None
    if stage == 'i':
        rom, allocation = generate(base, out, before)
        allowed = bytearray(len(before))
        for bank, a, b in allocation['regions']:
            at = bank*16384+a-0x8000
            allowed[at:at+b-a] = bytes([1])*(b-a)
        if any(not allowed[index] for index, (a, b) in enumerate(zip(rom, before)) if a != b):
            raise ValueError('ready packets changed storage outside certified allocation regions')
    if stage == 'l':
        tails = before[s['p_sprite_tails_data']:s['p_sprite_tails_data']+135]
        limits = bytes(min(tails[y+28-47:y+46-47])-7 for y in range(19, 134))
        if len(limits) != 115 or min(limits) != 84 or max(limits) != 153:
            raise ValueError('unexpected per-height player limits')
        (out / 'limits.bin').write_bytes(limits)
    q, code = {}, b''
    if stage != 'm':
        source = ROOT / f'src/presentation_inherited_{stage}.asm'
        run = subprocess.run([str(verified_tool('sjasmplus')), '--nologo', f'--inc={out}',
                              f'--raw={out/"patch.bin"}', f'--sym={out/"patch.sym"}', f'--lst={out/"patch.lst"}', str(source)],
                             cwd=ROOT, capture_output=True, text=True)
        (out / 'assembler.log').write_text(run.stdout+run.stderr)
        if run.returncode:
            raise ValueError(run.stdout+run.stderr)
        q = symbols(out / 'patch.sym')
        code = (out / 'patch.bin').read_bytes()
    patches = []
    def patch(at, old, new):
        patches.append(apply_patch(rom, at, old, new))
    def ins(op, address):
        return bytes((op, address & 255, address >> 8))
    if stage == 'i':
        start, end = s['presentation_world_prepare.object']-16384, s['presentation_world_prepare.floes']-16384
        old = ins(205, s['p_world_primitive'])
        patch(before.index(old, start, end), old, ins(205, q['i_primitive']))
        start, end = s['p_fixed_put_actor']-16384, s['p_fixed_resolve']-16384
        old = ins(205, s['p_fixed_resolve_known'])
        patch(before.index(old, start, end), old, ins(205, q['i_actor']))
        patch(s['presentation_init']-16384, bytes.fromhex('2180c0'), ins(205, q['i_init']))
        patch(0x3A08, b'\xff'*len(code), code)
    elif stage == 'j':
        patch(s['p_template_strip_publish.mask']-16384, bytes.fromhex('3ae6c2'), ins(195, q['j_strip']))
        patch(q['j_strip']-16384, b'\xff'*len(code), code)
    elif stage == 'k':
        patch(s['presentation_init']-16384, ins(205, 0x7A08), ins(205, q['k_init']))
        for target, new in [('p_template_decode_names', 'k_decode'), ('p_fast_cell', 'k_name_address')]:
            old = ins(205, s[target])
            at = before.index(old, s['p_fixed_floe_prepare']-16384, s['p_template_object_fuse']-16384)
            patch(at, old, ins(205, q[new]))
        patch(q['k_init']-16384, b'\xff'*len(code), code)
    elif stage == 'l':
        for start, end, target, jump in [
                ('p_player_prepare', 'p_player_prepare.general', 'p_player_prepare.general', False),
                ('p_player_cache_lookup', 'p_player_cache_lookup.ordinary_key', 'p_player_cache_lookup.miss', True)]:
            at = before.index(bytes.fromhex('3a66c0fe54'), s[start], s[end])
            size = 8 if jump else 7
            old = before[at:at+size]
            if old[5] != (0xD2 if jump else 0x30):
                raise ValueError('unexpected player eligibility hook')
            patch(at, old, ins(205, q['l_entry'])+ins(210, s[target])+bytes(size-6))
        at = before.index(bytes.fromhex('3a66c05f8783cb3f'), s['p_player_cache_lookup'], s['p_player_cache_lookup.miss'])+3
        old = bytes.fromhex('5f8783cb3fc6084f')
        patch(at, old, ins(205, q['l_x'])+bytes(len(old)-3))
        patch(0xB253, bytes(len(code)), code)
    else:
        if i_symbols is None:
            raise ValueError('generated I symbols required')
        i = symbols(Path(i_symbols))
        at, verified = i['i_actor']+7, 0x7A53
        if before[verified-0x4000:verified-0x4000+3] != bytes.fromhex('22e3c2'):
            raise ValueError('unverified actor contract')
        patch(at-0x4000, bytes.fromhex('3a95cc'), ins(195, verified))
        raw_symbols += f'\nm_actor_contract: EQU 0x{at:08X}\nm_actor_verified: EQU 0x{verified:08X}\n'.encode()
    if sha(rom) != EXPECTED[stage]:
        raise ValueError(f'sealed {stage.upper()} ROM mismatch: {sha(rom)}')
    name = f'frostbite-inherited-{stage}.rom'
    (out / name).write_bytes(rom)
    (out / 'presentation.sym').write_bytes(raw_symbols)
    (out / 'geometry').symlink_to((base / 'geometry').resolve(), target_is_directory=True)
    if stage == 'i':
        meta['baseline_template_assets'] = json.loads(json.dumps(meta['template_assets']))
        assets = out / 'template-assets'
        assets.mkdir()
        for bank in meta['template_assets']['physical_banks']:
            bank_name = f'assets-{bank:03d}.bin'
            data = bytes(rom[bank*16384:(bank+1)*16384])
            (assets / bank_name).write_bytes(data)
            meta['template_assets']['files'][bank_name] = sha(data)
        meta['template_assets']['baseline_logical_patterns_sha256'] = meta['template_assets'].pop('logical_patterns_sha256')
        meta['template_assets']['private_live_domain_sha256'] = sha((out / 'live-domain.json').read_bytes())
        meta['template_assets']['scope'] = 'Live row/bear grammar byte-exact; unreachable pattern/half slots reclaimed; raw floe namespace unchanged.'
        meta['baseline_static_presentation'] = json.loads(json.dumps(meta['static_presentation']))
        extras = {k: meta['static_presentation'][k] for k in ('footer_tiles', 'footer_states', 'header_glyphs')}
        meta['static_presentation'] = {**json.loads(json.dumps(meta['template_assets'])), **extras}
    else:
        (out / 'template-assets').symlink_to((base / 'template-assets').resolve(), target_is_directory=True)
    meta['version'] = f'inherited-{stage}-internal'
    meta['rom'].update(filename=name, sha256=sha(rom))
    meta[f'inherited_{stage}'] = dict(parent_rom_sha256=sha(before), patches=patches, code_bytes=len(code),
                                     scope='Reproduced sealed diagnostic ancestry; no runtime or human acceptance claim.')
    (out / 'build.json').write_text(json.dumps(meta, indent=2)+'\n')
    return meta
