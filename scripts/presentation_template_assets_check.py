"""Reopen all finite-template physical banks and compare complete source masks."""
import argparse
from functools import reduce
import hashlib
import json
from pathlib import Path

from environment import ROOT
from presentation_fast_model import prepare
from presentation_fixed_floe import strip
from presentation_floe_templates import compile_templates,cells,read_pattern
from presentation_floe_templates_check import FILES as BASE_FILES
from presentation_palette import audit_palette
from presentation_source_cases import verify_files
from presentation_template_assets import pack,legacy_grids,logical,SHADOW_OFFSET
from reference_traces import private_output

FILES=tuple(dict.fromkeys((*BASE_FILES,'scripts/presentation_template_assets.py','scripts/presentation_template_assets_check.py')))


def check(out,geometry,contacts):
    sha=lambda data:hashlib.sha256(data).hexdigest()
    producer={name:sha((ROOT/name).read_bytes()) for name in FILES};geometry=Path(geometry).resolve();contacts=Path(contacts).resolve()
    config=json.loads((ROOT/'references/presentation-assets-config.json').read_text());palette_path=ROOT/config['palette'];palette=audit_palette(palette_path)
    original=ROOT/'references/roms/frostbite.bin';rom=original.read_bytes();source_meta=json.loads((geometry/'geometry.json').read_text())
    palette_files=sorted(p for p in palette_path.rglob('*') if p.is_file()) if palette_path.is_dir() else [palette_path]
    source_files=[original,*palette_files,geometry/'geometry.json',geometry/'row-pointer-map.bin',*sorted(geometry.glob('geometry-*.bin')),
        contacts/'floe-roots.bin',contacts/'floe-base.bin']
    old_static=geometry.parent/'static';static_meta=json.loads((old_static/'static.json').read_text());source_files.append(old_static/'static.json')
    source_files.extend(old_static/name for name in static_meta['files'])
    consumed={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in source_files}
    tables=prepare(rom,palette,geometry);compiled=compile_templates(tables)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);meta=pack(geometry,compiled,rom,palette,contacts,out/'assets')
    raw=b''.join((out/'assets'/f'assets-{bank:03d}.bin').read_bytes() for bank in meta['physical_banks']);sections=meta['sections']
    def section(name):
        node=sections[name];return raw[node['offset']:node['offset']+node['size']]
    patterns=compiled['files']['logical-patterns.bin'];pairs=section('pattern_pairs');halves=section('pattern_halves')
    for index in range(meta['patterns']):
        if read_pattern(pairs,halves,index)!=patterns[index*8:index*8+8]:raise ValueError('physical half dictionary changed a logical pattern')
    old_raw=b''.join((geometry/f'geometry-{bank:03d}.bin').read_bytes() for bank in source_meta['physical_banks'])
    expected,groups=legacy_grids(old_raw,source_meta);grids=0
    for family,cases in groups.items():
        for root,group in zip(meta['roots'][family],cases):
            position=logical(root)
            for variant,old_index in enumerate(group):
                code=int.from_bytes(raw[position+variant*2:position+variant*2+2],'little');kind,number=code>>12,code&4095
                if kind>=len(meta['classes']):raise ValueError('physical grid references an absent class')
                cls=meta['classes'][kind];at=cls['offset']+number*cls['stride']
                if number>=cls['count']:raise ValueError('physical grid index exceeds its class')
                ids=tuple(int.from_bytes(raw[i:i+2],'little') for i in range(at,at+cls['stride'],2))
                if {'columns':cls['columns'],'rows':cls['rows'],'patterns':ids}!=expected[old_index]:raise ValueError('repacked physical grid differs from original geometry')
                grids+=1
    old_static_raw=b''.join((old_static/f'assets-{bank:03d}.bin').read_bytes() for bank in static_meta['physical_banks'])
    for name in ('header','footer_tiles','footer_names'):
        old=static_meta['sections'][name]
        if section(name)!=old_static_raw[old['offset']:old['offset']+old['size']]:raise ValueError('physical static constructor fragments changed')
    if raw[SHADOW_OFFSET:]!=(contacts/'floe-roots.bin').read_bytes()+(contacts/'floe-base.bin').read_bytes():raise ValueError('far contact root/base tail changed')
    programs=section('template_names');directory=section('template_index');floes=section('floe_patterns');cases=0
    for phase in range(8):
        for delta_index,delta in enumerate(meta['deltas']):
            for root in range(160):
                index=(phase*len(meta['deltas'])+delta_index)*16+root%16
                at=sections['template_keys']['offset']+int.from_bytes(directory[index*2:index*2+2],'little')
                program,count=raw[at:at+2]
                if not 1<=count<=14 or at%16384+2+count*2>16384:raise ValueError('invalid/cross-bank physical template')
                ids=[int.from_bytes(raw[i:i+2],'little') for i in range(at+2,at+2+count*2,2)]
                if any(identifier>=meta['floe_patterns'] for identifier in ids):raise ValueError('physical template mask index outside raw floe pool')
                candidate=cells(programs[program*32:program*32+30],[identifier+1 for identifier in ids],root,88+phase)
                actual={cell:floes[(identifier-1)*8:identifier*8] for cell,identifier in candidate.items()}
                original_strip=strip(tables,root,delta,88+phase,15)
                wanted={cell:bytes(reduce(int.__or__,(layer['pattern'][y] for layer in layers),0) for y in range(8)) for cell,layers in original_strip['layers'].items()}
                if actual!=wanted:raise ValueError(f'physical template mask differs phase{phase} delta{delta} root{root}')
                cases+=1
        print(f'phase{phase}: {cases} physical template cases, zero differences',flush=True)
    verify_files(consumed)
    if any(sha((ROOT/name).read_bytes())!=value for name,value in producer.items()):raise ValueError('physical asset producer changed')
    report={'complete':True,'template_cases':cases,'row_bear_grids':grids,'patterns':meta['patterns'],'floe_patterns':meta['floe_patterns'],
        'prefix_used_bytes':meta['prefix_used_bytes'],'remaining_before_shadow':meta['remaining_before_shadow'],'asset_banks':len(meta['physical_banks']),
        'producer_files':producer,'input_files':consumed,'assets':meta,'native_accepted':False,'frame_deadline_accepted':False,
        'scope':'Reopened physical14-bank finite-template packing: every logical pattern, all8960 original row/bear grids, full old static fragments/contact root-base bytes, all12800 original-control floe translations. Native reader proof is separate; no full source raster, game, timing, audio or human verdict.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','template_cases','row_bear_grids','patterns','floe_patterns','remaining_before_shadow')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('out','geometry','contacts'):p.add_argument('--'+name,type=Path,required=True)
    check(**vars(p.parse_args()))
