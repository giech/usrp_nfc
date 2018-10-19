#!/usr/bin/env python

# Written by Ilias Giechaskiel
# https://ilias.giechaskiel.com
# June 2015

from gnuradio import gr
from gnuradio import blocks

import usrp_src
import transition_sink
import background
import record

class decoder(gr.hier_block2):
    def __init__(self, src="uhd", dst=None, repeat=False, reader=True, tag=True, samp_rate=2e6, emulator=None):
        gr.hier_block2.__init__(self, "decoder",
                gr.io_signature(0, 0, 0), # Input signature
                gr.io_signature(0, 0, 0)) # Output signature

        if src == "uhd":
            self._src = usrp_src.usrp_src(samp_rate=samp_rate, dst=dst)
            hi_val = 1.1
        else:
            self._wav = blocks.wavfile_source(src, repeat)
            self._r2c = blocks.float_to_complex(1)
            self._src = blocks.complex_to_mag_squared(1)
            self.connect(self._wav, self._r2c, self._src)
            hi_val = 1.09 # may need to be set to 1.05 depending on antenna setup

        self._back = background.background(reader, tag, emulator)    
        self._trans = transition_sink.transition_sink(samp_rate, self._back.append, hi_val=hi_val)
        self.connect(self._src, self._trans)

        if dst and dst != "uhd" and src == "uhd":
            self._rec = record.record(dst, samp_rate)
            self.connect(self._src, self._rec)

