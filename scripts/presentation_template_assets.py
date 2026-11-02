"""Optional finite-template asset layout; the existing geometry stays immutable.

Original row/bear grids and logical pattern IDs are preserved. Floes use their
complete source-control programs instead of runtime primitive descriptors.
"""
import hashlib
import json
from pathlib import Path

from presentation_fragments import BankImage,GEOMETRY_BANKS,pack_descriptors
from presentation_static_assets import header_fragments,footer_tiles
from reference_traces import private_output

SHADOW_OFFSET=13*16384+0x2700


def logical(pointer):
    if len(pointer)!=3 or pointer[2]not in GEOMETRY_BANKS:raise ValueError('invalid asset bank pointer')
    address=int.from_bytes(bytes(pointer[:2]),'little')
    if not 0x8000<=address<0xC000:raise ValueError('asset pointer outside mapper window')
    return GEOMETRY_BANKS.index(pointer[2])*16384+address-0x8000


def legacy_grids(raw,metadata):
    records=[];groups={'row':[],'floe':[],'bear':[]}
    for family,variants in (('row',128),('bear',32)):
        for root in metadata['roots'][family]:
            position=logical(root)
            if position%16384+variants*2>16384 or position+variants*2>len(raw):raise ValueError('truncated/cross-bank legacy directory')
            group=[]
            for index in range(variants):
                code=int.from_bytes(raw[position+index*2:position+index*2+2],'little');kind,number=code>>12,code&4095
                if kind>=len(metadata['classes']):raise ValueError('legacy directory class outside metadata')
                cls=metadata['classes'][kind];stride=cls['columns']*cls['rows']*2;at=cls['offset']+number*stride
                if number>=cls['count'] or stride!=cls['stride'] or at+stride>len(raw):raise ValueError('invalid/truncated legacy grid')
                ids=tuple(int.from_bytes(raw[i:i+2],'little') for i in range(at,at+stride,2))
                if any(value>=metadata['patterns'] for value in ids):raise ValueError('legacy grid pattern outside original atlas')
                group.append(len(records));records.append({'columns':cls['columns'],'rows':cls['rows'],'patterns':ids})
            groups[family].append(group)
    return records,groups


def seal_shadow(prefix,payload):
    if len(prefix)>SHADOW_OFFSET or len(payload)!=6400:raise ValueError('asset/root collision or incomplete far shadow')
    return bytes(prefix)+bytes([255])*(SHADOW_OFFSET-len(prefix))+bytes(payload)


def floe_pool(compiled):
    blobs=compiled['files'];directory=blobs['template-index.bin'];records=blobs['template-keys.bin'];patterns=blobs['logical-patterns.bin'];used=set()
    if len(directory)!=compiled['template_count']*2 or len(patterns)!=compiled['patterns']*8:raise ValueError('complete logical floe input required')
    for index in range(compiled['template_count']):
        at=int.from_bytes(directory[index*2:index*2+2],'little')
        if at+2>len(records):raise ValueError('truncated floe record')
        count=records[at+1]
        if not 1<=count<=14 or at+2+count*2>len(records):raise ValueError('invalid floe record size')
        for pos in range(at+2,at+2+count*2,2):
            identifier=int.from_bytes(records[pos:pos+2],'little')
            if not 0<identifier<compiled['patterns'] or not any(patterns[identifier*8:identifier*8+8]):raise ValueError('invalid empty floe mask')
            used.add(identifier)
    mapping={identifier:index for index,identifier in enumerate(sorted(used))}
    return b''.join(patterns[identifier*8:identifier*8+8] for identifier in mapping),mapping


