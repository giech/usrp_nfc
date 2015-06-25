#!/usr/bin/env python

# Written by Ilias Giechaskiel
# https://ilias.giechaskiel.com
# June 2015

from gnuradio import gr
from gnuradio import blocks

class record(gr.hier_block2):

    def __init__(self, dst, samp_rate=2e6):
        gr.hier_block2.__init__(self, "record",
                gr.io_signature(1, 1, gr.sizeof_gr_complex),
                gr.io_signature(0, 0, 0))
       
        self._sink = blocks.wavfile_sink(dst, 1, int(samp_rate))
        self._c2 = blocks.complex_to_real(1)
        self.connect(self, self._c2, self._sink)
