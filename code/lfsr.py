#!/usr/bin/env python

# Written by Ilias Giechaskiel
# https://ilias.giechaskiel.com
# June 2015

class lfsr:
    def __init__(self, init_value, positions):
        self._ar = []
        self._ar[:] = init_value
        self._pos = []
        self._pos[:] = positions
        self._index = 0


    def advance(self, ticks=1):
        ll = len(self._ar)
        for i in xrange(ticks):
            b = self.get_current_value()
            self._ar[self._index] = b
            self._index = (self._index + 1) %ll


    def get_current_value(self):
        b = 0
        ind = self._index
        ar = self._ar        
        ll = len(ar)
        for i in self._pos:
            
            b ^= ar[(i + ind) % ll]

        return b

    def get_contents(self):
        ret = []
        ar = self._ar
        ind = self._index
        ll = len(ar)
        for i in xrange(ll):
            ret.append(ar[(ind + i) % ll])

        return ret
