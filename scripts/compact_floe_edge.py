"""Bounded analytic HMOVE-edge masks; isolated from the default game.

Regular clocks X8..159 use the qualified floe footprints. The hidden clocks
retain the source's stopped-counter samples, delayed GRP/ENAM writes and
whole-byte equality gates. No original ROM bytes are embedded here.
"""
from functools import lru_cache

from compact_floe import build_assets, literal_atoms
from stella_floe import control_pairs


def active_rectangle(q):
    q %= 160
    return q < 72 and q % 32 < 8


@lru_cache(None)
def rectangle_window(q):
    if type(q) is not int or not 0 <= q < 160:
        raise ValueError('source counter0..159 required')
    return sum(active_rectangle(q+i) << i for i in range(16))


def held_window(q, clocks):
    if type(clocks) is not int or not 0 <= clocks <= 15:
        raise ValueError('motion clocks0..15 required')
    seq = rectangle_window(q)
    low = (1 << clocks) - 1
    sample = clocks-1 if clocks else 0
    return seq & low | ((65535 ^ low) if seq & (1 << sample) else 0)


def player_mask(sequence, player_x):
    if type(sequence) is not int or not 0 <= sequence <= 65535 or type(player_x) is not int or not 0 <= player_x < 160:
        raise ValueError('16-clock sequence and complete player X required')
    result = 0
    for clock in range(8):
        bit = (clock-player_x) % 160
        if sequence & (1 << clock) and bit < 8:
            result |= 128 >> bit
    return result


def visible_player_mask(player_x):
    if type(player_x) is not int or not 0 <= player_x < 160:
        raise ValueError('complete player X required')
    return sum(128 >> bit for bit in range(8) if 8 <= player_x+bit < 160)


def edge_row_masks(counter_p1, counter_m1, clocks_p1, clocks_m1, player_x, row):
    """Return old, old-if-equal, new-if-different and final-glyph masks.

    Rows0..6 are the ice body; row7 is its clearing/latch-read line. The first
    three masks apply when the current player tag is0..18. The last applies
    only when that tag is-1 and the preceding row still holds glyph byte0.
    """
    if (any(type(v) is not int or not 0 <= v < 160 for v in (counter_p1,counter_m1,player_x))
            or any(type(v) is not int or not 0 <= v <= 15 for v in (clocks_p1,clocks_m1))
            or type(row) is not int or not 0 <= row < 8):
        raise ValueError('complete counter, motion, player-X and row domains required')
    sp = held_window((counter_p1-2) % 160,clocks_p1)
    sm = held_window((counter_m1-1) % 160,clocks_m1)
    maximum = max(8,clocks_p1,clocks_m1)
    if row == 0:
        before = exiting = 0
        # GRP applies atH64 before motion clock12. ENAM applies atH73,
        # after the final possible motion clock14. Both can sample P0's
        # conditional held value after its eight clocks have stopped.
        after = bool(active_rectangle(counter_p1+min(12,clocks_p1)-2)
                     or sp & (((1 << clocks_p1)-1) & 0x7000) or sm & 0x4000)
        after_ne = False
    elif row == 7:
        # ENAM clears atH19, after clock0. GRP clears atH37/H73.
        before = sp & 255 | sm & 1
        exiting = sp & 63 | sm & 1
        after = False
        after_ne = bool(sp & 128) and not active_rectangle(counter_p1+8-2)
    else:
        seq = sp | sm
        before = seq & ((1 << min(12,maximum))-1)
        exiting = seq & 7
        after = bool(seq & ((1 << maximum)-1) & 0x7000)
        after_ne = bool(seq & 0x1000)
    old = player_mask(before,player_x)
    if player_x < 8 and (before & 0xF00 or player_x == 0 and after):
        old |= 128 >> (7-player_x)
    equal = 128 >> (7-player_x) if after and 1 <= player_x < 8 else 0
    different = 128 >> (8-player_x) if (after or after_ne) and 1 <= player_x <= 8 else 0
    return old,equal,different,player_mask(exiting,player_x)


def compile_edge_rows(control,motion_clocks,player_x,floe_x):
    if (len(control) != 2 or any(type(k) is not int or not 0 <= k <= 15 for k in control)
            or len(motion_clocks) != 6 or any(type(k) is not int or not 0 <= k <= 15 for k in motion_clocks)
            or type(floe_x) is not int or not 0 <= floe_x < 160):
        raise ValueError('two first-row clocks, six body clocks and floe X required')
    cp,cm = (2-floe_x) % 160,(-3-floe_x) % 160
    result = []
    for row in range(8):
        kp,km = control if row == 0 else (8,8) if row == 7 else (motion_clocks[row-1],)*2
        result.append(edge_row_masks(cp,cm,kp,km,player_x,row))
        cp,cm = (cp+kp-8) % 160,(cm+km-8) % 160
    return tuple(result)


