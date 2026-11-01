"""Capture and seal exact-ROM progression acceptance; private raw data stays local."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess

from environment import ROOT
from floe_delivery import audit_artifacts, cpu_rows, tree
import floe_bench
from floe_tables import verified_profiles as verified_floes
import hazard_bench
import hazard_delivery as hazard
from hazard_check import run_target
from hazard_query import RawContacts
from hazard_tables import verified_profiles
from native_contract import compare, reference
from native_write_loop_check import HELPERS as LOOP_HELPERS, audit_saved as audit_loop
from native_shift_check import HELPERS as SHIFT_HELPERS, audit_saved as audit_shift
import progression_build as build_profile
from progression_cases import phase_cases
from progression_check import HELPERS as PHASE_HELPERS
from progression_play import HELPERS as PLAY_HELPERS, assess_receipt, input_records, source_helpers
from progression_routes import validate_policy
from reference_inventory import verified_input
from reference_provenance import audit_manifest, snapshot_paths
from reference_state import decode_state
from reference_traces import private_output
from render_bench import validate_source_files
from stella_floe import digest
from trace_compare import compare_traces, validate_trace
import render_model as model

VIEWS = {f'{f}-layout{l}-width{w}': (f, l, w) for f in ('ntsc', 'pal') for l in (0, 1) for w in (0, 1)}
ROUTES = {f'{kind}-v{v}' for kind in ('progression', 'exhaustion-restart') for v in range(4)} | set(hazard.ROUTE_STEPS)
CAUSES = {**hazard.NEGATIVE_CAUSES, 'score': 'RAM CA', 'record': 'RAM CE', 'player': 'RAM C7'}
HELPERS = tuple(dict.fromkeys((*hazard.DELIVERY_HELPERS, *LOOP_HELPERS, *PLAY_HELPERS, *PHASE_HELPERS,
    'scripts/progression_delivery.py', 'scripts/progression_routes.py', 'references/progression-routes.json',
    'scripts/progression_build.py', 'scripts/native_write_loop.py', 'scripts/progression_bench.py')))


def validate_matrix(routes):
    if set(routes) != ROUTES: raise ValueError('all four variations and original hazard routes required')
    for entry in routes.values():
        if any(not isinstance(entry.get(k), str) or not entry[k] for k in ('source', 'replay', 'native')):
            raise ValueError('original source/replay and exact native route required')
        if set(entry.get('paced', {})) != set(VIEWS) or any(not v for v in entry['paced'].values()):
            raise ValueError('every natural route requires all eight clock/presentation views')


def validate_paced(report, sha, route_sha, steps, mode):
    hazard.validate_target('paced', report, sha, steps)
    if (tuple(report.get(k) for k in ('family', 'layout', 'width')) != mode
            or report.get('original_route_sha256') != route_sha):
        raise ValueError('paced source route/family/view binding differs')


def observed_maximum(report, raw):
    busy = raw.get('busy_cycles')
    if (not isinstance(busy, list) or not busy or busy != report.get('busy_cycles')
            or any(type(v) is not int or not 0 < v < report['frame_budget'] for v in busy)
            or type(report.get('max_busy_cycles')) is not int or report['max_busy_cycles'] != max(busy)):
        raise ValueError('raw stress timing maximum differs or exceeds budget')
    return max(busy)


def native_maximum(raw, count, maximum, natural=False):
    if not count or len(raw) != count * 137:
        raise ValueError('complete actual native timing rows required')
    cycles = [struct.unpack_from('<I', raw, i * 137 + 133)[0] for i in range(count)]
    # Natural row0 is the cold reset checkpoint, before any timed phase.
    if ((natural and cycles[0] != 0) or any(v <= 0 for v in cycles[1 if natural else 0:])
            or max(cycles) != maximum):
        raise ValueError('raw native timing maximum differs')
    return maximum


def validate_negative(name, report, sha):
    if (name not in CAUSES or report.get('detected') is not True or report.get('harness_dirty') is not False
            or report.get('rom_sha256') != sha or CAUSES[name] not in report.get('detail', '')):
        raise ValueError('complete effective current-ROM negative witness required')


def reader_for(config):
    return RawContacts(ROOT / config['floe_catalog'], *(ROOT / config['catalogs'][n] for n in ('edge', 'ordinary', 'shore')))


def replay_fixtures(config_path, kind, out):
    """Reuse frozen actual original observations; execute fresh target fixtures."""
    config = json.loads(Path(config_path).read_text()); reader = reader_for(config)
    old = ROOT / config['baseline'][kind]; original = json.loads(old.read_text())
    build_dir = ROOT / config['build']; out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    if kind == 'geometry':
        hazard.audit_geometry(old, original)
        directory = old.parent / 'native'
        for entry in original['source_observations']:
            name = f'original-{entry["start"]:05d}'
            shutil.copytree(old.parent / name, out / name)
        target = out / 'native'
    elif kind == 'mechanics':
        hazard.audit_mechanics(old, reader, ROOT / config['floe_catalog'] / 'initial.state')
        directory = old.parent; target = out
        # run_target owns the fresh directory; the parent was reserved above.
        out.rmdir()
    else: raise ValueError('known fixture family required')
    expected = json.loads((directory / 'expected.json').read_text())
    report, _ = run_target(target, build_dir, (directory / 'cases.bin').read_bytes(), expected,
        step_fixture=kind == 'mechanics', build_files=build_profile.FILES,
        additional_helpers=('scripts/progression_delivery.py', 'scripts/hazard_delivery.py', 'scripts/hazard_mechanics.py'))
    for key in ('source_observations', 'full_original_phase_cases', 'declared_neutral_hazard_cases', 'actual_literal_views', 'scenarios', 'initial_sha256'):
        if key in original: report[key] = original[key]
    report.update(original_fixture_receipt_sha256=digest(old),
        scope='Fresh actual standard MSX1 target against frozen independently audited original observations/controlled phases. Complete CPU/all128RAM; no neutral contact substitutions. Original captures unchanged; manual/physical acceptance separate.')
    (out / f'{kind}.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def audit_original(name, source, replayed):
    source = Path(source); replayed = Path(replayed)
    route = json.loads((source / 'route.json').read_text()); replay = json.loads((replayed / 'replay.json').read_text())
    paths = source_helpers(route); audit_manifest(route, paths); audit_manifest(replay, paths)
    audit_artifacts(source, route['files'])
    if (route.get('clean_start') is not True or replay.get('complete') is not True
            or replay.get('identical_full_cpu_ram_tia_riot_inputs') is not True
            or replay.get('route_sha256') != digest(source / 'route.json') or replay.get('steps') != route['steps']):
        raise ValueError('complete independent original route/replay binding required')
    expected_name = f'{route["kind"]}-v{route["variation"]}' if 'variation' in route else route['kind']
    if expected_name != name: raise ValueError('named gate must use its own variation/interaction')
    trace = json.loads((source / 'trace.json').read_text()); actual = json.loads((replayed / 'trace.json').read_text())
    validate_trace(trace); validate_trace(actual); validate_policy(trace['policy'])
    if (compare_traces(trace, actual) or (source / 'final.state').read_bytes() != (replayed / 'final.state').read_bytes()
            or digest(source / 'final.state') != route['files']['final.state']):
        raise ValueError('complete original CPU/RAM/TIA/RIOT/input/final capsule replay differs')
    inputs = json.loads((source / 'inputs.json').read_text()); input_records(inputs, trace['steps'])
    if assess_receipt(trace['steps'], route) != route['assessment']: raise ValueError('original route predicate changed')
    return route, trace


def audit_phases(path, report, reader, initial):
    base = decode_state(Path(initial).read_bytes()); original = (ROOT / 'references/roms/frostbite.bin').read_bytes()
    cases = phase_cases(base['ram']); records = (path.parent / 'cases.bin').read_bytes()
    expected = json.loads((path.parent / 'expected.json').read_text())
    if len(cases) != 818 or len(expected) != 818 or len(records) != 818 * 136:
        raise ValueError('all818 declared full-phase fixtures required')
    from floe_reference import visible_reference
    from progression_cases import validate_phase
    for i, (name, ram) in enumerate(cases):
        console = int(name.split('-')[1], 16) if name.startswith('console-') else 63
        packed = ram + bytes(base['cpu'][k] for k in ('a', 'x', 'y', 'p', 'sp')) + bytes((255, console, 0))
        if records[i * 136:(i + 1) * 136] != packed: raise ValueError('progression initial/input fixture changed')
        visible = visible_reference(original, ram, base['cpu'], reader.contacts(ram))
        case = {'id': name, 'start': 'F476', 'stops': ['F019'], 'registers': visible['registers'],
                'ram': {f'{j + 128:02X}': f'{v:02X}' for j, v in enumerate(visible['ram'])}, 'limit': 12000,
                'mmio': {'0280': 'FF', '0282': f'{console:02X}', '0284': '00', '000C': '8C', '000D': '8C'}}
        want = reference(original, case); validate_phase(name, ram, want['ram']); compare(want, expected[i])


def audit_failure(name, report, positives, build):
    validate_negative(name, report, build['rom']['sha256'])
    directory = ROOT / report['directory']; audit_manifest(report, tuple(report['utility_fingerprints']))
    audit_artifacts(directory, report['artifacts'])
    metadata = json.loads((directory / 'build.json').read_text())
    if metadata != build or digest(directory / build['rom']['filename']) != build['rom']['sha256']:
        raise ValueError('negative copied ROM/build differs')
    launch = (directory / 'launch.tcl').read_text()
    if f'set inject {{{name}}}' not in launch and f'set inject_fault {name}\n' not in launch:
        raise ValueError('intended actual runtime mutation missing')
    if name in ('score', 'record', 'player', 'collision', 'rng', 'row_priority', 'sticky'):
        expected = json.loads((directory / 'expected.json').read_text()); actual = (directory / 'actual.bin').read_bytes()
        receipt = json.loads((directory / 'complete.json').read_text())
        if receipt['cases'] != len(expected) or len(actual) != len(expected) * 137 or not expected:
            raise ValueError('complete native mutation witness required')
        got = {'registers': dict(zip(('a', 'x', 'y', 'p', 'sp'), actual[:5])), 'ram': list(actual[5:133])}
        try: compare(expected[0], got)
        except ValueError as error:
            if CAUSES[name] not in str(error): raise ValueError('wrong raw native mutation cause') from error
        else: raise ValueError('native fault escaped actual comparison')
    elif name in ('spacing', 'sprite', 'guard'):
        if f'FLOE_FAIL {CAUSES[name]}' not in (directory / 'emulator.log').read_text():
            raise ValueError('actual emulator mutation failure missing')
    elif name in ('state', 'contact'):
        normal = (ROOT / positives['ntsc']['directory'] / 'states.bin').read_bytes()[:404]
        fault = (directory / 'states.bin').read_bytes()[:404]
        offset = 266 if name == 'state' else 133; field = 47 if name == 'state' else 59
        if (len(fault) != 404 or normal[:offset] != fault[:offset]
                or [i for i, (a, b) in enumerate(zip(normal[offset:offset + 133], fault[offset:offset + 133])) if a != b] != [field]):
            raise ValueError('intended actual state/contact mutation missing')
    else:
        pixels = (directory / 'presented.bin').read_bytes(); regs = (directory / 'presented_regs.bin').read_bytes()
        scenes = (directory / 'scene_actual.bin').read_bytes()
        if not any(bytes(model.decode_pixels(pixels[i * 16384:(i + 1) * 16384], list(regs[i * 8:(i + 1) * 8])))
                   != bytes(build_profile.expected_pixels(floe_bench.decode_scene(scenes[i * 32:(i + 1) * 32])))
                   for i in range(len(pixels) // 16384)):
            raise ValueError('actual progression-banner pixel/cache fault absent')


def seal(config_path, out):
    config = json.loads(Path(config_path).read_text()); validate_matrix(config['routes'])
    out = private_output(out)
    if out.exists(): raise ValueError('fresh immutable progression delivery directory required')
    build_dir = ROOT / config['build']; build = json.loads((build_dir / 'build.json').read_text())
    rom = build_dir / build['rom']['filename']; sha = digest(rom)
    if build['source_dirty'] or sha != build['rom']['sha256'] or build['original'] != verified_input(ROOT / 'references/roms/frostbite.bin'):
        raise ValueError('clean exact ROM/original build required')
    validate_source_files(build); audit_manifest({'tool_source_commit': build['source_commit'], 'utility_fingerprints': build['source_files']}, build_profile.FILES)
    hazard.validate_source_summary(build['tables']); roots = {'build': build_dir}; checks = {}
    reader = reader_for(config)
    for kind in hazard.COMPONENT_CASES:
        root = ROOT / config['catalogs'][kind]; _, _, audit = verified_profiles(root)
        if audit != build['tables']['components'][kind]: raise ValueError('frozen original catalog/build binding differs')
        roots['catalog-' + kind] = root
    root = ROOT / config['floe_catalog']; original_floes, _ = verified_floes(root)
    if original_floes['cases'] != 8704000 or digest(root / 'catalog.json') != build['tables']['floe_catalog_sha256']:
        raise ValueError('complete raw floe source changed')
    roots['catalog-floe'] = root
    for name, value in build['tables']['files'].items():
        if digest(build_dir / 'tables' / name) != value: raise ValueError('compiled source contact table changed')
    observer = hazard.audit_observer(ROOT / config['observer'], build['original']); roots['observer'] = (ROOT / config['observer']).parent
    for key, paths, audit in (('loop_unit', LOOP_HELPERS, audit_loop), ('shift_unit', SHIFT_HELPERS, audit_shift)):
        path = ROOT / config[key]; report = json.loads(path.read_text()); audit_manifest(report, paths); audit_artifacts(path.parent, report['artifacts'])
        if report.get('complete') is not True or report.get('exploratory') is not False: raise ValueError('clean complete actual-Z80 microproof required')
        if digest(path.parent / 'unit.rom') != report['rom_sha256']: raise ValueError('microproof ROM changed')
        stats = audit(path.parent)
        if key == 'loop_unit':
            if any(report.get(k) != v for k, v in stats.items()) or report['cases'] != 135168: raise ValueError('complete original/actual-Z80 loop proof differs')
            checks[key] = stats
        else:
            hazard.validate_shift_unit(report)
            if stats != report['max_cycles_including_rpc']: raise ValueError('actual shift rows differ')
            checks[key] = {k: report[k] for k in ('cases', 'variants', 'max_cycles_including_rpc')}
        roots[key] = path.parent
    for kind, count in (('geometry', 14828), ('mechanics', 652), ('phases', 818)):
        path = ROOT / config[kind]; r = json.loads(path.read_text())
        hazard.validate_target('geometry' if kind == 'geometry' else 'mechanics', r, sha, count)
        audit_manifest(r, tuple(r['utility_fingerprints'])); directory = path.parent / 'native' if kind == 'geometry' else path.parent
        audit_artifacts(directory, r['artifacts']); cpu_rows(directory); hazard.audit_binary(directory, r, build); hazard.audit_profile(directory, r, 'Frostbite_Floes.xml')
        if kind == 'geometry': hazard.audit_geometry(path, r)
        elif kind == 'mechanics': hazard.audit_mechanics(path, reader, root / 'initial.state')
        else: audit_phases(path, r, reader, root / 'initial.state')
        native_maximum((directory / 'actual.bin').read_bytes(), count, r['max_native_cycles'])
        roots[kind] = path.parent; checks[kind] = {'cases': count, 'max_native_cycles': r['max_native_cycles'], 'report_sha256': digest(path)}
    for name, entry in config['routes'].items():
        source = ROOT / entry['source']; replayed = ROOT / entry['replay']; route, trace = audit_original(name, source, replayed)
        roots['source-' + name] = source; roots['replay-' + name] = replayed
        path = ROOT / entry['native']; r = json.loads(path.read_text()); directory = path.parent
        if (r.get('complete') is not True or r.get('exploratory') is not False or r.get('canonical_ram_injections') != 0
                or r.get('cases') != route['steps'] or r.get('original_route_sha256') != digest(source / 'route.json')
                or r.get('assessment') != route['assessment']): raise ValueError('complete exact-ROM native natural route required')
        audit_manifest(r, tuple(r['utility_fingerprints'])); audit_artifacts(directory, r['artifacts']); cpu_rows(directory)
        hazard.audit_binary(directory, r, build); hazard.audit_profile(directory, r, 'Frostbite_Floes.xml')
        expected = json.loads((directory / 'expected.json').read_text())
        if (directory / 'cases.bin').read_bytes() != input_records(json.loads((source / 'inputs.json').read_text()), trace['steps']): raise ValueError('native natural raw inputs differ')
        if len(expected) != len(trace['steps']): raise ValueError('native route checkpoint count differs')
        for p, want in zip(trace['steps'], expected): compare({'ram': p['ram'], 'registers': p['cpu']}, want)
        native_maximum((directory / 'actual.bin').read_bytes(), r['cases'], r['max_native_cycles'], natural=True)
        roots['native-' + name] = directory
        checks['native-' + name] = {'cases': r['cases'], 'max_native_cycles': r['max_native_cycles'], 'assessment': r['assessment']}
        for view, relative in entry['paced'].items():
            mode = VIEWS[view]; path = ROOT / relative; r = json.loads(path.read_text()); validate_paced(r, sha, digest(source / 'route.json'), route['steps'], mode)
            audit_manifest(r, tuple(r['utility_fingerprints'])); audit_artifacts(path.parent, r['artifacts'])
            hazard.audit_binary(path.parent, r, build); hazard.audit_profile(path.parent, r, 'Frostbite_Paced.xml', mode[0])
            _, busy, cycles = __import__('hazard_paced').verify_saved(path.parent, source, mode[0], r,
                assessor=assess_receipt, pixels=build_profile.expected_pixels, scene_builder=build_profile.presentation)
            if (r['max_busy_cycles'], r['max_native_cycles']) != (max(busy), max(cycles)): raise ValueError('raw paced maxima differ')
            roots[f'paced-{name}-{view}'] = path.parent
            checks[f'paced-{name}-{view}'] = {k: r[k] for k in ('source_steps', 'frames', 'max_busy_cycles', 'frame_budget', 'min_margin_cycles', 'assessment')}
    suite = json.loads((ROOT / config['suite']).read_text()); hazard.validate_suite_manifest(suite, sha)
    with hazard_bench.scope(build_dir, builder=build_profile):
        for name, r in suite.items():
            directory = ROOT / r['directory']; raw = json.loads((directory / 'complete.json').read_text())
            maximum = observed_maximum(r, raw)
            for key, value in raw.items():
                if r.get(key) != value: raise ValueError('raw stress receipt differs')
            floe_bench.validate_receipt(r, r['frame_budget'], r['layout'], r['width'], r['transitions'])
            audit_manifest(r, tuple(r['utility_fingerprints'])); audit_artifacts(directory, r['artifacts'])
            hazard.audit_binary(directory, r, build); hazard.audit_profile(directory, r, 'Frostbite_Movement.xml', r['family'])
            floe_bench.verify_data(directory, r, reader, (ROOT / 'references/roms/frostbite.bin').read_bytes())
            roots['stress-' + name] = directory; checks['stress-' + name] = {'max_busy_cycles': maximum, 'frame_budget': r['frame_budget'], 'canonical_nusiz_codes': r['canonical_nusiz_codes']}
    negatives = json.loads((ROOT / config['negatives']).read_text())
    if set(negatives) != set(CAUSES): raise ValueError('all fourteen intentional controls required')
    for name, r in negatives.items(): audit_failure(name, r, suite, build); roots['negative-' + name] = ROOT / r['directory']
    reader.verify_consumed()
    previous = ROOT / config['previous_rom']
    if digest(previous) != '37beb4d58bfc6566ba064ff59d48118ce6bc70655f92dcc9695cb534a88bfd93': raise ValueError('published v0.0.5 bytes changed')
    evidence = {name: {'directory': str(path.relative_to(ROOT)), 'files': tree(path)} for name, path in roots.items()}
    producer = snapshot_paths(HELPERS)
    out.mkdir(parents=True, exist_ok=False); (out / 'private-evidence.json').write_text(json.dumps(evidence, sort_keys=True, indent=2) + '\n')
    result = {'schema_version': 1, 'version': build['version'], 'diagnostic': True, 'rom': build['rom'], 'source_commit': build['source_commit'],
        'source': build['original'], 'source_cells': build['tables']['cases'], 'physical_leaf_queries': build['tables']['physical_leaf_queries'],
        'observer_acceptance': {k: observer[k] for k in hazard.OBSERVER_COUNTS}, 'native_write_loops': build['native_write_loops'],
        'checks': checks, 'negative_controls': list(CAUSES), 'private_evidence_manifest_sha256': digest(out / 'private-evidence.json'),
        'manual_emulator': 'Pending owner feedback', 'physical_hardware': 'Pending owner feedback', 'limitations': build['limitations'], 'packager': producer}
    shutil.copyfile(rom, out / rom.name); shutil.copyfile(build_dir / 'build.json', out / 'build.json')
    (out / 'validation.json').write_text(json.dumps(result, indent=2) + '\n'); (out / 'SHA256SUMS').write_text(f'{sha}  {rom.name}\n')
    if digest(out / rom.name) != sha: raise ValueError('frozen release copy differs')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--config', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--fixtures', choices=('geometry', 'mechanics')); args = p.parse_args()
    r = replay_fixtures(args.config, args.fixtures, args.out) if args.fixtures else seal(args.config, args.out)
    print(json.dumps({k: r[k] for k in ('version', 'rom', 'cases', 'negative_controls') if k in r}))
