#!/usr/bin/env python

# Written by Ilias Giechaskiel
# https://ilias.giechaskiel.com
# June 2015

from command import CommandType, CommandStructure, TagType, PacketType
from cipher import cipher
from utilities import Convert

from miller import miller_encoder
from rand import Rand

class AccessType:
    READ = 0
    WRITE = 1
    INCREMENT = 2
    OTHERS = 3

class AccessResult:
    ALL  = (1, 1, 1)
    NONE = (0, 0, 0)
    P010 = (0, 1, 0)
    P011 = (0, 1, 1)
    P101 = (1, 0, 1)

class AuthKey:
    NONE = 0
    A = 1
    B = 2

class Tag:

    @staticmethod
    def generate_1k():
        zero_block = [0x00]*16
        keya = [0xFF]*6
        keyb = [0xFF]*6
        acc  = [0xFF, 0x07, 0x80, 0x69] # access controls
        key_block  = keya + acc + keyb
        zero_sector = zero_block*3 + key_block 
        tag_block = [0xCD, 0x76, 0x92, 0x74, 
                     0x5D, 0x88, 0x04, 0x00,
                     0x85, 0x00, 0x00, 0x00,
                     0x04, 0x13, 0x45, 0x01] 
        tag_sector = tag_block + zero_block*2 + key_block
        mem = tag_sector + 15*zero_sector

        return mem

    @staticmethod
    def get_keys_from_mem(mem):
        start = 16*3
        key_block = mem[start:start+16]
        keya = key_block[0:6]
        keyb = key_block[10:16]
        return (keya, keyb)

    def __init__(self, callback = None, tag_type=TagType.ULTRALIGHT, memory=None, rands=None):
        self._tag_type = tag_type
        self._mem = memory

        if tag_type == TagType.CLASSIC1K:
            self._random = Rand(rands)
            keya, keyb = Tag.get_keys_from_mem(self._mem)
            self._keya = keya
            self._keyb = keyb

        self._callback = callback if callback else self._display

        if self._tag_type == TagType.ULTRALIGHT:
            self.process_packet = self.process_packet_ul
        elif self._tag_type == TagType.CLASSIC1K:
            self.process_packet = self.process_packet_1k
        else:
            print "TAG TYPE UNSUPPORTED"

        self._uid = self._get_uid()
        self._halt = False
        self._selected = False
        self._encode = None
        self._reset()

    def wake_up(self):
        self._halt = False

    def _get_uid(self):
        if self._tag_type == TagType.ULTRALIGHT:
            return self._mem[0:9]
        elif self._tag_type == TagType.CLASSIC1K:
            return self._mem[0:5]

    def _display(self, bits):
        print bits

    def _handle_next(self, cmd, extra):
        if not cmd:
            return None
        struct = CommandStructure.encode_command(cmd, extra)
        print "TAG OUTGOING"
        struct.display()

        all_bits = Convert.to_bit_ar(struct.all_bytes(), True)
        if self._encode:
            all_bits = self._encode(all_bits, cmd)   
        #print all_bits
        self._callback(all_bits)
        return (cmd, struct)
        

    def set_encoder(self, encode):
        self._encode = encode  

    def process_packet_ul(self, cmd, struct):
        if cmd.packet_type() != PacketType.READER_TO_TAG:
           return None

        print "TAG INCOMING"
        struct.display()

        next_cmd = None
        extra_param = []

        decoded = False

        if cmd == CommandType.WUPA:
            next_cmd = CommandType.ATQAUL
            decoded = True
        elif cmd == CommandType.REQA:
            if not self._halt:
                next_cmd = CommandType.ATQAUL
            decoded = True
        elif cmd == CommandType.ANTI1R:
            next_cmd = CommandType.ANTI1U
            extra_param = self._uid[0:4]
            decoded = True
        elif cmd == CommandType.SEL1R:
            if struct.extra() == [0x88] + self._uid[0:4]:
                self._selected = True
                next_cmd = CommandType.SEL1U
            decoded = True

        if decoded:
            ret = self._handle_next(next_cmd, extra_param)
            return ret
        if not self._selected:
            return None

        if cmd == CommandType.ANTI2R:
            next_cmd = CommandType.ANTI2T
            extra_param = self._uid[4:]
        elif cmd == CommandType.SEL2R:
            if struct.extra() != self._uid[4:]:                
                self._selected = False
                self._reset()
            else:
                next_cmd = CommandType.SEL2T
        elif cmd == CommandType.READR:
            val = struct.extra()[0]
            if val <= 0x0F:
                next_cmd = CommandType.READT
                beg = val*4
                if val <= 0x0C:
                    extra_param = self._mem[beg:beg+16]
                else:
                    diff = val - 0x0C
                    extra_param = self._mem[beg:]
                    extra_param += self._mem[0:diff*4]
        elif cmd == CommandType.HALT:
            self._halt = True
            self._selected = False
            self._reset()

        ret = self._handle_next(next_cmd, extra_param) 
        return ret

    def _reset(self):
        self._auth = None
        self._auth_key = AuthKey.NONE
        self._auth_prosp = None
        self._at = None

    @staticmethod
    def _check_complements(a, na):
        for i in xrange(4):
            ai  = a&1
            nai = na&1
            if ai != 1 - nai:
                return False
            a >>= 1
            na >>= 1
        return True

    def _get_sector_access_bits(self, num):
        offset = num*16 + 54
        bytes = self._mem[offset:offset+4]
        return self._decode_access_bits(bytes)

    def _decode_access_bits(self, bytes):
        not_ones   = bytes[0] & 0xFF
        not_twos   = (bytes[0] >> 4) & 0xFF
        not_threes = bytes[1] & 0xFF
        ones       = (bytes[1] >> 4) & 0xFF
        twos       = bytes[2] & 0xFF
        threes     = (bytes[2] >> 4) & 0xFF

        if not Tag._check_complements(ones, not_ones):
            print "ERROR WITH ONES"
        if not Tag._check_complements(twos, not_twos):
            print "ERROR WITH TWOS"
        if not Tag._check_complements(threes, not_threes):
            print "ERROR WITH THREES"

        ar = [ones, twos, threes]
        ll = len(ar)
        ret = []
        for i in xrange(4):
            val = 0
            for j in xrange(ll):
                val |= ((ar[j]>> i) & 1) << (2-j)
            ret.append(val)
        return ret

    def _get_access_result(self, block, access_type):
        sector = self._auth
        if sector == None:
            return AccessResult.NONE
        if block/4 != sector/4:
            return AccessResult.NONE
        rem = block%4
        access_bits = self._get_sector_access_bits(sector)[rem]
        
        if rem != 3: # regular access
            if access_type == AccessType.READ:
                if access_bits == 7:
                    return AccessResult.NONE
                elif access_bits in [3, 5]:
                    if self._auth_key == AuthKey.B:
                        return AccessResult.ALL
                    else:
                        return AccessResult.NONE
                else:
                    return AccessResult.ALL
            elif access_type == AccessType.WRITE:
                if access_bits == 0:
                    return AccessResult.ALL
                elif access_bits in [3, 4, 6]:
                    if self._auth_key == AuthKey.B:
                        return AccessResult.ALL
                    else:
                        return AccessResult.NONE
                else:
                    return AccessResult.NONE
            elif access_type == AccessType.INCREMENT:
                if access_bits == 0:
                    return AccessResult.ALL
                elif access_bits == 6:
                    if self._auth_key == AuthKey.B:
                        return AccessResult.ALL
                    else:
                        return AccessResult.NONE
                else:
                    return AccessResult.NONE
            elif access_type == AccessType.OTHERS:
                return access_bits in [0, 1, 6]
            else:
                print "WRONG ACCESS TYPE!"
        else:
            if access_type == AccessType.READ:
                if access_bits in [0, 1, 2]:
                    if self._auth_key == AuthKey.A:
                        return AccessResult.P011
                    else:
                        return AccessResult.NONE
                else:
                    return AccessResult.P010
            elif acccess_type == AccessType.WRITE:
                if access_bits in [2, 6, 7]:
                    return AccessResult.NONE
                elif access_bits == 5:
                    if self._auth_key == AuthKey.B:
                        return AccessResult.P010
                    else:
                        return AccessResult.NONE
                elif access_bits == 0:
                    if self._auth_key == AuthKey.A:
                        return AccessResult.P101
                    else:
                        return AccessResult.NONE
                elif access_bits == 4:
                    if self._auth_key == AuthKey.B:
                        return AccessResult.P101
                    else:
                        return AccessResult.NONE
                elif access_bits == 1:
                    if self._auth_key == AuthKey.A:
                        return AccessResult.P101
                    else:
                        return AccessResult.NONE
                elif access_bits == 3:
                    if self._auth_key == AuthKey.B:
                        return AccessResult.P101
                    else:
                        return AccessResult.NONE
                else:
                    print "SHOULD NEVER GET HERE"
                    return AccessResult.NONE
                    
    def _set_at(self, auth_key, prosp):
        self._reset()
        self._auth_key = auth_key
        self._auth_prosp = prosp
        extra_param = self._random.get_next()
        c = cipher(self._keya if self._auth_key == AuthKey.A else self._keyb)
        uid_bits = Convert.to_bit_ar(self._uid[0:4])
        nonce_bits = Convert.to_bit_ar(extra_param)
        c.set_tag_bits(uid_bits, nonce_bits, 0)
        self._at = c.get_at()
        return extra_param


    def process_packet_1k(self, cmd, struct):
        if cmd.packet_type() != PacketType.READER_TO_TAG:
           return None

        print "INCOMING"
        struct.display()

        next_cmd = None
        extra_param = []

        decoded = False

        if cmd == CommandType.WUPA:
            next_cmd = CommandType.ATQA1K
            decoded = True
            self._selected = False
            self._reset()
        elif cmd == CommandType.REQA:
            if not self._halt:
                next_cmd = CommandType.ATQA1K
            decoded = True
            self._selected = False
            self._reset()
        elif cmd == CommandType.ANTI1R:
            next_cmd = CommandType.ANTI1G
            extra_param = self._uid
            decoded = True
        elif cmd == CommandType.SEL1R:
            if struct.extra() == self._uid:
                self._selected = True
                next_cmd = CommandType.SEL1K
            decoded = True

        if decoded:
            ret = self._handle_next(next_cmd, extra_param)
            return ret
        if not self._selected:
            return None

        if cmd == CommandType.AUTHA:
            next_cmd = CommandType.RANDTA
            extra_param = self._set_at(AuthKey.A, struct.extra()[0])
        elif cmd == CommandType.AUTHB:
            next_cmd = CommandType.RANDTA
            extra_param = self._set_at(AuthKey.A, struct.extra()[0])
        elif cmd == CommandType.RANDRB:
            next_cmd = CommandType.RANDTB
            extra_param = self._at
            self._auth = self._auth_prosp
        elif cmd == CommandType.SEL2R:
            self._selected = False
            self._reset()
        elif cmd == CommandType.READR:
            val = struct.extra()[0]
            if val <= 0x3F:
                auth = self._get_access_result(val, AccessType.READ)
                if auth != AccessResult.NONE:
                    next_cmd = CommandType.READT
                    beg = val*16
                    mem = self._mem[beg:beg+16]
                    if auth == AccessResult.ALL:
                        extra_param = mem
                    else:
                        extra_param = []
                        for i in xrange(16):
                            if i < 6:
                                mult = auth[0]
                            elif i < 10:
                                mult = auth[1]
                            else:
                                mult = auth[2]
                            byte = mem[i]*mult
                            extra_param.append(byte)
        elif cmd == CommandType.HALT:
            self._halt = True
            self._reset()

        ret = self._handle_next(next_cmd, extra_param) 
        return ret
