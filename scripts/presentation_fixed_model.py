"""Host proof of permanent primitive slots and shared source copy templates."""
from collections import defaultdict

from graphics_mapping import map_x
from original_graphics import view
from presentation_constructors import construct
from presentation_fast_model import frame as sparse_frame,geometry,combine_cell,prepare,full_pixels
from presentation_fixed import COUNTS,world_slot,floe_slot,intern_floe,header_slot,igloo_slot,fused_slot,footer_name,retain
from presentation_fixed_floe import strip
from presentation_fragments import background_vram


def frame(tables,ram):
    sparse=sparse_frame(tables,ram);description=sparse['description']
    vram=bytearray(background_vram(tables['background'],ram));names=bytes(vram[0x1800:0x1B00])
    slots={};keys={};footer_count=0
    if description is None:return {'vram':bytes(vram),'description':None,'counts':[0,0,0],'footer_count':0,'keys':{}}
    rom=tables['rom'];colors=tables['colors'];coarse=int(description['coarse_shift'])
    backgrounds=[{128+i:tables['background']['patterns'][bank][i*8:i*8+8]+tables['background']['colors'][bank][i*8:i*8+8]
        for i in range(tables['background']['tiles_per_bank'][bank])} for bank in range(3)]
    def put(row,column,key,pair):
        bank,identifier=pair
        if bank!=row//8 or (row,column)in keys:raise ValueError('fixed role belongs to the wrong bank or repeats a cell')
        tile=construct(key,patterns=tables['patterns'],backgrounds=backgrounds[bank],header=tables['header'],footer=tables['footer']['tiles'])
        retain(slots,pair,tile);keys[row,column]=key
        vram[bank*2048+identifier*8:bank*2048+identifier*8+8]=tile[:8]
        vram[0x2000+bank*2048+identifier*8:0x2000+bank*2048+identifier*8+8]=tile[8:]
        vram[0x1800+row*32+column]=identifier
    for (row,column),key in sparse['keys'].items():
        if row<3:put(row,column,key,header_slot(row,column))
        elif row<6:put(row,column,key,igloo_slot(row,column))
        elif row>=22:
            index=(row-22)*11+column-4
            put(row,column,key,(2,footer_name(0,index)));footer_count+=1
    layers=defaultdict(list)
    def add(bitmap,width,height,x,y,color,role,source_row,copy,plane=None):
        x%=160;compiled=geometry(bytes(bitmap),width,height,x%16,y%8);left=map_x(x)//8;top=y//8
        for index,pattern in enumerate(compiled['patterns']):
            if not any(pattern):continue
            grid_row,grid_col=divmod(index,compiled['columns']);row=top+grid_row;column=left+grid_col
            if column>=31:column-=30
            if column in (0,1) or not 0<=row<24:continue
            identifier=tables['indices'].get(pattern)
            if identifier is None:raise ValueError('fixed role lacks its finite original-derived pattern')
            layers[row,column].append({'role':role,'id':identifier,'pattern':pattern,'color':colors[color],
                'source_row':source_row,'copy':copy,'grid_row':grid_row,'grid_col':grid_col,'plane':plane})
    bear=description['bear'];image=view(rom,bear['address'],19,bear['reflect'],2)['pixels']
    add(image+image[-16:],16,20,bear['x'],51+coarse,bear['color'],'bear',0,0)
    copies=[0]*4
    for obj in description['objects']:
        source_row=obj['row'];copy=copies[source_row];copies[source_row]+=1
        if colors[obj['color']]==4:continue
        image=view(rom,obj['address'],8,obj['reflect'])['pixels']
        add(image,8,8,obj['x'],obj['y']-7+coarse,obj['color'],'object',source_row,copy)
    signed=lambda v:(v>>4)-16 if v&128 else v>>4
    delta=4+signed(ram[0x1C])-signed(ram[0x1D]);floe_owners={};floe_counts=[0]*4
    for source_row in range(4):
        color=ram[0x2B+source_row]&254
        if colors[color]==4:continue
        first=(ram[0x1F+source_row]-signed(ram[0x1C]))%160
        rendered=strip(tables,first,delta,167-source_row*26+coarse,colors[color],source_row)
        floe_counts[source_row]=len(rendered['keys'])
        for cell,values in rendered['layers'].items():layers[cell].extend(values)
        for cell,(key,index) in rendered['program'].items():floe_owners[cell]=floe_slot(source_row,index)
    for (row,column),values in layers.items():
        # The seven existing black HMOVE sprites cover x16..19 throughout
        # rows64..175. Those bank1/2 pixels need no separately clipped role.
        key=combine_cell(values,names[row*32+column],row=row,column=column if row<8 else 3,coarse=bool(coarse))
        if key is None:continue
        roles={value['role'] for value in values}
        if roles=={'object','floe'}:
            obj=next(v for v in values if v['role']=='object')
            pair=fused_slot(row,obj['copy'],obj['grid_col'],coarse)
        elif roles=={'floe'}:pair=floe_owners[row,column]
        else:
            if len(roles)!=1:raise ValueError('unexpected fixed-role intersection')
            if len({v['copy'] for v in values})!=1:raise ValueError(f'different source copies share tile{row,column}: {[(v["role"],v["copy"],v["plane"],v["grid_row"],v["grid_col"]) for v in values]}')
            owner=max(values,key=lambda v:-1 if v['plane']is None else v['plane'])
            pair=world_slot(owner['role'],owner['source_row'],owner['grid_row'],owner['grid_col'],coarse,owner['plane'])
        put(row,column,key,pair)
    counts=[sum(1 for b,identifier in slots if b==bank and identifier<64) for bank in range(3)]
    if any(value>limit for value,limit in zip(counts,COUNTS)):raise ValueError('fixed roles exceed their declared physical slots')
    return {'vram':bytes(vram),'description':description,'counts':counts,'footer_count':footer_count,'keys':keys,
        'floe_slots_used':floe_counts}
