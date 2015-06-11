#!/usr/bin/env python

from gnuradio import gr
from gnuradio import analog
from gnuradio import blocks
from gnuradio import uhd

class usrp_sink(gr.hier_block2):

    def __init__(self, samp_rate=4e6, freq=13.56e6):
        gr.hier_block2.__init__(self, "usrp_sink",
                gr.io_signature(1, 1, gr.sizeof_gr_complex),
                gr.io_signature(0, 0, 0))

        self._sink = uhd.usrp_sink(
            device_addr="",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self._sink.set_samp_rate(samp_rate)
        self._sink.set_center_freq(freq)
        self.connect(self, self._sink)
        
