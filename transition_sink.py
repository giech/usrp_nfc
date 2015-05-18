#!/usr/bin/env python

import numpy
from gnuradio import gr

class transition_sink(gr.sync_block):
    "Transition sink" 
    def __init__(self, start_bit, samp_rate, c, max_len=50):
        gr.sync_block.__init__(
            self,
            name = "transition_sink",
            in_sig = [numpy.float32], # Input signature: 1 float at a time
            out_sig = None, # Output signature: 1 float at a time
        )

        self._max = max_len
        self._start_bit = start_bit
        self._samp_rate = samp_rate
        self._reset_bit(self._start_bit)
        self._f = c

    def _reset_bit(self, bit):
        self._dur = 1
        self._last_bit = bit
        
    def _get_cur_value(self):
        return (self._last_bit, self._dur*1e6/self._samp_rate) 

    def work(self, input_items, output_items):
        callback = []
        for bit in input_items[0]:
            
            if bit != self._last_bit:
                callback.append(self._get_cur_value())
                self._reset_bit(bit)
            else:
                self._dur += 1

            if self._dur > self._max:#   and self._last_bit == self._start_bit:
                callback.append(self._get_cur_value())
                self._reset_bit(self._last_bit)

        self._f(callback)
        return len(input_items[0]) # The number of items produced is returned, this can be less than noutput_items

