"""Audit actual source contact components before compiling native tables.

The ordinary copy union below is a candidate until its independent alias gate
passes. It consumes original single-copy truth, never rasterized MSX graphics.
"""
import json
from pathlib import Path
import argparse

from environment import ROOT
from hazard_catalog import HELPERS,capture_plan,make_case,producer,validate_partitions
from reference_inventory import verified_input
from reference_provenance import audit_manifest
from reference_state import decode_state
from stella_hazard import HELPERS as OBSERVER_HELPERS,digest,validate_observation,verified_backend
from collision_compact import CompactRows,read_row
from floe_tables import pointer,verified_profiles as verified_floe_profiles
from floe_catalog import YS as FLOE_YS
from floe_tables import shadow_byte
from reference_traces import private_output
from reference_routes import source_reset_checkpoint


def validate_layout(manifest,rom):
    if (manifest.get('complete') is not True or manifest.get('exploratory') is not False
            or manifest.get('producer_dirty_at_start') is not False):
        raise ValueError('complete nonexploratory clean-start source component required')
    expected=capture_plan(manifest['kind'],rom)
    if any(manifest.get(key)!=value for key,value in expected.items()):
        raise ValueError('complete exact source component domain required')
    count=validate_partitions(manifest['partitions'],expected)
    if manifest.get('cases')!=count:raise ValueError('complete component count required')
    return count


def profile_record(plan,data,y,mode,coordinate):
    if len(data)!=plan['cases_per_player']*58:raise ValueError('complete original profile required')
    if type(mode) is not int or not 0<=mode<len(plan['modes']):raise ValueError('source mode outside captured domain')
    try:yi=plan['ys'].index(y);xi=plan['coordinates'].index(coordinate)
    except ValueError:raise ValueError('source coordinate outside captured domain') from None
    offset=((yi*len(plan['modes'])+mode)*len(plan['coordinates'])+xi)*58
    return data[offset:offset+58]


def copy_union(px,y,shape,reflection,nusiz,object_x,single):
    if nusiz not in range(4) or not 0<=px<160 or not 0<=object_x<160:
        raise ValueError('complete original copy coordinates required')
    offsets=((0,),(0,16),(0,32),(0,16,32))[nusiz];result=bytearray(58)
    for offset in offsets:
        dx=(px-object_x-offset)%160
        if dx>=153:dx-=160
        if not -7<=dx<=7:continue
        data=single(px,y,shape,reflection,dx)
        for index,value in enumerate(data):result[index]|=value
    return bytes(result)


