#!/usr/bin/env python

from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.eng_option import eng_option
from optparse import OptionParser

from binary_src import binary_src


class tag_emulate(gr.top_block):
    def __init__(self, samp_rate=2e6):
        super(tag_emulate, self).__init__()

        self.sub_freq = sub_freq = 847500
        self.samp_rate = samp_rate = 2000000
        self.freq = freq = 13560000
        self.M = M = 0.3
        self.A = A = 0.7

        self.binary_src = binary_src(samp_rate, encode="manchester", idle_bit=0)
        self.binary_src.set_bits([1,0,0,1,0,0,0,0,1])
        self.mult = blocks.multiply_vcc(1)
        self.add = blocks.add_vcc(1) # add or multiply?
        self.carrier = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq, A, 0)
        
        self.subcarrier = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, sub_freq, M, 0) # analog.GR_SQR_WAVE?

        self.c2m = blocks.complex_to_mag_squared(1) #complex_to_mag_squared

        self.sink = blocks.wavfile_sink("/home/ilias/Desktop/test.wav", 1, samp_rate, 8)
        
        ##################################################
        # Connections
        ##################################################
        self.connect((self.carrier, 0), (self.add, 0))
        
        self.connect((self.subcarrier, 0), (self.mult, 0))
        self.connect((self.binary_src, 0), (self.mult, 1))
        self.connect(self.mult, (self.add, 1))
        self.connect(self.add, self.c2m, self.sink)
        
        self.c2r = blocks.complex_to_real(1)
        self.sink2 = blocks.wavfile_sink("/home/ilias/Desktop/test2.wav", 1, samp_rate, 8)
        self.connect(self.add, self.c2r, self.sink2)

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    gr.enable_realtime_scheduling()
    tb = tag_emulate()
    tb.run()

