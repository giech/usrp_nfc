#!/usr/bin/env python

from gnuradio import gr
from gnuradio import blocks

class digitizer(gr.hier_block2):

    def __init__(self, mult=1, add=0, lo=0, hi=1, start=0): # lo + hi are orig
        
        gr.hier_block2.__init__(self, "digitizer",
                gr.io_signature(1, 1, gr.sizeof_float), # Input signature
                gr.io_signature(1, 1, gr.sizeof_float))       # Output signature

        
        self._mult  = mult
        self._add   = add
        self._lo    = lo
        self._hi    = hi
        self._start = start

        self.mult  = blocks.multiply_const_vff((self._mult, ))
        self.add   = blocks.add_const_vff((self._add, ))
        self.thres = blocks.threshold_ff(self._lo, self._hi, self._start)
        # If the signal excedes the hi value, it will output a 1 until the signal falls below the lo value. 

        self.connect(self, self.mult, self.add, self.thres, self)