def verified_profiles(root,*,exploratory=False):
    root=Path(root);manifest=json.loads((root/'catalog.json').read_text())
    rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if exploratory:
        expected=capture_plan(manifest['kind'],rom,manifest['player_x'])
        if any(manifest.get(key)!=value for key,value in expected.items()) or manifest.get('complete') is not True:
            raise ValueError('complete explicitly selected exploratory domain required')
        if manifest.get('exploratory') is not True:raise ValueError('explicit exploratory evidence required')
        count=validate_partitions(manifest['partitions'],expected)
        if manifest.get('cases')!=count:raise ValueError('exploratory count mismatch')
    else:count=validate_layout(manifest,rom)
    if manifest['source']!=verified_input(ROOT/'references/roms/frostbite.bin'):
        raise ValueError('source ROM identity mismatch')
    audit_manifest({'tool_source_commit':manifest['producer_commit'],'utility_fingerprints':manifest['helpers']},HELPERS)
    if manifest['helpers']!=producer():raise ValueError('current source reader differs from frozen capture helpers')
    backend=verified_backend(root/'stella')
    if (backend!=manifest['backend_build'] or backend.get('producer_dirty') is not False
            or digest(root/'stella')!=manifest['binary_sha256']
            or digest(root/'frostbite-hazard-observer.json')!=manifest['backend_build_sha256']):
        raise ValueError('frozen original observer identity mismatch')
    audit_manifest({'tool_source_commit':backend['producer_commit'],'utility_fingerprints':backend['helpers']},OBSERVER_HELPERS)
    initial=(root/'initial.state').read_bytes();base=decode_state(initial)['ram']
    prepared,preparation=source_reset_checkpoint(ROOT/'outputs/reference-traces/summary.json')
    if (digest(root/'initial.state')!=manifest['initial_sha256'] or initial!=prepared
            or manifest['preparation']!=preparation):raise ValueError('source preparation capsule changed')
    profiles={};receipts=0;global_workspaces=set();expected_helpers={key:manifest['helpers'][key] for key in OBSERVER_HELPERS}
    audited_commits=set()
    for part in manifest['partitions']:
        directory=root/f'worker-{part["start"]:03d}-{part["stop"]:03d}'
        if json.loads((directory/'partition.json').read_text())!=part:raise ValueError('partition receipt changed')
        xs=manifest['player_x'][part['start']:part['stop']]
        if set(part['profiles'])!={f'player-{px:03d}.truth' for px in xs}:raise ValueError('complete unique profile set required')
        for px in xs:
            path=directory/f'player-{px:03d}.truth'
            if digest(path)!=part['profiles'][path.name]:raise ValueError('raw source profile changed')
            data=path.read_bytes()
            if len(data)!=manifest['cases_per_player']*58:raise ValueError('partial original profile')
            profiles[px]=path
        expected={}
        entries=[(mode,x) for mode in range(len(manifest['modes'])) for x in manifest['coordinates']]
        for px in xs:
            for yi,y in enumerate(manifest['ys']):
                for offset in range(0,len(entries),8192):
                    name=(directory/f'px-{px:03d}-y-{yi:02d}-batch-{offset:05d}'/'observation.json').relative_to(root).as_posix()
                    expected[name]=(px,yi,offset,len(entries[offset:offset+8192]))
        if len(part['receipts'])!=len(expected) or {r['path'] for r in part['receipts']}!=set(expected):
            raise ValueError('complete unique bounded source observation receipts required')
        loaded_px=None;profile=None
        for receipt in part['receipts']:
            path=root/receipt['path'];px,yi,offset,n=expected[receipt['path']]
            if receipt!={'path':receipt['path'],'sha256':digest(path),'player_x':px,'y_index':yi,'offset':offset,'cases':n}:
                raise ValueError('source receipt identity or ordering changed')
            observed=json.loads(path.read_text());commit=observed['producer_commit']
            if commit not in audited_commits:
                audit_manifest({'tool_source_commit':commit,'utility_fingerprints':manifest['helpers']},HELPERS)
                audited_commits.add(commit)
            global_workspaces.add((commit,observed['producer_dirty']))
            if (observed['helpers']!=expected_helpers or observed['cases']!=n
                    or observed['mode']!=('shore ROI' if manifest['kind']=='shore' else 'top-object ROI')
                    or observed['backend_build']!=backend or observed['backend_build_sha256']!=manifest['backend_build_sha256']
                    or observed['backend']['binary_sha256']!=manifest['binary_sha256']):
                raise ValueError('batch producer/backend differs from frozen source closure')
            if set(observed['files'])!={'initial.state','cases.bin','results.bin','raw/stella.log'}:
                raise ValueError('complete source evidence files required')
            for name,sha in observed['files'].items():
                if digest(path.parent/name)!=sha:raise ValueError('raw source batch changed')
            if (path.parent/'initial.state').read_bytes()!=initial:raise ValueError('batch preparation capsule mismatch')
            raw=(path.parent/'results.bin').read_bytes();cases=(path.parent/'cases.bin').read_bytes()
            validate_observation(raw,(path.parent/'raw/stella.log').read_text(),n,True)
            if len(cases)!=n*128:raise ValueError('partial original geometry fixtures')
            if loaded_px!=px:profile=profiles[px].read_bytes();loaded_px=px
            for index,(mode,x) in enumerate(entries[offset:offset+n]):
                if cases[index*128:(index+1)*128]!=make_case(manifest,base,px,manifest['ys'][yi],mode,x):
                    raise ValueError('source case is not the declared component coordinate')
                start=(yi*len(entries)+offset+index)*58
                if raw[index*78:index*78+58]!=profile[start:start+58]:
                    raise ValueError('profile differs from raw original observation')
            receipts+=1
    report={'cases':count,'receipts':receipts,'manifest_sha256':digest(root/'catalog.json'),
            'observed_workspace_states':[{'commit':commit,'dirty':dirty} for commit,dirty in sorted(global_workspaces)]}
    return manifest,profiles,report


def read_bytes(banks,first,location,size):
    bank,address=location
    if not first<=bank<first+len(banks) or not 0x8000<=address or address+size>0xC000:
        raise ValueError('compiled contact pointer crosses a physical bank')
    result=bytes(banks[bank-first][address-0x8000:address-0x8000+size])
    if len(result)!=size:raise ValueError('compiled contact pointer crosses emitted data')
    return result


