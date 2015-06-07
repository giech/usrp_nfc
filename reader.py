from command import CommandType, CommandStructure, TagType, PacketType
from cipher import cipher
from utilities import Convert

from miller import miller_encoder

class Reader:
    def __init__(self, callback = None, rands=None, key=None):
        self._reset_tag()      
        self._callback = callback if callback else self._display
        self._encoder = None
        self._rands = [[0x15, 0x45, 0x90, 0xA8], 
                       [0x01, 0x3A, 0x6B, 0xBA],
                       [0xEE, 0x08, 0xB0, 0x0A], 
                       [0x2F, 0x44, 0xA3, 0x06], 
                       [0xC7, 0xC9, 0xD8, 0x8B], 
                       [0xCE, 0x0C, 0xD2, 0x7C], 
                       [0x9B, 0xF6, 0xC8, 0x66], 
                       [0x73, 0xB3, 0xBB, 0x75], 
                       [0x96, 0x66, 0x8E, 0x10],
                       [0x72, 0x10, 0xA5, 0xFB],
                       [0x52, 0x3A, 0xA8, 0x5B],
                       [0xE0, 0x8E, 0x57, 0xCB],
                       [0x78, 0x81, 0xCB, 0x50],
                       [0x4D, 0x95, 0xCA, 0x3A],
                       [0xAE, 0x8D, 0x9C, 0x9C],
                       [0xD6, 0x8D, 0x04, 0x06]
                      ] if not rands else rands
        self._key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF] if not key else key

    def _display(self, bits):
        print bits

    def _reset_tag(self):
        self._uid = []
        self._tag_type = None
        self._encryption = None
        self._readaddr = 0
        self._cur_addr = 0
        self._auth_addr = 0
        self._rand_ind = 0

    def _handle_next(self, cmd, extra):
        struct = CommandStructure.encode_command(cmd, extra)
        print "OUTGOING"
        struct.display()
        if cmd == CommandType.HALT:
           self._reset_tag()

        all_bits = Convert.to_bit_ar(struct.all_bytes(), True)
        if self._encode:
            all_bits = self._encode(all_bits, cmd)   
        #print all_bits
        self._callback(all_bits, cmd == CommandType.HALT)

    def set_encoder(self, encode):
        self._encode = encode
        

    def process_packet(self, cmd, struct):
        if cmd.packet_type() != PacketType.TAG_TO_READER:
           return

        print "INCOMING"
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
            rands = self._rands
            index = self._rand_ind
            extra_param.extend(rands[index])
            self._rand_ind = (index + 1) % len(rands)
            
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

        self._handle_next(next_cmd, extra_param)
