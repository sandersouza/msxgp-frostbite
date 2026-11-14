"""Independent 6502 store attribution and actual native PSG gain qualification."""
import argparse
from pathlib import Path
import json
from collections import Counter
from py65.devices.mpu6502 import MPU
from mechanics_probe import SliceBus
from native_contract import compare
from presentation_audio import MASKS
from native_effect_gain import project_write, SITES
from presentation_records import parse_records
from presentation_source_cases import collect
from native_audio_check import check as native_check
import presentation_audio_check as audio
from environment import ROOT
from build_native_delivery import sources
from build_native_flat_image import digest


def qualification_inputs(base,delivery):
    result=sources()
    for path in (base/'presentation.sym',base/'build.json',
                 delivery/'linked/native-link.json',delivery/'cold/cold-image.json',
                 delivery/'cartridge/FROSTBIT.ROM'):
        result[str(path.resolve())]=digest(path.read_bytes())
    return result


def original_stores(rom, record, sample):
    """Replay the observed post-visible CPU slice; verify all state and writes.

    INPT reads retain the low seven undriven operand-bus bits (0C), as
    observed in the original capsules. INTIM final wait sample is zero; this
    interpreter attributes writes, not original instruction timing.
    """
    samples = {0x280:sample['swcha'], 0x282:sample['swchb'], 0x284:0,
               12:12|(0 if sample['fire'][0] else 128),
               13:12|(0 if sample['fire'][1] else 128)}
    bus = SliceBus(rom, samples)
    bus.ram[:] = bytes(record['visible']['ram'])
    cpu = MPU(memory=bus, pc=0xF476)
    for k,v in record['visible']['registers'].items():
        setattr(cpu,k,v)
    events = []
    for _ in range(20000):
        if cpu.pc == 0xF019:
            break
        pc, before = cpu.pc, len(bus.writes)
        cpu.step()
        for row in bus.writes[before:]:
            address, value = int(row['address'],16), int(row['value'],16)
            if 21 <= address <= 26:
                events.append((pc,address,value))
    else:
        raise ValueError('bounded original store attribution exceeded')
    compare(record['after'], dict(ram=list(bus.ram),registers={k:getattr(cpu,k) for k in ('a','x','y','p','sp')}))
    if [(a,v) for _,a,v in events] != [(a,v) for _,a,v in record['audio']]:
        raise ValueError('independent CPU store sequence differs from observed original')
    return events


def replay_selected(source, writes, previous, stores):
    if [(a,v) for _,a,v in stores] != [(a,v) for _,a,v in writes]:
        raise ValueError('exact original events required for gain attribution')
    source = bytearray(source)
    history = []
    for (cycle,address,value),(pc,_,_) in zip(writes,stores):
        source[address-21] = value & MASKS[address-21]
        previous = project_write(bytes(source),previous,pc,address)
        history.append(dict(cycle=cycle,address=address,raw=value,
                            psg_writes=previous['writes'],psg=previous['psg'].hex()))
    return bytes(source),previous,history


def check(base,delivery,out):
    producer=qualification_inputs(base,delivery)
    from reference_inventory import verified_input
    path=ROOT/'references/roms/frostbite.bin';verified_input(path);rom=path.read_bytes()
    source=collect();streams=[];counts=Counter();causes=Counter()
    for audit in source['audits']:
        root=ROOT/audit['root'];report=json.loads((root/'report.json').read_bytes())
        samples=json.loads((root/'fixtures.json').read_bytes()) if audit['family']=='fixtures' else report['points']
        for batch in sorted(root.glob('batch-*')):
            offset=int(batch.name.split('-')[1])
            for record in parse_records((batch/'records.bin').read_bytes()):
                if record['visible']['ram'][0x47] not in (0,1):
                    continue
                stores=original_stores(rom,record,samples[offset+record['index']]['input'])
                streams.append(stores)
                counts.update(f'{pc:04X}/{value}' for pc,address,value in stores if pc in SITES)
                for pc,address,value in stores:
                    if pc in (0xF4D7,0xF4D9) and value==4:
                        ram=record['visible']['ram']
                        causes['freezing' if ram[0x70] else 'drowning' if ram[0x6B] else 'unclassified']+=1
    original=audio.replay;index=0
    def replay(initial,writes,previous):
        nonlocal index
        stores=streams[index];index+=1
        return replay_selected(initial,writes,previous,stores)
    audio.replay=replay
    try:
        result=native_check(base,delivery,out)
    finally:
        audio.replay=original
    if index!=len(streams):
        raise ValueError('all source intervals required')
    if qualification_inputs(base,delivery)!=producer:
        raise ValueError('qualification source or product changed')
    result.update(selective_gain=True,original_store_attribution=True,selected_writes=dict(counts),
                  requested_amplitude_factor=1.25,nominal_realized_factor=2**0.5,
                  missing_selected_store_sites=[f'{pc:04X}' for pc in SITES if not any(k.startswith(f'{pc:04X}/') for k in counts)],
                  death_cause_writes=dict(causes),qualification_sources=producer)
    (out/'effect-gain-check.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','delivery','out'):p.add_argument('--'+n,type=Path,required=True)
    check(**vars(p.parse_args()))
