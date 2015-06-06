#!/usr/bin/env python

import numpy
from gnuradio import gr

class transition_sink(gr.sync_block):
    "Transition sink" 
    def __init__(self, samp_rate, callback, lo_val = 0.1, hi_val = 1.1, av_window=2000, max_len=50):
        gr.sync_block.__init__(
            self,
            name = "transition_sink",
            in_sig = [numpy.float32], # Input signature: 1 float at a time
            out_sig = None, # Output signature: 1 float at a time
        )

        self._max = max_len
        self._factor = 1e6/samp_rate
        self._dur = 1
        self._last_bit = 0

        self._index = 0
        self._filled = 0
        self._length = av_window
        self._ar = [0]*self._length
        self._sum = 0
        self._current_state = 0

        self._lo_val = lo_val
        self._hi_val = hi_val
        self._callback = callback


    def work_stable(self, input_items, output_items):
        
        ii0 = input_items[0].tolist()
        ar = self._ar
        length = self._length

        index = self._index
        cur_state = self._current_state
        ss = self._sum
        lo = self._lo_val
        hi = self._hi_val
        dur = self._dur
        last_bit = self._last_bit
        mx = self._max
        factor = self._factor

        callbacks = []

        for bit in ii0:
            prev = ar[index]
            prev_state = cur_state

            ratio = bit*length/ss

            if lo > ratio:
                val = -1
                cur = prev
                cur_state = 2
            elif cur_state != 2 and ratio > hi: # must ignore temp spikes during reader modulation
                val = 1
                cur = prev
                cur_state = 1
            else:
                val = 0
                cur = bit
            
            
            ar[index] = cur
            index = (index + 1) % length 
            ss += (cur - prev)

            if val == last_bit:
                dur += 1
            else:
                d = mx if prev_state == 0 else dur
                v = last_bit + 1 if cur_state == 2 else last_bit
                x = ((v, d*factor), cur_state - 1)
                callbacks.append(x)
                dur = 1
                last_bit = val


            if dur > mx:
                v = last_bit + 1 if cur_state == 2 else last_bit
                callbacks.append(((v, mx*factor), cur_state - 1))
                dur = 1
                cur_state = 0

        self._callback(callbacks)        
        self._index = index
        self._current_state = cur_state
        self._sum = ss
        self._dur = dur
        self._last_bit = last_bit
        return len(ii0)

    def work(self, input_items, output_items):
        ii0 = input_items[0].tolist()
        ar = self._ar
        filled = self._filled
        length = self._length
        need = length - filled
        have = len(ii0)
        can  = min(have, need)

        ar[filled: filled + can] = ii0[0: can]
        self._filled = filled + can 

        if can == need:
            self._sum = sum(ar)
            self._dur = length % self._max
            self.work = self.work_stable
        return can

