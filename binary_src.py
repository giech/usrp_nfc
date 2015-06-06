#!/usr/bin/env python

import numpy
from utilities import PulseLength
from gnuradio import gr

from manchester import manchester_encoder
from miller import miller_encoder

# This actually has horrible race conditions, but it works for now

class encoder:
    @staticmethod
    def encode_bits(bits):
        return [(bit, PulseLength.FULL) for bit in bits]

class binary_src(gr.sync_block):
    "Binary source" 
    def __init__(self, samp_rate, encode="same", idle_bit=0, repeat=[], pause_dur=25000):
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
        self._has_finished = True
        self._pause_dur = pause_dur

    def _encode_pause(self, pause, has_finished):
        if has_finished:
            pause = self._pause_dur
        if pause == 0:
            return [(2, 0)]
        div = 1000        
        d = pause/div
        a = [(self._idle, div)]*d
        r = pause %div
        if r:
            a += [(self._idle, r)]
        return a 

    def set_bits(self, bits, has_finished=False, pause=0):
        encoded = self._encode_pause(pause/2, has_finished)
        self._bits.extend(encoded + self._encoder.encode_bits(bits) + encoded)
        self._has_finished = has_finished

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
                if bit == 2: # indicates temp pause
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
                if self._has_finished and self._repeat:
                   self.set_bits(self._repeat, True, self._pause_dur)
                   continue

                index = 0
                self._bits = []
                rem = oi_len - ar_ind
                oi[ar_ind:] = [self._idle]*rem
                ar_ind = oi_len

        self._index = index

        return ar_ind
