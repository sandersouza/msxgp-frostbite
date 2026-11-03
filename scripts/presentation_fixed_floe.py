"""Whole seven-line floe strips, including unions between slanted copies."""
from collections import defaultdict

from graphics_mapping import map_x
from presentation_build import flat_water_ids
from presentation_fast_model import geometry,combine_cell
from presentation_fixed import intern_floe,integer,floe_pair


def strip(tables,root,delta,y,color,source_row=0):
    integer(root,0,159);integer(delta,-11,19);integer(y,0,185);integer(color,1,15);integer(source_row,0,3)
    rom=tables['rom'];water=flat_water_ids(tables['background']);motion=[0]
    signed=lambda v:(v>>4)-16 if v&128 else v>>4
    for line in range(1,7):motion.append(motion[-1]-signed(rom[0xDD2+7-line]))
    layers=defaultdict(list)
    for copy,offset in enumerate((0,32,64)):
        planes=((None,0,8+delta),) if 0<=delta<=8 else ((0,0,8),(1,delta,8))
        for plane,shift,size in planes:
            width=size+8;bitmap=bytearray(width*7)
            for line,dx in enumerate(motion):bitmap[line*width+8+dx:line*width+8+dx+size]=bytes([1])*size
            x=(root+offset+shift-8)%160;compiled=geometry(bytes(bitmap),width,7,x%16,y%8);left=map_x(x)//8;top=y//8
            for index,pattern in enumerate(compiled['patterns']):
                if not any(pattern):continue
                grid_row,grid_col=divmod(index,compiled['columns']);row=top+grid_row;column=left+grid_col
                if column>=31:column-=30
                if column in (0,1):continue
                identifier=tables['indices'].get(pattern)
                if identifier is None:raise ValueError('floe strip pattern absent from the complete finite atlas')
                layers[row,column].append({'role':'floe','id':identifier,'pattern':pattern,'color':color,
                    'source_row':source_row,'copy':copy,'grid_row':grid_row,'grid_col':grid_col,'plane':plane})
    pool={};program={};pairs={}
    for (row,column),values in sorted(layers.items()):
        key=combine_cell(values,water[row//8],row=row,column=3,coarse=False)
        pair=floe_pair(key,water[row//8],color)
        if pair in pairs and pairs[pair]!=key:raise ValueError('pair identity aliases different complete floe keys')
        pairs[pair]=key
        program[row,column]=(key,intern_floe(pool,key))
    return {'layers':layers,'program':program,'keys':pool,'pairs':pairs}
