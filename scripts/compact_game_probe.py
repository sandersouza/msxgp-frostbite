"""Apply existing source/pixel/IRQ oracles to compact integration experiments."""
import argparse
import hashlib
import json
from pathlib import Path
import types

from environment import ROOT
from reference_traces import private_output
import presentation_border_check as border
import presentation_credit_reference_check as checker


def check(build,out,mode):
    if mode not in ('ntsc','pal','bear-ntsc','bear-pal','matrix'):raise ValueError('declared route required')
    build=Path(build).resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    out.parent.mkdir(parents=True,exist_ok=True)
    producer=Path(__file__).read_bytes();previous=border.legacy.probe
    if mode.startswith('bear-'):
        source=(ROOT/'scripts/presentation_fixed_clock_probe.py').read_text()
        needle="source=ROOT/'outputs/progression/route-progression-v0-a'"
        if source.count(needle)!=1:raise ValueError('bear-route injection differs')
        source=source.replace(needle,"source=ROOT/'outputs/hazards/route-bear-chase-a'")
        copy=out.parent/(out.name+'-bear-probe.py')
        with copy.open('x') as stream:stream.write(source)
        module=types.ModuleType('compact_route_bear');module.__file__=str(copy)
        exec(compile(source,str(copy),'exec'),module.__dict__)
        def probe(*args,**kwargs):
            old=module.clocks;module.clocks=border.legacy.clocks
            module.adapted_frame=border.legacy.adapted_frame
            module.audit_row=lambda *a,**kw:border.legacy.audit_row(*a,**kw)
            module.audit_active=lambda *a,**kw:border.legacy.audit_active(*a,**kw)
            try:return module.probe(*args,**kwargs)
            finally:module.clocks=old
        border.legacy.probe=probe
    try:result=checker.check(build,out,mode.split('-')[-1],620 if mode.startswith('bear-') else 2115 if mode=='matrix' else 2252)
    finally:border.legacy.probe=previous
    if Path(__file__).read_bytes()!=producer:raise ValueError('driver changed')
    m=json.loads((build/'build.json').read_bytes())
    receipt=dict(complete=result['complete'],mode=mode,rom_sha256=m['rom']['sha256'],
        driver_sha256=hashlib.sha256(producer).hexdigest(),
        scope='Existing unweakened original-source/pixel/owner/IRQ oracle; bounded routes, no human or physical acceptance.')
    (out/'compact-route.json').write_text(json.dumps(receipt,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',required=True)
    a=p.parse_args();print(check(a.build,a.out,a.mode))
