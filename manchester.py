#!/usr/bin/env python

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

class manchester_sink(gr.hier_block2):

    def __init__(self):
        gr.hier_block2.__init__(self, "manchester_sink",
                gr.io_signature(1, 1, gr.sizeof_float), # Input signature
                gr.io_signature(0, 0, 0))       # Output signature

        self._dig = digitizer.digitizer(mult=4.5, add=-0.675, lo=0, hi=0.5, start=0)
        self._sink = gr_queue.queue_sink_f()

        self.connect(self, self._dig, self._sink)

    def get_sink(self):
        return self._sink


class manchester_top(gr.top_block):

    def __init__(self, src="/home/ilias/Desktop/all-read.wav"):
        super(manchester_top, self).__init__()

        self._src = blocks.wavfile_source(src, False)
        self._sink = manchester_sink()               

        self.connect(self._src, self._sink)
    
    def get_sink(self):
        return self._sink.get_sink()

class manchester_decoder:

    def __init__(self, sink, samp_rate=2000000):
        self._t = transition.transition(0, samp_rate)        
        self._sink = sink
        dur = u.PulseLength.HALF
        self._lo = dur - 1
        self._mid = dur + 1
        self._hi = 2*dur + 1 
        self._reset_decoder()
            
    def _reset_decoder(self):
        self._prev_set = False
        self._prev = 0

    def decode(self):
        for cur, dur in self._t.add_next_bit_by_stream(self._sink):
            
            err = u.ErrorCode.NO_ERROR
            if dur < self._lo:
                err = u.ErrorCode.TOO_SHORT
            elif dur > self._hi:
                err = u.ErrorCode.TOO_LONG
            
            if err != u.ErrorCode.NO_ERROR:
                self._reset_decoder()
                yield err
                continue

            dual = dur > self._mid
            
            prev = self._prev
            
            if self._prev_set:
                if prev == cur or (prev != 0 and prev != 1):
                    yield u.ErrorCode.INTERNAL
                    continue
                
                yield int(prev)
                self._prev_set = dual
            else:
                if dual:
                    yield u.ErrorCode.ENCODING
                    continue    
                self._prev_set = True

            self._prev = cur
    
    def process(self, cpp):
        for bit in self.decode():
            cpp.append_bit(bit, PacketType.TAG_TO_READER)

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = manchester_top()
    tb.start()
    md = manchester_decoder(tb.get_sink())
    cpp = CombinedPacketProcessor()
    md.process(cpp)
