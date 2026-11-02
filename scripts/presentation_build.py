"""Distinct private native presentation profile; runtime acceptance is pending."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from environment import ROOT, verified_tool
import hazard_build
from hazard_tables import compile_catalog
from native_write_loop import generate
from original_graphics import SOURCE_SHA256
from presentation_assets import compile_assets, memory_layout
from presentation_fragments import background_tables, pack_background, compile_geometry, pack_geometry_metadata
from presentation_palette import HELPERS as PALETTE_FILES, audit_palette
from presentation_sprites import tables as sprite_tables
from presentation_static_assets import pack_static
from presentation_cache_hash import table as cache_crc_table
from presentation_fixed import COUNTS as FIXED_COUNTS
from presentation_floe_templates import compile_templates
from presentation_template_assets import pack as pack_template_assets
from reference_inventory import verified_input
from reference_traces import private_output
from render_build import symbols

VERSION = '0.0.7-presentation'
ROM_BYTES = 4194304
FILES = tuple(dict.fromkeys((*hazard_build.FILES, *PALETTE_FILES, 'scripts/presentation_build.py',
    'scripts/presentation_assets.py', 'scripts/native_write_loop.py', 'src/presentation.asm',
    'src/presentation_cache.asm', 'src/presentation_geometry.asm', 'src/presentation_world.asm', 'references/presentation-assets-config.json', 'references/presentation-assets-result.json')))
FILES = tuple(dict.fromkeys((*FILES, 'scripts/presentation_fragments.py', 'scripts/presentation_model.py', 'scripts/graphics_mapping.py', 'src/presentation_hud.asm',
                            'scripts/presentation_sprites.py', 'src/presentation_sprites.asm', 'src/presentation_player_cache.asm',
                            'scripts/presentation_static_assets.py','scripts/presentation_cache_hash.py',
                            'src/presentation_fast_cache.asm','src/presentation_typed.asm',
                            'src/presentation_fast_world.asm','src/presentation_fast_hud.asm','src/presentation_dirty.asm','src/presentation_dirty_rows.asm')))
FILES=tuple(dict.fromkeys((*FILES,'scripts/presentation_fixed.py','src/presentation_fixed_runtime.asm','src/presentation_fixed_pool.asm','src/presentation_fixed_floe.asm','src/presentation_fixed_emit.asm','src/presentation_fixed_memo.asm')))
FILES=tuple(dict.fromkeys((*FILES,'scripts/presentation_fast_model.py','scripts/presentation_constructors.py','scripts/presentation_floe_templates.py',
    'scripts/presentation_template_assets.py','src/presentation_template_reader.asm','src/presentation_template_loader.asm','src/presentation_template_floe.asm','src/presentation_name_rows.asm','src/presentation_template_upload.asm','src/presentation_background_cover.asm','src/presentation_template_strip.asm','src/presentation_name_decode.asm','src/presentation_player_variants.asm','src/presentation_footer.asm','src/presentation_header_keys.asm','src/presentation_header.asm')))


def bank_layout(contact_banks):
    if type(contact_banks) is not int or not 1 <= contact_banks <= 242:
        raise ValueError('contact banks must fit the fixed256-bank cartridge')
    contacts = list(range(14, 14 + contact_banks))
    return {'resident': 0, 'fragments': 1, 'native': 2, 'contacts': contacts,
            'available_assets': list(range(3, 14)) + list(range(14 + contact_banks, 256))}


def profile(*,fast=False,fixed=False,templates=False):
    if any(type(value)is not bool for value in (fast,fixed,templates)):raise ValueError('explicit presentation-profile selection required')
    fixed=fixed or templates
    fast=fast or fixed
    ram = memory_layout()
    for region in ram['regions']:
        if region['name'] == 'scene_snapshots': region['name'] = 'sprite_pattern_work'
        # TIA reads use C300..30F; RIOT reads use C340..347. Native code
        # masks the ports before addressing them, so C380 is not bus state.
        if region['name'] == 'source_io_read': region['end'] = 0xC348
    ram['regions'].append({'name':'player_templates','start':0xC380,'end':0xC3C0})
    # Existing native acquisition scratch is retained separately from bus IO.
    ram['regions'].append({'name': 'native_contacts', 'start': 0xC780, 'end': 0xC7A0})
    if fast:
        ram['regions']=[row for row in ram['regions'] if row['name'] not in ('diagnostic_input','tile_bytes')]
        for row in ram['regions']:
            if row['name']=='tile_signatures':row['name']='tile_hashes'
            if row['name']=='sprite_pattern_work':row['end']=0xC540
        ram['regions'] += [{'name':name,'start':start,'end':end} for name,start,end in (
            ('scene_a',0xC540,0xC5A0),('scene_b',0xC5A0,0xC600),
            ('tile_references',0xC080,0xC200),('graphics_rpc',0xC760,0xC780),
            ('constructor_keys',0xD000,0xD900),('constructor_links',0xD900,0xDA80),
            ('constructor_buckets',0xDB00,0xE100),('cache_crc',0xE100,0xE200),('sprite_shadow',0xE200,0xE500),('fusion_work',0xE500,0xE540),
            ('visual_state_work',0xE540,0xE580),('renderer_work',0xE580,0xE800))]
    if fixed:
        ram['regions']=[row for row in ram['regions'] if row['name'] not in ('tile_references','tile_hashes','constructor_links','constructor_buckets','sprite_shadow')]
        ram['regions'] += [{'name':name,'start':start,'end':end} for name,start,end in (
            ('player_render_reserved',0xC080,0xC200),('fixed_control',0xCB00,0xCC80),('footer_keys',0xD900,0xDA08),
            ('fixed_reserved',0xDA08,0xDB00),('name_staging',0xDB00,0xDE00),('player_render_work',0xDE00,0xE100),
            ('primitive_staging',0xE200,0xE500))]
    if templates:
        ram['regions']=[row for row in ram['regions'] if row['name'] not in ('renderer_work','player_render_work','player_render_reserved')]
        ram['regions'] += [{'name':name,'start':start,'end':end} for name,start,end in (
            ('floe_name_cache',0xDE00,0xE000),('player_render_work',0xE000,0xE100),
            ('dirty_row_work',0xE580,0xE598),('world_memo',0xE5A0,0xE5AC),('floe_template_identities',0xE5C0,0xE5E0),('floe_decode_codes',0xE600,0xE610),
            ('player_variant_templates',0xC080,0xC180),('player_render_reserved',0xC180,0xC200),('player_variant_control',0xE610,0xE614),('header_key_work',0xE620,0xE64B))]
    return {'version': VERSION, 'signature': 'FBP0', 'source_sha256': SOURCE_SHA256,
            'clock_hz': 3579545, 'ram_bytes': 65536, 'vram_bytes': 16384, 'mapper': 'ASCII16',
            'rom_bytes': ROM_BYTES, 'ram': ram,'sparse_profile':fast,'fixed_roles':fixed,'floe_templates':templates,'raw_floe_key_type':9 if templates else None,'live_cache_references':fast and not fixed,
            'fixed_slot_counts':list(FIXED_COUNTS) if fixed else None,'diagnostic_flags':[0xC2DE,0xC2DF] if fast else [0xC11E,0xC11F],
            'player_variants_per_generation':4 if templates else 1,
            'header_span_constructor':templates,
            'static_vram_regions': [{'name': 'hmove_sprite', 'start': 0x3FE0 if templates else 0x3C00, 'end': 0x4000 if templates else 0x3C20}], 'runtime_qualified': False,
            'scope': 'New build profile; source/live target equivalence and timing gates remain pending'}


def validate_rom(data):
    errors = []
    if len(data) != ROM_BYTES: errors.append('4MiB ASCII16 cartridge required')
    if data[:2] != b'AB' or data[16:20] != b'FBP0': errors.append('distinct presentation cartridge signature required')
    if len(data) < 20 or not 0x4014 <= int.from_bytes(data[2:4], 'little') < 0x8000 or any(data[4:16]):
        errors.append('resident cartridge entry and zero vectors required')
    return errors


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pack_contact_shadow(roots,base):
    if len(roots)!=4800 or len(base)!=1600:raise ValueError('complete ten160-entry root/base directories required')
    return bytes(roots)+bytes(base)+bytes([255])*(16384-6400)


def contact_shadow(directory,out,tables,*,root_address=0x8000,bank_image=None):
    directory=Path(directory);out=Path(out)
    roots=(directory/'floe-roots.bin').read_bytes();base=(directory/'floe-base.bin').read_bytes()
    image=pack_contact_shadow(roots,base)
    if root_address!=0x8000:
        if root_address!=0xA700 or bank_image is None or len(bank_image)!=16384 or bank_image[0x2700:]!=roots+base:raise ValueError('template root/base tail differs from the packed bank')
        image=bytes(bank_image)
    (out/'contact-shadow.bin').write_bytes(image)
    lines=[f'floe_roots EQU ${root_address:04X}',f'floe_base EQU ${root_address+4800:04X}']
    for name,key in (('hazard_row','edge'),('hazard_shore','shore')):
        ys=tables['profile_ys'][key];lines.extend((f'{name}_min_y EQU {min(ys)}',f'{name}_max_y EQU {max(ys)}'))
    lines.extend((f'contact_record_bank EQU {tables["codec"]["record_bank"]}',f'contact_block_bank EQU {tables["codec"]["block_bank"]}'))
    def blob(label,name,aligned=False):
        if aligned:lines.append('    ALIGN 256')
        lines.extend((label+':',f'    INCBIN "{directory/name}"'))
    blob('floe_control_index','floe-controls.bin',True)
    lines.append('floe_control_pointers:')
    for index in range(10):lines.append(f'    DW floe_roots+{index*480},floe_base+{index*160}')
    for kind in ('edge','ordinary','shore'):blob(f'hazard_{kind}_modes',f'{kind}-modes.bin')
    blob('hazard_ordinary_common_modes','ordinary-common.bin')
    blob('hazard_shape_index','hazard-shapes.bin',True);blob('hazard_bear_index','hazard-bear.bin')
    (out/'presentation_contact_resident.inc').write_text('\n'.join(lines)+'\n')
    return {'bank':255,'root_address':root_address,'root_bytes':4800,'base_address':root_address+4800,'base_bytes':1600,
        'sha256':digest(out/'contact-shadow.bin'),'resident_include_sha256':digest(out/'presentation_contact_resident.inc'),
        'source_files':{name:digest(directory/name) for name in ('floe-roots.bin','floe-base.bin')}}


def flat_water_ids(tables):
    result=[]
    for bank in range(3):
        patterns=tables['patterns'][bank];colors=tables['colors'][bank]
        candidates=[128+i for i in range(len(patterns)//8) if patterns[i*8:i*8+8]==bytes([255])*8 and colors[i*8:i*8+8]==bytes([68])*8]
        if len(patterns)!=len(colors) or len(patterns)%8 or len(candidates)!=1:raise ValueError('one exact solid-water identity per SCREEN2 bank required')
        result.append(candidates[0])
    return result


def pack_crc_shadow(boot):
    image=boot['bank'];offset=boot['used_bytes'];crc=cache_crc_table();end=offset+len(crc)
    if len(image)!=16384 or not 0<=offset<=16384 or end>16384 or any(v!=255 for v in image[offset:end]):
        raise ValueError('CRC page must fit the unused primitive-bank tail')
    return {**boot,'bank':image[:offset]+crc+image[end:],'used_bytes':end,
        'assembly':boot['assembly']+f'p_fast_crc_rom_data EQU ${0x8000+offset:04X}\n',
        'cache_crc':{'offset':offset,'size':256,'ram_start':0xE100,'sha256':hashlib.sha256(crc).hexdigest()}}


def build(floes, edge, ordinary, shore, aliases, out, *, explore=False,fast=False,fixed=False,templates=False):
    if any(type(value)is not bool for value in (fast,fixed,templates)):raise ValueError('explicit presentation-profile selection required')
    fixed=fixed or templates
    fast=fast or fixed
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    if dirty and not explore: raise ValueError('commit presentation producers before canonical build')
    fingerprints = {name: digest(ROOT / name) for name in FILES}
    original = verified_input(ROOT / 'references/roms/frostbite.bin'); rom = (ROOT / 'references/roms/frostbite.bin').read_bytes()
    config = json.loads((ROOT / 'references/presentation-assets-config.json').read_text())
    measured = audit_palette(ROOT / config['palette'])
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    tables = compile_catalog(floes, edge, ordinary, shore, aliases, out / 'tables'); banks = bank_layout(tables['banks'])
    shadow=None
    if fixed and not templates:
        if 255 not in banks['available_assets']:raise ValueError('fixed root shadow requires free bank255')
        shadow=contact_shadow(out/'tables',out,tables)
    fragments = compile_assets(rom, out / 'assets', measured_palette=measured,sprite_patterns_end=0x4000 if templates else 0x3C00)
    background = background_tables(rom, measured)
    water=flat_water_ids(background)
    (out/'presentation_simple.inc').write_text(''.join(f'pt_water_id{bank} EQU {identifier}\n' for bank,identifier in enumerate(water)))
    if background['gradient_profiles'] > 8: raise ValueError('native background profile exceeds its measured8-state gradient domain')
    boot = pack_background((out / 'assets/fragments.bin').read_bytes(), fragments['used_bytes'], background,black_sprite_address=0x3FE0 if templates else 0x3C00)
    geometry = compile_geometry(rom, out / 'geometry')
    if not set(geometry['physical_banks']).issubset(banks['available_assets']): raise ValueError('geometry overlaps contact banks')
    static=pack_static(rom,measured,out/'geometry',geometry,out/'static')
    if not set(static['physical_banks']).issubset(banks['available_assets']):raise ValueError('static fragments overlap contact banks')
    actual_static=static;boot_geometry=geometry;template_assets=None
    if templates:
        from presentation_fast_model import prepare as prepare_template_tables
        compiled_templates=compile_templates(prepare_template_tables(rom,measured,out/'geometry'))
        template_assets=pack_template_assets(out/'geometry',compiled_templates,rom,measured,out/'tables',out/'template-assets')
        if not set(template_assets['physical_banks']).issubset(banks['available_assets']):raise ValueError('template assets overlap contacts')
        boot_geometry=template_assets
        actual_static={**template_assets,'footer_tiles':template_assets['sections']['footer_tiles']['size']//16,'header_glyphs':34,'footer_states':16}
        shadow=contact_shadow(out/'tables',out,tables,root_address=0xA700,bank_image=(out/'template-assets/assets-255.bin').read_bytes())
        (out/'presentation_template.inc').write_text((out/'template-assets/presentation_template.inc').read_text())
    source_static=out/('template-assets' if templates else 'static')/'presentation_static.inc'
    (out/'presentation_static.inc').write_text(source_static.read_text())
    geo_boot = pack_geometry_metadata(boot, boot_geometry, (out / 'geometry/row-pointer-map.bin').read_bytes())
    if fast:geo_boot=pack_crc_shadow(geo_boot)
    (out / 'presentation_geometry.inc').write_text(geo_boot['assembly'])
    (out / 'boot.bin').write_bytes(geo_boot['bank'])
    (out / 'presentation_background.inc').write_text(boot['assembly'] +
        f'p_world_color_data EQU ${0x8000 + fragments["sections"]["colors"]["offset"]:04X}\n')
    (out / 'presentation_background_init.inc').write_text(boot['initializers'])
    sprite_data = sprite_tables(rom, measured)
    sprite_includes = ['    ALIGN 256']
    for name, data in sprite_data.items():
        path = out / f'sprite-{name}.bin'; path.write_bytes(data)
        sprite_includes += [f'p_sprite_{name}_data:', f'    INCBIN "{path}"']
    (out / 'presentation_sprite_data.inc').write_text('\n'.join(sprite_includes) + '\n')
    (out / 'core.inc').write_text(generate(rom, carry_fusion=True)); (out / 'data.bin').write_bytes(rom[0xC00:])
    (out / 'boot_tables.inc').write_text(f'    INCBIN "{out / "boot.bin"}"\n')
    (out / 'resident_tables.inc').write_text('; Presentation metadata belongs to its explicit profile.\n')
    # Keep original fixed contact indices while reclaiming old synthetic-row banks.
    def asset_bank(bank):
        if templates:return '    ORG $8000\n'+f'    INCBIN "{out/"template-assets"/f"assets-{bank:03d}.bin"}"\n'
        if fixed and bank==255:return '    ORG $8000\n'+f'    INCBIN "{out/"contact-shadow.bin"}"\n'
        return '    ORG $8000\n' + (f'    INCBIN "{out / "static" / f"assets-{bank:03d}.bin"}\"\n' if bank in static['physical_banks'] else '    DS $4000,$FF\n')
    (out / 'row_banks.inc').write_text(''.join(asset_bank(bank) for bank in range(3,14)))
    (out / 'cartridge_padding.inc').write_text(''.join(asset_bank(bank) for bank in range(14 + tables['banks'],256)))
    (out/'cache-crc.bin').write_bytes(cache_crc_table())
    (out / 'entry.asm').write_text('    DEFINE WITH_HAZARDS\n    DEFINE WITH_FLOES\n    DEFINE WITH_PROGRESSION\n    DEFINE WITH_PRESENTATION\n'+
        ('    DEFINE WITH_PRESENTATION_FAST\n' if fast else '')+('    DEFINE WITH_PRESENTATION_FIXED\n' if fixed else '')+('    DEFINE WITH_PRESENTATION_TEMPLATES\n    DEFINE WITH_PRESENTATION_HEADER_FAST\n' if templates else '')+'    INCLUDE "movement.asm"\n')
    artifact = out / f'frostbite-{VERSION}.rom'; assembler = verified_tool('sjasmplus')
    command = [str(assembler), '--nologo', f'--inc={ROOT/"src"}', f'--inc={out}', f'--inc={out/"tables"}',
               f'--raw={artifact}', f'--sym={out/"presentation.sym"}', f'--lst={out/"presentation.lst"}', str(out / 'entry.asm')]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    (out / 'assembler.log').write_text(compiled.stdout + compiled.stderr)
    if compiled.returncode: raise ValueError('presentation assembler failed: ' + (compiled.stdout + compiled.stderr)[-2500:])
    errors = validate_rom(artifact.read_bytes())
    if errors: raise ValueError('; '.join(errors))
    syms = symbols(out / 'presentation.sym')
    if (subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() != commit
            or any(digest(ROOT / name) != value for name, value in fingerprints.items())
            or verified_input(ROOT / 'references/roms/frostbite.bin') != original):
        raise ValueError('presentation build producer changed during compilation')
    final_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    if not explore and final_dirty: raise ValueError('canonical presentation checkout changed')
    metadata = {'version': VERSION, 'diagnostic': True, 'runtime_qualified': False, 'profile': profile(fast=fast,fixed=fixed,templates=templates),
                'source_commit': commit, 'source_dirty': dirty or final_dirty, 'exploratory': explore,
                'original': original, 'source_files': fingerprints, 'rom': {'filename': artifact.name, 'size': artifact.stat().st_size,
                'sha256': digest(artifact), 'mapper': 'ASCII16'}, 'fragments': fragments, 'tables': tables,
                'background': {'tiles_per_bank': background['tiles_per_bank'], 'gradient_profiles': background['gradient_profiles'],
                               'boot_used_bytes': geo_boot['used_bytes'], 'boot_sha256': digest(out / 'boot.bin'), 'sections': boot['sections']},
                'geometry': geometry, 'geometry_metadata': {'sections': geo_boot['sections'], 'used_bytes': geo_boot['used_bytes']},
                'static_presentation':actual_static,'legacy_static_presentation':static if templates else None,'template_assets':template_assets,
                'flat_water_ids':water,
                'cache_crc':geo_boot.get('cache_crc'),
                'contact_shadow':shadow,
                'banks': {**banks, 'resident_used': syms['resident_end'] - 0x4000, 'native_used': syms['native_end'] - 0x8000,
                          'assets_used': syms['assets_end'] - 0x8000}, 'assembler_sha256': digest(assembler),
                'limitations': 'Private renderer development profile; whole-frame timing, ordered PSG and integrated natural gameplay acceptance remain unqualified. Not a human-testable game delivery.'}
    (out / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n'); return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('floes', 'edge', 'ordinary', 'shore', 'aliases', 'out'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--fast',action='store_true',help='Private sparse constructor profile; no runtime qualification implied')
    parser.add_argument('--fixed',action='store_true',help='Private fixed-role profile; implies --fast, no runtime qualification implied')
    parser.add_argument('--templates',action='store_true',help='Private complete-floe template profile; implies --fixed, no runtime qualification implied')
    parser.add_argument('--explore', action='store_true'); args = parser.parse_args()
    result = build(**vars(args)); print(json.dumps({key: result[key] for key in ('version', 'rom', 'runtime_qualified')}))
