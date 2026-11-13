"""Exact32-byte temperature packets with one contiguous padded bottom stream."""
from presentation_temperature_programs import pack_program

def burst_program(old,pair):
    if len(old)!=32 or type(pair)is not int or not 0<=pair<=255:raise ValueError('one bounded original temperature packet required')
    if bytes(old)!=pack_program(bytes(old[:24]),pair>>4,pair&15):raise ValueError('original font/key identity changed')
    middle=bytes(old[i]for i in(0,8,16));bottom=b''.join(bytes(old[i+1:i+8])+bytes(1)for i in(0,8,16))
    return middle+bottom+bytes((pair,0,0,0,0))

def burst_table(old):
    if len(old)!=8192:raise ValueError('all256 original32-byte programs required')
    return b''.join(burst_program(old[i*32:(i+1)*32],i)for i in range(256))
