"""Run bounded acceptance stages without changing source producers or ROM bytes."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess

from environment import ROOT
from floe_delivery import tree
from hazard_check import run_target
import hazard_delivery as hazard
import hazard_bench
from hazard_query import RawContacts
import progression_build
import progression_play
from progression_delivery import CAUSES, HELPERS, VIEWS, reader_for, replay_fixtures, validate_matrix, validate_negative
from reference_provenance import snapshot_paths
from reference_traces import private_output
from stella_floe import digest

RUNNER_HELPERS = tuple(dict.fromkeys((*HELPERS, 'scripts/progression_suite.py')))


def run_jobs(config, stage, workers):
    jobs = []; build_dir = ROOT / config['build']; sha = json.loads((build_dir / 'build.json').read_text())['rom']['sha256']
    validate_matrix(config['routes'])
    for name, entry in config['routes'].items():
        requested = [('native', entry['native'], None)] if stage == 'native' else [(view, path, VIEWS[view]) for view, path in entry['paced'].items()]
        for label, relative, mode in requested:
            receipt = ROOT / relative
            if receipt.exists():
                r = json.loads(receipt.read_text())
                if (r.get('rom', {}).get('sha256') != sha or r.get('complete') is not True
                        or r.get('exploratory') is not False or r.get('original_route_sha256') != digest(ROOT / entry['source'] / 'route.json')):
                    raise ValueError('existing immutable route result is not the requested candidate')
                if mode is not None and tuple(r[k] for k in ('family', 'layout', 'width')) != mode:
                    raise ValueError('existing immutable paced view differs')
                print(f'REUSE {name} {label}', flush=True); continue
            args = [str(ROOT / '.venv/bin/python'), '-B', 'scripts/progression_play.py', '--source', entry['source'],
                    '--out', str(receipt.parent), '--build-dir', config['build']]
            if mode is not None: args += ['--paced', '--family', mode[0], '--layout', str(mode[1]), '--width', str(mode[2])]
            jobs.append((name, label, args))
    log_dir = private_output(ROOT / config['logs']); log_dir.mkdir(parents=True, exist_ok=True)
    def execute(job):
        name, label, args = job; log = log_dir / f'{stage}-{name}-{label}.log'
        with log.open('w') as f: result = subprocess.run(args, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
        return name, label, result.returncode, log
    failures = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for future in as_completed([pool.submit(execute, job) for job in jobs]):
            name, label, code, log = future.result()
            print(f'{"PASS" if code == 0 else "FAIL"} {name} {label} {log.relative_to(ROOT)}', flush=True)
            if code: failures.append((name, label, str(log)))
    if failures: raise ValueError('acceptance jobs failed: ' + json.dumps(failures))


def stress(config):
    build_dir = ROOT / config['build']; reader = reader_for(config); reports = {}
    destination = private_output(ROOT / config['suite'])
    if destination.exists(): raise ValueError('fresh immutable stress manifest required')
    for name, (family, layout, width, transitions) in hazard.STRESS_MODES.items():
        r = hazard_bench.capture(build_dir, reader, builder=progression_build, family=family,
            layout=layout, width=width, transitions=transitions, catalog='counts' if name == 'counts' else 'dense',
            mixed=name.startswith('mixed'), additional_helpers=('scripts/progression_suite.py', 'scripts/progression_delivery.py'))
        reports[name] = r
        print(f'STRESS_PASS {name} {r["max_busy_cycles"]}/{r["frame_budget"]}', flush=True)
    destination.parent.mkdir(parents=True, exist_ok=True); destination.write_text(json.dumps(reports, indent=2) + '\n')
    return reports


def negatives(config):
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip():
        raise ValueError('clean committed negative producer required')
    producer = snapshot_paths(RUNNER_HELPERS); build_dir = ROOT / config['build']
    build = json.loads((build_dir / 'build.json').read_text()); sha = build['rom']['sha256']
    root = private_output(ROOT / config['negative_root']); root.mkdir(parents=True, exist_ok=False)
    reader = reader_for(config); reports = {}
    mechanics = (ROOT / config['mechanics']).parent
    expected = json.loads((mechanics / 'expected.json').read_text()); records = (mechanics / 'cases.bin').read_bytes()
    for name in CAUSES:
        directory = root / name
        try:
            if name in ('score', 'record', 'player'):
                progression_play.natural(ROOT / config['routes']['progression-v1']['source'], directory, build_dir, inject=name)
            elif name in ('collision', 'rng', 'row_priority', 'sticky'):
                run_target(directory, build_dir, records, expected, step_fixture=True, inject=name,
                    build_files=progression_build.FILES, additional_helpers=RUNNER_HELPERS)
            else:
                # Only this serial stage creates pace-ntsc-* directories. The
                # independent natural matrix writes explicitly named folders.
                before = set(build_dir.glob('pace-ntsc-*'))
                try:
                    hazard_bench.capture(build_dir, reader, builder=progression_build, inject=name,
                        catalog='counts' if name == 'cache' else 'dense', additional_helpers=RUNNER_HELPERS)
                except ValueError:
                    made = set(build_dir.glob('pace-ntsc-*')) - before
                    if len(made) != 1: raise ValueError('negative stress directory is ambiguous')
                    directory = made.pop()
                    raise
        except ValueError as error:
            report = {**producer, 'detected': True, 'detail': str(error), 'rom_sha256': sha,
                'build_source_commit': build['source_commit'], 'harness_dirty': False,
                'directory': str(directory.relative_to(ROOT)), 'artifacts': tree(directory)}
            validate_negative(name, report, sha); reports[name] = report
            (root / f'{name}.json').write_text(json.dumps(report, indent=2) + '\n')
            print(f'NEGATIVE_PASS {name} {CAUSES[name]}', flush=True)
        else: raise ValueError(f'{name}: intended runtime mutation escaped detection')
    if snapshot_paths(RUNNER_HELPERS) != producer or digest(build_dir / build['rom']['filename']) != sha:
        raise ValueError('negative producer or ROM changed')
    destination = ROOT / config['negatives']; destination.write_text(json.dumps(reports, indent=2) + '\n')
    return reports


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--config', type=Path, required=True)
    p.add_argument('--stage', choices=('native', 'paced', 'geometry', 'mechanics', 'stress', 'negatives'), required=True)
    p.add_argument('--workers', type=int, default=4); args = p.parse_args(); config = json.loads(args.config.read_text())
    if not 1 <= args.workers <= 8: p.error('workers must be1..8')
    if args.stage in ('native', 'paced'): run_jobs(config, args.stage, args.workers)
    elif args.stage in ('geometry', 'mechanics'):
        replay_fixtures(args.config, args.stage, (ROOT / config[args.stage]).parent)
    elif args.stage == 'stress': stress(config)
    else: negatives(config)
