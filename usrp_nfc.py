#!/usr/bin/env python


from gnuradio import gr
from gnuradio.eng_option import eng_option
from optparse import OptionParser

import usrp_src
import transition_sink
import background
import decoder
import usrp_sink
import binary_src
import multiplier
import record

from parser import Parser
from tag import Tag

# TODO: READER-TAG emulation

class nfc_eavesdrop(gr.top_block):
    def __init__(self, src="uhd", dst=None, decode="all", samp_rate=2e6):
        super(nfc_eavesdrop, self).__init__()

        reader = decode == "all" or decode == "reader"
        tag = decode == "all" or decode == "tag"

        self._dec = decoder.decoder(src=src, dst=dst, reader=reader, tag=tag, samp_rate=samp_rate)
        self.connect(self._dec)


class reader_emulate(gr.top_block):
    def __init__(self, src="uhd", dst="uhd", samp_rate=2e6, extra=None):
        super(reader_emulate, self).__init__()

        in_rate = samp_rate

        uhd = dst == "uhd"

        if uhd:
            out_rate = 2*in_rate
            dst = None
        else:
            out_rate = in_rate

        self._bin_src = binary_src.binary_src(out_rate, encode="miller", idle_bit=1, repeat=[0, 1, 1, 0, 0, 1, 0]) # repeat REQA


        parser = Parser(extra)
        self._reader = parser.get_reader(self._bin_src.set_bits)

        # Do not record this
        self._dec = decoder.decoder(src=src, dst=None, reader=False, tag=True, samp_rate=in_rate, emulator=self._reader)
        self.connect(self._dec)

        self._mult = multiplier.multiplier(samp_rate=out_rate)
        self.connect(self._bin_src, self._mult)
        if uhd:
            self._sink = usrp_sink.usrp_sink(out_rate)
        else:   
            self._sink = record.record(dst, out_rate)
        
        self.connect(self._mult, self._sink)

# add file parsing for tag
class tag_emulate(gr.top_block):
    def __init__(self, src="uhd", dst="uhd", samp_rate=2e6, extra=None):
        super(tag_emulate, self).__init__()

        in_rate = samp_rate
        uhd = dst == "uhd"

        if uhd:
            out_rate = 2*in_rate
            dst = None
        else:
            out_rate = in_rate

        self._bin_src = binary_src.binary_src(out_rate, encode="manchester", idle_bit=0)

        parser = Parser(extra)
        self._tag = parser.get_tag(self._bin_src.set_bits)

        # Do not record here
        self._dec = decoder.decoder(src=src, dst=None, reader=True, tag=False, samp_rate=in_rate, emulator=self._tag)
        self.connect(self._dec)

        
        self._mult = multiplier.multiplier(samp_rate=out_rate)
        self.connect(self._bin_src, self._mult)
        if uhd:
            # active load modulation
            self._real = blocks.complex_to_real(1)     
            self._thres = blocks.threshold_ff(0.02, 0.1, 0)
            self._r2c = blocks.float_to_complex(1)
            
            self._sink = usrp_sink.usrp_sink(out_rate)
            self.connect(self._mult, self._real, self._thres, self._r2c, self._sink)
        else:   
            self._sink = record.record(dst, out_rate)
            self.connect(self._mult, self._sink)



if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option)
    parser.add_option("-t", "--type", dest="type", help="action type [tag, reader, all]", choices=["tag", "reader", "all"], default="all")
    parser.add_option("-a", "--action", dest="action", help="action [eavesdrop, emulate]", choices=["eavesdrop", "emulate"], default="eavesdrop")


    parser.add_option("-i", "--input", dest="src", help="input wav file or uhd", default="uhd")
    parser.add_option("-s", "--sample_rate", dest="samp_rate", help="sample rate", default="2e6", type="eng_float")
    parser.add_option("-o", "--output", dest="dst", help="output")
    parser.add_option("-e", "--extra_file", dest="extra", help="helper file for emulation")
    (options, args) = parser.parse_args()


    dst = options.dst if hasattr(options, 'dst') else None
    extra = options.extra if hasattr(options, 'extra') else None
    
    t = options.type
    if options.action == "eavesdrop":
        tb = nfc_eavesdrop(src=options.src, dst=dst, decode=t, samp_rate=options.samp_rate)
    else: #emulate
        if t == "tag":
            tb = tag_emulate(src=options.src, dst=dst, samp_rate=options.samp_rate, extra=extra)
        elif t == "reader":
            tb = reader_emulate(src=options.src, dst=dst, samp_rate=options.samp_rate, extra=extra)
        else:
            print "CANNOT YET"

    gr.enable_realtime_scheduling()
    tb.run()
    print "PROCESSING FINISHED"
    import time
    time.sleep(1)
