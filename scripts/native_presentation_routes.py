"""Run retained input-only routes on the accepted native cartridge.

Adapts the bounded historical probe without changing its pinned producer or game.
Keyboard input follows the source-selected player; physical joystick and live
PSG streams remain separate acceptance obligations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import types
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def adapt_probe(text, source, steps):
    if type(steps) is not int or not 2 <= steps <= 10000:
        raise ValueError('bounded retained route required')
    replacements = [
        ('2<=steps<=2252', f'2<=steps<={steps}'),
        ("source=ROOT/'outputs/progression/route-progression-v0-a'",
         f'source=Path({str(source)!r})'),
        (' if {{[debug read memory 0xC047]!=0}} {{fail one-player-contract}}',
         ' set player [debug read memory 0xC047]\n'
         ' if {{$player ni {{0 1}}}} {{fail invalid-active-player}}\n'
         ' if {{$player==0}} {{set keys $swcha;set fire $fire0}} else '
         '{{set keys [expr {{(($swcha&15)<<4)|15}}];set fire $fire1}}'),
        ('set mask [expr {{(($swcha&16)?0:32)|(($swcha&32)?0:64)|(($swcha&64)?0:16)|(($swcha&128)?0:128)|($fire0?1:0)}}]',
         'set mask [expr {{(($keys&16)?0:32)|(($keys&32)?0:64)|(($keys&64)?0:16)|(($keys&128)?0:128)|($fire?1:0)}}]'),
    ]
    for before, after in replacements:
        if text.count(before) != 1:
            raise ValueError('unique historical route hook required: ' + before)
        text = text.replace(before, after)
    return text


def check(base, delivery, source, out, family):
    import native_flat_takeover_check as native
    import compact_game_probe as compact
    from progression_play import assess_receipt, source_helpers
    from reference_provenance import audit_manifest
    from reference_traces import private_output
    from environment import ROOT

    source, delivery, base = source.resolve(), delivery.resolve(), base.resolve()
    out = private_output(out)
    if out.exists():
        raise ValueError('fresh route output required')
    receipt = json.loads((source/'route.json').read_bytes())
    audit_manifest(receipt, source_helpers(receipt))
    if receipt.get('clean_start') is not True:
        raise ValueError('independent clean source start required')
    identities = {source/name: value for name, value in receipt['files'].items()}
    identities[source/'route.json'] = digest(source/'route.json')
    if any(digest(path) != value for path, value in identities.items()):
        raise ValueError('source route changed')
    trace = json.loads((source/'trace.json').read_bytes())
    horizon = receipt.get('extension', {}).get('original_horizon')
    if 'extension' in receipt:
        ext = receipt['extension']
        if type(horizon) is not int or horizon + ext['appended_intervals'] != len(trace['steps']):
            raise ValueError('explicit original horizon and independent tail required')
        parent = Path(ext['parent_path'])
        if digest(parent/'route.json') != ext['parent_receipt_sha256']:
            raise ValueError('parent source receipt changed')
        for name, value in ext['parent_files'].items():
            identities[parent/name] = value
        identities[parent/'route.json'] = ext['parent_receipt_sha256']
        if any(digest(path) != value for path, value in identities.items()):
            raise ValueError('extended source parent changed')
        parent_trace = json.loads((parent/'trace.json').read_bytes())
        if trace['steps'][:horizon] != parent_trace['steps']:
            raise ValueError('original source prefix changed in extended route')
    # Reserve one independent source point for a possible second PAL IRQ step.
    # A route is accepted only if its terminal assessment is reached below.
    steps = len(trace['steps']) - 2
    original = ROOT/'scripts/presentation_fixed_clock_probe.py'
    producer_sha = digest(Path(__file__))
    out.parent.mkdir(parents=True, exist_ok=True)
    copy = out.parent/(out.name+'-route-probe.py')
    with copy.open('x') as stream:
        stream.write(adapt_probe(original.read_text(), source, steps))
    module = types.ModuleType('native_route_probe')
    module.__file__ = str(copy)
    exec(compile(copy.read_text(), str(copy), 'exec'), module.__dict__)
    if module.__name__ in sys.modules:
        raise ValueError('route oracle module already active')
    sys.modules[module.__name__] = module
    legacy = compact.border.legacy
    previous_probe, previous_check = legacy.probe, compact.check

    def probe(build, target, clock_family, ignored_steps=2252, expanded=False):
        module.clocks = legacy.clocks
        module.adapted_frame = legacy.adapted_frame
        module.audit_row = lambda *a, **kw: legacy.audit_row(*a, **kw)
        module.audit_active = lambda *a, **kw: legacy.audit_active(*a, **kw)
        module.decorate_owners = legacy.decorate_owners
        return module.probe(build, target, clock_family, steps, expanded)

    def routed(build, target, mode):
        if mode != family:
            raise ValueError('route family mismatch')
        return compact.checker.check(build, target, family, steps)

    legacy.probe, compact.check = probe, routed
    try:
        native.check(base, delivery/'linked', out, family, delivery/'cold',
                     delivery/'cartridge/FROSTBIT.ROM')
    finally:
        legacy.probe, compact.check = previous_probe, previous_check
        del sys.modules[module.__name__]
    actual = (out/'route-cpu.bin').read_bytes()
    if len(actual) % 133:
        raise ValueError('partial source checkpoint')
    points = [dict(index=i, ram=list(actual[i*133+5:(i+1)*133]),
                   registers=dict(zip(('a','x','y','p','sp'), actual[i*133:i*133+5])))
              for i in range(len(actual)//133)]
    if horizon is not None and len(points) < horizon:
        raise ValueError('original source horizon not completed')
    assessment = assess_receipt(points[:horizon] if horizon is not None else points, receipt)
    if assessment != receipt['assessment']:
        raise ValueError('complete original route milestones not reached')
    if any(digest(path) != value for path, value in identities.items()):
        raise ValueError('source changed during qualification')
    if digest(Path(__file__)) != producer_sha:
        raise ValueError('route adapter changed during qualification')
    native_receipt = json.loads((out/'native-takeover.json').read_bytes())
    result = dict(complete=True, family=family, assessment=assessment,
                  source_checkpoints=len(points), source_route_sha256=identities[source/'route.json'],
                  original_horizon=horizon, executed_tail_points=len(points)-horizon if horizon is not None else 0,
                  executed_ROM_sha256=native_receipt['executed_ROM_sha256'],
                  native_receipt_sha256=digest(out/'native-takeover.json'),
                  original_probe_sha256=digest(original), adapted_probe_sha256=digest(copy),
                  producer_sha256=producer_sha, live_PSG_checked=False,
                  physical_joystick_ports_checked=False, manual_listening=False,
                  scope='Input-only source-selected keyboard replay; full CPU/RAM, committed pixels and native guards, terminal source milestones. No live PSG or physical-device verdict.')
    (out/'native-route.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'delivery', 'source', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--family', choices=('ntsc','pal'), required=True)
    check(**vars(parser.parse_args()))
