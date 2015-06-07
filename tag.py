from command import CommandType, CommandStructure, TagType, PacketType
from cipher import cipher
from utilities import Convert

from miller import miller_encoder

class Tag:
    def __init__(self, callback = None, rands=None, key=None):
        self._mem = [0x04, 0xBE, 0x6F, 0x5D,
                     0x22, 0x09, 0x29, 0x80,
                     0x82, 0x48, 0x00, 0x00,
                     0xE1, 0x10, 0x12, 0x00,
                     0x01, 0x03, 0xA0, 0x10,
                     0x44, 0x03, 0x00, 0xFE,
                     0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x00, 
                     0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x00, 
                     0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x00] 
        self._tag_type = TagType.ULTRALIGHT
        self._callback = callback

        if self._tag_type == TagType.ULTRALIGHT:
            self.process_packet = self.process_packet_ul

        self._uid = self._get_uid()
        self._halt = False
        self._selected = False
        

    def _get_uid(self):
        if self._tag_type == TagType.ULTRALIGHT:
            return self._mem[0:9]

    def _display(self, bits):
        print bits

    def _handle_next(self, cmd, extra):
        if not cmd:
            return
        struct = CommandStructure.encode_command(cmd, extra)
        print "OUTGOING"
        struct.display()

        all_bits = Convert.to_bit_ar(struct.all_bytes(), True)
        if self._encode:
            all_bits = self._encode(all_bits, cmd)   
        #print all_bits
        self._callback(all_bits)
        

    def set_encoder(self, encode):
        self._encode = encode  

    def process_packet_ul(self, cmd, struct):
        if cmd.packet_type() != PacketType.READER_TO_TAG:
           return

        print "INCOMING"
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
            self._handle_next(next_cmd, extra_param)
            return
        if not self._selected:
            return

        if cmd == CommandType.ANTI2R:
            next_cmd = CommandType.ANTI2T
            extra_param = self._uid[4:]
        elif cmd == CommandType.SEL2R:
            if struct.extra() != self._uid[4:]:
                self._selected = False
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

        self._handle_next(next_cmd, extra_param) 
