#!/usr/bin/env python

import lfsr
from utilities import Convert

class cipher:
    def __init__(self, key):
        self._bits = Convert.to_bit_ar(key)

    def get_ar(self):
        return self._ar[:]

    def get_at(self):
        return self._at[:]

    def enc_bits(self, bits, xor=0, is_enc=0, has_parity=1):
        or_bits = self._bits
        k = []
        i = 0
        for bit in bits:
            cur = or_bits[-48:]
            f = cipher._f(cur)
            k.append(f ^ bit)
            if i < 8 or not has_parity: # non-parity bit
                next = cipher._L(cur) ^ (bit&xor) ^ (f&is_enc)
                or_bits.append(next)
                i += 1
            else:
                i = 0
        return k

    def _set_lfsr(self, bits):
        ls = lfsr.lfsr(bits, [16, 18, 19, 21])
        ls.advance(64)
        self._ar = Convert.to_byte_ar(ls.get_contents())
        ls.advance(32)
        self._at = Convert.to_byte_ar(ls.get_contents())

    @staticmethod
    def _remove_parity(bits):
        removed = []
        ll = len(bits)
        for i in xrange(ll):
            if i % 9 != 8:
                removed.append(bits[i])
        return removed

    @staticmethod
    def _add_parity(bits): # only 0s
        ll = len(bits)
        added = []
        for i in xrange(ll):
            added.append(bits[i])
            if i % 8 == 7:
                added.append(0)
        return added

    def set_tag_bits(self, uid_bits, nonce_bits, is_enc=0):
        if is_enc:
            uid_bits = cipher._add_parity(uid_bits)

        ll = len(uid_bits)
        xor_bits = [uid_bits[i] ^ nonce_bits[i] for i in xrange(ll)]
        b = self.enc_bits(xor_bits, 1, is_enc, is_enc) # have parity info only when encrypted
        bits = [uid_bits[i] ^ b[i] for i in xrange(ll)] if is_enc else nonce_bits
        
        self._set_lfsr(cipher._remove_parity(bits) if is_enc else nonce_bits)
        return bits

    @staticmethod
    def _L(k):
        return k[0] ^ k[5] ^ k[9] ^ k[10] ^ k[12] ^ k[14] ^ k[15] ^ k[17] ^ k[19] ^ k[24] ^ k[25] ^ k[27] ^ k[29] ^ k[35] ^ k[39] ^ k[41] ^ k[42] ^ k[43]

    @staticmethod
    def _to_byte_ar(k):
        ret = []
        cur = 0
        curi = 0
        for bit in k:
            if curi < 8:
                cur |= bit << curi
                curi += 1
            if curi == 8:
       #         print format(cur, "#04x"), 
                ret.append(cur)
                curi = 0
                cur = 0
      #  print ''
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

    def _b(self, i):
        s = cipher._f(self._bits[i: i+48])
        return s

