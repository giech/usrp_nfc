#!/usr/bin/env python

from gnuradio import blocks
from gnuradio import gr

import utilities as u
from packets import PacketType

class manchester_decoder:

    def __init__(self, cpp):
        self._cpp = cpp
        dur = u.PulseLength.HALF
        self._lo = dur - 1
        self._mid = dur + 1
        self._hi = 2*dur + 1 
        self._reset_decoder()
            
    def _reset_decoder(self):
        self._prev_set = False
        self._prev = 0

    def _process_bit(self, bit):
        self._cpp.append_bit(bit, PacketType.TAG_TO_READER)

    def process_transition(self, transitions):
        for trans in transitions:
            #print trans
            cur, dur = trans
            err = u.ErrorCode.NO_ERROR
            if dur < self._lo:
                err = u.ErrorCode.TOO_SHORT
            elif dur > self._hi:
                err = u.ErrorCode.TOO_LONG
            
            if err != u.ErrorCode.NO_ERROR:
                self._reset_decoder()
                self._process_bit(err)
                continue
            dual = dur > self._mid
            
            prev = self._prev
            
            if self._prev_set:
                if prev == cur or (prev != 0 and prev != 1):
                    self._process_bit(u.ErrorCode.INTERNAL)
                    continue
                
                self._process_bit(int(prev))
                self._prev_set = dual
            else:
                if dual:
                    self._process_bit(u.ErrorCode.ENCODING)
                    continue    
                self._prev_set = True

            self._prev = cur


class manchester_encoder:

    @staticmethod
    def encode_bits(bits):
        durs = [(1, u.PulseLength.HALF), (0, u.PulseLength.HALF)]
        last = 0
        for bit in bits[1:]:
            if bit == last:
                durs[-1] = (bit, u.PulseLength.FULL)
                last = 1 - last
                durs.append((last, u.PulseLength.HALF))
            else:
                durs.append((1 - last, u.PulseLength.HALF))
                durs.append((last, u.PulseLength.HALF) )
                
        return durs

if __name__ == '__main__':
    from packets import CommandType
    bytes = CommandType.get_bytes(CommandType.SEL1T) 
    bits = CommandType.get_bits(CommandType.SEL1T, bytes)    
    ans = manchester_encoder.encode_bits(bits)
    for pair in ans:
        print pair
