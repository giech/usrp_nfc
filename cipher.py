#!/usr/bin/env python

import lsfr

class cipher:

    def __init__(self, key, uid, tag_nonce, reader_nonce=None):
        # key is 48 bits
        # tag_nonce is 32 bites
        # uid is 32 bits
        # reader_nonce is 32 bits

        bits = cipher._to_bit_ar(key)
        self._bits = bits
        #print len(bits)

        tag_bits = cipher._to_bit_ar(tag_nonce)

        ls = lsfr.lsfr(tag_bits, [16, 18, 19, 21])
        ls.advance(64)
        self._ar = ls.get_contents()
        print self._ar
        ls.advance(32)
        self._at = ls.get_contents()

        uid_bits = cipher._to_bit_ar(uid)
     #   rdr_bits = cipher._to_bit_ar(reader_nonce)       

        for i in xrange(32):
            next_bit = cipher._L(bits[-48:]) ^ tag_bits[i] ^ uid_bits[i]
            bits.append(next_bit)

        if reader_nonce:
            rdr_bits = cipher._to_bit_ar(reader_nonce)
            for i in xrange(32):
                next_bit = cipher._L(bits[-48:]) ^ rdr_bits[i]
                bits.append(next_bit)
                print rdr_bits[i] ^ cipher._f(bits[-48:])


       # for i in xrange(32):
       #     next_bit = cipher._L(bits[-48:]) ^ rdr_bits[i]
           # print next_bit
      #      bits.append(next_bit)
        #bits.append(cipher._L(bits[-48:]))

        

        
       # print self._at

    @staticmethod
    def _L(k):
        return k[0] ^ k[5] ^ k[9] ^ k[10] ^ k[12] ^ k[14] ^ k[15] ^ k[17] ^ k[19] ^ k[24] ^ k[25] ^ k[27] ^ k[29] ^ k[35] ^ k[39] ^ k[41] ^ k[42] ^ k[43]

    @staticmethod
    def _to_bit_ar(k):
        ret = []
        for b in k:
            for i in xrange(8):#xrange(7, -1, -1):
                ret.append((b >> i) & 1)
        #print ret
        return ret

    @staticmethod
    def _fa(a, b, c, d):
        return ((a or b) ^ (a and d)) ^ (c and ((a ^ b) or d))

    @staticmethod
    def _fb(a, b, c, d):
        return ((a and b) or c) ^ ((a ^ b) and (c or d))

    @staticmethod
    def _fc(a, b, c, d, e):
        return (a or ((b or e) and (d ^ e))) ^ ((a ^ (b and d)) and ((c ^ d) or (b and e)))

        
    @staticmethod
    def _f(ar):
        a = cipher._fa(ar[9], ar[11], ar[13], ar[15])
        b = cipher._fb(ar[17], ar[19], ar[21], ar[23])
        c = cipher._fb(ar[25], ar[27], ar[29], ar[31])
        d = cipher._fa(ar[33], ar[35], ar[37], ar[39])
        e = cipher._fb(ar[41], ar[43], ar[45], ar[47])
    
        return cipher._fc(a, b, c, d, e)

    def recover_reader(self, bytes):
        rdr_bits = cipher._to_bit_ar(bytes)
        bit_ar = self._bits        
        for bit in rdr_bits:
            cur_ar = bit_ar[-48:]
            c = cipher._f(cur_ar)
            unenc = bit ^ c
            bit_ar.append(cipher._L(cur_ar) ^ unenc)

        for i in xrange(32):
            bit_ar.append(cipher._L(bit_ar[-48:]))

        #print len(self._bits)

        for i in xrange(32):
            x= self._ar[i] ^ self._b(64 +i)
            print x  

    def _b(self, i):
        s = cipher._f(self._bits[i: i+48])
       # print s
        return s

    def get_ar(self):
        bs = [self._b(i) for i in xrange(64, 96)]

if __name__ == '__main__':
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF] # reverse the order of these
    uid = [0xCD, 0x76, 0x92, 0x74]#[0x74, 0x92, 0x76, 0xCD]#[0xCD, 0x76, 0x92, 0x74]
    tag_nonce = [0x0E, 0x61, 0x64, 0xD6]#[0xD6, 0x64, 0x61, 0x0E]#[0x0E, 0x61, 0x64, 0xD6]
    reader_enc_nonce = [0x78, 0x5A, 0x41, 0x80]#[0x80, 0x41, 0x5A, 0x78] #[0x78, 0x5A, 0x41, 0x80]
    
    ls = lsfr.lsfr(cipher._to_bit_ar(tag_nonce), [16, 18, 19, 21])
    cp = cipher(key, uid, tag_nonce)#, reader_enc_nonce)
    
    enc_ar = [0x50, 0x04, 0x8F, 0x22]
    cp.recover_reader(reader_enc_nonce)


if __name__ == '__main2__':
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    uid = [0x2a, 0x69, 0x8d, 0x43]#[0xB4, 0x79, 0xF7, 0xD7]
    tag_nonce = [0x3b, 0xae, 0x03, 0x2d]#[0xF3, 0xFB, 0xAE, 0xED]
    #rdr_nonce = [0x07, 0xC9, 0xA9, 0x95]
    cp = cipher(key, uid, tag_nonce)
