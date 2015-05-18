#!/usr/bin/env python

from gnuradio import blocks
from gnuradio import gr
from gnuradio.eng_option import eng_option
from optparse import OptionParser

from manchester import manchester_decoder
from miller import miller_decoder

import digitizer
import usrp_src 
from packets import CombinedPacketProcessor
import transition_sink

class decoding_sink(gr.hier_block2):

    def __init__(self, callback, start_bit, mult=5, lo=0.1, hi=0.5, samp_rate=2e6):
        
        gr.hier_block2.__init__(self, "decoding_sink",
                gr.io_signature(1, 1, gr.sizeof_float), # Input signature
                gr.io_signature(0, 0, 0))       # Output signature


        self._dig = digitizer.digitizer(mult=mult, lo=lo, hi=hi, start=start_bit)
        self._sink = transition_sink.transition_sink(start_bit, samp_rate, callback)
        self.connect(self, self._dig, self._sink)
    
    def set_threshold(self, lo, hi):
        self._dig.set_lo(lo)
        self._dig.set_hi(hi)
    

class nfc_eavesdrop(gr.top_block):
    def __init__(self, src="uhd", decode="all", samp_rate=2e6):
        super(nfc_eavesdrop, self).__init__()


        if src == "uhd":
            self._src = usrp_src.usrp_src()
        else:
            self._src = blocks.wavfile_source(src, False)

        cpp = CombinedPacketProcessor()


        if decode == "all" or decode == "reader":
            mild = miller_decoder(cpp)
            self._mils = decoding_sink(mild.process_transition, 1, mult=5, lo=0.1, hi=0.5, samp_rate=samp_rate)
            self.connect(self._src, self._mils)

        if decode == "all" or decode == "tag":
            mand = manchester_decoder(cpp)
            self._mans = decoding_sink(mand.process_transition, 0, mult=5, lo=0.75, hi=1.25, samp_rate=samp_rate)
            self.connect(self._src, self._mans)

    def set_threshold(self, decoder, lo, hi):
        if decoder == "reader" and hasattr(self, '_mils'):
            self._mils.set_threshold(lo, hi)           
        elif decoder == "tag" and hasattr(self, '_mans'):
            self._mans.set_threshold(lo, hi)
        else:
            print "ERROR SETTING THRES"


    def set_usrp_thresholds(self):
        if hasattr(self, '_mans'):
            self.set_threshold("tag", 0.45, 0.5)
        if hasattr(self, '_mils'):        
            self.set_threshold("reader", 0.1, 0.3)

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    src = "uhd"    
    decode = "all"

    tb = nfc_eavesdrop(src=src, decode=decode)
    if src == "uhd":
        tb.set_usrp_thresholds()
    tb.run()
