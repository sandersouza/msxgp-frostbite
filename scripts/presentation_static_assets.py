"""Small source-derived header fragments and finite footer tile programs."""
import hashlib
import json
from pathlib import Path

from graphics_mapping import map_frame
from presentation_fragments import BankImage,GEOMETRY_BANKS
from reference_traces import private_output
from original_graphics import view
from presentation_model import background_rows,footer
from presentation_sprites import expand_pair


def header_fragments(rom):
    if len(rom)!=4096:raise ValueError('whole original ROM required')
    result=bytearray()
    for glyph in range(34):
        address=0xF00+glyph*8 if glyph<32 else 0xF53 if glyph==32 else 0xD6D
        rows=rom[address:address+8][::-1]
        for shift,column in ((1,0),(1,1),(5,0),(5,1),(5,2)):
            for row in rows:
                expanded=int.from_bytes(expand_pair(row,0),'big')<<8
                result.append((expanded>>shift>>(16-column*8))&255)
    return bytes(result)


def igloo_mask(bits,column):
    if type(bits)is not int or not 0<=bits<=255 or type(column)is not int or not 0<=column<6:raise ValueError('PF1 byte and igloo column required')
    index=(0,1,2,4,5,6)[column];pair=(bits>>index)&3
    first=(252,240,192)[column%3];second=first^255
    return (first if pair&1 else 0)|(second if pair&2 else 0)


def tile(pixels,background):
    if len(pixels)!=64 or len(background)!=64:raise ValueError('whole final/background tile required')
    patterns=bytearray();colors=bytearray()
    for y in range(8):
        row=pixels[y*8:y*8+8];bg=background[y*8]
        if any(c!=bg for c in background[y*8:y*8+8]):raise ValueError('footer background must be flat within each row')
        foreground={c for c in row if c!=bg}
        if len(foreground)>1:raise ValueError('footer needs more than two colors in one row')
        fg=next(iter(foreground)) if foreground else bg
        patterns.append(sum(128>>x for x,c in enumerate(row) if c==fg));colors.append(fg*16+bg)
    return bytes(patterns+colors)


def decode_tile(data):
    if len(data)!=16:raise ValueError('whole tile required')
    return bytes((data[y+8]>>(4 if data[y]&(128>>x) else 0))&15 for y in range(8) for x in range(8))


