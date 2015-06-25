#!/usr/bin/env python

# Written by Ilias Giechaskiel
# https://ilias.giechaskiel.com
# June 2015

class ErrorCode:
    NO_ERROR  = 0
    TOO_SHORT = 2
    TOO_LONG  = 3
    ENCODING  = 4
    INTERNAL  = 5
    WRONG_DUR = 6
    GENERAL   = 7


class PulseLength:
    FULL = 9.44
    ZERO  = 3.00
    HALF  = FULL/2
    ZERO_REM = FULL - ZERO
    ONE_REM = HALF - ZERO
    ONE_HALF = FULL + HALF


class CRC:        
    CRC_14443_A = 0x6363
    CRC_14443_B	= 0xFFFF

    @staticmethod
    def calculate_crc(data, cktp=CRC_14443_A):
        wcrc = cktp
        for b in data:               
            b = b ^ (wcrc & 0xFF)
            b = b ^ (b << 4) & 0xFF
            wcrc = ((wcrc >> 8) ^ (b << 8) ^ (b << 3) ^ (b >> 4))
        
        if (cktp == CRC.CRC_14443_B):
            wcrc = ~wcrc

        return [wcrc & 0xFF, (wcrc >> 8) & 0xFF]

    @staticmethod
    def check_crc(data, cktp=CRC_14443_A):
        crc = CRC.calculate_crc(data[:-2], cktp)
        return crc[0] == data[-2] and crc[1] == data[-1]


class Convert:
    @staticmethod
    def to_bit_ar(bytes, parity=False):
        ret = []
        set_bits = 0 
        for b in bytes:
            for i in xrange(8):
                bit = (b >> i) & 1
                set_bits += bit
                ret.append(bit)
            if parity:
                ret.append(1-(set_bits & 1))
                set_bits = 0
        return ret

    @staticmethod
    def to_byte_ar(bits):
        ret = []
        cur = 0
        curi = 0
        for bit in bits:
            if curi < 8:
                cur |= bit << curi
                curi += 1
            if curi == 8:
                ret.append(cur)
                curi = 0
                cur = 0
        return ret

