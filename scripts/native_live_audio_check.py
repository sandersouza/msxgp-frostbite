"""Passive continuous audio capture beside native source/picture qualification.

Independent original intervals come from the pinned Stella observer, repeated
without instrumentation. No canonical state or PSG register is injected.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import types

from environment import ROOT
from native_presentation_routes import check as route_check
from presentation_audio import psg_step, OWNED_REGISTERS
from presentation_audio_source_check import registers, replay
from presentation_audio_check import verify_streams
from presentation_records import parse_records
from reference_state import decode_state
from reference_provenance import snapshot_paths
from render_build import symbols


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def observe(source, out):
    import presentation_reference as reference
    if out.exists():
        raise ValueError('fresh source audio output required')
    source_hashes = {name: sha(source/name) for name in ('trace.json','inputs.json','journal.json')}
    trace = json.loads((source/'trace.json').read_bytes())
    inputs = json.loads((source/'inputs.json').read_bytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    initial = out.parent/(out.name+'-initial.state')
    with initial.open('xb') as stream:
        stream.write(bytes.fromhex(trace['steps'][0]['state_bytes']))
    # Check the complete executed helper set against its commit. An unrelated
    # untracked user experiment is not part of this source-observer producer.
    # Preserve the original save/restore batch boundaries. Shifting them by one
    # interval changes Stella's display-jitter bookkeeping even with equal CPU
    # and audio state, so the whole retained capsule would no longer be exact.
    boundaries = []
    cursor = 0
    for segment in json.loads((source/'journal.json').read_bytes()):
        size = segment['intervals']
        boundaries.extend(cursor+min(i+10,size)-1 for i in range(0,size,10))
        cursor += size
    if cursor != len(inputs) or boundaries[-1] != len(inputs)-1:
        raise ValueError('original source journal must cover every interval')
    ends = dict(zip([0]+boundaries[:-1], boundaries))
    code = Path(reference.__file__).read_text()
    replacements = {
        'for offset in range(0, len(inputs), 10):': 'for offset in OBSERVER_ENDS:',
        'samples = inputs[offset:offset + 10];': 'samples = inputs[offset:OBSERVER_ENDS[offset]];'}
    for old,new in replacements.items():
        if code.count(old) != 1:
            raise ValueError('unique source observer batching hook required')
        code = code.replace(old,new)
    copied = out.parent/(out.name+'-observer.py')
    copied.write_text(code)
    module = types.ModuleType('native_aligned_audio_observer')
    module.__file__ = str(copied)
    exec(compile(code,str(copied),'exec'), module.__dict__)
    module.OBSERVER_ENDS = ends
    module._producer = lambda: snapshot_paths(reference.HELPERS)
    producer = sha(Path(__file__))
    report = module.observe(out, initial, inputs[1:],
        ROOT/'outputs/presentation/backend-canonical-b/source/stella')
    for point, expected in zip(report['points'], trace['steps'][1:]):
        if point['state_sha256'] != hashlib.sha256(bytes.fromhex(expected['state_bytes'])).hexdigest():
            raise ValueError('original audio observation differs from retained route capsule')
    if (len(report['points']) != len(trace['steps'])-1 or sha(Path(__file__)) != producer
        or any(sha(source/name) != value for name,value in source_hashes.items())):
        raise ValueError('source observation truncated or producer changed')
    (out/'native-source-audio.json').write_text(json.dumps(dict(
        complete=True, source_trace_sha256=sha(source/'trace.json'),
        source_inputs_sha256=sha(source/'inputs.json'), producer_sha256=producer,
        observer_report_sha256=sha(out/'report.json'),
        batching_ends=ends, adapted_observer_sha256=sha(copied),
        scope='Original full-capsule instrumented/plain repeats, matched to every retained source point; scoped committed helper manifest, unrelated user file excluded.'), indent=2)+'\n')


def hooks(out, syms, cold):
    event_hooks = '\n'.join(
        f'debug set_bp {syms[f"p_audio_apply_{reg:02X}"]} {{$::live_audio}} {{puts $::live_events "$::route_index {reg} [expr {{[reg AF]>>8}}]"}}'
        for reg in range(21,27))
    return f'''
set live_audio 0
set live_selected -1
set live_events [open {{{out/'live-events.tsv'}}} w]
set live_writes [open {{{out/'live-writes.tsv'}}} w]
debug set_bp {cold['native_symbols']['nc_source_ready']} {{!$::live_audio}} {{
 set f [open {{{out/'live-initial.bin'}}} wb]
 puts -nonewline $f [debug read_block memory 0xE000 6][debug read_block {{PSG regs}} 0 16]
 close $f
 set ::live_unowned "[debug read_block {{PSG regs}} 4 2][debug read_block {{PSG regs}} 11 3]"
 set ::live_audio 1
}}
{event_hooks}
debug set_bp {syms['sample_native_input']} {{$::live_audio}} {{set ::live_gpio15 [debug read {{PSG regs}} 15]}}
debug set_bp {syms['sample_native_return']} {{$::live_audio}} {{
 if {{![info exists ::live_gpio15] || [debug read {{PSG regs}} 15]!=$::live_gpio15}} {{fail live-sampler-restoration}}
}}
debug set_watchpoint write_io {{160 161}} {{}} {{
 if {{![info exists ::wp_last_address] || ![info exists ::wp_last_value]}} {{fail live-audio-payload}}
 if {{($::wp_last_address&255)==160}} {{
  set ::live_selected $::wp_last_value
  if {{$::live_audio}} {{
   set sampler [expr {{[reg PC]>={syms['sample_native_input']} && [reg PC]<={syms['sample_native_return']}}}]
   if {{$sampler && $::live_selected ni {{14 15}}}} {{fail live-sampler-selection}}
   if {{!$sampler && $::live_selected ni {{0 1 2 3 6 7 8 9 10}}}} {{fail live-audio-selection}}
  }}
 }} elseif {{$::live_audio}} {{
  set sampler [expr {{[reg PC]>={syms['sample_native_input']} && [reg PC]<={syms['sample_native_return']}}}]
  if {{$sampler}} {{
   if {{$::live_selected!=15}} {{fail live-sampler-write}}
  }} else {{
   if {{$::live_selected ni {{0 1 2 3 6 7 8 9 10}}}} {{fail live-audio-unowned}}
   if {{$::live_selected==7 && ($::wp_last_value&192)!=128}} {{fail live-audio-gpio}}
   puts $::live_writes "$::route_index $::live_selected $::wp_last_value"
  }}
 }}
}}
debug set_bp {syms['native_return']} {{$::live_audio}} {{
 if {{"[debug read_block {{PSG regs}} 4 2][debug read_block {{PSG regs}} 11 3]" ne $::live_unowned}} {{fail live-audio-unowned-state}}
}}
'''


def check(base, delivery, source, observation, out, family, effect_gain=False):
    from native_effect_gain_check import qualification_inputs
    qualification_producer=qualification_inputs(base,delivery)
    identities = {path: sha(path) for path in (source/'trace.json',source/'inputs.json',
        observation/'native-source-audio.json',observation/'report.json',observation/'initial.state')}
    receipt = json.loads((observation/'native-source-audio.json').read_bytes())
    if (receipt['source_trace_sha256'] != sha(source/'trace.json') or
        receipt['source_inputs_sha256'] != sha(source/'inputs.json') or
        receipt['observer_report_sha256'] != sha(observation/'report.json')):
        raise ValueError('exact independent audio source required')
    report = json.loads((observation/'report.json').read_bytes())
    trace = json.loads((source/'trace.json').read_bytes())
    if ((observation/'initial.state').read_bytes() != bytes.fromhex(trace['steps'][0]['state_bytes'])
        or sha(observation/'initial.state') != report['initial_sha256']):
        raise ValueError('original audio initial capsule differs')
    records = []
    for journal in report['journals']:
        if journal['offset'] != len(records):
            raise ValueError('source audio interval gap or duplicate')
        path = observation/f'batch-{journal["offset"]:05d}'/'records.bin'
        if sha(path) != journal['records_sha256']:
            raise ValueError('source audio raw stream changed')
        batch = parse_records(path.read_bytes())
        if len(batch) != journal['count']:
            raise ValueError('source audio journal count differs')
        records.extend(batch)
        identities[path] = journal['records_sha256']
    if len(records) != len(trace['steps'])-1 or len(report['points']) != len(records):
        raise ValueError('complete original audio interval sequence required')
    s = symbols(base/'presentation.sym')
    cold = json.loads((delivery/'cold/cold-image.json').read_bytes())
    original_run = subprocess.run
    producer = sha(Path(__file__))

    def run(args, *a, **kw):
        if isinstance(args, list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p = Path(args[args.index('-script')+1])
            p.write_text(p.read_text()+hooks(out.resolve(), s, cold))
        return original_run(args, *a, **kw)

    subprocess.run = run
    try:
        result = route_check(base, delivery, source, out, family)
    finally:
        subprocess.run = original_run
    initial = (out/'live-initial.bin').read_bytes()
    source_latches = registers(decode_state((observation/'initial.state').read_bytes()))
    base_psg = bytes((1,0,1,0,0,0,1,191,0,0,0,0,0,0,0,0))
    previous = psg_step(source_latches, {'psg':base_psg})
    if len(initial) != 22 or initial[:6] != source_latches or any(initial[6+r] != previous['psg'][r] for r in OWNED_REGISTERS):
        raise ValueError('native/source cold audio initialization differs')
    expected_events, expected_writes = [], []
    if result['source_checkpoints']-1 > len(records):
        raise ValueError('native run exceeded original audio observation')
    selected_counts = {}
    inputs = json.loads((source/'inputs.json').read_bytes())
    if effect_gain:
        from native_effect_gain_check import original_stores, replay_selected
        from native_effect_gain import SITES
        from reference_inventory import verified_input
        original = ROOT/'references/roms/frostbite.bin';verified_input(original)
        original = original.read_bytes()
    for index, record in enumerate(records[:result['source_checkpoints']-1], 1):
        if effect_gain:
            stores = original_stores(original,record,inputs[index])
            source_latches, previous, history = replay_selected(source_latches,record['audio'],previous,stores)
            for pc,address,value in stores:
                if pc in SITES:
                    key=f'{pc:04X}/{value}';selected_counts[key]=selected_counts.get(key,0)+1
        else:
            source_latches, previous, history = replay(source_latches, record['audio'], previous)
        if source_latches != registers(decode_state(bytes.fromhex(trace['steps'][index]['state_bytes']))):
            raise ValueError('original audio stream and capsule latches differ')
        for event in history:
            expected_events.append((index, event['address'], event['raw']))
            expected_writes.extend((index, reg, value) for reg, value in event['psg_writes'])
    read = lambda name: [tuple(map(int,line.split())) for line in (out/name).read_text().splitlines()]
    actual_events, actual_writes = read('live-events.tsv'), read('live-writes.tsv')
    verify_streams(actual_events, expected_events, actual_writes, expected_writes)
    # Same captured stream, deliberate omitted-event negative; no target mutation.
    if not actual_events:
        raise ValueError('nonempty natural audio coverage required')
    try:
        verify_streams(actual_events[1:], expected_events, actual_writes, expected_writes)
    except ValueError:
        pass
    else:
        raise ValueError('missing-event negative accepted')
    if not actual_writes:
        raise ValueError('nonempty physical PSG coverage required')
    try:
        verify_streams(actual_events, expected_events, actual_writes[1:], expected_writes)
    except ValueError:
        pass
    else:
        raise ValueError('missing-physical-write negative accepted')
    if sha(Path(__file__)) != producer or any(sha(path) != value for path,value in identities.items()):
        raise ValueError('live audio producer changed')
    result = dict(result, live_PSG_checked=True, original_events=len(expected_events),
        physical_PSG_writes=len(expected_writes), omitted_event_negative_rejected=True,
        selective_effect_gain=effect_gain,selected_source_writes=selected_counts,
        omitted_physical_write_negative_rejected=True,
        audio_producer_sha256=producer, audio_source_receipt_sha256=sha(observation/'native-source-audio.json'),
        event_capture_sha256=sha(out/'live-events.tsv'), physical_capture_sha256=sha(out/'live-writes.tsv'),
        scope='Continuous native source/pixels/audio sequence against independent original raw events. Manual listening/physical joystick and hardware acceptance remain separate.')
    if qualification_inputs(base,delivery)!=qualification_producer:
        raise ValueError('live audio qualification source/product changed')
    result['qualification_sources']=qualification_producer
    (out/'native-live-audio.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('base','delivery','source','observation','out'):
        p.add_argument('--'+name, type=Path, required=name in ('source','out'))
    p.add_argument('--family', choices=('ntsc','pal'))
    p.add_argument('--observe-only', action='store_true')
    p.add_argument('--effect-gain', action='store_true')
    a = p.parse_args()
    if a.observe_only:
        observe(a.source.resolve(), a.out.resolve())
    else:
        check(a.base.resolve(), a.delivery.resolve(), a.source.resolve(), a.observation.resolve(), a.out.resolve(), a.family, a.effect_gain)
