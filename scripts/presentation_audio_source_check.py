"""Audit original ordered audio against complete independent Stella capsules.

Each controlled fixture restores its baseline; natural intervals carry the
actual previous capsule. Never guess initially latched audio registers.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from environment import ROOT
from presentation_audio import events,psg_step,MASKS
from presentation_records import parse_records
from presentation_source_cases import collect,verify_files,FILES as SOURCE_FILES
from reference_state import decode_state
from reference_traces import STATE_NAME,private_output

FILES=tuple(dict.fromkeys((*SOURCE_FILES,'scripts/presentation_audio.py','scripts/presentation_audio_source_check.py','scripts/reference_state.py')))


def registers(capsule):
    channels=capsule['tia']['audio']['channels']
    if len(channels)!=2:raise ValueError('two complete original oscillator states required')
    values=bytes(channels[channel][field] for field in ('control','frequency','volume') for channel in (0,1))
    if any(value&~mask for value,mask in zip(values,MASKS)):raise ValueError('invalid original hardware audio latch')
    return values


def replay(initial,writes,previous):
    if not isinstance(initial,bytes) or len(initial)!=6:raise ValueError('complete original starting audio latches required')
    state=bytearray(initial);history=[]
    for cycle,address,value in writes:
        state[address-21]=value&MASKS[address-21]
        previous=psg_step(bytes(state),previous)
        history.append({'cycle':cycle,'address':address,'raw':value,'psg_writes':previous['writes'],'psg':previous['psg'].hex()})
    return bytes(state),previous,history


def check(out):
    sha=lambda data:hashlib.sha256(data).hexdigest();producer={name:sha((ROOT/name).read_bytes()) for name in FILES}
    domain=collect();out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    report_rows=[];modes=Counter();phases=Counter();same=0;silent=0;max_writes=0;write_count=0
    base={'psg':bytes((1,0,1,0,0,0,1,63,0,0,0,0,0,0,0,0))}
    for audit in domain['audits']:
        root=ROOT/audit['root'];initial=decode_state((root/'initial.state').read_bytes());before=initial
        controlled=audit['family']=='fixtures';projected=psg_step(registers(initial),base)
        for batch in sorted(root.glob('batch-*')):
            parsed=parse_records((batch/'records.bin').read_bytes());intervals=events(parsed)
            for record,interval in zip(parsed,intervals):
                if controlled:before=initial;projected=psg_step(registers(initial),base)
                start=registers(before);latches=bytearray(start)
                for cycle,address,value in interval['writes']:
                    index=address-21;masked=value&MASKS[index]
                    same+=masked==latches[index];latches[index]=masked
                    if index<2:modes[masked]+=1
                    phases['visible' if cycle<=record['visible_cycles'] else 'post_visible']+=1
                after=decode_state((batch/'plain/settings/state'/f'{STATE_NAME}.st{record["index"]}').read_bytes())
                final,projected,history=replay(start,interval['writes'],projected)
                if final!=registers(after):raise ValueError(f'original audio event/capsule latches differ: {batch}/{record["index"]}')
                if final!=bytes(latches):raise ValueError('raw event replay lost or reordered source writes')
                write_count+=len(history);max_writes=max(max_writes,len(history));silent+=not history
                report_rows.append({'id':f'{audit["root"]}/{batch.name}/{record["index"]}','family':audit['family'],
                    'source_before':start.hex(),'source_after':final.hex(),'source_cycles':record['cycles'],'visible_cycles':record['visible_cycles'],
                    'events':history,'after_capsule_sha256':after['state_sha256']})
                before=after
    verify_files(domain['files'])
    if any(sha((ROOT/name).read_bytes())!=value for name,value in producer.items()):raise ValueError('audio source producer changed')
    raw=out/'source-audio.json';raw.write_text(json.dumps(report_rows,indent=2)+'\n')
    report={'complete':True,'intervals':len(report_rows),'ordered_writes':write_count,'same_masked_value_writes':same,'silent_intervals':silent,
        'maximum_writes_per_interval':max_writes,'control_writes':dict(sorted(modes.items())),'phases':dict(phases),
        'source_receipt_sha256':domain['source_receipt_sha256'],'producer_files':producer,'input_files':domain['files'],'raw_sha256':sha(raw.read_bytes()),
        'native_accepted':False,'frame_deadline_accepted':False,
        'scope':'Frozen original audio writes replayed from structurally decoded actual initial/previous full Stella oscillator capsules to independent after-capsule latches. Controlled fixtures reset independently; natural intervals carry source state. Every raw/same-value event and silent interval retained. PSG is only a documented host projection; no native hooks, physical PSG/listening or combined timing acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','intervals','ordered_writes','same_masked_value_writes','silent_intervals','maximum_writes_per_interval','control_writes','phases')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    check(**vars(p.parse_args()))
