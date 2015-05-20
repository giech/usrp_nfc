#!/usr/bin/env python

from gnuradio import blocks
from gnuradio import gr
from gnuradio.eng_option import eng_option
from optparse import OptionParser

from manchester import manchester_decoder
from miller import miller_decoder

import usrp_src 
from packets import CombinedPacketProcessor
import transition_sink

class nfc_eavesdrop(gr.top_block):
    def __init__(self, src="uhd", decode="all", samp_rate=2e6):
        super(nfc_eavesdrop, self).__init__()


        if src == "uhd":
            self._src = usrp_src.usrp_src()
        else:
            self._src = blocks.wavfile_source(src, False)

        cpp = CombinedPacketProcessor()
        
        self._trans = transition_sink.transition_sink(samp_rate)
        self._connect(self._src, self._trans)

        if decode == "all" or decode == "reader":
            mild = miller_decoder(cpp)
            self._trans.register_lo_callback(mild.process_transition)

        if decode == "all" or decode == "tag":
            mand = manchester_decoder(cpp)
            self._trans.register_hi_callback(mand.process_transition)

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    src = "uhd" # "/home/ilias/Desktop/nfc-preamble.wav"    
    decode = "all"

    tb = nfc_eavesdrop(src=src, decode=decode)
    tb.run()
