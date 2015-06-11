#!/usr/bin/env python

from gnuradio import gr
from gnuradio import blocks

import usrp_src
import transition_sink
import background

class decoder(gr.hier_block2):
    def __init__(self, src="uhd", dst=None, repeat=False, reader=True, tag=True, samp_rate=2e6, emulator=None):
        gr.hier_block2.__init__(self, "decoder",
                gr.io_signature(0, 0, 0), # Input signature
                gr.io_signature(0, 0, 0)) # Output signature

        if src == "uhd":
            self._src = usrp_src.usrp_src(samp_rate=samp_rate, dst=dst)
            hi_val = 1.1
        else:
            self._src = blocks.wavfile_source(src, repeat)
            hi_val = 1.05

        self._back = background.background(reader, tag, emulator)    
        self._trans = transition_sink.transition_sink(samp_rate, self._back.append, hi_val=hi_val)
        self._connect(self._src, self._trans)
