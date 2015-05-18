#!/usr/bin/env python
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
import gr_queue
from optparse import OptionParser

class miller(gr.top_block):

    def __init__(self):
        super(miller, self).__init__()
        self.samp_rate = samp_rate = 2000000
        self.mult_const = mult_const = 5

        self.blocks_wavfile_source_0 = blocks.wavfile_source("/home/ilias/Desktop/all-read.wav", False)
        self.blocks_threshold_ff_0 = blocks.threshold_ff(0.1, 0.5, 1)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vff((mult_const, ))

        self.sink = gr_queue.queue_sink_f()


        self.connect((self.blocks_wavfile_source_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_threshold_ff_0, 0))
        self.connect(self.blocks_threshold_ff_0, self.sink)

    def __iter__(self):
        return self.sink.__iter__()


def transition(stream):
    last = 1
    last_i = 0
    for i, val in enumerate(stream):
        if val != last:
            yield (last, i-last_i)
            last_i = i
            last = val

        if i - last_i > 50 and last == 1:
            yield (1, 1000)
            last = val


def miller_decode(stream):
    prev_bit = 1
    ZERO_LEN = 3.0
    PULSE_LEN = 9.44
    HALF_LEN = PULSE_LEN/2
    TOL = 0.5

    dur_0 = 0
    dur_1 = 0
    cur_type = 0

    for cur, dur in transition(stream):
        dur = dur / float(stream.samp_rate)*1e6
        #print cur, dur
        if (dur < 2.5 or dur > 17):
            if cur == 1 and ((cur_type == 0 and dur_0 != 0) or (cur_type == 1 and dur_1 != 0)):
                dur_0 = 0
                dur_1 = 0
                yield cur_type 
            yield 2
            continue

        if dur_0 == 0: # just starting
            if cur == 0:
                if abs(dur - ZERO_LEN) > TOL:
                    print "ERROR WITH 0 LEN...", dur
                    yield 2
                dur_0 = ZERO_LEN
                cur_type = 0
            else:
                if abs(dur - HALF_LEN) < TOL:
                    cur_type = 1
                    dur_0 = HALF_LEN
                elif abs(dur - PULSE_LEN) < TOL:
                    yield 0
                elif abs(dur - HALF_LEN - PULSE_LEN) < TOL:
                    yield 0
                    cur_type = 1
                    dur_0 = HALF_LEN
                else:
                    print "ERROR WITH DUR", dur
                    yield 2
        else:
            if cur_type == 0:
                if cur != 1:
                    print "ERROR WITH 0 CONT"
                    yield 2
                
                if abs(dur - (PULSE_LEN - ZERO_LEN)) < TOL:
                    dur_0 = 0
                    yield 0
                elif abs(dur - (PULSE_LEN + HALF_LEN - ZERO_LEN)) < TOL:
                    dur_0 = HALF_LEN
                    cur_type = 1
                    yield 0
                else:
                    print "ERROR WITH 0 LEN", dur
                    yield 2
            else:
                if dur_1 == 0:
                    if cur != 0:
                        print "ERROR WITH 1 CONT"
                        yield 2
                    if abs(dur - ZERO_LEN) > TOL:
                        print "ERROR WITH 1 CONT LEN", dur
                        yield 2
                    dur_1 = ZERO_LEN
                else:
                    rem = HALF_LEN - ZERO_LEN
                    if dur < rem:
                        print "TOO SHORT"
                        yield 2
                    else:
                        dur_0 = 0
                        dur_1 = 0
                        yield 1
                        dur = dur - rem
        
                        if abs(dur - PULSE_LEN) < TOL:
                            yield 0
                        elif abs(dur - HALF_LEN) < TOL:
                            dur_0 = HALF_LEN
                            cur_type = 1
                        elif abs(dur - (PULSE_LEN + HALF_LEN)) < TOL:
                            yield 0
                            dur_0 = HALF_LEN
                            cur_type = 1
                        else:
                            print "ERROR WITH BLAH"
                            yield 2

def process_bytes(bytes):
   for byte in bytes:    
        print format(byte, "#04X")
   print "FINISHED SECTION"
   # print "CRC OK" if check_crc(bytes) else "CRC FAILED"

def reader_decode(stream):
    started = False    
    cur_byte = 0
    cur_bits = 0
    set_bits = 0
    bytes = []

    for bit in miller_decode(stream):
        if bit != 0 and bit != 1:
            if not started:
                continue
            else:
                if cur_bits == 8:
                    if set_bits & 1 == 1: # must have odd bits, so that it would finish with 0, i.e. (|_|)------
                        bytes.append(cur_byte)
                    else:
                        print "ERROR WITH LAST BYTE"

                process_bytes(bytes)

                # reset
                started = False    
                cur_byte = 0
                cur_bits = 0
                set_bits = 0
                bytes = []
        if not started:
            if bit == 0:
                started = True
            continue

        if cur_bits < 8:       
            cur_byte = cur_byte | (bit << cur_bits)
            cur_bits += 1
            set_bits += bit
        else:
            if set_bits & 1 != bit:
                bytes.append(cur_byte)
            else:
                print "ERROR WITH PARITY BIT!!"
            cur_byte = 0
            cur_bits = 0
            set_bits = 0    
    
if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = miller()   
    tb.start()
    reader_decode(tb)
    

