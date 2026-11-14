"""Qualify native RAM enemy code/data and reclaim the old NAME-cache storage."""
import argparse
import json
from pathlib import Path
import subprocess

from build_compact_packet_experiment import digest
import compact_grid_window_check
from render_build import symbols


def check(build, out, mode):
    build, out = build.resolve(), out.resolve()
    m = json.loads((build/'build.json').read_bytes())
    node = m.get('compact_enemy_ram', {})
    if not node.get('RAM_only_hot_constructor'):
        raise ValueError('explicit native RAM SGT module required')
    initializers = []
    for row in node['initializers']:
        data = (build/row['file']).read_bytes()
        if len(data) != row['size'] or digest(data) != row['sha256']:
            raise ValueError('initializer changed')
        initializers.append((row['ram_address'], data))
    s = symbols(build/'presentation.sym')
    cache = m.get('compact_bear_record_cache')
    expected_cache = None
    if cache:
        if (cache.get('complete_native_records'), cache.get('RAM_cache_address'), cache.get('RAM_cache_bytes'),
                cache.get('published_id_plus_one'), cache.get('reserved_zero_byte')) != (96, 0xDFC0, 64, 0xDFBE, 0xDFBF):
            raise ValueError('explicit exact original-record cache contract required')
        expected_cache = build/cache['original_records_file']
        if expected_cache.stat().st_size != 6144 or digest(expected_cache.read_bytes()) != cache['original_records_sha256']:
            raise ValueError('independent full original record bytes changed')
    marker = out/'enemy-ram-validated.txt'
    cache_marker = out/'bear-record-publications.txt'
    original_run = subprocess.run

    def run(args, *a, **kw):
        if isinstance(args, list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p = Path(args[args.index('-script')+1])
            text = p.read_text()
            fail = 'fail_matrix' if mode == 'matrix' else 'fail'
            text += '\nset enemy_ram_guard 0\nset enemy_ram_bank -1\n'
            if mode == 'matrix':
                text += 'debug set_watchpoint read_mem 0xC760 {} {set ::enemy_ram_guard 1}\n'
            else:
                body = '\n'.join(f' if {{[debug read_block memory {address} {len(data)}] ne [binary format H* {data.hex()}]}} {{fail enemy-ram-preload-{address}}}'
                                 for address, data in initializers)
                text += f'''
debug set_bp {s['t_main.frame']} {{!$::enemy_ram_guard}} {{
{body}
 set ::enemy_ram_guard 1
 set ::enemy_ram_bank [debug read memory {s['t_bank']}]
 set f [open {{{marker}}} w];puts $f "exact132-pattern-native-RAM-module";close $f
}}
debug set_watchpoint write_mem 0x7000 {{$::enemy_ram_guard}} {{set ::enemy_ram_bank $::wp_last_value}}
debug set_watchpoint read_mem {{0xA800 0xB7FF}} {{$::enemy_ram_guard && $::enemy_ram_bank==64}} {{fail hot-enemy-ROM-source-read}}
'''
            for address, data in initializers:
                span = f'{{{address} {address+len(data)-1}}}'
                text += f'debug set_watchpoint write_mem {span} {{$::enemy_ram_guard}} {{{fail} immutable-enemy-RAM-write}}\n'
                if mode == 'matrix':
                    text += f'debug set_watchpoint read_mem {span} {{$::enemy_ram_guard}} {{{fail} cold-uninitialized-enemy-RAM-read}}\n'
            unused = ((0xDFBF, 0xDFBF), (0xE370, 0xE4FF)) if cache else ((0xDFBE, 0xDFFF), (0xE370, 0xE4FF))
            for first, last in unused:
                for access in ('read_mem', 'write_mem'):
                    text += f'debug set_watchpoint {access} {{{first} {last}}} {{$::enemy_ram_guard}} {{{fail} unused-enemy-RAM-suffix}}\n'
            if cache:
                text += f'''
set f [open {{{expected_cache}}} rb];set bear_expected_records [read $f];close $f
set bear_record_publications 0
debug set_watchpoint write_mem 0xDFBE {{$::enemy_ram_guard}} {{
 set key $::wp_last_value
 if {{$key!=0 && $key!=255}} {{
  if {{$key<1 || $key>96}} {{{fail} invalid-bear-record-publication}}
  set at [expr {{($key-1)*64}}]
  if {{[debug read_block memory 0xDFC0 64] ne [string range $::bear_expected_records $at [expr {{$at+63}}]]}} {{{fail} original-bear-record-cache-differs}}
  incr ::bear_record_publications
  set f [open {{{cache_marker}}} w];puts $f $::bear_record_publications;close $f
 }}
}}
debug set_watchpoint write_mem {{0xDFC0 0xDFFF}} {{$::enemy_ram_guard}} {{
 set key [debug read memory 0xDFBE]
 if {{$key!=0 && $key!=255}} {{{fail} valid-bear-record-mutated-without-invalidation}}
}}
'''
            p.write_text(text)
        return original_run(args, *a, **kw)
    subprocess.run = run
    try:
        compact_grid_window_check.check(build, out, mode)
    finally:
        subprocess.run = original_run
    if mode != 'matrix' and not marker.exists():
        raise ValueError('RAM module guards never armed')
    publications = int(cache_marker.read_text()) if cache_marker.exists() else 0
    if cache and mode == 'matrix' and not publications:
        raise ValueError('original record publication guard never exercised')
    result = dict(complete=True, mode=mode, rom_sha256=m['rom']['sha256'],
        native_RAM_code_bytes=112, immutable_RAM_asset_bytes=1214,
        unused_suffix_bytes=401 if cache else 466,
        exact_original_record_cache_publications=publications if cache else None,
        hot_source_ROM_reads=0 if mode != 'matrix' else None,
        cold_matrix_avoids_uninitialized_RAM=mode == 'matrix',
        all_original_and_retirement_oracles_retained=True,
        producer_sha256=digest(Path(__file__).read_bytes()),
        scope='Exact preload, immutable code/data and unused suffix read/write guards; whole-game source/pixel/owner/IRQ checks retained.')
    (out/'enemy-ram-check.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mode', choices=('ntsc', 'pal', 'bear-ntsc', 'bear-pal', 'matrix'), required=True)
    args = parser.parse_args()
    check(args.build, args.out, args.mode)
