#!/usr/bin/env python

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
        

    # should not be method
    def process_packet(self):
        print "PACKET START, TYPE ", self._type
        for byte in self._bytes:    
            print format(byte, "#04X")
        print "PACKET END"


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
            else:
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
                pp.get_packets()[-1].process_packet()
        else:
            print "ERROR", ret 
        return ret
    

    
