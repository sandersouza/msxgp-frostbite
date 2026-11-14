"""Immutable accepted target namespaces are host oracles, never native payloads."""
from contextlib import contextmanager
import json
import sys
from compact_live_probe import CONTROL_SHA
from build_compact_packet_experiment import digest
from environment import ROOT
from render_build import symbols
import presentation_constructors
import presentation_direct_enemy as geometry


@contextmanager
def original_namespaces(metadata):
    base=ROOT/'outputs/presentation/credit-reference-at/build-final'
    m=json.loads((base/'build.json').read_bytes());rom=(base/m['rom']['filename']).read_bytes()
    if digest(rom)!=CONTROL_SHA:raise ValueError('immutable accepted host oracle required')
    node=metadata['compact_retired_floe_assets']
    if node['validation_raw_floe_oracle_sha256']!=CONTROL_SHA or metadata['compact_retired_templates']['validation_geometry_oracle_sha256']!=CONTROL_SHA:
        raise ValueError('declared independent host namespaces required')
    packed=m['template_assets'];section=packed['sections']['floe_patterns']
    data=b''.join(rom[b*16384:(b+1)*16384] for b in packed['physical_banks'])
    raw=data[section['offset']:section['offset']+section['size']]
    if digest(raw)!=node['original_floe_patterns_sha256'] or len(raw)!=packed['floe_patterns']*8:
        raise ValueError('complete accepted raw floe namespace differs')
    floes=[raw[i:i+8] for i in range(0,len(raw),8)]
    old_construct=presentation_constructors.construct;old_geometry=geometry.resident_geometry;old_decorate=geometry.decorate_actor_owners
    expected=old_geometry(rom,symbols(base/'presentation.sym'))
    def construct(*args,**kw):
        if 'floe_patterns' in kw:kw['floe_patterns']=floes
        return old_construct(*args,**kw)
    def resident(*a,**kw):return expected
    def decorate(raw,caches,ignored,g):return old_decorate(raw,caches,rom,expected)
    changed=[]
    for module in tuple(sys.modules.values()):
        if module is None:continue
        for name,old,new in (('construct',old_construct,construct),('resident_geometry',old_geometry,resident),('decorate_actor_owners',old_decorate,decorate)):
            if getattr(module,name,None) is old:changed.append((module,name,old));setattr(module,name,new)
    try:yield dict(oracle_rom_sha256=CONTROL_SHA,floe_namespace_sha256=digest(raw))
    finally:
        for module,name,old in changed:setattr(module,name,old)
