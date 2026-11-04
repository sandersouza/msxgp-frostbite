"""Reproduce the private N-B paired evidence report; original assets required."""
import argparse
import importlib.util
import json
import mmap
from pathlib import Path
import statistics

from environment import ROOT


def validate_sequence(result, family, rom_sha, capture_size):
    records, receipt = result['records'], result['receipt']
    count = len(records)
    if (result['family'] != family or not count
            or [r['frame'] for r in records] != list(range(count))
            or capture_size != count * 49304
            or receipt['frames'] != count or not receipt['complete']
            or receipt['rom_sha256'] != rom_sha):
        raise ValueError('mismatched or incomplete paired evidence')


def report(path):
    base = ROOT/'outputs/presentation/playfield-m-c'
    spec = importlib.util.spec_from_file_location('mc_analyzer', base/'analyze.py')
    analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzer)
    analyzer.ROOT = path
    for family in ('ntsc', 'pal'):
        alias = path/(family+'-a')
        if not alias.exists():
            alias.symlink_to(family+'-b', target_is_directory=True)
        assert alias.resolve() == (path/(family+'-b')).resolve()
    results = [analyzer.analyze(f) for f in ('ntsc', 'pal')]
    baseline = json.loads((base/'analysis.json').read_text())
    old_sha = analyzer.sha(base/'build'/json.loads((base/'build/build.json').read_text())['rom']['filename'])
    new_sha = analyzer.sha(path/'build-b'/json.loads((path/'build-b/build.json').read_text())['rom']['filename'])
    assert old_sha == baseline['candidate_rom_sha256']
    assert new_sha == json.loads((path/'build-b/build.json').read_text())['rom']['sha256']
    analysis = dict(clock=analyzer.CLOCK, results=results,
        baseline_rom_sha256=baseline['candidate_rom_sha256'],
        candidate_rom_sha256=json.loads((path/'build-b/build.json').read_text())['rom']['sha256'],
        profiler_sha256=analyzer.sha(base.parent/'architecture-review-f/profiler.py'),
        analyzer_sha256=analyzer.sha(base/'analyze.py'),
        report_source_sha256=analyzer.sha(Path(__file__).resolve()),
        model_scope='N-B measured whole-frame results. Oracle and zero-world fields are hypothetical floors. Bypassed helper counters do not indicate eliminated body work.')
    rows, checks = [], []
    assert [r['family'] for r in baseline['results']] == ['ntsc', 'pal']
    assert [r['family'] for r in results] == ['ntsc', 'pal']
    for old, new in zip(baseline['results'], results, strict=True):
        family = new['family']
        before, after = base/(family+'-a'), path/(family+'-b')
        validate_sequence(old, family, old_sha, (before/'captures.bin').stat().st_size)
        validate_sequence(new, family, new_sha, (after/'captures.bin').stat().st_size)
        assert len(old['records']) == len(new['records'])
        assert (before/'route-cpu.bin').read_bytes() == (after/'route-cpu.bin').read_bytes()
        with (before/'captures.bin').open('rb') as f, (after/'captures.bin').open('rb') as g:
            with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as a, mmap.mmap(g.fileno(),0,access=mmap.ACCESS_READ) as b:
                assert len(a) == len(b)
                for x, y in zip(old['records'], new['records'], strict=True):
                    at = x['frame']*49304
                    for offset, size in [(0,128),(128,16384),(16520,16384),(32912,16384)]:
                        assert a[at+offset:at+offset+size] == b[at+offset:at+offset+size]
                    assert all(v == y['phases'][k] for k,v in x['phases'].items() if k != 'world')
                    assert (x['bytes'],x['writes']) == (y['bytes'],y['writes'])
        for population in ('active','all'):
            a, b = old['groups'][population], new['groups'][population]
            rows.append(dict(family=family,population=population,frames=a['frames'],
                baseline_rate=a['updates_per_second'],candidate_rate=b['updates_per_second'],
                rate_gain=b['updates_per_second']/a['updates_per_second']-1,
                baseline_busy=a['metrics']['busy']['mean'],candidate_busy=b['metrics']['busy']['mean'],
                baseline_world=a['stages']['world']['mean'],candidate_world=b['stages']['world']['mean'],
                candidate_p95=b['metrics']['busy']['p95'],candidate_max=b['metrics']['busy']['maximum']))
        checks.append(dict(family=family,frames=len(new['records']),native_points=new['receipt']['native_checkpoints'],
            cpu_ram_identical=True,all_three_vram_snapshots_identical=True,traffic_identical=True,nonworld_cycles_identical=True))
    for new, old in [('matrix-b','matrix-a'),('density-b','density-m')]:
        assert json.loads((path/new/'check.json').read_text())['complete']
        assert (path/new/'captures.bin').read_bytes() == (base/old/'captures.bin').read_bytes()
    timing = [[[int(v) for v in line.split()] for line in (d/'timing.tsv').read_text().splitlines()]
              for d in (base/'density-m',path/'density-b')]
    raw = (path/'density-b/cases.bin').read_bytes()
    density = []
    for label, ids in [('all',range(1920)),('three_copies',[i for i in range(1920) if raw[i*128+0x58:i*128+0x5c]==b'\x03'*4]),('repeat3',range(2,1920,3))]:
        a,b = [statistics.mean(t[i][1] for i in ids) for t in timing]
        density.append(dict(population=label,frames=len(ids),baseline=a,candidate=b,reduction=1-b/a))
    result = dict(rows=rows,checks=checks,density=density,matrix_complete_captures_identical=True,density_complete_captures_identical=True)
    (path/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
    (path/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: paired CPU/RAM, all VRAM snapshots, traffic and non-world cycles; matrix and density captures exact')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    report(parser.parse_args().root.resolve())
