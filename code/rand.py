#!/usr/bin/env python

# Written by Ilias Giechaskiel
# https://ilias.giechaskiel.com
# June 2015

import random
from datetime import datetime

class Rand:

    def __init__(self, rands = None):
        if rands:
            self._rands = rands
            self._randll = len(rands)
            self.get_next = self._get_next_ar
            self.reset = self._reset_ar
        else:
            self._seed = datetime.now()
            self.get_next = self._get_next_rand
            self.reset = self._reset_rand
        self.reset()

    def _get_next_ar(self):
        index = self._index
        r = self._rands[index]
        self._index = (index + 1) % self._randll
        return r

    def _reset_ar(self):
        self._index = 0

    def _get_next_rand(self):
        rands =  []
        for i in xrange(4):
            rands.append(random.randint(0, 255))        
        return rands

    def _reset_rand(self):
        random.seed(self._seed)
