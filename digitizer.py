#!/usr/bin/env python

from gnuradio import gr
from gnuradio import blocks

class digitizer(gr.hier_block2):

    def __init__(self, mult=1, lo=0, hi=1, start=0): # lo + hi are orig
        
        gr.hier_block2.__init__(self, "digitizer",
                gr.io_signature(1, 1, gr.sizeof_float), # Input signature
                gr.io_signature(1, 1, gr.sizeof_float))       # Output signature

        self._m = mult
        self._l = lo
        self._h = hi

        self._mult  = blocks.multiply_const_vff((self._m, ))
        self._thres = blocks.threshold_ff(self._l, self._h, start)
        # If the signal excedes the hi value, it will output a 1 until the signal falls below the lo value. 

        self.connect(self, self._mult, self._thres, self)

    def set_mult(self, mult):
        self._m = mult
        self._mult.set_k(mult)

    def get_mult(self):
        return self._m

    def set_lo(self, lo):
        self._l = lo
        self._thres.set_lo(lo)

    def get_lo(self):
        return self._l

    def set_hi(self, hi):
        self._h = hi
        self._thres.set_hi(hi)

    def get_hi(self):
        return self._h

