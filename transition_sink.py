#!/usr/bin/env python

import numpy
from gnuradio import gr

class transition_sink(gr.sync_block):
    "Transition sink" 
    def __init__(self, samp_rate, callback, lo_val = 0.1, hi_val = 1.1, av_window=1000, max_len=50):
        gr.sync_block.__init__(
            self,
            name = "transition_sink",
            in_sig = [numpy.float32], # Input signature: 1 float at a time
            out_sig = None, # Output signature: 1 float at a time
        )

        self._max = max_len
        self._samp_rate = samp_rate
        self._reset_bit(0)

        self._index = 0
        self._filled = 0
        self._length = av_window
        self._ar = [0]*self._length
        self._sum = 0
        self._current_state = 0

        self._lo_val = lo_val
        self._hi_val = hi_val
        self._callback = callback

    def _reset_bit(self, bit):
        self._dur = 1
        self._last_bit = bit
    
    def _get_cur_value(self):
        return self._get_cur_value_dur(self._dur)

    def _get_cur_value_dur(self, dur):
        bit = self._last_bit
        if (self._current_state == -1):
            bit += 1
        return (bit, dur*1e6/self._samp_rate)

    def _do_callback(self, data):
        if self._current_state == -1:
            self._callback(data, 1)      
        elif self._current_state == 1:
            self._callback(data, 0)

    def work(self, input_items, output_items):
        ii0 = input_items[0].tolist()
        
        for bit in ii0:
            prev = self._ar[self._index]

            prev_state = self._current_state

            if (self._filled < self._length - 1):
                self._filled += 1
                cur = bit
                val = 0
            else:
                ratio = bit*self._length/self._sum
                if self._lo_val > ratio:
                    val = -1
                    cur = prev
                    self._current_state = -1
                elif self._current_state != -1 and ratio > self._hi_val: # must ignore temp spikes during reader modulation
                    val = 1
                    cur = prev
                    self._current_state = 1
                else:
                    val = 0
                    cur = bit
            
            
            self._ar[self._index] = cur
            self._index = (self._index + 1) % self._length 
            self._sum += (cur - prev)

            if (val == self._last_bit):
                self._dur += 1
            else:
                if prev_state == 0:
                    self._do_callback(self._get_cur_value_dur(self._max))
                else:
                    self._do_callback(self._get_cur_value())
                self._reset_bit(val)


            if self._dur > self._max:
                self._do_callback(self._get_cur_value())
                self._reset_bit(self._last_bit)
                self._current_state = 0

        return len(input_items[0]) # The number of items produced is returned, this can be less than noutput_items

