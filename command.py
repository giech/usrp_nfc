from packets import PacketType
import utilities

class Command:

    def __init__(self, name, stage, init_bytes, packet_type, crc=False, num_extra_bytes=0, xor_check=-1):
        self._name = name 
        self._stage = stage       
        self._init_bytes = []
        self._init_bytes[:] = init_bytes
        self._packet_type = packet_type
        self._crc = crc
        self._num_extra_bytes = num_extra_bytes
        self._len = len(init_bytes) + num_extra_bytes + (2 if crc else 0)
        self._xor = xor_check

    def stage(self):
        return self._stage

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

    def is_compatible(self, bytes):
        end_len = len(bytes)        
        if self._len != end_len:
            return False

        init_bytes = self._init_bytes
        header_len = len(init_bytes)
        for i in xrange(header_len):
            if init_bytes[i] != bytes[i]:
                return False

        if self._crc:
            end_len -= 2
            if not utilities.CRC.check_crc(bytes):
                return False

        if self._xor >= 0:
            a = self._xor
            for b in bytes[header_len: end_len]:
                a ^= b 
            if a != 0:
                return False

        return True

# only NXP
class TagType:
    ULTRALIGHT = 0
    CLASSIC1K  = 1
    CLASSIC4K  = 2
    DESFIRE    = 3



