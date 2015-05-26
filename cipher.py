#!/usr/bin/env python

import lsfr
class cipher:
    def __init__(self, key):
        self._bits = cipher._to_bit_ar(key)

    def get_ar(self):
        return self._ar[:]

    def get_at(self):
        return self._at[:]

    def enc_bytes(self, bytes, xor=0, is_enc=0): # is_enc, xor must be 0 or 1
        bits = cipher._to_bit_ar(bytes)
        ll = len(bits)
        
        or_bits = self._bits

        k = []
        for i in xrange(ll):
            cur = or_bits[-48:]
            f = cipher._f(cur)
            b = bits[i]            
            k.append(f)
            next = cipher._L(cur) ^ (b&xor) ^ (f & is_enc)
            or_bits.append(next)

        return cipher._to_byte_ar(k)

    def set_tag(self, uid, nonce, is_enc=0):
        ll = len(uid)
        xor = [uid[i] ^ nonce[i] for i in xrange(ll)]
        b = self.enc_bytes(xor, 1, is_enc)
        ans = [nonce[i] ^ b[i] for i in xrange(ll)]

        bits = cipher._to_bit_ar(ans if is_enc else nonce)
        ls = lsfr.lsfr(bits, [16, 18, 19, 21])
        ls.advance(64)
        self._ar = cipher._to_byte_ar(ls.get_contents())
        ls.advance(32)
        self._at = cipher._to_byte_ar(ls.get_contents())
        return ans
    
    def enc_bytes_with_xor(self, bytes, xor=0, is_enc=0):
        a = self.enc_bytes(bytes, xor, is_enc)
        ll = len(a)
        for i in xrange(ll):
            a[i] ^= bytes[i]
        return a

            
    def encrypt_next_bits(self, bits):
        k = []
        ll = len(bits)
        for i in xrange(ll):
            cur_48 = self._bits[-48:]
            self._bits.append(cipher._L(cur_48))
            k.append(cipher._f(cur_48) ^ bits[i])
        return k

    def encrypt_next_bytes(self, bytes):
        bits = cipher._to_bit_ar(bytes)
        return cipher._to_byte_ar(self.encrypt_next_bits(bits))


    @staticmethod
    def _L(k):
        return k[0] ^ k[5] ^ k[9] ^ k[10] ^ k[12] ^ k[14] ^ k[15] ^ k[17] ^ k[19] ^ k[24] ^ k[25] ^ k[27] ^ k[29] ^ k[35] ^ k[39] ^ k[41] ^ k[42] ^ k[43]

    @staticmethod
    def _to_bit_ar(k):
        ret = []
        for b in k:
            for i in xrange(8):#xrange(7, -1, -1):
                ret.append((b >> i) & 1)
        return ret

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

    def get_last_parity_bits(self, num=4):
        bits = []
        ll = len(self._bits)
        for i in xrange(num-1, -1, -1):
            r = self._b(ll - 48 - 8*i)
            bits.append(r)
        return bits


    def _b(self, i):
        s = cipher._f(self._bits[i: i+48])
        return s

if __name__ == '__main2__':
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    uid = [0x9c, 0x59, 0x9b, 0x32]
    tag_nonce = [0x82, 0xa4, 0x16, 0x6c]
    reader_enc_nonce = [0xa1, 0xe4, 0x58, 0xce]
    cp = cipher(key, uid, tag_nonce)


    cp.recover_reader_nonce(reader_enc_nonce)
    cp.recover_next_bytes([0x6e, 0xea, 0x41, 0xe0])
    cp.recover_next_bytes([0x5c, 0xad, 0xf4, 0x39])
    cp.recover_next_bytes([0x8e, 0x0e, 0x5d, 0xb9]) # this is another auth request: ['0x60', '0x00', '0xf5', '0x7b']
    n2 = cp.recover_next_bytes([0x5a, 0x92, 0x0d, 0x85])
    a = cp.recover_next_bytes([0x98, 0xd7, 0x6b, 0x77, 0xd6, 0xc6, 0xe8, 0x70])
    cp2 = cipher(key, uid,n2)
    cp2.recover_reader_nonce(a[0:4]) 
    cp2.recover_next_bytes(a[4:])


def p(bytes):
    for b in bytes:
        print format(b, "#04x")
    print ''

