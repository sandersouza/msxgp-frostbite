"""Finite physical slot ownership for source primitives, not gameplay code.

Every pattern has a permanent role within one offscreen generation. Copies
share a role; source object/floe intersections have nine separate cell roles.
"""

COUNTS=(56,60,50)


def integer(value,low,high):
    if type(value)is not int or not low<=value<=high:raise ValueError('fixed-role argument outside declared domain')
    return value


def world_slot(role,source_row,grid_row,column,coarse,plane=None):
    integer(coarse,0,1);integer(source_row,0,3);integer(grid_row,0,2)
    if role=='bear':
        if source_row or plane is not None:raise ValueError('single source bear required')
        integer(column,0,3)
        return (0,grid_row*4+column) if grid_row<2 else (1,column)
    if role=='object':
        if plane is not None:raise ValueError('object cannot select a floe plane')
        integer(column,0,2);top=(153-source_row*26+coarse)//8
        rows=((153-source_row*26+coarse)%8+15)//8
        if grid_row>=rows:raise ValueError('object grid row outside source geometry')
        row=top+grid_row
        if source_row==0:return 2,3+grid_row*3+column
        if source_row==1:return (1,16+column) if row==15 else (2,column)
        return (1,10+grid_row*3+column) if source_row==2 else (1,4+grid_row*3+column)
    raise ValueError('unknown world role')


def floe_slot(source_row,index):
    integer(source_row,0,3);integer(index,0,15)
    bank,base=((2,25),(2,9),(1,35),(1,19))[source_row]
    return bank,base+index


def intern_floe(pool,key):
    if len(key)!=6:raise ValueError('whole exact floe constructor key required')
    key=bytes(key)
    if key not in pool:
        if len(pool)>=16:raise ValueError('source floe strip exceeds its16 fixed slots')
        pool[key]=len(pool)
    return pool[key]


def header_slot(row,column):
    integer(row,0,2);integer(column,5,14)
    return 0,8+row*10+column-5


def igloo_slot(row,column):
    integer(row,3,5);integer(column,22,27)
    return 0,38+(row-3)*6+column-22


def fused_slot(row,copy,column,coarse):
    integer(copy,0,2);integer(column,0,2);integer(coarse,0,1)
    if coarse and row==12 or not coarse and row==15:return 1,51+copy*3+column
    if not coarse and row==20:return 2,41+copy*3+column
    raise ValueError('fusion outside the original shared scanline bands')


def footer_name(page,index):
    integer(page,0,1);integer(index,0,21)
    return 160+page*22+index


def retain(slots,pair,tile):
    bank,identifier=pair;integer(bank,0,2);integer(identifier,0,255)
    if len(tile)!=16:raise ValueError('whole fixed-role pattern and colour tile required')
    if pair in slots and slots[pair]!=tile:raise ValueError(f'fixed role{pair} aliases different tile contents')
    slots[pair]=bytes(tile)
