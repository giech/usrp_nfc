#!/usr/bin/env python

import gr_queue

class transition:
    def __init__(self, start_bit, samp_rate, max_len=50):
        self._max = max_len
        self._start_bit = start_bit
        self._samp_rate = samp_rate
        self._reset_bit(self._start_bit)
        
    def _get_tuple(self):
        return (self._last_bit, self._dur*1e6/self._samp_rate)

    def _reset_bit(self, bit):
        self._dur = 1
        self._last_bit = bit

    def add_next_bit_by_stream(self, stream):
        for bit in stream:
            if bit != self._last_bit:
                yield self._get_tuple()
                self._reset_bit(bit)
            else:
                self._dur += 1

            if self._dur > self._max and self._last_bit == self._start_bit:
                yield self._get_tuple()
                self._reset_bit(self._last_bit)
