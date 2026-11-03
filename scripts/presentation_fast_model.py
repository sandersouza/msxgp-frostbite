"""Sparse typed presentation constructors, never a native gameplay replacement."""
from collections import defaultdict
from functools import lru_cache,reduce
import hashlib
import json
from pathlib import Path

from graphics_mapping import map_x,map_y,palette_map
from original_graphics import view
from presentation_check import decode_target
from presentation_constructors import (mono_key,union_key,literal_key,header_key,igloo_key,footer_key,construct)
from presentation_fragments import background_tables,background_vram,mask_tiles
from presentation_model import describe
from presentation_static_assets import header_fragments,footer_tiles,igloo_mask


def combine_cell(layers,background,*,row,column,coarse):
    clip=column==2;roles=defaultdict(list)
    for layer in layers:
        mask=bytes(v&15 for v in layer['pattern']) if clip else layer['pattern']
        if any(mask):roles[layer['role']].append({**layer,'mask':mask})
    if not roles:return None
    if len(roles)==1:
        values=next(iter(roles.values()));colors={v['color'] for v in values}
        if len(colors)!=1:raise ValueError('one primitive family cannot change color within a tile')
        unique={v['id']:v for v in values};ids=sorted(unique);color=next(iter(colors))
        if len(ids)==1:return mono_key(ids[0],background,color,clip)
        if len(ids)==2 and set(roles)=={'floe'}:return union_key(*ids,color,clip)
        raise ValueError('unexpected source primitive overlap')
    if set(roles)!={'object','floe'}:raise ValueError('unexpected source layer intersection')
    kind=3 if coarse and row==12 else 1 if not coarse and row==20 else 2 if not coarse and row==15 else None
    if kind is None:raise ValueError('shared world cells must use their declared fixed rows')
    masks={}
    for role,values in roles.items():
        if len({v['color'] for v in values})!=1:raise ValueError('source row colors disagree')
        masks[role]=bytes(reduce(int.__or__,(v['mask'][y] for v in values),0) for y in range(8))
    obj,floe=masks['object'],masks['floe']
    wanted_obj={0} if kind==1 else {7} if kind==2 else {6,7}
    wanted_floe={7} if kind==1 else {0,1} if kind==2 else {0}
    if any(value for y,value in enumerate(obj) if y not in wanted_obj) or any(value for y,value in enumerate(floe) if y not in wanted_floe):
        raise ValueError('source primitive escaped its fused scanlines')
    values=(obj[0],floe[7],0) if kind==1 else (floe[0],floe[1],obj[7]) if kind==2 else (floe[0],obj[6],obj[7])
    return literal_key(values,roles['object'][0]['color'],roles['floe'][0]['color'],kind)


@lru_cache(maxsize=12000)
def geometry(bitmap,width,height,x,y):return mask_tiles(bitmap,width,height,x,y)


