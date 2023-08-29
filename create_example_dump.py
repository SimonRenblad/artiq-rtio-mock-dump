# Intended to create an exhaustive mock binary trace dump from the core ARTIQ analyzer

import struct
import math
from enum import Enum

class ExceptionType(Enum):
    legacy_reset = 0b000000
    legacy_reset_falling = 0b000001
    legacy_reset_phy = 0b000010
    legacy_reset_phy_falling = 0b000011
    legacy_o_underflow_reset = 0b010000
    legacy_o_sequence_error_reset = 0b010001
    legacy_o_collision_reset = 0b010010
    legacy_i_overflow_reset = 0b100000
    legacy_o_sequence_error = 0b010101

    o_underflow = 0b010100

    i_overflow = 0b100001

def cast_int(d):
    return struct.unpack('>Q', struct.pack('>d', d))[0]

def write_output(channel, value, time, address):
    dump = b""
    msg_type = (channel << 2) + 0b00
    dump += struct.pack(">QIQQI", value, address, time, time, msg_type)
    return dump

def write_input(channel, value, time, address):
    dump = b""
    msg_type = (channel << 2) + 0b01
    dump += struct.pack(">QIQQI", value, address, time, time, msg_type)
    return dump

def write_exception(channel, counter, exception_type):
    msg_type = (channel << 2) + 0b10
    fmt = ">" + 11*"x" + "BQ" + 8*"x" + "I"
    return struct.pack(fmt, exception_type.value, counter, msg_type) 

def write_stopped(counter):
    fmt = ">" + 12*"x" + "Q" + 8*"x" + "I"
    return struct.pack(fmt, counter, 0b11)

# Need additional cast to handle 1 bit, 16 bit 32 bit and flagging messages
# This is TODO for tomorrow
def cast_ttl(i): # can only be 0 n 1
    return i

def cast_ttl_clock_gen(i, ref_period): # is it an int.. yes
    return int(i * ref_period * (2**24))

def dds_multi_freq_cast(i, sys_clk):
    i = int(i / sys_clk * 2**32)
    y = i >> 16
    x = i & 0xffff
    return x, y

def dds_pow_cast(i):
    return int(i * 2**16)

def spi2_cast_config(chip_sel, div, length, flags):
    data = chip_sel << 24
    data += div << 16
    data += length << 8
    data += flags
    return data

def spi2_cast(i):
    return i

def write_log(channel, value, time, address):
    dump = b'' 
    i = 0
    while i < len(value): 
        sub = value[i:i+4]
        k = 0
        for c in sub:
            k <<= 8
            k += ord(c)
        dump += write_output(channel, k, time, address) 
        i += 4
    return dump

def main():

    # write TTL
    dump = write_input(0, cast_ttl(0), 1, 0)
    dump += write_input(0, cast_ttl(1), 2, 0)
    dump += write_output(1, cast_ttl(0), 3, 0)
    dump += write_output(1, cast_ttl(1), 4, 0)
    dump += write_output(1, cast_ttl(0), 5, 1) # should create an X -> np.nan
    dump += write_output(1, cast_ttl(1), 6, 1)
    dump += write_output(1, cast_ttl(0), 7, 0)

    # write TTL Clock Gen
    dump += write_output(2, cast_ttl_clock_gen(1e-9, 3e9), 1, 0)
    dump += write_output(2, cast_ttl_clock_gen(1e-6, 3e9), 2, 0)

    # write DDS # TODO improve this
    dump += write_output(27, 0x4, 1, 0x81)
    a, b = dds_multi_freq_cast(1, 3e9)
    dump += write_output(27, a, 2, 0x11)
    dump += write_output(27, b, 3, 0x13)
    dump += write_output(27, dds_pow_cast(5), 4, 0x31)
    dump += write_output(27, 0, 5, 0x80)
    dump += write_output(27, a, 6, 0x11)
    dump += write_output(27, b, 7, 0x13)
    dump += write_output(27, 0, 8, 0x80)

    # write SPI2
    dump += write_output(3, spi2_cast_config(1, 2, 3, 4), 0, 1)
    dump += write_output(3, 2345, 1, 0)
    dump += write_output(3, 432, 2, 0)
    for i in range(100000):
        dump += write_output(3, i % 100, i + 3, 0)

    # write log
    dump += write_log(30, "log\x1Ehead\x1D", 1, 0)

    c = ord('E')
    sent_bytes = len(dump)
    total_byte_count = sent_bytes+15
    error_occurred = 0
    log_channel = 30
    dds_onehot_sel = 1

    header = struct.pack('>BIQbbb', c, sent_bytes, total_byte_count, error_occurred, log_channel, dds_onehot_sel)
    
    dump = header + dump

    with open("dump11.bin", "wb") as f:
        f.write(dump)

if __name__=="__main__":
    main()
