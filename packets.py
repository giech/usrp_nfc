#!/usr/bin/env python

import cipher
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
         #   print "XOR passed"    

        return True


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
        

class CommandType:
    REQA   = Command("REQA", 0, [0x26], PacketType.READER_TO_TAG)
    WUPA   = Command("WUPA", 0, [0x52], PacketType.READER_TO_TAG)
    ATQAUL = Command("ATQAUL", 0, [0x44, 0x00], PacketType.TAG_TO_READER)
    ATQA1K = Command("ATQA1K", 0, [0x04, 0x00], PacketType.TAG_TO_READER) ### DIFFERENT
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


    _tag_commands = {0: [ATQAUL, ATQA1K],
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

    # should really just follow previous commands...
    @staticmethod
    def get_command_type(bytes, state, packet_type):
        ar = CommandType._tag_commands if packet_type == PacketType.TAG_TO_READER else CommandType._reader_commands
        ar_len = len(ar)
        ind = state.get_cur_cmd().stage()
        
    
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

    @staticmethod
    def get_decrypted_bytes(packet, state):
        c = state.get_cipher()
        bytes = packet.get_bytes()
        prev_cmd = state.get_cur_cmd()
        if c:
            ll = len(bytes)
            check_parity = True
            if prev_cmd == CommandType.AUTHA and ll == CommandType.RANDTA.total_len():
                key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
                ret = bytes
                check_parity = False
            elif prev_cmd == CommandType.RANDTA and ll == CommandType.RANDRB.total_len():
                rdr_enc_nonce = bytes[0:ll/2]
                rdr_nonce = c.enc_bytes_with_xor(rdr_enc_nonce, 1, 1)
                enc_ar = bytes[ll/2:]
                ar = c.enc_bytes_with_xor(enc_ar)
                if ar != c.get_ar():
                    print 'ERROR WITH AR'
                ret = rdr_nonce + ar
            elif prev_cmd == CommandType.RANDRB and ll == CommandType.RANDTB.total_len():
                ret = c.enc_bytes_with_xor(bytes)
                if ret != c.get_at():
                    print "ERROR WITH AT"
            else:
                ret = c.enc_bytes_with_xor(bytes)      

            if check_parity and not packet.check_parity(ret, c.get_last_parity_bits(ll)):
                print 'PROBLEM WITH PARITY!!!'
            return ret
        else:
            return bytes

    @staticmethod
    def decode_command(packet, state, packet_type):
        bytes = CommandType.get_decrypted_bytes(packet, state)
        tp = CommandType.get_command_type(bytes, state, packet_type)
        cur_name = state.get_cur_cmd().name()
        if not tp:
            name = "UNKNOWN"
            s = CommandStructure(name, [], bytes)
        else:
            name = tp.name()
            header = tp.header()
            crc = bytes[-2:] if tp.needs_crc() else []
            extra = bytes[len(header):len(bytes)-len(crc)]

            # should add extra description stuff
            s = CommandStructure(name, tp.header(), extra, crc)
            state.set_cur_cmd(tp)

            if tp == CommandType.ANTI1G:
                uid = extra[0:4]
                state.set_uid(uid)
            elif tp == CommandType.RANDTA:
                key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
                c = cipher.cipher(key)
                if not state.get_cipher():
                    c.set_tag(state.get_uid(), extra)
                else:
                    bytes = packet.get_bytes()
                    s.set_extra(extra)
                    c.set_tag(state.get_uid(), extra, 1)
                    print "PARITY CHECK", packet.check_parity(bytes, c.get_last_parity_bits(4))
                   # raise 1
                state.set_cipher(c)
            elif tp == CommandType.REQA or tp == CommandType.HALT:
                state.set_cipher(None)
                

        if name != cur_name:
            s.display()
        else:
            print name, '\n'

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



class State:

    def __init__(self, init_cmd=CommandType.REQA):
        self.set_cur_cmd(init_cmd)
        self._uid = None
        self._cipher = None
    
    def set_cur_cmd(self, cmd):
        self._cmd = cmd

    def get_cur_cmd(self):
        return self._cmd

    def set_uid(self, uid):
        self._uid = uid

    def get_uid(self):
        return self._uid

    def set_cipher(self, cipher):
        self._cipher = cipher

    def get_cipher(self):
        return self._cipher

class Packet:
    def __init__(self, packet_type, enc=False):
        self._bytes = []
        self._parity = []
        self._reset_current_byte()
        self._type = packet_type
        self._closed = False
        self._enc = enc

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
            if self._enc:
                self._bytes.append(cur)
                self._parity.append(bit)
                return PacketError.NO_ERROR
            else:      
                if ok:
                    self._bytes.append(cur)
                    self._parity.append(bit)
                    return PacketError.NO_ERROR
                else:
                    return PacketError.PARITY_ERROR

    def close_packet(self):
        if self._closed:
            return PacketError.CLOSED_ERROR  

        self._closed = True
        if self._cur_bits == 8:
            s = self._set_bits & 1
            if s != PacketType.start_bit(self._type) or self._enc: # explain?
               self._bytes.append(self._cur_byte)
               self._parity.append(PacketType.start_bit(self._type))#1 - s)
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

    def is_encrypted(self):
        return self._enc

    def check_parity(self, bytes, enc_parity):
        ll = len(bytes)
        p = self._parity
        if ll != len(p):
            print "HERE:", lep(p), ll, len(enc_parity)
            return False
        ok = True
        for i in xrange(ll):
            s = 0
            b = bytes[i]
            for j in xrange(8):
                s += b &1
                b >>= 1
          #  print s&1, enc_parity[i], (1- p[i])
            if s&1^enc_parity[i] == p[i]:
                 ok = False

        return ok


class PacketProcessor:
    def __init__(self, packet_type):
        self._packets = []
        self._type = packet_type
        self._enc = False
        self._reset_packet()

    def _reset_packet(self):
        self._started = False
        self._cur = Packet(self._type, self._enc)

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
          #  print bit
            if not self._started and bit == PacketType.start_bit(self._type):
                self._started = True
            else: # check logic
                ret = self._cur.append_bit(bit)
        return ret

    def get_packets(self):
        return self._packets

    def get_packet_length(self):
        return len(self._packets)

    def set_encryption(self, enc):
        self._enc = enc
        self._reset_packet()


class CombinedPacketProcessor:
    def __init__(self):
        self._current_state = State()
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
                packet = pp.get_packets()[-1]
                if packet.get_bytes():
                    CommandType.decode_command(packet, self._current_state, packet_type)
                    state = self._current_state # could have changed
                    cur_cmd = state.get_cur_cmd()
                    if cur_cmd == CommandType.REQA or cur_cmd == CommandType.HALT:
                        for pp in self._packet_processors:
                            pp.set_encryption(False)
                    elif cur_cmd == CommandType.RANDTA:
                        for pp in self._packet_processors:
                            pp.set_encryption(True)
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
            print format(byte, "#04x")
        print "PACKET END"
    
