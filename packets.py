#!/usr/bin/env python

import utilities

class PacketError:
    NO_ERROR     = 0
    PARITY_ERROR = 1
    CLOSED_ERROR = 2
    PARITY_CLOSE_ERROR = 3
    TRUNCATED_ERROR = 4

class PacketType:
    TAG_TO_READER = 0
    READER_TO_TAG = 1
    NUM_TYPES = 2

    @staticmethod
    def start_bit(t):
        if t == PacketType.TAG_TO_READER:
            return 1 # must have even number, so that last bit would be 1, ie |-|________
        elif t == PacketType.READER_TO_TAG:
            return 0
        else:
            raise ValueError('Unknown Packet Type', str(t))


class Command:

    def __init__(self, name, init_bytes, packet_type, crc=False, num_extra_bytes=0):
        self._name = name        
        self._init_bytes = []
        self._init_bytes[:] = init_bytes
        self._packet_type = packet_type
        self._crc = crc
        self._num_extra_bytes = num_extra_bytes
        self._len = len(init_bytes) + num_extra_bytes + (2 if crc else 0)

    def name(self):
        return self._name
    
    def packet_type(self):
        return self._packet_type

    def needs_crc(self):
        return self._crc

    def num_extra_bytes(self):
        return self._num_extra_bytes

    def header(self):
        return self._init_bytes

    def total_len(self):
        return self._len
  
class CommandStructure:

    def __init__(self, name, header, extra=[], crc=[]):
        self._name = name
        self._header = header
        self._extra = extra
        self._crc = crc

    def name(self):
        return self._name
    
    def header(self):
        return self._header
   
    def extra(self):
        return self._extra

    def crc(self):
        return self._crc

    @staticmethod
    def pretty_print(bytes):
        for byte in bytes:
            print format(byte, "#04X"),

    def display(self):
        print "COMMAND:", self._name
        print "HEADER:", 
        CommandStructure.pretty_print(self._header)
        print "\nEXTRA:",
        CommandStructure.pretty_print(self._extra)
        print "\nCRC:",
        CommandStructure.pretty_print(self._crc)
        print '\n'
        

class CommandType:
    REQA   = Command("REQA", [0x26], PacketType.READER_TO_TAG)
    WUPA   = Command("WUPA", [0x52], PacketType.READER_TO_TAG)
    ATQA   = Command("ATQA", [0x44, 0x00], PacketType.TAG_TO_READER)
    ANTI1R = Command("ANTI1R", [0x93, 0x20], PacketType.READER_TO_TAG) # says 0x20 to 0x67?
    ANTI1T = Command("ANTI1T", [0x88], PacketType.TAG_TO_READER, num_extra_bytes=4)
    SEL1R  = Command("SEL1R", [0x93, 0x70, 0x88], PacketType.READER_TO_TAG, True, 4)
    SEL1T  = Command("SEL1T", [0x04], PacketType.TAG_TO_READER, True)
    ANTI2R = Command("ANTI2R", [0x95, 0x20], PacketType.READER_TO_TAG) # says 0x20 to 0x67?
    ANTI2T = Command("ANTI2T", [], PacketType.TAG_TO_READER, num_extra_bytes=5)
    SEL2R  = Command("SEL2R", [0x95, 0x70], PacketType.READER_TO_TAG, True, 5)
    SEL2T  = Command("SEL2T", [0x00], PacketType.TAG_TO_READER, True)
    READR  = Command("READR", [0x30], PacketType.READER_TO_TAG, True, 1)
    READT  = Command("READT", [], PacketType.TAG_TO_READER, True, 16)
    HALT   = Command("HALT", [0x50, 0x00], PacketType.READER_TO_TAG, True)
    WRITE  = Command("WRITE", [0xA2], PacketType.READER_TO_TAG, True, 5)
    COMPW1 = Command("COMPW1", [0xA0], PacketType.READER_TO_TAG, True, 1)
    COMPW2 = Command("COMPW2", [], PacketType.READER_TO_TAG, True, 16)

    _map_first_bytes = {0x00: [SEL2T],
                        0x04: [SEL1T],
                        0x26: [REQA],
                        0x30: [READR], 
                        0x44: [ATQA],
                        0x50: [HALT], 
                        0x52: [WUPA],
                        0x88: [ANTI1T],
                        0x93: [ANTI1R, SEL1R],
                        0x95: [ANTI2R, SEL2R],
                        0xA0: [COMPW1],
                        0xA2: [WRITE]
                       }

    _map_second_bytes = {0x00: [ATQA, HALT],
                         0x20: [ANTI1R, ANTI2R],
                         0x70: [SEL1R, SEL2R]
                        }

    # should really just follow previous commands...
    @staticmethod
    def get_command_type(bytes):
        try:
            first_options = CommandType._map_first_bytes[bytes[0]]
            option = first_options[0] 
            if len(first_options) > 1:
                second_options = CommandType._map_second_bytes[bytes[1]]
                if first_options[1] in second_options:
                    option = first_options[1]            
            
            if option.total_len() == len(bytes):
                return option            
            
        except KeyError:
            pass
        return None

    @staticmethod
    def decode_command(bytes):
        tp = CommandType.get_command_type(bytes)
        if not tp:
            s = CommandStructure("UNKNOWN", [], bytes)
        else:
            name = tp.name()
          #  if name == "REQA":
          #      return
            header = tp.header()
            crc = bytes[-2:] if tp.needs_crc() else []
            extra = bytes[len(header):len(bytes)-len(crc)]

            s = CommandStructure(name, tp.header(), extra, crc)
        s.display()

    @staticmethod
    def get_bytes(command, extra_bytes = []):
        bytes = []
        bytes[:] = command.header()
        bytes.extend(extra_bytes)
        if command.needs_crc():
            bytes.extend(utilities.CRC.calculate_crc(bytes))
        return bytes

    
    @staticmethod
    def get_bits(command, all_bytes):
        bits = [PacketType.start_bit(command.packet_type())] # maybe remove this
        for byte in all_bytes:
            set_bits = 0
            for i in xrange(8):
                bit = byte & 1
                set_bits += bit
                byte >>= 1
                bits.append(bit)
            bits.append(1 - (set_bits & 1)) # 1 if even number
        return bits

