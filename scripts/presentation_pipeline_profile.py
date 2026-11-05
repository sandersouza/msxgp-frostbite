"""Additional inclusive prepare-stage costs on the unchanged original F route."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import presentation_prepared_route as route
from presentation_experiment_evidence import validate_probe
from render_build import symbols

PROBES={
    'player-lookup':'p_player_cache_lookup',
    'player-way':'p_player_variant_lookup',
    'static-lookup':'p_static_lookup',
    'dirty-compare':'p_dirty_compare',
    'header-masks':'p_template_header_mask_column',
    'header-keys':'p_template_header_keys',
    'header-driver':'p_fast_header_prepare',
    'igloo-driver':'p_fast_igloo_prepare',
    'header-all':'presentation_hud_prepare',
}


def add_detail_probes(text,entries,path):
    start='set ::tracking 1;set ::started'
    dump='puts -nonewline $::captures'
    if text.count(start)!=1 or text.count(dump)!=1:raise ValueError('unrecognized original F frame scaffold')
    zero=';'.join(f'set ::cost_count(detail-{label}) 0;set ::cost_sum(detail-{label}) 0' for label in entries)
    rows=';'.join(f'puts $::detailfile "$::index {label} $::cost_count(detail-{label}) $::cost_sum(detail-{label})"' for label in entries)
    text=text.replace(start,zero+'\n    '+start,1).replace(dump,rows+'\n        '+dump,1)
    text+=f'\nset detailfile [open {{{path}}} w]\n'
    text+='\n'.join(f'debug set_bp {address} {{}} {{begin_probe_cost detail-{label}}}' for label,address in entries.items())
    return text+'\n'


def check(build,out,family):
    s=symbols(build/'presentation.sym');entries={label:s[name] for label,name in PROBES.items()}
    original_run=subprocess.run
    def instrument(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            script=Path(args[args.index('-script')+1])
            script.write_text(add_detail_probes(script.read_text(),entries,out/'pipeline-costs.tsv'))
        return original_run(args,*a,**kw)
    subprocess.run=instrument
    try:route.check(build,out,family)
    finally:subprocess.run=original_run
    frames=2253 if family=='ntsc' else 1886
    meta=json.loads((build/'build.json').read_text());validate_probe(out,meta['rom']['sha256'],frames)
    rows=[line.split() for line in (out/'pipeline-costs.tsv').read_text().splitlines()]
    if len(rows)!=frames*len(entries):raise ValueError('missing detailed timing rows')
    for i,row in enumerate(rows):
        if len(row)!=4 or int(row[0])!=i//len(entries) or row[1]!=list(entries)[i%len(entries)] or any(int(x)<0 for x in row[2:]):
            raise ValueError('invalid detailed cost row')
    result=dict(complete=True,frames=frames,rom_sha256=meta['rom']['sha256'],
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        artifacts={'pipeline-costs.tsv':hashlib.sha256((out/'pipeline-costs.tsv').read_bytes()).hexdigest()},
        scope='Additional inclusive routine costs only; never sum overlapping probes. Same ROM, complete original-state/pixel/owner route checks retained.')
    (out/'pipeline-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--family',choices=('ntsc','pal'),required=True)
    args=parser.parse_args();check(args.build.resolve(),args.out.resolve(),args.family)