def pack(geometry_dir,compiled,rom,palette,contact_dir,out):
    sha=lambda data:hashlib.sha256(data).hexdigest()
    geometry_dir=Path(geometry_dir);contact_dir=Path(contact_dir);metadata=json.loads((geometry_dir/'geometry.json').read_text())
    if sha(rom)!=metadata['source_sha256'] or metadata['patterns']!=compiled['original_patterns']:raise ValueError('template and original geometry authorities differ')
    raw=bytearray();inputs={}
    for bank in metadata['physical_banks']:
        name=f'geometry-{bank:03d}.bin';blob=(geometry_dir/name).read_bytes()
        if len(blob)!=16384 or sha(blob)!=metadata['files'][name]:raise ValueError('original geometry bank changed')
        inputs[str((geometry_dir/name).resolve())]=sha(blob);raw.extend(blob)
    if metadata['physical_banks']!=list(GEOMETRY_BANKS[:len(metadata['physical_banks'])]):raise ValueError('original logical bank map differs')
    records,groups=legacy_grids(bytes(raw),metadata);image=BankImage(GEOMETRY_BANKS);sections={}
    def put(name,data,record=False,alignment=2):
        pointer=image.store(data,record=record,alignment=alignment)
        sections[name]={'offset':logical(pointer),'size':len(data),'pointer':list(pointer)}
        return logical(pointer)
    put('pattern_pairs',compiled['files']['pattern-pairs.bin'],alignment=4)
    put('pattern_halves',compiled['files']['pattern-halves.bin'],alignment=4)
    encoded=pack_descriptors(records,image);directories={};roots={family:[] for family in groups}
    for family,cases in groups.items():
        for group in cases:
            data=b''.join(encoded['ids'][index].to_bytes(2,'little') for index in group)
            if data not in directories:directories[data]=image.store(data,alignment=2)
            roots[family].append(list(directories[data]))
    # Keep the static constructor records whole, exactly as the old packer.
    footer=footer_tiles(rom,palette)
    for name,data,alignment in (('header',header_fragments(rom),8),('footer_tiles',b''.join(footer['tiles']),16),
        ('footer_names',b''.join(index.to_bytes(2,'little') for index in footer['descriptors']),2)):
        put(name,data,record=True,alignment=alignment)
    blobs=compiled['files'];source_keys=blobs['template-keys.bin'];source_index=blobs['template-index.bin']
    raw_floes,floe_ids=floe_pool(compiled)
    put('floe_patterns',raw_floes,alignment=8)
    new_index=bytearray();key_base=None;key_records=[]
    for index in range(compiled['template_count']):
        at=int.from_bytes(source_index[index*2:index*2+2],'little')
        if at+2>len(source_keys):raise ValueError('truncated source template')
        count=source_keys[at+1];data=source_keys[at:at+2+count*2]
        if not 1<=count<=14 or len(data)!=2+count*2:raise ValueError('incomplete complete-strip template')
        data=data[:2]+b''.join(floe_ids[int.from_bytes(data[pos:pos+2],'little')].to_bytes(2,'little') for pos in range(2,len(data),2))
        pointer=image.store(data,record=True,alignment=2);position=logical(pointer)
        if key_base is None:key_base=position
        offset=position-key_base
        if offset>=65536:raise ValueError('template record arena exceeds uint16 offsets')
        new_index.extend(offset.to_bytes(2,'little'));key_records.append((position,data))
    sections['template_keys']={'offset':key_base,'size':image.used_bytes-key_base,'records':compiled['template_count']}
    put('template_index',bytes(new_index))
    programs=blobs['template-names.bin']
    if len(programs)!=compiled['program_count']*30:raise ValueError('complete program dictionary required')
    put('template_names',b''.join(programs[i:i+30]+bytes(2) for i in range(0,len(programs),30)),alignment=32)
    roots_data=(contact_dir/'floe-roots.bin').read_bytes();base_data=(contact_dir/'floe-base.bin').read_bytes()
    if len(roots_data)!=4800 or len(base_data)!=1600:raise ValueError('complete far root/base directory required')
    prefix_used=image.used_bytes;sealed=seal_shadow(image.data,roots_data+base_data);image.data=bytearray(sealed)
    sections['contact_roots']={'offset':SHADOW_OFFSET,'size':4800,'pointer':[0,167,255]}
    sections['contact_base']={'offset':SHADOW_OFFSET+4800,'size':1600,'pointer':[192,185,255]}
    for position,data in key_records:
        if sealed[position:position+len(data)]!=data or position%16384+len(data)>16384:raise ValueError('persisted template key record crosses or differs')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);files={}
    for bank,blob in zip(GEOMETRY_BANKS,image.images()):
        name=f'assets-{bank:03d}.bin';(out/name).write_bytes(blob);files[name]=sha(blob)
    (out/'logical-patterns.bin').write_bytes(blobs['logical-patterns.bin'])
    (out/'floe-patterns.bin').write_bytes(raw_floes)
    (out/'floe-logical-ids.bin').write_bytes(b''.join(identifier.to_bytes(2,'little') for identifier in floe_ids))
    static=''.join(f'p_static_{name}_data EQU ${int.from_bytes(bytes(sections[name]["pointer"][:2]),"little"):04X}\np_static_{name}_bank EQU {sections[name]["pointer"][2]}\n' for name in ('header','footer_tiles','footer_names'))
    static+=f'p_static_footer_tile_count EQU {len(footer["tiles"])}\n';(out/'presentation_static.inc').write_text(static)
    assembly=''.join(f'p_template_{name}_offset EQU ${sections[name]["offset"]:06X}\n' for name in ('pattern_pairs','pattern_halves','floe_patterns','template_index','template_keys','template_names'))
    assembly+=f'p_template_pattern_count EQU {compiled["patterns"]}\np_template_half_count EQU {len(blobs["pattern-halves.bin"])//4}\np_template_floe_count EQU {len(floe_ids)}\np_template_delta_count EQU {len(compiled["deltas"])}\np_template_deltas:\n    DB '+','.join(map(str,compiled['deltas']))+'\n'
    (out/'presentation_template.inc').write_text(assembly)
    result={'source_sha256':sha(rom),'patterns':compiled['patterns'],'logical_pattern_bytes':len(blobs['logical-patterns.bin']),
        'pattern_encoding':'two uint16 half indices, then four-byte halves','classes':encoded['classes'],'roots':roots,'sections':sections,
        'used_bytes':len(sealed),'prefix_used_bytes':prefix_used,'remaining_before_shadow':SHADOW_OFFSET-prefix_used,'physical_banks':list(GEOMETRY_BANKS),
        'template_count':compiled['template_count'],'deltas':compiled['deltas'],'program_count':compiled['program_count'],'name_stride':32,
        'max_floe_slots':compiled['max_slots'],'floe_patterns':len(floe_ids),'floe_patterns_sha256':sha(raw_floes),'verified_row_bear_grids':len(records),'files':files,'input_files':inputs,
        'logical_patterns_sha256':sha(blobs['logical-patterns.bin']),
        'scope':'Finite-template packing only. Stable logical PGT IDs and full row/bear grids; complete original-control floe programs replace runtime floe primitive descriptors. Not native/frame/original-raster acceptance.'}
    (out/'assets.json').write_text(json.dumps(result,indent=2)+'\n');return result