def edge_convolve(glyph,footprint,control,motion_clocks,player_x,floe_x,y,*,reflect=False):
    if len(glyph) != 19 or len(footprint) != 7 or type(y) is not int or y not in (0,*range(45,78)):
        raise ValueError('complete glyph, footprint and declared source Y required')
    rows = compile_edge_rows(control,motion_clocks,player_x,floe_x)
    if not y:
        return False
    if reflect:
        glyph = bytes(int(f'{b:08b}'[::-1],2) for b in glyph)
    visible = visible_player_mask(player_x)
    for row,(old_mask,equal_mask,different_mask,exit_mask) in enumerate(rows):
        tag = y-50-row
        if tag == -1:
            if glyph[0] & exit_mask:
                return True
        elif 0 <= tag < 19:
            old = glyph[tag+1] if tag < 18 else 0
            new = glyph[tag]
            if old & old_mask or (old & equal_mask if old == new else new & different_mask):
                return True
            if row < 7 and new & footprint[row] & visible:
                return True
    return False


def build_edge_assets(original,oracle):
    assets,base_proof = build_assets(original,oracle)
    control_clocks = tuple(tuple((v >> 4)^8 for v in pair) for pair in control_pairs(original))
    motion = tuple((original[0xDD2+7-row] >> 4)^8 for row in range(1,7))
    atoms = literal_atoms(assets['glyphs'],assets['bases'])
    ys = (0,*range(45,78))
    all_views = (1 << 228)-1
    all_cells = (1 << (228*34))-1
    planes = {}
    valid,exiting,equal = {},{},{}
    for row in range(-1,8):
        planes[row] = tuple(sum((atoms[y-50-row][bit] if y and 0 <= y-50-row < 19 else 0) << (yi*228)
                                for yi,y in enumerate(ys)) for bit in range(8))
        valid[row] = sum(all_views << (yi*228) for yi,y in enumerate(ys) if y and 0 <= y-50-row < 19)
        exiting[row] = sum(all_views << (yi*228) for yi,y in enumerate(ys) if y and y-50-row == -1)
        if row >= 0:
            eq = all_cells
            for a,b in zip(planes[row-1],planes[row]):
                eq &= ~(a ^ b)
            equal[row] = eq
    columns = 0
    for control,pair in enumerate(control_clocks):
        for px in (*range(9),*range(154,160)):
            rows = [oracle.row(control,px,yi) for yi in range(34)]
            clip = visible_player_mask(px)
            for fx in range(160):
                dx = (fx-px) % 160
                group = assets['directory'][control*160+dx]
                footprint = assets['footprints'][group*7:group*7+7]
                predicted = 0
                for row,(before,eq,ne,exit_mask) in enumerate(compile_edge_rows(pair,motion,px,fx)):
                    for bit in range(8):
                        flag = 128 >> bit
                        old,new = planes[row-1][bit],planes[row][bit]
                        if before & flag:
                            predicted |= old & valid[row]
                        if eq & flag:
                            predicted |= old & equal[row] & valid[row]
                        if ne & flag:
                            predicted |= new & ~equal[row] & valid[row]
                        if exit_mask & flag:
                            predicted |= old & exiting[row]
                        if row < 7 and footprint[row] & clip & flag:
                            predicted |= new
                actual = sum(oracle.records[row[dx]][0] << (yi*228) for yi,row in enumerate(rows))
                if predicted != actual:
                    raise ValueError(f'analytic edge differs at {control}/{px}/{fx}')
                columns += 1
    assets.update(edge_windows=b''.join(rectangle_window(q).to_bytes(2,'little') for q in range(160)),
                  edge_low_masks=b''.join(((1 << k)-1).to_bytes(2,'little') for k in range(16)),
                  edge_bits=b''.join((1 << (k-1 if k else 0)).to_bytes(2,'little') for k in range(16)),
                  edge_control_clocks=bytes(k for pair in control_clocks for k in pair),
                  edge_motion_clocks=bytes(motion))
    return assets,dict(complete=True,edge_columns=columns,edge_cells=columns*34,literal_views=228,
        source_y=[45,77],outside_y_sentinel=0,edge_player_x=[*range(9),*range(154,160)],
        interior_proof=base_proof,sizes={k:len(v) for k,v in assets.items()},
        scope='Host proof of all declared floe edge cells and clipped visible footprints; no native kernel or whole-game integration proof.')
