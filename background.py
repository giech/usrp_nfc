#!/usr/bin/env python

import collections
import threading

from packets import PacketType, CombinedPacketProcessor


from manchester import manchester_decoder
from miller import miller_decoder

class background:
    def __init__(self, reader=False, tag=False):
        self._deque = collections.deque()
        cpp   = CombinedPacketProcessor()
        self._reader = miller_decoder(cpp) if reader else None
        self._tag    = manchester_decoder(cpp) if tag else None 

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True # Daemonize thread
        thread.start() 

    def append(self, transitions, t):
        self._deque.append((transitions, t))

    def run(self):
        while True:
            if not self._deque:
                continue
            transitions, t = self._deque.popleft()
            if t == PacketType.TAG_TO_READER and self._tag:
                self._tag.process_transition([transitions])
            elif t == PacketType.READER_TO_TAG and self._reader:
                self._reader.process_transition([transitions])
                
