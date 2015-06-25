#!/usr/bin/env python

# Written by Ilias Giechaskiel
# https://ilias.giechaskiel.com
# June 2015

from command import CommandType, CommandStructure, TagType, PacketType
from cipher import cipher
from utilities import Convert

from miller import miller_encoder

from rand import Rand

class Reader:
    def __init__(self, callback = None, rands=None, keya=None, keyb=None):

        self._callback = callback if callback else self._display
        self._encoder = None
        self._random = Rand(rands)

        self._keya = keya
        self._keyb = keyb
    
        self._key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF] if not self._keya else self._keya
        self._reset_tag()      
        self._encode = None

    def _display(self, bits, finished=False):
        print bits, finished

    def _reset_tag(self):
        self._uid = []
        self._tag_type = None
        self._encryption = None
        self._readaddr = 0
        self._cur_addr = 0
        self._auth_addr = 0
        self._random.reset()

    def _handle_next(self, cmd, extra):
        struct = CommandStructure.encode_command(cmd, extra)
        print "READER OUTGOING"
        struct.display()
        if cmd == CommandType.HALT:
           self._reset_tag()

        all_bits = Convert.to_bit_ar(struct.all_bytes(), True)
        if self._encode:
            all_bits = self._encode(all_bits, cmd)   
        #print all_bits
        self._callback(all_bits, cmd == CommandType.HALT)
        return (cmd, struct) 

    def set_encoder(self, encode):
        self._encode = encode
        

    def process_packet(self, cmd, struct):
        if cmd.packet_type() != PacketType.TAG_TO_READER:
           return None

        print "READER INCOMING"
        struct.display()

        next_cmd = CommandType.HALT
        extra_param = []

        if cmd == CommandType.ATQAUL:
            self._tag_type = TagType.ULTRALIGHT
            next_cmd = CommandType.ANTI1R
        elif cmd == CommandType.ATQA1K:
            self._tag_type = TagType.CLASSIC1K
            next_cmd = CommandType.ANTI1R
        elif cmd == CommandType.ATQA4K:
            self._tag_type = TagType.CLASSIC4K
            #next_cmd = CommandType.ANTI1R
            next_cmd = CommandType.HALT # don't have access to this, but similar to 1k
        elif cmd == CommandType.ATQADS:
            self._tag_type = TagType.DESFIRE
            next_cmd = CommandType.HALT # can't handle this
        elif cmd == CommandType.ANTI1U:
            extra_param = [0x88] + struct.extra()
            uid = extra_param[1:4] # should check tag type...
            self._uid.extend(uid)
            next_cmd = CommandType.SEL1R
        elif cmd == CommandType.ANTI1G:
            extra_param = struct.extra()
            uid = extra_param[0:4]
            self._uid.extend(uid)
            next_cmd = CommandType.SEL1R
        elif cmd == CommandType.SEL1U:
            next_cmd = CommandType.ANTI2R
        elif cmd == CommandType.SEL1K:
            next_cmd = CommandType.AUTHA
            self._auth_addr = 0x3C
            self._cur_addr = 0x3F
            extra_param = [self._auth_addr]
        elif cmd == CommandType.ANTI2T:
            extra_param = struct.extra()
            uid = extra_param[0:4]
            self._uid.extend(uid)
            next_cmd = CommandType.SEL2R
        elif cmd == CommandType.RANDTA:
            extra_param.extend(self._random.get_next())
            
            c = cipher(self._key)
            uid_bits = Convert.to_bit_ar(self._uid)
            nonce_bits = Convert.to_bit_ar(struct.extra())
            c.set_tag_bits(uid_bits, nonce_bits, 0)
            extra_param.extend(c.get_ar())
            next_cmd = CommandType.RANDRB
        elif cmd == CommandType.RANDTB:
            next_cmd = CommandType.READR
            extra_param = [self._cur_addr]
        elif cmd == CommandType.SEL2T:
            next_cmd = CommandType.READR
            self._cur_addr = 0x00            
            extra_param = [self._cur_addr]
        elif cmd == CommandType.READT:
            addr = self._cur_addr
            if self._tag_type == TagType.ULTRALIGHT:
                if addr > 0x08:
                    next_cmd = CommandType.HALT
                else:
                    addr += 0x04
                    next_cmd = CommandType.READR
                    extra_param = [addr]
            elif self._tag_type == TagType.CLASSIC1K:
                if addr % 4 == 0:
                    if addr == 0:
                        next_cmd == CommandType.HALT
                    else:
                        next_cmd = CommandType.AUTHA
                        addr -= 1
                        self._auth_addr -= 0x04
                        extra_param = [self._auth_addr]
                else:
                    addr -= 1
                    next_cmd = CommandType.READR
                    extra_param = [addr]

            self._cur_addr = addr
            
        else:
            print "ERROR, Unexpected command!!"

        ret = self._handle_next(next_cmd, extra_param)
        return ret
