#!/usr/bin/env python

import numpy
from utilities import PulseLength
from gnuradio import gr

from manchester import manchester_encoder

class binary_src(gr.sync_block):
    "Binary source" 
    def __init__(self, samp_rate, bits):
        gr.sync_block.__init__(
            self,
            name = "binary_src",
            in_sig = None, # Input signature: 1 float at a time
            out_sig = [numpy.complex64], # Output signature: 1 float at a time
        )

        
        self._bits = manchester_encoder.encode_bits(bits)
        self._index = 0
        self._mult = samp_rate/1e6

    def work(self, input_items, output_items):
        
        oi = output_items[0]

        oi_len = len(oi)
       
        index = self._index
        bits = self._bits
        ll = len(bits)
        mult = self._mult
        ar_ind = 0

        while True:
            bit, dur = bits[index]
            dur = int(dur*mult)        
            end = ar_ind + dur
            if end > oi_len:
                break
            oi[ar_ind:end] = [bit]*dur
            ar_ind = end
            index = (index + 1)%ll

        self._index = index


        return ar_ind
