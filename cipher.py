#!/usr/bin/env python

import lsfr

class cipher:

    def __init__(self, key, uid, tag_nonce, reader_nonce=None):
        # 48, 32, 32 bits

        bits = cipher._to_bit_ar(key)
        self._bits = bits


        tag_bits = cipher._to_bit_ar(tag_nonce)

        ls = lsfr.lsfr(tag_bits, [16, 18, 19, 21])
        ls.advance(64)
        self._ar = ls.get_contents()
        ls.advance(32)
        self._at = ls.get_contents()
        uid_bits = cipher._to_bit_ar(uid)


        for i in xrange(32):
            next_bit = cipher._L(bits[-48:]) ^ tag_bits[i] ^ uid_bits[i]
            bits.append(next_bit)

    def set_nonce(self, bytes):
        bits = self._bits[0:80]
        self._bits = bits
        rdr_bits = cipher._to_bit_ar(bytes)
        k = []
        for i in xrange(32):
            cur_48 = bits[-48:]
            cur_bit = rdr_bits[i]
            next_bit = cipher._L(cur_48) ^ cur_bit
            enc_bit = cipher._f(cur_48) ^ cur_bit
            bits.append(next_bit)
            k.append(enc_bit)

        k.extend(self.encrypt_next_bits(self._ar))

        k.extend(self.encrypt_next_bits(self._at))

        return cipher._to_byte_ar(k)

            
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
                print format(cur, "#04x"), 
                ret.append(cur)
                curi = 0
                cur = 0
        print ''
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

    def recover_reader_nonce(self, bytes):
        return self.recover_next_bytes(bytes, xor=True)

    def recover_next_bytes(self, bytes, xor=False):
        rdr_bits = cipher._to_bit_ar(bytes)
        bit_ar = self._bits        
        u = []
        for bit in rdr_bits:
            cur_ar = bit_ar[-48:]
            c = cipher._f(cur_ar)
            unenc = bit ^ c
            u.append(unenc)
            l = cipher._L(cur_ar)
            bit_ar.append(l ^ unenc if xor else l)

        return cipher._to_byte_ar(u)

    def _b(self, i):
        s = cipher._f(self._bits[i: i+48])
        return s

    def get_ar(self):
        bs = [self._b(i) for i in xrange(64, 96)]

if __name__ == '__main__':
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]#[0x62, 0xBE, 0xA1, 0x92, 0xFA, 0x37]#[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    uid = [0xCD, 0x76, 0x92, 0x74]#[0xc1, 0x08, 0x41, 0x6a]#[0xCD, 0x76, 0x92, 0x74]
    tag_nonce = [0x0E, 0x61, 0x64, 0xD6]#[0xab, 0xcd, 0x19, 0x49]#[0x0E, 0x61, 0x64, 0xD6]
    reader_enc_nonce = [0x78, 0x5A, 0x41, 0x80]#[0x59, 0xd5, 0x92, 0x0f]#[0x78, 0x5A, 0x41, 0x80]
    reader_nonce = [0x15, 0x45, 0x90, 0xa8]#[0x16, 0x05, 0x49, 0x0d] #[0x15, 0x45, 0x90, 0xa8]
    cp = cipher(key, uid, tag_nonce)
    cp.set_nonce(reader_nonce)
    cp.recover_next_bytes([0x69, 0xAC, 0x4F, 0x02])
    cp.recover_next_bytes([0xBC, 0x2F, 0xBD, 0xB1, 0x75, 0x44, 0x3C, 0xD7, 0xD2, 0x28, 0x3B, 0xA5, 0x08, 0x04, 0x88, 0x18, 0x89, 0x42])
    
    #cp.recover_reader_nonce(reader_enc_nonce)
   # cp.recover_next_bytes([0x15, 0xb9, 0xd5, 0x53, 0xa7, 0x9a, 0x3f, 0xee])


#EXTRA: 0X78 0X5A 0X41 0X80 0X50 0X04 0X8F 0X22 

#EXTRA: 0XCE 0XCA 0X0D 0X83 

