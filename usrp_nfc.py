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

from reader import Reader
from tag import Tag

# TODO: Read Tag from file
# TODO: Pick randomness + remove from Reader, Tag file
# TODO: READER-TAG emulation
# TODO: Parsing

class nfc_eavesdrop(gr.top_block):
    def __init__(self, src="uhd", dst=None, decode="all", samp_rate=2e6):
        super(nfc_eavesdrop, self).__init__()

        reader = decode == "all" or decode == "reader"
        tag = decode == "all" or decode == "tag"

        self._dec = decoder.decoder(src=src, dst=dst, reader=reader, tag=tag, samp_rate=samp_rate)
        self.connect(self._dec)


class reader_emulate(gr.top_block):
    def __init__(self, src="uhd", dst="uhd", samp_rate=2e6):
        super(reader_emulate, self).__init__()

        in_rate = samp_rate
        out_rate = 2*in_rate


        self._bin_src = binary_src.binary_src(out_rate, encode="miller", idle_bit=1, repeat=[0, 1, 1, 0, 0, 1, 0]) # repeat REQA
        self._reader = Reader(self._bin_src.set_bits)

        self._dec = decoder.decoder(src=src, dst=dst, reader=False, tag=True, samp_rate=in_rate, emulator=self._reader)
        self.connect(self._dec)

        uhd = dst == "uhd"
        if uhd:
            dst = None
        self._mult = multiplier.multiplier(samp_rate=out_rate)
        self.connect(self._bin_src, self._mult)
        if uhd:
            self._sink = usrp_sink.usrp_sink(out_rate)
        else:   
            self._sink = record.record(dst, out_rate, True)# mag
        
        self.connect(self._mult, self._sink)

# add file parsing for tag
class tag_emulate(gr.top_block):
    def __init__(self, src="uhd", dst="uhd", samp_rate=2e6):
        super(tag_emulate, self).__init__()

        in_rate = samp_rate
        out_rate = 2*in_rate

        tag_type = 1 # Tag Type
        if tag_type == 0:
            src =  "/home/ilias/Desktop/recs/ultralight.wav"
        else:
            src =  "/home/ilias/Desktop/recs/1k.wav"


        self._bin_src = binary_src.binary_src(out_rate, encode="manchester", idle_bit=0)
        self._tag = Tag(self._bin_src.set_bits, tag_type)

        self._dec = decoder.decoder(src=src, dst=dst, reader=True, tag=False, samp_rate=in_rate, emulator=self._tag)
        self.connect(self._dec)

        uhd = dst == "uhd"
        if uhd:
            dst = None
        self._mult = multiplier.multiplier(samp_rate=out_rate)
        self.connect(self._bin_src, self._mult)
        if uhd:
            # digitize
            self._real = blocks.complex_to_real(1)     
            self._thres = blocks.threshold_ff(0.02, 0.1, 0)
            self._r2c = blocks.float_to_complex(1)
            
            self._sink = usrp_sink.usrp_sink(out_rate)
            self.connect(self._mult, self._real, self._thres, self._r2c, self._sink)
        else:   
            self._sink = record.record(dst, out_rate, True)# mag
            self.connect(self._mult, self._sink)



if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option)
    parser.add_option("-i", "--input", dest="src", help="input wav file or uhd", default="uhd")
    parser.add_option("-s", "--sample_rate", dest="samp_rate", help="sample rate", default="2e6", type="eng_float")
    parser.add_option("-o", "--output", dest="dst", help="output")
    parser.add_option("-f", "--format", dest="f", help="output format")
    parser.add_option("-d", "--decode", dest="decode", help="decode", default="all")
    (options, args) = parser.parse_args()
    print options

    dst = options.dst if hasattr(options, 'dst') else None
    gr.enable_realtime_scheduling()
    tb = nfc_eavesdrop(src=options.src, dst=dst, decode=options.decode, samp_rate=options.samp_rate)
    tb.run()
    print "PROCESSING FINISHED"
    import time
    time.sleep(1)
