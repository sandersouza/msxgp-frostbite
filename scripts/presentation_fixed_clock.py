"""Fixed-clock contracts independent of rendering cadence."""


def map_ram_page0(primary,expanded,secondary):
    if any(type(x)is not int or not 0<=x<256 for x in (primary,secondary)) or type(expanded)is not bool:
        raise ValueError('explicit primary/secondary slot register bytes required')
    return (primary&252)|(primary>>6),((secondary&252)|(secondary>>6)) if expanded else secondary


def admit_commit(ready,tick,last):
    if type(ready)is not bool or any(type(x)is not int or not 0<=x<65536 for x in (tick,last)):
        raise ValueError('ready flag and uint16 VBlank counters required')
    return ready and ((tick-last)&65535)>=2


def ram_code(meta,rom):
    import hashlib
    record=meta['fixed_clock'];size=record['ram_code_bytes']
    at=115*16384+0x3800;code=rom[at:at+size]
    if not 0<size<=1792 or hashlib.sha256(code).hexdigest()!=record['ram_code_sha256']:
        raise ValueError('fixed-clock RAM image differs')
    return code


def declare_ram(text,code,fail):
    read='debug read_block memory 0xE880 0xAC0'
    write='debug write_block memory 0xE880 [string repeat [binary format c 165] 0xAC0]'
    if text.count(read)!=1 or text.count(write)!=1 or text.count('0xAC0')!=3 or not 0<len(code)<=1792:
        raise ValueError('unrecognized Q guard or oversized fixed-clock kernel')
    check=f'if {{[debug read_block memory 0xE900 {len(code)}] ne [binary format H* {code.hex()}]}} {{{fail} ram-code}}\n    '
    text=text.replace('if {['+read,check+'if {['+read,1)
    text=text.replace(read,'debug read_block memory 0xF080 0x280').replace(write,
        'debug write_block memory 0xF080 [string repeat [binary format c 165] 0x280]').replace('0xAC0','0x280')
    source='[debug read_block memory 0xC000 128] ne $::ram'
    if text.count(source)!=1:raise ValueError('missing controlled source guard')
    return text.replace(source,source+' || [debug read_block memory 0xF000 128] ne $::ram',1)
