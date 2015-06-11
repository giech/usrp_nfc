#!/usr/bin/env python

from gnuradio import gr
from gnuradio import blocks

class record(gr.hier_block2):

    def __init__(self, dst, samp_rate=4e6, mag=False):
        gr.hier_block2.__init__(self, "record",
                gr.io_signature(1, 1, gr.sizeof_gr_complex),
                gr.io_signature(0, 0, 0))
       
        self._sink = blocks.wavfile_sink(dst, 1, int(samp_rate)) # samp_rate vs 2e6?
        if mag:
            self._c2 = blocks.complex_to_mag_squared(1)
        else:
            self._c2 = blocks.complex_to_real(1)
        self.connect(self, self._c2, self._sink)