if __name__ == '__main3__':
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    uid = [0x9c, 0x59, 0x9b, 0x32]
    tag_nonce = [0x82, 0xa4, 0x16, 0x6c]
    reader_enc_nonce = [0xa1, 0xe4, 0x58, 0xce, 0x6e, 0xea, 0x41, 0xe0] #EF EA 1C DA 8D 65 73 4B 
    enc_at = [0x5c, 0xad, 0xf4, 0x39] # 9A 42 7B 20 
    enc_auth = [0x8e, 0x0e, 0x5d, 0xb9] # 60 00 F5 7B 
    enc_tag = [0x5a, 0x92, 0x0d, 0x85] #  A5 5D 95 0B 
    enc_rr = [0x98, 0xd7, 0x6b, 0x77, 0xd6, 0xc6, 0xe8, 0x70] # EF 60 E2 6F 14 91 FB DB 
    enc_rrrr = [0xca, 0x7e, 0x0b, 0x63] # A5 38 5D 38 

    '''
    cp = cipher(key)    
    cp.set_tag(uid, tag_nonce)

    b = cp.enc_bytes_with_xor(reader_enc_nonce[0:4], 1, 1)
    p(b)
    b = cp.enc_bytes_with_xor(reader_enc_nonce[4:])
    p(b)
    b = cp.enc_bytes_with_xor(enc_at)
    p(b)
    b = cp.enc_bytes_with_xor(enc_auth)
    p(b)
'''

    cp2 = cipher(key)
    new_nonce = cp2.set_tag(uid, enc_tag, 1)
    print "NEW NONCE"
    p(new_nonce)

    b = cp2.enc_bytes_with_xor(enc_rr[:4], 1)
    p(b)

    cp2 = cipher(key)
    b = cp2.set_tag(uid, new_nonce)
    print "NONCE ENC"
    p(b)

    print "AR"
    p(cp2.get_ar())

   # b = cp2.enc_bytes_with_xor(enc_rr[0:4], 1, 1)
  #  p(b)

    b = cp2.enc_bytes_with_xor([0xef, 0x60, 0xe2, 0x6f], 1, 0)
    p(b)


if __name__ == '__main__':
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    uid = [0XCD, 0X76, 0X92, 0X74]
    enc_nonce = [0X70, 0xbd, 0Xed, 0X81] 
    enc_rn = [0XD0, 0X3A, 0XF1, 0X16]
    enc_ar = [0XDF, 0XFB, 0X98, 0XF8]


    cp = cipher(key)
    b = cp.set_tag(uid, enc_nonce, 1)
    p(b)

    b = cp.enc_bytes_with_xor(enc_rn, 1, 1)
    p(b)

    b = cp.enc_bytes_with_xor(enc_ar)
    p(b)

    p(cp.get_ar())

if __name__ == '__main3__':
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    uid = [0x9c, 0x59, 0x9b, 0x32]

    enc_nonce = [0x5a, 0x92, 0x0d, 0x85]
    cp = cipher(key)
    b = cp.set_tag(uid, enc_nonce, 1)
    p(b)

    rn_enc = [0x98, 0xd7, 0x6b, 0x77]
    ar_enc = [0xd6, 0xc6, 0xe8, 0x70]
    b = cp.enc_bytes_with_xor(rn_enc, 1, 1)
    p(b)

    b = cp.enc_bytes_with_xor(ar_enc)
    p(b)

    p(cp.get_ar())

    # this works if you have plaintext
    '''
    rn = [0x77, 0xB7, 0x89, 0x18]
    b = cp.enc_bytes_with_xor(rn,1)
    p(b)

    b = cp.enc_bytes_with_xor(cp.get_ar())
    p(b)

    b = cp.enc_bytes_with_xor([0xca, 0x7e, 0x0b, 0x63])
    p(b)

    p(cp.get_at())
'''
    #b = cp.enc_bytes_with_xor(cp.get_at())
    #p(b)

if __name__ == '__main2__':
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    uid = [0x15, 0x4d, 0xe5, 0x21]
    tag_nonce = [0x08,  0x23, 0xb3, 0x16]
    reader_enc_nonce = [0xcd,  0x8c,  0x18,  0xd7,  0x74,  0x86,  0xeb,  0x32] # 00 00 00 00 72 3a 73 0a
    enc_at = [0x69, 0x05,  0xed,  0x49  ] # f2 59 7f 9e
    enc_auth = [0x0e,  0xb9,  0xbb,  0xd4 ] # 60  03  6e  49
    enc_tag = [0x4e,  0xd9,  0xce,  0xa2] #   b1  0e  be  bc
    enc_rr = [0x7f,  0x16,  0x9a,  0x25,  0x50,  0xae,  0x0d,  0xe7 ] # 68  f0  cd  33  2e  bd  74  dc

    '''
    cp = cipher(key)    
    cp.set_tag(uid, tag_nonce)

    b = cp.enc_bytes_with_xor(reader_enc_nonce[0:4], 1, 1)
    p(b)
    b = cp.enc_bytes_with_xor(reader_enc_nonce[4:])
    p(b)
    b = cp.enc_bytes_with_xor(enc_at)
    p(b)
    b = cp.enc_bytes_with_xor(enc_auth)
    p(b)
'''

    cp2 = cipher(key)
    new_nonce = cp2.set_tag(uid, enc_tag, 1)
    print "NEW NONCE"
    p(new_nonce)

    rn = [0x68,  0xf0,  0xcd,  0x33]

    print "HERE"
    b = cp2.enc_bytes_with_xor(rn, xor=1)
    p(b)



    cp3 = cipher(key)
    b = cp3.set_tag(uid, new_nonce)
    print "NONCE ENC"
    p(b)

    print "AR"
    p(cp3.get_ar())# 94 40 a7 42 WTF

    b = cp3.enc_bytes_with_xor(enc_rr[0:4])
    p(b)

   # b = cp2.enc_bytes_with_xor(rn)
   # p(b)
