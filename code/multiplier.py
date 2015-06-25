#!/usr/bin/env python

# Written by Ilias Giechaskiel
# https://ilias.giechaskiel.com
# June 2015

from gnuradio import gr
from gnuradio import analog
from gnuradio import blocks

class multiplier(gr.hier_block2):

    def __init__(self, samp_rate=4e6, freq=13.56e6, A=1):
        gr.hier_block2.__init__(self, "multiplier",
                gr.io_signature(1, 1, gr.sizeof_gr_complex),
                gr.io_signature(1, 1, gr.sizeof_gr_complex))
        
        self._carrier = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq, A, 0)
        self._mult = blocks.multiply_vcc(1)
        self.connect((self._carrier, 0), (self._mult, 0))
        self.connect((self, 0), (self._mult, 1))       
        self.connect(self._mult, self)
