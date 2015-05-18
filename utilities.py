#!/usr/bin/env python


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
        
        if (cktp == CRC_14443_B):
            wcrc = ~wcrc

        return [wcrc & 0xFF, (wcrc >> 8) & 0xFF]

    @staticmethod
    def check_crc(data, cktp=CRC_14443_A):
        crc = calculate_crc(data[:-2], cktp)
        return crc[0] == data[-2] and crc[1] == data[-1]
