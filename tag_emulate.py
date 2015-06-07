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
import load_modulator
from tag import Tag

# ~ 30-40mV, ~ 18mA for amplitude of 1
        

class tag_emulate(gr.top_block):
    def __init__(self, src="uhd", dst="uhd", samp_rate=2e6):
        super(tag_emulate, self).__init__()

        if src == "uhd":
            self._src = usrp_src.usrp_src()
            hi_val = 1.05
        else:
            self._src = blocks.wavfile_source(src, False)
            hi_val = 1.05 # 1.1

        self._bin_src = binary_src(samp_rate, encode="manchester", idle_bit=0)
        
        self._tag = Tag(self._bin_src.set_bits)
        self._back = background.background(True, False, self._tag)    
        self._trans = transition_sink.transition_sink(samp_rate, self._back.append, hi_val=hi_val)
        self._connect(self._src, self._trans)


        freq = 13560000
        A = 1

        self._mult = blocks.multiply_vcc(1)
        self._carrier = analog.sig_source_c(samp_rate, analog.GR_CONST_WAVE, freq, A, 0)
        self._lm = load_modulator.load_modulator(self._carrier)

        self.connect(self._bin_src, self._lm)
   #     self.connect((self._carrier, 0), (self._mult, 0))
   #     self.connect((self._lm, 0), (self._mult, 1))       

        if dst == "uhd":
            self._sink = uhd.usrp_sink(
                device_addr="",
                stream_args=uhd.stream_args(
                    cpu_format="fc32",
                    channels=range(1),
                ),
            )
            self._sink.set_samp_rate(samp_rate)
            #self._sink.set_center_freq(freq)
            self.connect(self._carrier, self._sink)
        else:
            self._c2 = blocks.complex_to_mag_squared(1) #complex_to_mag_squared #complex_to_real
            self._sink = blocks.wavfile_sink(dst, 1, int(samp_rate))
            self.connect(self._bin_src, self._c2, self._sink)

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    gr.enable_realtime_scheduling()

    src =  "/home/ilias/Desktop/recs/ultralight.wav"
    dst = "/home/ilias/Desktop/test.wav"
    tb = tag_emulate(src, dst)
    tb.run()

