from command import CommandType, CommandStructure, TagType, PacketType
from cipher import cipher
from utilities import Convert

from miller import miller_encoder

class Reader:
    def __init__(self, callback = None): # add callback here. must inform fsm as well for 1K cards...
        self._cur_cmd = CommandType.REQA
        self._reset_tag()      
        self._callback = callback if callback else self._display

    def _display(self, bits):
        print bits

    def _reset_tag(self):
        self._uid = []
        self._tag_type = None
        self._encryption = None
        self._readaddr = 0
        self._cur_addr = 0
        self._auth_addr = 0

    def _handle_next(self, cmd, extra):
        struct = CommandStructure.encode_command(cmd, extra)
        print "OUTGOING"
        struct.display()
        if cmd == CommandType.HALT:
           self._reset_tag()

        all_bits = Convert.to_bit_ar(struct.all_bytes(), True)
        # encrypt here if necessary        
        self._callback(all_bits)
        

    def process_packet(self, cmd, struct, packet_type):
        if packet_type != PacketType.TAG_TO_READER:
           return # maybe

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


## auth decreases by 4, reader by 1

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
