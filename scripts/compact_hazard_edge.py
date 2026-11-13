"""Analytic ordinary/shore source-clock masks, unlinked from the game."""
from functools import lru_cache

from compact_floe import enemy_mask

OFFSETS=((0,),(0,16),(0,32),(0,16,32))


def ordinary_context(player_x,object_x,copies):
    if (any(type(v) is not int or not 0<=v<160 for v in (player_x,object_x))
            or type(copies) is not int or not 0<=copies<4):
        raise ValueError('complete source coordinates and NUSIZ0..3 required')
    offsets=OFFSETS[copies]
    def distance(px):
        for offset in offsets:
            value=(px-object_x-offset)%160
            if value>=153:value-=160
            if -7<=value<=7:return value+7
        return 255
    point=next(((8-object_x-offset)%160 for offset in offsets
                if (8-object_x-offset)%160<8),255)
    return distance(player_x),distance(0),point,player_x


def align_clock_byte(value,player_x):
    if player_x<=8:return value<<player_x&255
    if player_x>=153:return value>>(160-player_x)
    return 0


def clip_player(player_x,last_limit=159):
    return sum(128>>bit for bit in range(8) if 8<=player_x+bit<=last_limit)


def _row_masks(clock,after_always,after_different,player_x,visible):
    before=align_clock_byte(clock,player_x)
    if player_x==0 and after_always:before|=1
    equal=1<<player_x if after_always and 1<=player_x<8 else 0
    different=1<<(player_x-1) if (after_always or after_different) and 1<=player_x<=8 else 0
    return before,equal,different,align_clock_byte(clock&224,player_x),visible


def ordinary_program(glyph,context):
    if len(glyph)!=8 or len(context)!=4:
        raise ValueError('complete enemy glyph and horizontal context required')
    visible_distance,clock_distance,sample,px=context
    if (any(type(v) is not int or v not in (*range(15),255) for v in (visible_distance,clock_distance))
            or type(sample) is not int or sample not in (*range(8),255)
            or type(px) is not int or not 0<=px<160):
        raise ValueError('qualified distance indices, next sample and player X required')
    old=0;rows=[]
    for row in range(8):
        new=glyph[7-row]
        clock=enemy_mask(old,clock_distance-7) if clock_distance!=255 else 0
        event=sample!=255 and old!=new
        on=bool(new&(128>>sample)) if event else bool(clock&1)
        visible=enemy_mask(new,visible_distance-7) if visible_distance!=255 else 0
        visible&=clip_player(px,24 if row==7 else 159)
        rows.append(_row_masks(clock,on and event,on,px,visible));old=new
    return tuple(rows)


@lru_cache(None)
def expanded_bear_byte(value):
    if type(value) is not int or not 0<=value<=255:
        raise ValueError('source byte required')
    return sum(3<<(14-bit*2) for bit in range(8) if value&(128>>bit))


def wide_mask(value,player_x,body_x):
    if any(type(v) is not int or not 0<=v<160 for v in (player_x,body_x)):
        raise ValueError('complete player/body coordinates required')
    distance=(player_x-body_x)%160
    if distance>=153:distance-=160
    pattern=expanded_bear_byte(value)
    if not -7<=distance<16:return 0
    return ((pattern<<distance if distance>=0 else pattern>>-distance)>>8)&255


def bear_position(bear_x):
    if type(bear_x) is not int or not 0<=bear_x<160:
        raise ValueError('source bear coordinate required')
    body=(bear_x+(6 if bear_x<15 else 1))%160
    clocks=14-bear_x%15
    return body,clocks,(body-8+clocks)%160


def _wide_clock_window(value,left):
    distance=(-left)%160
    if distance>=145:distance-=160
    if not -15<=distance<16:return 0
    pattern=expanded_bear_byte(value)
    return (pattern<<distance if distance>=0 else pattern>>-distance)&65535


def shore_program(glyph,player_x,bear_x):
    if len(glyph)!=19 or any(glyph[:2]) or type(player_x) is not int or not 0<=player_x<160:
        raise ValueError('qualified19-byte bear glyph with blank final rows and complete player X required')
    body,clocks,initial=bear_position(bear_x)
    old=0;rows=[];clip=clip_player(player_x)
    for row in range(18):
        new=glyph[18-row]
        visible=wide_mask(new,player_x,body)&clip
        if row==0:
            window=_wide_clock_window(new,initial)
            selector=1<<(15-min(12,clocks))
            selector|=sum(1<<(15-clock) for clock in range(12,clocks))
            after=bool(window&selector)
            rows.append(_row_masks(0,after,False,player_x,visible))
        else:
            clock=wide_mask(old,0,body)
            sample=(8-body)%160
            event=sample<16 and old!=new
            on=bool(new&(128>>(sample//2))) if event else bool(clock&1)
            rows.append(_row_masks(clock,on and event,on,player_x,visible))
        old=new
    return tuple(rows)
