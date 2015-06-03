from command import CommandType, CommandStructure, TagType, PacketType
from cipher import cipher

class fsm:
    
    def __init__(self):
        self._cur_cmd = CommandType.REQA
        self._reset_tag()
        self.set_keys()

    def _reset_tag(self):
        self._uid = []
        self._tag_type = None
        self._encryption = None
        self._readaddr = 0


    def _check_parity(self, bits):
        bytes = []
        cur_byte = 0
        set_bits = 0
        cur_ind = 0       
        for bit in bits:
            if cur_ind < 8:
                cur_byte |= (bit << cur_ind)
                cur_ind += 1
                set_bits += bit
            else:
                if set_bits & 1 == bit: # OK 
                    return None
                else:
                    bytes.append(cur_byte)

                set_bits = cur_byte = cur_ind = 0

        if cur_ind == 8: # should check parity here. see below
            bytes.append(cur_byte)

        return bytes 

    def _fix_ending(self, bits, packet_type):
        ll = len(bits)        
        rem = ll % 9
        start_bit = PacketType.start_bit(packet_type)
        if rem == 0: # complete
            return bits 
        elif rem == 8: # missing final one -- assume same as end bit
            return bits + [start_bit]
        elif rem == 1: # one extra due to overlap
            extra = bits[-1]
            if extra != start_bit:
                print "EXTRA ERROR"
            return bits[:-1]
        else:
            print "MANY MORE ERROR"
            return bits[0:ll-rem]

    def _decrypt_bits(self, bits):
        c = self._encryption        
        if c:
            start_bits = []
            rem_bits = bits
            if self._cur_cmd == CommandType.RANDTA and (len(bits)+1)/9 == CommandType.RANDRB.total_len():
                ll = len(rem_bits)/2           
                rdr_enc_nonce = bits[0:ll]
                start_bits = c.enc_bits(rdr_enc_nonce, 1, 1)                
                rem_bits = bits[ll:]
            elif self._cur_cmd in [CommandType.AUTHA, CommandType.AUTHB]:
                c = cipher(self._cur_key)
                self._encryption = c
                start_bits = c.set_tag_bits(cipher.to_bit_ar(self._uid), bits, 1)
                rem_bits = []
            bits = start_bits + c.enc_bits(rem_bits)
        return bits
    

    def set_keys(self, key_a=[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], key_b=[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]):
        self._keya = key_a
        self._keyb = key_b
        self._cur_key = key_a

    def encrypt_bits(self, bits):
        c = self._encryption
        if c:
            return c.enc_bits(bits)
        else:
            return bits

    def process_command(self, cmd_tp, cmd_str):
        if cmd_tp in [CommandType.REQA, CommandType.WUPA, CommandType.HALT]:
            self._reset_tag()
            self._encryption = None
        elif cmd_tp == CommandType.ATQAUL:
            self._tag_type = TagType.ULTRALIGHT
        elif cmd_tp == CommandType.ATQA1K:
            self._tag_type = TagType.CLASSIC1K
        elif cmd_tp == CommandType.ATQA4K:
            self._tag_type = TagType.CLASSIC4K
        elif cmd_tp == CommandType.ATQADS:
            self._tag_type = TagType.DESFIRE
        elif cmd_tp == CommandType.ANTI1U:
            uid = cmd_str.extra()[0:3]
            self._uid.extend(uid)
        elif cmd_tp == CommandType.ANTI1G:
            uid = cmd_str.extra()[0:4]
            self._uid.extend(uid)
        elif cmd_tp == CommandType.SEL1R:
            start = 1 if self._tag_type == TagType.ULTRALIGHT else 0
            uid = cmd_str.extra()[start:4]
            if uid != self._uid:
                print "MISMATCH BETWEEN READER-TAG UID", uid, self._uid
        elif cmd_tp == CommandType.ANTI2T:
            uid = cmd_str.extra()[0:4]
            self._uid.extend(uid)
        elif cmd_tp == CommandType.SEL2R:
            uid = cmd_str.extra()[0:4]
            if uid != self._uid[-4:]:
                print "MISMATCH BETWEEN READER_TAG UID#2", uid, self._uid
        elif cmd_tp == CommandType.AUTHA:
            self._cur_key = self._keya
        elif cmd_tp == CommandType.AUTHB:
            self._cur_key = self._keyb
        elif cmd_tp == CommandType.RANDTA:
            if not self._encryption:
                self._encryption = cipher(self._cur_key)
                uid_bits = cipher.to_bit_ar(self._uid)
                nonce_bits = cipher.to_bit_ar(cmd_str.extra())
                self._encryption.set_tag_bits(uid_bits, nonce_bits, 0)
        elif cmd_tp == CommandType.RANDRB:
            ar = cmd_str.extra()[4:]
            if ar != self._encryption.get_ar():
                print "ERROR WITH AR"
        elif cmd_tp == CommandType.RANDTB:
            at = cmd_str.extra()
            if at != self._encryption.get_at():
                print "ERROR WITH AT"
        elif cmd_tp == CommandType.READR:
            self._read = cmd_str.extra()

    def process_bits(self, bits, packet_type):
        bits = self._fix_ending(bits, packet_type)

        bits = self._decrypt_bits(bits)
        
        bytes = self._check_parity(bits)

        if not bytes:
            print "PARITY ERROR"
            return
        
        prev_cmd = self._cur_cmd
        cmd = CommandType.get_command_type(bytes, packet_type, prev_cmd)
        if cmd:
            self._cur_cmd = cmd


        c = CommandStructure.decode_command(cmd, bytes)
        self.process_command(cmd, c)
        c.display()
