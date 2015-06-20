#!/usr/bin/env python

import collections
import threading

from packets import PacketType, CombinedPacketProcessor


from manchester import manchester_decoder
from miller import miller_decoder

class background:
    def __init__(self, reader=False, tag=False, emulator=None):
        self._deque = collections.deque()
        cpp   = CombinedPacketProcessor(emulator)
        self._reader = miller_decoder(cpp) if reader else None
        self._tag    = manchester_decoder(cpp) if tag else None 

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True # Daemonize thread
        thread.start() 

    def append(self, transitions):
        self._deque.append(transitions)

    def process_transitions(self, transitions, t):
        if t == PacketType.TAG_TO_READER and self._tag:
            self._tag.process_transition(transitions)
        elif t == PacketType.READER_TO_TAG and self._reader:
            #print "CALLING", transitions, t
            self._reader.process_transition(transitions)

    def run(self):
        while True:
            if not self._deque:
                continue
            transitions = self._deque.popleft()
            a = [] 
            cur = PacketType.TAG_TO_READER
            for val, t in transitions:
                if t == cur:
                    a.append(val)
                else:
                    self.process_transitions(a, cur)
                    a = [val]
                    cur = t
            if a:
                self.process_transitions(a, cur)
                
