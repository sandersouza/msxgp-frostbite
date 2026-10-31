"""Structural Stella7.0 DEBUGGER/NTSC/4K/joystick state contract.

Source contract: stella d55b1aec0d067a4c901a6dcdf81cb8f579685659.
Complete TIA fields/bytes are retained; this is not a TIA simulation.
"""
import hashlib
import sys
from source_timing import Reader, STATE_HEADER


def fields(reader, schema):
    result = {}
    sizes = {'B': 1, 'H': 2, 'I': 4, 'Q': 8}
    for descriptor in schema.split():
        name, kind = descriptor.split(':')
        if kind == '?': result[name] = reader.boolean()
        elif kind == 'd': result[name] = reader.take(8).hex()
        else: result[name] = reader.number(sizes[kind])
    return result


def analog_connection(reader):
    result = fields(reader, 'type:I resistance:I')
    if result['type'] not in (0, 1, 2):
        raise ValueError('invalid controller analog connection')
    return result


def decode_state(data):
    if sys.byteorder != 'little' or len(data) > 4 * 1024 * 1024:
        raise ValueError('unsupported byte order or oversized state')
    r = Reader(data)
    if r.number(4) != len(STATE_HEADER) or r.take(len(STATE_HEADER)) != STATE_HEADER:
        raise ValueError('unsupported Stella7 state header')
    result = fields(r, 'cycles:Q data_bus:B')
    cpu_offset = r.position
    cpu = fields(r, 'a:B x:B y:B sp:B ir:B pc:H n:? v:? b:? d:? i:? not_z:? c:? execution:B')
    cpu['p'] = (0x20 | (cpu['n'] << 7) | (cpu['v'] << 6) | (cpu['b'] << 4)
                | (cpu['d'] << 3) | (cpu['i'] << 2) | ((not cpu['not_z']) << 1) | cpu['c'])
    counter_offset = r.position
    cpu.update(fields(r, 'distinct_accesses:I last_address:H last_peek:H last_poke:H data_poke:H '
                     'source_s:I source_a:I source_x:I source_y:I flags:B halt:? last_break:Q'))
    result['cpu'] = cpu
    ram_offset = r.position
    result['ram'] = list(r.take(128))
    result['riot'] = fields(r, 'timer:I subtimer:I divider:I wrapped:? last_cycle:Q set_cycle:Q '
                            'timer_reads:I ddra:B ddrb:B out_a:B out_b:B interrupt:B edge_positive:? '
                            'out_timer0:B out_timer1:B out_timer2:B out_timer3:B')
    tia_start = r.position
    if r.number(4) != 16:
        raise ValueError('unsupported TIA delay queue size')
    queue = []
    for _ in range(16):
        count = r.number(1)
        if count > 16: raise ValueError('invalid TIA delay queue count')
        queue.append([list(r.take(2)) for _ in range(count)])
    cursor = r.number(1)
    indices = list(r.take(255))
    if cursor >= 16 or any(index >= 16 and index != 255 for index in indices):
        raise ValueError('invalid TIA delay queue cursor/index')
    frame = fields(r, 'rendering:? vsync:? vblank:? current_lines:I last_lines:I previous_lines:I total:I layout:I')
    if frame['layout'] not in (0, 1): raise ValueError('unsupported TIA frame layout')
    frame['jitter'] = fields(r, 'sensitivity:I recovery:I y_start:I last_scanlines:I last_vsync:I unstable:I jitter:I')
    frame.update(fields(r, 'state:I line:I vsync_lines:I y:I last_y:I vblank_lines:I frame_lines:I '
                        'height:I y_start:I vcenter:I max_vcenter:I size_adjust:I jitter_enabled:?'))
    tia = {'queue': queue, 'queue_cursor': cursor, 'queue_indices': indices, 'frame': frame}
    tia['background'] = fields(r, 'color:B object_color:B debug_color:B debug:?')
    tia['playfield'] = fields(r, 'collision:I disabled_mask:I enabled_mask:I suppressed:? '
        'left_color:B right_color:B p0_color:B p1_color:B object_color:B debug_color:B debug:? color_mode:B '
        'score_glitch:? pattern:I effective_pattern:I refp:? reflected:? pf0:B pf1:B pf2:B x:I')
    tia['missiles'] = [fields(r, 'collision:I disabled_mask:I enabled_mask:I enabled:? suppressed:? enam:? '
        'resmp:B motion_clocks:B counter:B moving:? width:B effective_width:B visible:? rendering:? '
        'render_counter:B copy:B decode_offset:B color:B object_color:B debug_color:B debug:? inverted:?') for _ in range(2)]
    tia['players'] = [fields(r, 'collision:I disabled_mask:I enabled_mask:I color:B object_color:B debug_color:B '
        'debug:? suppressed:? motion_clocks:B counter:B moving:? rendering:? render_counter:B render_trip:B '
        'copy:B divider:B divider_pending:B sample_counter:B divider_change:B decode_offset:B old_pattern:B '
        'new_pattern:B pattern:B reflected:? delaying:? inverted:?') for _ in range(2)]
    tia['ball'] = fields(r, 'collision:I disabled_mask:I enabled_mask:I color:B object_color:B debug_color:B '
        'debug:? old_enabled:? new_enabled:? enabled:? suppressed:? delaying:? signal:? motion_clocks:B '
        'counter:B moving:? width:B effective_width:B last_tick:B rendering:? render_counter:B inverted:?')
    audio = fields(r, 'counter:B')
    audio['channels'] = [fields(r, 'control:B frequency:B volume:B clock:? feedback:? bit4:? hold:? '
                              'divider:B pulse:B noise:B') for _ in range(2)]
    audio.update(fields(r, 'sum0:I sum1:I count:I sample_bytes:Q'))
    if audio['sample_bytes'] > 1024 * 1024: raise ValueError('oversized TIA audio sample queue')
    audio['samples'] = r.take(audio['sample_bytes']).hex()
    tia['audio'] = audio
    tia['analog'] = []
    for _ in range(4):
        analog = fields(r, 'threshold:d charge:d')
        analog['connection'] = analog_connection(r)
        analog.update(fields(r, 'timestamp:Q console_timing:I clock:d dumped:?'))
        tia['analog'].append(analog)
    tia['inputs'] = [fields(r, 'latched_mode:? value:B') for _ in range(2)]
    tia.update(fields(r, 'hstate:I hcounter:I hdelta:I render_start:I collision_update:? collision_scheduled:? '
        'collision_mask:I movement_clock:I moving:? extended_blank:? lines_unchanged:I priority:I subclock:B '
        'last_cycle:Q sprite_bits:B collision_bits:B blank_color:B timestamp:Q'))
    tia['shadow_registers'] = list(r.take(64))
    tia.update(fields(r, 'frame_start:Q frame_wsync:Q framebuffer_lines:I frontbuffer_lines:I '
                        'pf_delay:B pf_color_delay:B background_delay:B swap_delay:B'))
    tia_end = r.position
    result['tia_bytes'] = data[tia_start:tia_end].hex()
    result['tia'] = tia
    if r.number(4) != 0: raise ValueError('state does not describe plain4K bank offset0')
    rng_offset = r.position
    result['host_rng'] = r.number(4)
    result['controllers'] = []
    for _ in range(2):
        result['controllers'].append({'digital': [r.boolean() for _ in range(5)],
                                      'analog': [analog_connection(r) for _ in range(2)]})
    result['switches'] = r.number(1)
    if r.position != len(data): raise ValueError('unexpected trailing Stella state content')
    result['_offsets'] = {'cpu': cpu_offset, 'counter': counter_offset, 'ram': ram_offset, 'rng': rng_offset}
    result['state_sha256'] = hashlib.sha256(data).hexdigest()
    return result


def freeze_poweron(data, seed):
    state = decode_state(data)
    if state['cycles'] != 0 or state['cpu']['pc'] != 0xF000 or state['tia']['frame']['total'] != 0:
        raise ValueError('seed capsule must be at verified power-on PCF000/cycle0/frame0')
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise ValueError('host seed must be uint32')
    raw = bytearray(data)
    counter, rng = state['_offsets']['counter'], state['_offsets']['rng']
    raw[counter:counter+4] = bytes(4)
    raw[rng:rng+4] = seed.to_bytes(4, 'little')
    decode_state(bytes(raw))
    return bytes(raw)
