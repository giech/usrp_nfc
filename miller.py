#!/usr/bin/env python

from gnuradio import blocks
from gnuradio import gr

import utilities as u
from packets import PacketType

class miller_decoder:
    BEGINNING    = 0
    ZERO_STAGE_0 = 1
    ONE_STAGE_0  = 2
    ONE_STAGE_1  = 3

    def __init__(self, cpp):
        self._cpp = cpp

        self._prev = 0
        
        self._lo = u.PulseLength.ZERO - 1
        self._hi = 2*u.PulseLength.FULL 
        self._thres = 0.7
        self._reset()

    def _get_cur_stage(self):
        if self._dur_0 == 0:
            return miller_decoder.BEGINNING
        else:
            if self._cur_type == 0:
                return miller_decoder.ZERO_STAGE_0
            else:
                if self._dur_1 == 0:
                    return miller_decoder.ONE_STAGE_0
                else:
                    return miller_decoder.ONE_STAGE_1

    def _set_cur_stage(self, stage):
        if stage == miller_decoder.BEGINNING:
            self._dur_0 = 0
            self._dur_1 = 0
            self._cur_type = 0
        elif stage == miller_decoder.ZERO_STAGE_0:
            self._dur_0 = u.PulseLength.ZERO
            self._cur_type = 0
        elif stage == miller_decoder.ONE_STAGE_0:
            self._dur_0 = u.PulseLength.HALF
            self._cur_type = 1
        elif stage == miller_decoder.ONE_STAGE_1:
            self._dur_0 = u.PulseLength.HALF
            self._dur_1 = u.PulseLength.ZERO
            self._cur_type = 1
        else:
            raise ValueError('Unknown Stage', str(stage))


    def _is_close(self, dur, av):
        return abs(dur - av) <= self._thres

    def _reset(self):
        self._has_started = False
        self._set_cur_stage(miller_decoder.BEGINNING)

    def process(self, cpp):
        for bit in self.decode():
            cpp.append_bit(bit, PacketType.READER_TO_TAG)

    def handle_beginning(self, cur, dur):
        rets = []

        if cur == 0:
            if self._is_close(dur, u.PulseLength.ZERO):
                self._set_cur_stage(miller_decoder.ZERO_STAGE_0)
                self._has_started = True
            else:
                rets.append(u.ErrorCode.TOO_LONG)
        elif self._has_started:
            bit = 0
            if self._prev == 0:
                bit = u.ErrorCode.ENCODING 

            if self._is_close(dur, u.PulseLength.HALF):
                self._set_cur_stage(miller_decoder.ONE_STAGE_0)
            elif self._is_close(dur, u.PulseLength.FULL):
                rets.append(bit) 
            elif self._is_close(dur, u.PulseLength.FULL + u.PulseLength.HALF):
                rets.append(bit)
                self._set_cur_stage(miller_decoder.ONE_STAGE_0)
            else:   
                rets.append(u.ErrorCode.WRONG_DUR)
        return rets

    def handle_zs0(self, cur, dur):
        rets = []
        if cur == 0:
            rets.append(u.ErrorCode.ENCODING)
        else:
            if self._is_close(dur, u.PulseLength.FULL - u.PulseLength.ZERO):
                self._set_cur_stage(miller_decoder.BEGINNING)
                rets.append(0)
            elif self._is_close(dur, u.PulseLength.FULL + u.PulseLength.HALF - u.PulseLength.ZERO):
                self._set_cur_stage(miller_decoder.ONE_STAGE_0)
                rets.append(0)
            else:
                
                rets.append(u.ErrorCode.WRONG_DUR)
        return rets

    def handle_os0(self, cur, dur):
        rets = []
        if cur != 0:
            rets.append(u.ErrorCode.ENCODING)
        elif not self._is_close(dur, u.PulseLength.ZERO):
            rets.append(u.ErrorCode.WRONG_DUR)
        else:
            self._set_cur_stage(miller_decoder.ONE_STAGE_1)
        return rets

    def handle_os1(self, cur, dur):
        rets = []
        
        if cur != 1:
            rets.append(u.ErrorCode.ENCODING)
        elif self._is_close(dur, u.PulseLength.HALF - u.PulseLength.ZERO):
            rets.append(1)
            self._set_cur_stage(miller_decoder.BEGINNING)
        else:
            rets.append(1)
            self._set_cur_stage(miller_decoder.BEGINNING)

            dur -= (u.PulseLength.HALF - u.PulseLength.ZERO)

            if self._is_close(dur, u.PulseLength.FULL):
                rets.append(0)
            elif self._is_close(dur, u.PulseLength.HALF):
                self._set_cur_stage(miller_decoder.ONE_STAGE_0)
            elif self._is_close(dur, u.PulseLength.FULL + u.PulseLength.HALF):
                rets.append(0)
                self._set_cur_stage(miller_decoder.ONE_STAGE_0)
            else:
                rets.append(u.ErrorCode.WRONG_DUR)

        return rets

    def _process_bit(self, bit):
        self._cpp.append_bit(bit, PacketType.READER_TO_TAG)

    def process_transition(self, transitions):
        for trans in transitions:
            cur, dur = trans
            
            err = u.ErrorCode.NO_ERROR
            cur_stage = self._get_cur_stage()
            #print "STAG", cur_stage            
            #print cur, dur
            
            if (dur < self._lo or dur > self._hi) and (cur_stage == miller_decoder.ZERO_STAGE_0 or cur_stage == miller_decoder.ONE_STAGE_1):
                self._process_bit(self._cur_type)
                err = u.ErrorCode.TOO_LONG # to finish
            elif dur < self._lo:
                err = u.ErrorCode.TOO_SHORT
            elif dur > self._hi:
                err = u.ErrorCode.TOO_LONG

            if err != u.ErrorCode.NO_ERROR:
                self._process_bit(err)
                self._reset()
                continue
            
            if cur_stage == miller_decoder.BEGINNING:
                rets = self.handle_beginning(cur, dur)
            elif cur_stage == miller_decoder.ZERO_STAGE_0:
                rets = self.handle_zs0(cur, dur)
            elif cur_stage == miller_decoder.ONE_STAGE_0:
                rets = self.handle_os0(cur, dur)
            elif cur_stage == miller_decoder.ONE_STAGE_1:
                rets = self.handle_os1(cur, dur)
            else:
                self._process_bit(u.ErrorCode.INTERNAL)

         #   print "RETS", rets

            for ret in rets:
                self._process_bit(ret)
                if ret > 1:
                    self._reset()   
                    self._prev = 0
                else:
                    self._prev = ret

