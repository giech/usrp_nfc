#!/usr/bin/env python

import numpy
from utilities import PulseLength
from gnuradio import gr

from manchester import manchester_encoder
from miller import miller_encoder

class encoder:
    @staticmethod
    def encode_bits(bits):
        return [(bit, PulseLength.FULL) for bit in bits]

class binary_src(gr.sync_block):
    "Binary source" 
    def __init__(self, samp_rate, encode="same", idle_bit=0, repeat=None): #delay in us, delay=(1,27000)
        gr.sync_block.__init__(
            self,
            name = "binary_src",
            in_sig = None, # Input signature: 1 float at a time
            out_sig = [numpy.complex64], # Output signature: 1 float at a time
        )

        if encode == "manchester":
            self._encoder = manchester_encoder
        elif encode == "miller":
            self._encoder = miller_encoder
        else:
            self._encoder = encoder

        self._mult = samp_rate/1e6
        self._index = 0
        self._bits = []
        self._idle = idle_bit
        self._repeat = repeat
        self._repeat_ind = 0

    def set_bits(self, bits):
        self._bits.extend(self._encoder.encode_bits(bits) + [(2, 0)])
        

    def work(self, input_items, output_items):
        
        oi = output_items[0]

        oi_len = len(oi)
       
        index = self._index
        bits = self._bits
        mult = self._mult
        ar_ind = 0

        
        while ar_ind < oi_len:
            ll = len(bits) # may change
            if ll and index < ll:
                bit, dur = bits[index]
                if bit == 2: # indicates pause
                    index = index + 1
                    break
                dur = int(dur*mult)
                end = ar_ind + dur
                if end > oi_len:
                    break
                oi[ar_ind:end] = [bit]*dur
                ar_ind = end
                index = index + 1
            else:
                index = 0
                self._bits = []
                rem = oi_len - ar_ind
                oi[ar_ind:] = [self._idle]*rem
                ar_ind = oi_len

        self._index = index

        return ar_ind
