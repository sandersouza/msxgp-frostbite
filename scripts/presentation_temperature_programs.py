"""Exact three-column lower-header programs for a temperature-unit change."""
def lower_key(old_middle,first,second):
    if not(0<=old_middle<256 and 0<=first<16 and 0<=second<64):raise ValueError('header key outside byte domain')
    high=(first<<4)&240;tail=((second<<2)|(first>>4))&255
    return (old_middle&15)|high,tail,high,tail


def pack_program(patterns,tens,units):
    if len(patterns)!=24 or not(0<=tens<16 and 0<=units<16):raise ValueError('three streams and two font nibbles required')
    keys=bytes((tens<<4,units<<2,units<<4,0,units<<4,128))
    return bytes(patterns)+keys+bytes(2)


def compile_programs(source,dictionary):
    from presentation_header_dictionary import compile_dictionary,project_pair
    actual,sections=compile_dictionary(source)
    if actual!=dictionary:raise ValueError('live header dictionary differs from authoritative source')
    offsets={r['name']:r['offset']for r in sections};result=[];checks=0
    for tens in range(16):
        for units in range(16):
            offsets3=(offsets['regular_pair_1']+(tens*16+units)*8,offsets['single_2']+units*8,offsets['lower_temp_icon']+units*8)
            patterns=b''.join(dictionary[o:o+8]for o in offsets3)
            expected=b''.join((project_pair(source,tens,units,1),project_pair(source,units,0,2),project_pair(source,units,32,3)))
            if patterns!=expected:raise ValueError('source temperature stream differs')
            result.append(pack_program(patterns,tens,units));checks+=3
    return b''.join(result),dict(programs=256,bytes=8192,source_stream_checks=checks,domain='hy_first=0,hy_color=0,hy_up=0,hy_lo=14; font nibbles0..15; original fallback otherwise')