def prepare(rom,measured_palette,geometry_dir):
    geometry_dir=Path(geometry_dir);meta=json.loads((geometry_dir/'geometry.json').read_text());raw=bytearray()
    for bank in meta['physical_banks']:
        name=f'geometry-{bank:03d}.bin';data=(geometry_dir/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=meta['files'][name]:raise ValueError('geometry pattern pool changed')
        raw.extend(data)
    if hashlib.sha256(rom).hexdigest()!=meta['source_sha256']:raise ValueError('source/geometry identity differs')
    patterns=[bytes(raw[i:i+8]) for i in range(0,meta['pattern_bytes'],8)]
    colors=palette_map(measured_palette)
    if colors[6]!=14 or colors[144]!=4:raise ValueError('approved igloo/water palette contract changed')
    return {'rom':rom,'colors':colors,'patterns':patterns,'indices':{v:i for i,v in enumerate(patterns)},
            'background':background_tables(rom,measured_palette),'header':header_fragments(rom),'footer':footer_tiles(rom,measured_palette)}


def frame(tables,ram):
    rom=tables['rom'];colors=tables['colors'];vram=bytearray(background_vram(tables['background'],ram));base_names=bytes(vram[0x1800:0x1B00])
    if ram[0x3F]&128:return {'vram':bytes(vram),'keys':{},'counts':[0,0,0],'description':None}
    d=describe(rom,{'ram':ram});keys={};coarse=d['coarse_shift']
    def put(row,column,key):
        if (row,column) in keys:raise ValueError('sparse layers unexpectedly share a name cell')
        keys[row,column]=key
    glyph_id=lambda address:(address-0xFF00)//8 if address>=0xFF00 and (address&7)==0 else 32 if address==0xFF53 else 33 if address==0xFD6D else None
    score=[glyph_id(v['address']) for v in d['hud']['score']];status=[glyph_id(v['address']) for v in d['hud']['status']]
    if any(v is None for v in score+status):raise ValueError('header source glyph outside declared34')
    upper=colors[d['hud']['score'][0]['color']];lower=colors[d['hud']['status'][0]['color']];sky=colors[d['background'][10]]
    columns=((0,0,0),(0,1,1),(1,0,2),(1,2,3),(2,3,1),(3,0,2),(3,4,3),(4,5,1),(5,0,2),(5,0,4))
    for band in range(3):
        for col,(first,second,kind) in enumerate(columns,5):
            ids=(score[first],score[second],status[first],status[second])
            put(band,col,header_key(ids,upper,lower,sky,kind,band))
    for row,upper_byte,lower_byte in ((3,0,ram[0x44]),(4,ram[0x43],ram[0x42]),(5,ram[0x41],ram[0x40])):
        for column in range(6):
            top,bottom=igloo_mask(upper_byte,column),igloo_mask(lower_byte,column)
            if top or bottom:put(row,column+22,igloo_key(top,bottom,base_names[row*32+column+22]))
    phase=d['footer']['phase'];program=tables['footer']
    for index,identifier in enumerate(program['descriptors'][(phase*2+coarse)*22:(phase*2+coarse+1)*22]):
        if identifier:put(22+index//11,4+index%11,footer_key(identifier))
    layers=defaultdict(list)
    def add(bitmap,width,height,x,y,color,role):
        x%=160;compiled=geometry(bytes(bitmap),width,height,x%16,y%8);left=map_x(x)//8;top=y//8
        for index,pattern in enumerate(compiled['patterns']):
            if not any(pattern):continue
            row=top+index//compiled['columns'];column=left+index%compiled['columns']
            if column>=31:column-=30
            if column in (0,1) or not 0<=row<24:continue
            identifier=tables['indices'].get(pattern)
            if identifier is None:raise ValueError('primitive pattern missing from full finite atlas')
            layers[row,column].append({'role':role,'id':identifier,'pattern':pattern,'color':colors[color]})
    bear=d['bear'];image=view(rom,bear['address'],19,bear['reflect'],2)['pixels']
    add(image+image[-16:],16,20,bear['x'],51+coarse,bear['color'],'bear')
    for obj in d['objects']:
        if colors[obj['color']]==4:continue
        image=view(rom,obj['address'],8,obj['reflect'])['pixels']
        add(image,8,8,obj['x'],obj['y']-7+coarse,obj['color'],'object')
    signed=lambda v:(v>>4)-16 if v&128 else v>>4
    delta=4+signed(ram[0x1C])-signed(ram[0x1D]);motion=[0]
    for y in range(1,7):motion.append(motion[-1]-signed(rom[0xDD2+7-y]))
    for row in range(4):
        color=ram[0x2B+row]&254
        if colors[color]==4:continue
        first=(ram[0x1F+row]-signed(ram[0x1C]))%160
        for copy in (0,32,64):
            for offset,size in ((0,8+delta),) if 0<=delta<=8 else ((0,8),(delta,8)):
                width=size+8;bitmap=bytearray(width*7)
                for y,dx in enumerate(motion):bitmap[y*width+8+dx:y*width+8+dx+size]=bytes((1,))*size
                add(bitmap,width,7,(first+copy+offset-8)%160,167-row*26+coarse,color,'floe')
    for (row,column),values in layers.items():
        key=combine_cell(values,base_names[row*32+column],row=row,column=column,coarse=bool(coarse))
        if key is not None:put(row,column,key)
    resident=[{} for _ in range(3)]
    for (row,column),key in sorted(keys.items()):
        bank=row//8;cache=resident[bank]
        if key not in cache:
            if len(cache)>=64:raise ValueError(f'sparse constructor bank{bank} exceeds64 slots')
            backgrounds={identifier:bytes(vram[bank*2048+identifier*8:bank*2048+identifier*8+8]+vram[0x2000+bank*2048+identifier*8:0x2000+bank*2048+identifier*8+8]) for identifier in set(base_names[row*32:row*32+32])}
            tile=construct(key,patterns=tables['patterns'],backgrounds=backgrounds,header=tables['header'],footer=program['tiles'])
            identifier=len(cache);cache[key]=identifier
            vram[bank*2048+identifier*8:bank*2048+identifier*8+8]=tile[:8]
            vram[0x2000+bank*2048+identifier*8:0x2000+bank*2048+identifier*8+8]=tile[8:]
        vram[0x1800+row*32+column]=cache[key]
    return {'vram':bytes(vram),'keys':keys,'counts':[len(v) for v in resident],'description':d}


def full_pixels(tables,rendered):
    result=bytearray(decode_target(rendered['vram'],bytes((2,0xC2,6,255,3,0x36,7,1))));d=rendered['description']
    if d is None:return bytes(result)
    rom=tables['rom'];colors=tables['colors']
    def point(x,y,color,unblank=False):
        x%=160;ty=map_y(y)
        if ty is None or x<8 and not unblank:return
        for tx in range(map_x(x),map_x(x+1)):result[ty*256+tx]=colors[color]
    def command(item):
        image=view(rom,item['address'],item['height'],item.get('reflect',False))
        for i,bit in enumerate(image['pixels']):
            if bit:point(item['x']+i%image['width'],item['y']+i//image['width'],item['color'])
    for item in d['door']:command(item)
    player=d['player']
    for row in player['rows']:
        for dx in range(8):
            x=(player['x']+dx)%160;bit=dx if player['reflect'] else 7-dx
            pattern=row['prefix_pattern'] if x<row['update_x'] else row['pattern']
            color=row['prefix_color'] if x<row['color_update_x'] else row['color']
            if x>=row['suffix_x']:color=row['suffix_color']
            if pattern&(1<<bit):point(x,row['y']+int(d['coarse_shift'] and row['y']>=57),color)
            if d['coarse_shift'] and row['y']==56 and row['pattern']&(1<<bit):point(x,57,row['color'],True)
    for item in d['footer']['logo']:command(item)
    return bytes(result)
