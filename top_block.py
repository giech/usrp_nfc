!/usr/bin/env python

from gnuradio import blocks
from gnuradio import gr
from gnuradio.eng_option import eng_option
from optparse import OptionParser

import gr_queue
import numpy
import utilities as u
import digitizer

from packets import CombinedPacketProcessor, PacketType
import transition

class top_block(gr.top_block):



if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = top_block()
    tb.start()
    md = manchester_decoder(tb.get_sink())
    md.process()
