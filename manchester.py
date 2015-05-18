#!/usr/bin/env python

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
import gr_queue
from optparse import OptionParser

class manchester(gr.top_block):

    def __init__(self):
        super(manchester, self).__init__()

        self.samp_rate = samp_rate = 2000000
        self.zero_val = zero_val = 0.150
        self.mult_const = mult_const = 4.5

        self.blocks_wavfile_source_0 = blocks.wavfile_source("/home/ilias/Desktop/read1-fixed.wav", False)
        self.blocks_threshold_ff_0 = blocks.threshold_ff(0, 0.5, 0)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vff((mult_const, ))
        self.blocks_add_const_vxx_0 = blocks.add_const_vff((-zero_val*mult_const, ))

        self.sink = gr_queue.queue_sink_f()


        self.connect((self.blocks_wavfile_source_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_add_const_vxx_0, 0))
        self.connect((self.blocks_add_const_vxx_0, 0), (self.blocks_threshold_ff_0, 0))
        self.connect(self.blocks_threshold_ff_0, self.sink)

    def __iter__(self):
        return self.sink.__iter__()


def transition(stream):
    last = 0
    last_i = 0

    for i, val in enumerate(stream):
       # print i
        if val != last:
            yield (last, i-last_i)
            last_i = i
            last = val

        if i - last_i > 50 and last == 0:
            yield (0, 1000)
            last = val

# based on 
def manchester_decode(stream):
    prev_set = False
    prev = 0
    
    for cur, dur in transition(stream):
        # convert the time in samples to microseconds
        
        dur = dur / float(stream.samp_rate) * 1e6
        #print cur, dur
        if dur < 4 or dur > 10:
            prev_set = False
            prev = 0
            yield 2 # before start or after end
            continue

        dual = dur > 5.5
        
        if prev_set:
            if prev == cur:
                print "REJECT -- INTERNAL ERROR SAME"
            elif prev == 0:
                yield 0
            elif prev == 1:
                yield 1
            else:
                print "REJECT - INTERNAL ERROR NON BINARY"
            prev_set = dual
        else:
            if dual:
                print "REJECT -- WRONG ENCODING"
            else:
                prev_set = True

        prev = cur

CRC_14443_A = 0x6363
CRC_14443_B	= 0xFFFF

def calculate_crc(data, cktp=CRC_14443_A):
    wcrc = cktp
    for b in data:               
        b = b ^ (wcrc & 0xFF)
        b = b ^ (b << 4) & 0xFF
        wcrc = ((wcrc >> 8) ^ (b << 8) ^ (b << 3) ^ (b >> 4))
    
    if (cktp == CRC_14443_B):
        wcrc = ~wcrc

    return [wcrc & 0xFF, (wcrc >> 8) & 0xFF]

def check_crc(data, cktp=CRC_14443_A):
    crc = calculate_crc(data[:-2], cktp)
    return crc[0] == data[-2] and crc[1] == data[-1] 


def process_bytes(bytes):
   for byte in bytes:    
        print format(byte, "#04X")
   print "FINISHED SECTION"
   # print "CRC OK" if check_crc(bytes) else "CRC FAILED"


def tag_decode(stream):
    started = False    
    cur_byte = 0
    cur_bits = 0
    set_bits = 0
    bytes = []

    for bit in manchester_decode(stream):
        if bit != 0 and bit != 1:
            if not started:
                continue
            else:
                if cur_bits == 8:
                    if set_bits & 1 == 0: # must have even number, so that last bit would be 1, ie |-|________
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
            if bit == 1:
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
    tb = manchester()
    tb.start()
    tag_decode(tb)