def compile_component(pool,plan,profiles):
    """Intern every original cell before packing any profile/directory pointers."""
    result={'plan':plan,'profiles':{},'examples':{},'active_y':set()};columns=len(plan['coordinates']);cache={bytes(58):0}
    if columns not in (15,160):raise ValueError('complete declared source coordinate row required')
    for px in plan['player_x']:
        source=profiles[px];data=source.read_bytes() if isinstance(source,Path) else bytes(source)
        if len(data)!=plan['cases_per_player']*58:raise ValueError('partial original component profile')
        modes=[[] for _ in plan['modes']]
        for yi,y in enumerate(plan['ys']):
            for mode in range(len(modes)):
                offset=(yi*len(modes)+mode)*columns*58;ids=[]
                for x in range(columns):
                    coordinate=(px+x)%160 if plan['kind']=='floe' else x
                    record=data[offset+coordinate*58:offset+(coordinate+1)*58]
                    if plan['kind']=='ordinary' and any(record[29:]):raise ValueError('ordinary copy basis has a nonzero independent shadow')
                    if record not in cache:cache[record]=pool.intern_record(record)
                    ids.append(cache[record])
                row=pool.intern_indices(ids+[0]*(160-columns));modes[mode].append(row)
                if any(ids):result['active_y'].add(y)
                result['examples'].setdefault(row,(px,yi,mode))
        result['profiles'][px]=modes
    return result


def emit_component(packed,compiled):
    modes=bytearray();plan=compiled['plan']
    for mode in range(len(plan['modes'])):
        players=bytearray()
        for px in plan['player_x']:
            ys=b''.join(pointer(packed.rows[row]) for row in compiled['profiles'][px][mode])
            players.extend(pointer(packed.put(ys)))
        modes.extend(pointer(packed.put(players)))
    return bytes(modes)


def verify_aliases(ordinary,aliases):
    """Compare the candidate to independently executed real NUSIZ source cases."""
    normal_plan,normal_paths,_=ordinary;alias_plan,alias_paths,_=aliases
    if normal_plan['kind']!='ordinary' or alias_plan['kind']!='aliases':raise ValueError('independent ordinary and actual-copy components required')
    shapes=normal_plan['shapes'];mode_index={(m['shape'],m['reflection']):i for i,m in enumerate(normal_plan['modes'])};checked=0
    for px in alias_plan['player_x']:
        basis=normal_paths[px].read_bytes();data=alias_paths[px].read_bytes()
        for yi,y in enumerate(alias_plan['ys']):
            def single(player,vertical,shape,reflection,dx):
                start=((yi*len(normal_plan['modes'])+mode_index[(shape,reflection)])*15+dx+7)*58
                return basis[start:start+58]
            for copies in range(4):
                for x in range(160):
                    shape=shapes[(px+y+x+copies)%len(shapes)];reflection=bool((px^x^y)&1)
                    start=((yi*4+copies)*160+x)*58
                    if copy_union(px,y,shape,reflection,copies,x,single)!=data[start:start+58]:
                        raise ValueError(f'original copy factorization rejected PX{px} Y{y} shape{shape} ref{reflection} NUSIZ{copies} X{x}')
                    checked+=1
    return {'cases':checked,'literal_views':228,'channels':2,'complete_geometry':True,
            'scope':'Actual original NUSIZ0..3 at every ordinary P0 X, object X and vertical window, with rotating original shapes/reflections; pattern-independent copy clocks additionally follow pinned Player/DrawCounterDecodes. Not an exhaustive Cartesian product of all shapes and counts.'}


def verify_packed_component(packed,compiled,profiles,directory):
    p=compiled['plan'];columns=len(p['coordinates']);checked=0
    for mode in range(len(p['modes'])):
        ptr=directory[mode*3:mode*3+3];players=read_bytes(packed.banks,14,(ptr[2],int.from_bytes(ptr[:2],'little')),len(p['player_x'])*3)
        for xi,px in enumerate(p['player_x']):
            ptr=players[xi*3:xi*3+3];ys=read_bytes(packed.banks,14,(ptr[2],int.from_bytes(ptr[:2],'little')),len(p['ys'])*3)
            expected=b''.join(pointer(packed.rows[row]) for row in compiled['profiles'][px][mode])
            if ys!=expected:raise ValueError('compiled profile directory differs from complete source rows')
    last_px=None;source=None
    for row,(px,yi,mode) in compiled['examples'].items():
        if px!=last_px:
            path=profiles[px];source=path.read_bytes() if isinstance(path,Path) else bytes(path);last_px=px
        offset=(yi*len(p['modes'])+mode)*columns*58
        for x in range(160):
            coordinate=(px+x)%160 if p['kind']=='floe' else x
            want=source[offset+coordinate*58:offset+(coordinate+1)*58] if x<columns else bytes(58)
            if read_row(packed.banks,packed.metadata,packed.rows[row],x)!=want:
                raise ValueError('physical compact bank decoder differs from raw original source')
            checked+=1
    return checked


