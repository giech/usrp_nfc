#!/usr/bin/env python

from gnuradio import blocks
from gnuradio import gr
from gnuradio.eng_option import eng_option
from optparse import OptionParser

import usrp_src
import transition_sink
import background

# TODO: write output to wav file, option processing

class nfc_eavesdrop(gr.top_block):
    def __init__(self, src="uhd", decode="all", samp_rate=2e6):
        super(nfc_eavesdrop, self).__init__()


        if src == "uhd":
            self._src = usrp_src.usrp_src()
            hi_val = 1.05
        else:
            self._src = blocks.wavfile_source(src, False)
            hi_val = 1.05 # 1.1

        reader = decode == "all" or decode == "reader"
        tag = decode == "all" or decode == "tag"

        self._back = background.background(reader, tag)    
        self._trans = transition_sink.transition_sink(samp_rate, self._back.append, hi_val=hi_val)
        self._connect(self._src, self._trans)
        

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    src =  "/home/ilias/Desktop/recs/ultralight.wav"    
    decode = "all" #"tag"
    gr.enable_realtime_scheduling()
    tb = nfc_eavesdrop(src=src, decode=decode)
    tb.run()
    print "PROCESSING FINISHED"
    import time
    time.sleep(2)
