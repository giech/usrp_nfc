#!/usr/bin/env python

from gnuradio import gr
from gnuradio import blocks
from gnuradio.eng_option import eng_option
from gnuradio import uhd

class usrp_src(gr.hier_block2):

    def __init__(self, addr="", samp_rate=2e6, freq=13.57e6, rx_gain=6.5):
        
        gr.hier_block2.__init__(self, "usrp_src",
                gr.io_signature(0, 0, 0), # Input signature
                gr.io_signature(1, 1, gr.sizeof_float))       # Output signature

        self._src = uhd.usrp_source(
            device_addr=addr,
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )

        dec_rate = 32
        sw_dec = 2
        num_taps = int(64000 / ( (dec_rate * 4) * 256 )) #Filter matched to 1/4 of the 256 kHz tag 
        taps = [complex(1,1)] * num_taps
		
        self._filt = gr.fir_filter_ccc(sw_dec, taps);        


        self._src.set_samp_rate(64e6/dec_rate)#samp_rate)
        self._src.set_center_freq(freq, 0)
        print "GAIN", self._src.get_gain_range()		
        self._src.set_gain(rx_gain, 0)
        self._src.set_antenna("RX", 0)
        self._c2m2 = blocks.complex_to_mag_squared(1)

        self.connect(self._src, self._c2m2, self)