class Packet:
    def __init__(self, packet_type):
        self._bytes = []
        self._reset_current_byte()
        self._type = packet_type
        self._closed = False

    def _reset_current_byte(self):
        self._cur_byte = 0
        self._cur_bits = 0
        self._set_bits = 0

    def append_bit(self, bit):
        if self._closed:
            return PacketError.CLOSED_ERROR
        
        if self._cur_bits < 8:       
            self._cur_byte |= bit << self._cur_bits
            self._cur_bits += 1
            self._set_bits += bit
            return PacketError.NO_ERROR
        else:
            ok = self._set_bits & 1 != bit # even number of 1s => 1 following
            cur = self._cur_byte
            self._reset_current_byte()         
            if ok:
                self._bytes.append(cur)
                return PacketError.NO_ERROR
            else:
                return PacketError.PARITY_ERROR

    def close_packet(self):
        if self._closed:
            return PacketError.CLOSED_ERROR  

        self._closed = True
        if self._cur_bits == 8:

            if self._set_bits & 1 != PacketType.start_bit(self._type): # explain?
               self._bytes.append(self._cur_byte)
               return PacketError.NO_ERROR
            else:
               return PacketError.PARITY_CLOSE_ERROR
        elif self._cur_bits == 1 and self._cur_byte == PacketType.start_bit(self._type):
            return PacketError.NO_ERROR        
        elif self._cur_bits != 0:
            print self._cur_bits, self._cur_byte, PacketType.start_bit(self._type)
            return PacketError.TRUNCATED_ERROR
        else:
            return PacketError.NO_ERROR

    def get_bytes(self):
        return self._bytes


class PacketProcessor:
    def __init__(self, packet_type):
        self._packets = []
        self._type = packet_type
        self._reset_packet()

    def _reset_packet(self):
        self._started = False
        self._cur = Packet(self._type)

    def append_bit(self, bit):
        ret = PacketError.NO_ERROR        
        if bit != 0 and bit != 1:
            if self._started:
                err = self._cur.close_packet() # check
                if err != PacketError.NO_ERROR:
                    ret = err
                else:
                    self._packets.append(self._cur)
                self._reset_packet()
        else:
            if not self._started and bit == PacketType.start_bit(self._type):
                self._started = True
            else: # check logic
                ret = self._cur.append_bit(bit)
        return ret

    def get_packets(self):
        return self._packets

    def get_packet_length(self):
        return len(self._packets)


class CombinedPacketProcessor:
    def __init__(self):
        self._packet_processors = []
        self._packet_lens = []
        for i in range(PacketType.NUM_TYPES):
            self._packet_processors.append(PacketProcessor(i))
            self._packet_lens.append(0)

    def append_bit(self, bit, packet_type):

        pp = self._packet_processors[packet_type]     
        ret = pp.append_bit(bit)
        l = pp.get_packet_length() 
        if ret == PacketError.NO_ERROR:
            if self._packet_lens[packet_type] != l:
                self._packet_lens[packet_type] = l
                bytes = pp.get_packets()[-1].get_bytes()
                if bytes:
                    CommandType.decode_command(bytes)
        else:       
            print "ERROR", ret 
        return ret
    
if __name__ == '__main__':
    uid = [0x04, 0xBE, 0x6F, 0x22, 0x09, 0x29, 0x80]
    bcc = utilities.BCC.calculate_bcc(uid)
    part1 = []
    part1[:] = uid[0:3]
    part1.append(bcc[0])
    part2 = []
    part2[:] = uid[3:]
    part2.append(bcc[1])
    commands = [CommandType.get_bytes(CommandType.REQA),
                CommandType.get_bytes(CommandType.ATQA),
                CommandType.get_bytes(CommandType.ANTI1R),
                CommandType.get_bytes(CommandType.SEL1R, part1),
                CommandType.get_bytes(CommandType.ANTI2T, part2)
               ]
    for command in commands:
        print "PACKET START, TYPE "
        for byte in command:    
            print format(byte, "#04X")
        print "PACKET END"
    