class CommandType:
    REQA   = Command("REQA", 0, [0x26], PacketType.READER_TO_TAG)
    WUPA   = Command("WUPA", 0, [0x52], PacketType.READER_TO_TAG)
    
    ATQAUL = Command("ATQAUL", 0, [0x44, 0x00], PacketType.TAG_TO_READER)
    ATQA1K = Command("ATQA1K", 0, [0x04, 0x00], PacketType.TAG_TO_READER)
    ATQA4K = Command("ATQA1K", 0, [0x02, 0x00], PacketType.TAG_TO_READER)    
    ATQADS = Command("ATQADS", 0, [0x03, 0x44], PacketType.TAG_TO_READER)

    ANTI1R = Command("ANTI1R", 1, [0x93, 0x20], PacketType.READER_TO_TAG) # says 0x20 to 0x67?
    ANTI1U = Command("ANTI1U", 1, [0x88], PacketType.TAG_TO_READER, num_extra_bytes=4, xor_check=0x88) #ultralight
    ANTI1G = Command("ANTI1G", 1, [], PacketType.TAG_TO_READER, num_extra_bytes=5, xor_check=0) #general
    SEL1R  = Command("SEL1R", 2, [0x93, 0x70], PacketType.READER_TO_TAG, True, 5, xor_check=0) # DIFFERENT VALUE
    SEL1U  = Command("SEL1U", 2, [0x04], PacketType.TAG_TO_READER, True)
    
    SEL1K  = Command("SEL1K", 2, [0x08], PacketType.TAG_TO_READER, True)


    ANTI2R = Command("ANTI2R", 3, [0x95, 0x20], PacketType.READER_TO_TAG) # says 0x20 to 0x67?
    ANTI2T = Command("ANTI2T", 3, [], PacketType.TAG_TO_READER, num_extra_bytes=5, xor_check=0)

    AUTHA  = Command("AUTHA", 3, [0x60], PacketType.READER_TO_TAG, True, 1)
    
    AUTHB  = Command("AUTHB", 3, [0x61], PacketType.READER_TO_TAG, True, 1)

    RANDTA = Command("RANDTA", 3, [], PacketType.TAG_TO_READER, num_extra_bytes=4)
    RANDRB = Command("RANDRB", 4, [], PacketType.READER_TO_TAG, num_extra_bytes=8)
    RANDTB = Command("RANDTB", 4, [], PacketType.TAG_TO_READER, num_extra_bytes=4)

    SEL2R  = Command("SEL2R", 4, [0x95, 0x70], PacketType.READER_TO_TAG, True, 5, xor_check=0)
    SEL2T  = Command("SEL2T", 4, [0x00], PacketType.TAG_TO_READER, True)
    READR  = Command("READR", 5, [0x30], PacketType.READER_TO_TAG, True, 1)
    READT  = Command("READT", 5, [], PacketType.TAG_TO_READER, True, 16)


    HALT   = Command("HALT", 10, [0x50, 0x00], PacketType.READER_TO_TAG, True)

    # not yet seen
    WRITE  = Command("WRITE", 6, [0xA2], PacketType.READER_TO_TAG, True, 5)
    COMPW1 = Command("COMPW1", 6, [0xA0], PacketType.READER_TO_TAG, True, 1)
    COMPW2 = Command("COMPW2", 7, [], PacketType.READER_TO_TAG, True, 16)



    _tag_commands = {0: [ATQAUL, ATQA1K, ATQA4K, ATQADS],
                     1: [ANTI1U, ANTI1G],
                     2: [SEL1U, SEL1K],
                     3: [ANTI2T, RANDTA],
                     4: [SEL2T, RANDTB],
                     5: [READT]
                    }

    _reader_commands = {0: [REQA, WUPA],
                        1: [ANTI1R],
                        2: [SEL1R],
                        3: [ANTI2R, AUTHA, AUTHB],
                        4: [SEL2R, RANDRB],
                        5: [READR],
                        6: [WRITE, COMPW1],
                        7: [COMPW2],
                       10: [HALT]
                       }   

    _map_first_bytes = {0x00: [SEL2T],
                        0x02: [ATQA4K],
                        0x03: [ATQADS],
                        0x04: [SEL1U, ATQA1K],
                        0x08: [SEL1K],
                        0x26: [REQA],
                        0x30: [READR], 
                        0x44: [ATQAUL],
                        0x50: [HALT], 
                        0x52: [WUPA],
                        0x60: [AUTHA],
                        0x61: [AUTHB],
                        0x88: [ANTI1U],
                        0x93: [ANTI1R, SEL1R],
                        0x95: [ANTI2R, SEL2R],
                        0xA0: [COMPW1],
                        0xA2: [WRITE]
                       }

    _map_second_bytes = {0x00: [ATQAUL, HALT, ATQA1K],
                         0x20: [ANTI1R, ANTI2R],
                         0x70: [SEL1R, SEL2R]
                        }

    @staticmethod
    def get_command_type(bytes, packet_type, prev_cmd):
        ar = CommandType._tag_commands if packet_type == PacketType.TAG_TO_READER else CommandType._reader_commands
        ar_len = len(ar)
        ind = prev_cmd.stage()
        
    
        for v in (ind, ind+1):
            if v < ar_len:
                poss = ar[v]
                for p in poss:
                    if p.is_compatible(bytes):
                        return p

        try:
            first_options = CommandType._map_first_bytes[bytes[0]]
            option = first_options[0] 
            if len(first_options) > 1:
                second_options = CommandType._map_second_bytes[bytes[1]]
                if first_options[1] in second_options:
                    option = first_options[1]            
            
            if option.is_compatible(bytes):
                return option            
            
        except KeyError:
            pass
        return None




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
   
    def set_extra(self, extra):
        self._extra = extra

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
        if self._header:
            print "HEADER:", 
            CommandStructure.pretty_print(self._header)
            print ''
        if self._extra:
            print "EXTRA:",
            CommandStructure.pretty_print(self._extra)
            print ''
        if self._crc:        
            print "CRC:",
            CommandStructure.pretty_print(self._crc)
            print ''
        print '\n'

    def all_bytes(self):
        return self._header + self._extra + self._crc

    @staticmethod
    def decode_command(cmd, bytes):
        if cmd:
            name = cmd.name()
            header = cmd.header()
            crc = bytes[-2:] if cmd.needs_crc() else []
            extra = bytes[len(header):len(bytes)-len(crc)]
            return CommandStructure(name, header, extra, crc)
        else:
            return CommandStructure("UNKNOWN", [], bytes)

    @staticmethod
    def encode_command(cmd, bytes):
        if cmd:
            header = cmd.header()
            if cmd.needs_crc():
                crc = utilities.CRC.calculate_crc(header + bytes)
            else:
                crc = []
            return CommandStructure(cmd.name(), header, bytes, crc)
        else:
            return CommandStructure("UNKNOWN", [], bytes)


    
