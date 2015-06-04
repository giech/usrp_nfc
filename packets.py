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

import fsm

class PacketProcessor:
    def __init__(self, packet_type):
        self._type = packet_type
        self._start_bit = PacketType.start_bit(packet_type)
        self._reset_packet()

    def _reset_packet(self):
        self._started = False
        self._cur = []

    def append_bit(self, bit):
        ret = PacketError.NO_ERROR        
        if bit != 0 and bit != 1:
            if self._started:
                cur = self._cur
                self._reset_packet()
                return cur
        else:
            if not self._started and bit == self._start_bit:
                self._started = True
            else: # check logic
                self._cur.append(bit)
        return None



class CombinedPacketProcessor:
    def __init__(self, callback=None):
        self._packet_processors = []
        for i in range(PacketType.NUM_TYPES):
            self._packet_processors.append(PacketProcessor(i))
        self._fsm = fsm.fsm(callback)
        
    def append_bit(self, bit, packet_type):
        pp = self._packet_processors[packet_type]     
        ret = pp.append_bit(bit)
        if ret:
            self._fsm.process_bits(ret, packet_type)


    
