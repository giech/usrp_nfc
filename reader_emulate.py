#!/usr/bin/env python

from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.eng_option import eng_option
from optparse import OptionParser

from gnuradio import uhd

import usrp_src
from binary_src import binary_src

import background
import transition_sink
from reader import Reader
        

class reader_emulate(gr.top_block):
    def __init__(self, src="uhd", dst="uhd", samp_rate=2e6):
        super(reader_emulate, self).__init__()

        if src == "uhd":
            self._src = usrp_src.usrp_src()
            hi_val = 1.05
        else:
            self._src = blocks.wavfile_source(src, False)
            hi_val = 1.05 # 1.1

        self._bin_src = binary_src(samp_rate, encode="miller", idle_bit=1, repeat=[0, 1, 1, 0, 0, 1, 0])
        
        self._reader = Reader(self._bin_src.set_bits)
        self._back = background.background(False, True, self._reader)    
        self._trans = transition_sink.transition_sink(samp_rate, self._back.append, hi_val=hi_val)
        self._connect(self._src, self._trans)


        freq = 13560000
        A = 0.90

        self._mult = blocks.multiply_vcc(1)
        self._carrier = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq, A, 0)

        self.connect((self._carrier, 0), (self._mult, 0))
        self.connect((self._bin_src, 0), (self._mult, 1))       

        if dst == "uhd":
            self._sink = uhd.usrp_sink(
                device_addr="",
                stream_args=uhd.stream_args(
                    cpu_format="fc32",
                    channels=range(1),
                ),
            )
            self._sink.set_samp_rate(samp_rate)
            self._sink.set_center_freq(freq)
            self.connect(self._mult, self._sink)
        else:
            self._c2 = blocks.complex_to_mag_squared(1) #complex_to_mag_squared #complex_to_real
            self._sink = blocks.wavfile_sink(dst, 1, int(samp_rate))
            self.connect(self._mult, self._c2, self._sink)

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    gr.enable_realtime_scheduling()

    src =  "/home/ilias/Desktop/recs/ultralight.wav"
    dst = "/home/ilias/Desktop/test.wav"
    tb = reader_emulate(src)
    tb.run()

