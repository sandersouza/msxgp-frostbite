"""Opt-in source-store observers over the frozen native lowering pipeline.

Default generators are unchanged. Instrument actual decoded bus stores, never
high-level sound events; pure canonical indexed stores need no observer. The
existing zero-clear summary receives its complete ordered audio side effects.
"""
import native_fast
import native_write_loop
from native_codegen import mapped

STORES=frozenset(('STA','STX','STY'))
RMW=frozenset(('INC','DEC','ASL','LSR','ROL','ROR'))


def canonical_indexed(item,facts):
    return item['mode']=='zpx' and 128<=item['value']<=255 and bool(facts['x']) and max(facts['x'])+item['value']<256


def audio_address(address):
    target=mapped(address,True)
    return int(target[1:],16) if target.startswith('$') and 0xC715<=int(target[1:],16)<=0xC71A else None


def store_observer(item,facts):
    op=item['mnemonic'];mode=item['mode'];value=item['value']
    if op not in STORES:
        if op in RMW and mode!='acc':
            if mode in ('zpg','abs'):
                if audio_address(value)is not None:raise ValueError('source audio read-modify-write needs both original bus writes')
            elif not canonical_indexed(item,facts):
                indices=facts['x'] if mode in ('zpx','abx') else facts.get('y',range(256))
                mask=255 if mode in ('zpx','zpy') else 65535
                for index in indices:
                    try:target=audio_address((value+index)&mask)
                    except ValueError:continue  # existing generator owns invalid/ROM address rejection
                    if target is not None:raise ValueError('indexed source audio read-modify-write is not an audited lowering')
        return None
    if mode in ('zpg','abs'):
        address=audio_address(value)
        return None if address is None else f'p_audio_event_{address-0xC700:02X}'
    if canonical_indexed(item,facts):return None
    if mode not in ('zpx','zpy','abx','aby'):raise ValueError('unsupported original store addressing mode')
    return 'p_audio_event_indexed'


def clear_events(start):
    if type(start)is not int or not 0<=start<=255:raise ValueError('source clear entry X must be a byte')
    return tuple((reg,0) for alias in (0,64) for reg in range(21,27) if start<=alias+reg)


def generate(rom,carry_fusion=True):
    previous=native_fast.translate_fast
    def observed(item,facts,**options):
        code=previous(item,facts,**options);observer=store_observer(item,facts)
        return code+([f'call {observer}'] if observer else [])
    try:
        native_fast.translate_fast=observed
        code=native_write_loop.generate(rom,carry_fusion=carry_fusion)
    finally:native_fast.translate_fast=previous
    if '    call core_clear\n'not in code:raise ValueError('audited original clear summary boundary missing')
    return code.replace('    call core_clear\n','    call p_audio_core_clear\n')