def footer_tiles(rom,measured_palette):
    if len(rom)!=4096 or set(measured_palette)!=set(range(0,256,2)):raise ValueError('whole ROM and measured palette required')
    tiles=[bytes((255,))*8+bytes((17,))*8];indices={tiles[0]:0};descriptors=[];backgrounds=[]
    for phase in range(8):
        for coarse in (0,1):
            ram=[0]*128;ram[0x46]=12+phase;ram[0x68]=150 if coarse else 140
            rows=background_rows(rom,ram)
            if coarse:rows[57:]=rows[56:209]
            source=bytearray(33600)
            for y,color in enumerate(rows):source[y*160+8:y*160+160]=bytes((color,))*152
            if coarse:source[57*160:57*160+8]=bytes((rows[56],))*8
            base=map_frame(source,measured_palette);commands=footer(rom,ram)
            for command in commands['prefix']:
                glyph=view(rom,command['address'],command['height'])
                for index,bit in enumerate(glyph['pixels']):
                    if bit:source[(command['y']+index//8)*160+command['x']+index%8]=command['color']
            for command in commands['playfield']+commands['ball']:
                y=command['y'];x=command['x'];source[y*160+x:y*160+x+command['width']]=bytes((command['color'],))*command['width']
            final=map_frame(source,measured_palette);bg_tiles=[]
            for ty in (22,23):
                for tx in range(4,15):
                    def block(image):return b''.join(image[(ty*8+y)*256+tx*8:(ty*8+y)*256+tx*8+8] for y in range(8))
                    before=block(base);after=block(final)
                    if tx==4:bg_tiles.append(tile(before,before))
                    if before==after:descriptors.append(0);continue
                    packed=tile(after,before)
                    if packed not in indices:indices[packed]=len(tiles);tiles.append(packed)
                    descriptors.append(indices[packed])
            backgrounds.append(bg_tiles)
    return {'tiles':tiles,'descriptors':descriptors,'backgrounds':backgrounds,'rows':2,'columns':11,'x':4,'y':22,'states':16}


def decode_footer(package,phase,coarse):
    if not 0<=phase<8 or coarse not in (0,1):raise ValueError('footer phase and coarse state required')
    state=phase*2+coarse;image=bytearray(88*16)
    for number,identifier in enumerate(package['descriptors'][state*22:(state+1)*22]):
        data=package['tiles'][identifier] if identifier else package['backgrounds'][state][number//11]
        pixels=decode_tile(data);tx=number%11;ty=number//11
        for y in range(8):image[(ty*8+y)*88+tx*8:(ty*8+y)*88+tx*8+8]=pixels[y*8:y*8+8]
    return bytes(image)


def pack_static(rom,measured_palette,geometry_dir,geometry,out):
    """Append tiny independent records, retaining every existing geometry byte."""
    sha=lambda data:hashlib.sha256(data).hexdigest()
    if sha(rom)!=geometry['source_sha256']:raise ValueError('geometry and static tables use different source ROMs')
    banks=geometry['physical_banks'];used=geometry['used_bytes'];geometry_dir=Path(geometry_dir)
    if banks!=list(GEOMETRY_BANKS[:len(banks)]) or not 0<used<=len(banks)*16384 or (used+16383)//16384!=len(banks):
        raise ValueError('complete prefix of the declared geometry bank map required')
    original=bytearray();inputs={}
    for bank in banks:
        name=f'geometry-{bank:03d}.bin';data=(geometry_dir/name).read_bytes()
        if len(data)!=16384 or sha(data)!=geometry['files'][name]:raise ValueError('geometry bank identity changed')
        original.extend(data);inputs[name]=sha(data)
    if any(value!=255 for value in original[used:]):raise ValueError('geometry tail is not unused padding')
    image=BankImage(GEOMETRY_BANKS);image.data=original[:used];sections={}
    program=footer_tiles(rom,measured_palette)
    payloads={'header':header_fragments(rom),'footer_tiles':b''.join(program['tiles']),
              'footer_names':b''.join(index.to_bytes(2,'little') for index in program['descriptors'])}
    for name,data in payloads.items():
        pointer=image.store(data,record=True,alignment=16 if name=='footer_tiles' else 8 if name=='header' else 2)
        offset=GEOMETRY_BANKS.index(pointer[2])*16384+int.from_bytes(pointer[:2],'little')-0x8000
        sections[name]={'pointer':list(pointer),'size':len(data),'offset':offset}
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);files={}
    for bank,data in zip(GEOMETRY_BANKS,image.images()):
        path=out/f'assets-{bank:03d}.bin';path.write_bytes(data);files[path.name]=sha(data)
    persisted=b''.join((out/f'assets-{bank:03d}.bin').read_bytes() for bank in GEOMETRY_BANKS[:len(image.images())])
    if persisted[:used]!=original[:used]:raise ValueError('static packing modified geometry')
    for name,section in sections.items():
        if persisted[section['offset']:section['offset']+section['size']]!=payloads[name]:raise ValueError('persisted static record changed')
    if any(sha((geometry_dir/name).read_bytes())!=value for name,value in inputs.items()):raise ValueError('geometry changed during static packing')
    assembly=''.join(f'p_static_{name}_data EQU ${int.from_bytes(bytes(section["pointer"][:2]),"little"):04X}\np_static_{name}_bank EQU {section["pointer"][2]}\n' for name,section in sections.items())
    assembly+=f'p_static_footer_tile_count EQU {len(program["tiles"])}\n'
    (out/'presentation_static.inc').write_text(assembly)
    result={'source_sha256':sha(rom),'geometry_used_bytes':used,'used_bytes':image.used_bytes,
            'physical_banks':list(GEOMETRY_BANKS[:len(image.images())]),'sections':sections,'files':files,
            'header_glyphs':34,'footer_tiles':len(program['tiles']),'footer_states':16,
            'scope':'Finite presentation fragments only; unchanged geometry prefix, no prerecorded whole frames or gameplay'}
    (out/'static.json').write_text(json.dumps(result,indent=2)+'\n');return result