def compile_catalog(floes,edge,ordinary,shore,aliases,out):
    components={};audits={}
    for kind,path in (('edge',edge),('ordinary',ordinary),('shore',shore),('aliases',aliases)):
        components[kind]=verified_profiles(path);audits[kind]=components[kind][2]
    alias=verify_aliases(components['ordinary'],components['aliases'])
    floe_manifest,floe_profiles=verified_floe_profiles(floes)
    fplan={'kind':'floe','player_x':list(range(160)),'ys':list(FLOE_YS),
           'modes':floe_manifest['controls'],'coordinates':list(range(160)),
           'cases_per_player':len(FLOE_YS)*len(floe_manifest['controls'])*160}
    pool=CompactRows();compiled={};profiles={'floe':floe_profiles}
    compiled['floe']=compile_component(pool,fplan,floe_profiles)
    for kind in ('edge','ordinary','shore'):
        plan,paths,_=components[kind];profiles[kind]=paths;compiled[kind]=compile_component(pool,plan,paths)
        if 0 in compiled[kind]['active_y']:raise ValueError('outside hazard sentinel is not zero; early zero return forbidden')
    packed=pool.emit(14);directories={kind:emit_component(packed,component) for kind,component in compiled.items()}
    queries={kind:verify_packed_component(packed,component,profiles[kind],directories[kind]) for kind,component in compiled.items()}
    controls=floe_manifest['controls'];floe_roots=bytearray();base=bytearray()
    for control in range(len(controls)):
        for px in range(160):
            floe_roots.extend(pointer(packed.put(b''.join(pointer(packed.rows[row]) for row in compiled['floe']['profiles'][px][control]))))
        for fx in range(160):
            start=(control*160+fx)*58;record=floe_profiles[0][start:start+58]
            if any(record[:29]):raise ValueError('outside floe sentinel contacts P0')
            value=shadow_byte(record[29:]);base.append(value|7)
            for px in range(1,160):
                if floe_profiles[px][start:start+58]!=record:raise ValueError('outside floe sentinel depends on P0 X')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    def blob(name,data):
        path=out/name;path.write_bytes(data);return f'    INCBIN "{path.resolve()}"'
    resident=[f'contact_record_bank EQU {packed.metadata["record_bank"]}',f'contact_block_bank EQU {packed.metadata["block_bank"]}',
              'floe_roots:',blob('floe-roots.bin',floe_roots),'floe_base:',blob('floe-base.bin',base),'    ALIGN 256','floe_control_index:']
    row_ys=compiled['edge']['active_y']|compiled['ordinary']['active_y'];shore_ys=compiled['shore']['active_y']
    resident[:0]=[f'hazard_row_min_y EQU {min(row_ys)}',f'hazard_row_max_y EQU {max(row_ys)}',
                  f'hazard_shore_min_y EQU {min(shore_ys)}',f'hazard_shore_max_y EQU {max(shore_ys)}']
    indices=bytearray([255]*256)
    for index,(a,b) in enumerate(controls):indices[a|(b>>4)]=index
    resident.append(blob('floe-controls.bin',indices));resident.append('floe_control_pointers:')
    for index in range(len(controls)):resident.append(f'    DW floe_roots+{index*480},floe_base+{index*160}')
    for kind in ('edge','ordinary','shore'):
        resident.extend((f'hazard_{kind}_modes:',blob(f'{kind}-modes.bin',directories[kind])))
    resident.append('    ALIGN 256');resident.append('hazard_shape_index:');shape_index=bytearray([255]*256)
    for index,shape in enumerate(components['edge'][0]['shapes']):shape_index[shape]=index
    resident.append(blob('hazard-shapes.bin',shape_index));resident.append('hazard_bear_index:')
    resident.append(blob('hazard-bear.bin',bytes(index*2 for index in components['shore'][0]['bear_pose_aliases'])))
    (out/'contact_resident.inc').write_text('\n'.join(resident)+'\n');bank_lines=[]
    for index,data in enumerate(packed.banks):
        bank_lines.extend(('    ORG $8000',blob(f'contacts-{index+14:03d}.bin',data+bytes([255])*(16384-len(data)))))
    (out/'contact_banks.inc').write_text('\n'.join(bank_lines)+'\n')
    result={'schema_version':1,'cases':sum(components[k][0]['cases'] for k in components)+floe_manifest['cases'],
            'components':audits,'floe_catalog_sha256':digest(Path(floes)/'catalog.json'),'aliases':alias,
            'codec':packed.metadata,'unique_records':len(pool.records),'unique_blocks':len(pool.blocks),'unique_rows':len(pool.rows),
            'active_y':{kind:sorted(value['active_y']) for kind,value in compiled.items()},
            'physical_leaf_queries':queries,'banks':len(packed.banks),'used_bytes':sum(len(data) for data in packed.banks),
            'resident_data_bytes':len(floe_roots)+len(base)+256+40+sum(len(directories[k]) for k in ('edge','ordinary','shore'))+264,
            'files':{path.name:digest(path) for path in out.iterdir() if path.is_file()}}
    (out/'tables.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('floes','edge','ordinary','shore','aliases','out'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();print(json.dumps(compile_catalog(**vars(args)),indent=2))
