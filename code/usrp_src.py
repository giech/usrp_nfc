#!/usr/bin/env python

# Written by Ilias Giechaskiel
# https://ilias.giechaskiel.com
# June 2015

from gnuradio import gr
from gnuradio import blocks
from gnuradio import uhd

class usrp_src(gr.hier_block2):

    def __init__(self, samp_rate=2e6, dst=None, freq=13.57e6, rx_gain=6.5):

        gr.hier_block2.__init__(self, "usrp_src",
                gr.io_signature(0, 0, 0), # Input signature
                gr.io_signature(1, 1, gr.sizeof_float))       # Output signature

        self._src = uhd.usrp_source(
            device_addr="",
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )

        self._src.set_samp_rate(samp_rate)
        self._src.set_center_freq(freq, 0)
        self._src.set_gain(rx_gain, 0)
        self._src.set_antenna("RX", 0)
        self._c2m2 = blocks.complex_to_mag_squared(1)

        self.connect(self._src, self._c2m2, self)

        if dst and dst != "uhd":
            self._wav = blocks.wavfile_sink(dst, 1, int(samp_rate), 16)
            self.connect(self._c2m2, self._wav)
