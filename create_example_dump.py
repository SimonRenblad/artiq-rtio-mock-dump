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

def write_output(channel, f, n, address, typ):
    dump = b""
    msg_type = (channel << 2) + 0b00
    for i in range(n):
        d = f(i)
        if typ == float:
            d = cast_int(d)
        dump += struct.pack(">QIQQI", d, address, i, i, msg_type)
    return dump

def write_input(channel, f, n, address, typ):
    dump = b""
    msg_type = (channel << 2) + 0b01
    for i in range(n):
        d = f(i)
        if typ == float:
            d = cast_int(d)
        dump += struct.pack(">QIQQI", d, address, i, i, msg_type)
    return dump

def write_exception(channel, counter, exception_type):
    msg_type = (channel << 2) + 0b10
    fmt = ">" + 10*"x" + "BQ" + 9*"x" + "I"
    return struct.pack(fmt, exception_type.value, counter, msg_type) 

def write_stopped(counter):
    fmt = ">" + 11*"x" + "Q" + 9*"x" + "I"
    return struct.pack(fmt, counter, 0b11) 

def main():

    dump = write_output(8, lambda x: math.sin(x), 100, 23, float)

    dump += write_input(6, lambda x: x, 25, 23, int)
    
    dump += write_exception(9, 0, ExceptionType.o_underflow)

    dump += write_stopped(99)

    c = ord('E')
    sent_bytes = (100+25+2)*32
    total_byte_count = sent_bytes+15
    error_occurred = 0
    log_channel = 0
    dds_onehot_sel = 0

    header = struct.pack('>BIQbbb', c, sent_bytes, total_byte_count, error_occurred, log_channel, dds_onehot_sel)
    
    dump = header + dump

    with open("dump7.bin", "wb") as f:
        f.write(dump)

if __name__=="__main__":
    main()
