"""Opt-in native presentation gain at four verified original volume stores.

Original latches and CPU state stay unchanged. The requested amplitude factor
1.25 is quantized to the nearest static PSG level: 4 -> 5 (sqrt(2) nominal).
Silence is unchanged. No other source writer inherits this presentation gain.
"""
from pathlib import Path
from native_flat_asm import link_functions, split_functions
from environment import ROOT

SITES = {0xF4D7: 0, 0xF4D9: 1, 0xF7F0: 0, 0xF7F2: 1}


def project_volume(pc, raw):
    level = raw & 15
    return 5 if pc in SITES and level == 4 else level


def project_write(source, previous, pc, address):
    from presentation_audio import psg_step, OWNED_REGISTERS
    state = psg_step(source, previous)
    psg = bytearray(state['psg'])
    psg[8:10] = previous['psg'][8:10]
    if address in (25, 26):
        channel = address-25
        psg[8+channel] = project_volume(pc, source[4+channel])
    state['psg'] = bytes(psg)
    state['writes'] = tuple((r,psg[r]) for r in OWNED_REGISTERS if psg[r] != previous['psg'][r])
    return state


def install(layout, image, symbols, out, patch, spare):
    body = (ROOT/'src/native_effect_gain.asm').read_text()
    names = ('p_audio_event_done', 'p_audio_apply_19', 'p_audio_apply_1A',
             'p_audio_noise', 'p_audio_write_changed', 'p_audio_volume')
    pre = ''.join(f'{n} EQU ${symbols[n]:04X}\n' for n in names)
    entries = ('neg_event_0','neg_event_1','neg_apply_0','neg_apply_1',
               'neg_filter_0','neg_filter_1','neg_project')
    _, functions = split_functions(body, entries, 'neg_end')
    for channel in (0, 1):
        start = symbols[f'p_audio_apply_{25+channel:02X}']
        if image[start:start+2] != b'\xe6\x0f':
            raise ValueError('original masked volume handler entry required')
        layout.objects[f'code/neg_apply_{channel}'] = dict(address=start,size=18,alignment=1)
    first,last = spare
    if last-first != 35 or bytes(image[first:last]) != bytes(35):
        raise ValueError('exact zero-filled selected sparse-bear tail required')
    if any(first < row['address']+row['size'] and row['address'] < last
           for row in layout.objects.values()):
        raise ValueError('sparse-bear tail overlaps an allocated object')
    layout.objects['code/neg_project'] = dict(address=first,size=29,alignment=1)
    syms = link_functions(layout, out, functions, pre)
    for pc, channel in SITES.items():
        start = symbols[f'core_{pc:04X}']
        # Actual lowered STA preserves original A in B and writes the source bus.
        # Locate only within this one source instruction, never scan mixed ROM.
        end = symbols[f'core_{pc+2:04X}']
        needle = b'\xcd'+symbols[f'p_audio_event_{25+channel:02X}'].to_bytes(2,'little')
        block = bytes(image[start:end])
        if block.count(needle) != 1:
            raise ValueError('unique selected source volume observer required')
        site = start+block.index(needle)
        patch(site+1, syms[f'neg_event_{channel}'].to_bytes(2,'little'),
              f'selective presentation gain for original store {pc:04X}')
    return {n:v for n,v in syms.items() if n.startswith('neg_')}
