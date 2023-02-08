
from __future__ import annotations
import mido
import math
from dataclasses import dataclass

from .lerp import remap

@dataclass
class FloatNotePlayer:
    channel: int = 0

    current_pitchbend_range: float = 2.0
    current_pitchbend: int = 0
    current_coarse: int | None = None

    def split_hi_lo(self, word: int) -> tuple[int,int]:
        assert 0 <= word <= 0x3fff
        hi = word >> 7
        lo = word & 0x7f
        return hi, lo

    def address_rpn(self, param_num: int):
        hi, lo = self.split_hi_lo(param_num)
        yield mido.Message('control_change', channel=self.channel, control=0x64, value=lo) # 0x64 = control for 'RPN lo byte'
        yield mido.Message('control_change', channel=self.channel, control=0x65, value=hi) # 0x65 = control for 'RPN hi byte'
    
    def set_rpn_value(self, param_value: int | tuple[int, int|None]):
        try:
            hi, lo = param_value
        except TypeError:
            hi, lo = self.split_hi_lo(param_value)

        assert 0 <= hi <= 127
        assert 0 <= lo <= 127 or lo is None

        yield mido.Message('control_change', channel=self.channel, control=0x06, value=hi) # 0x06 = control for 'Data Entry (Coarse)'
        if lo is not None:
            yield mido.Message('control_change', channel=self.channel, control=0x26, value=lo) # 0x26 = control for 'Data Entry (Fine)'

    def set_rpn(self, param_num: int, param_value: int | tuple[int, int|None]):
        yield from self.address_rpn(param_num)
        yield from self.set_rpn_value(param_value)
        yield from self.address_rpn(0x3fff) # 0x3fff = "end of controller sequence"
    
    def set_pitchbend_range(self, semitones: float):
        self.current_pitchbend_range = semitones
        coarse = math.floor(semitones)
        fine = math.floor((semitones - coarse) * 128)
        yield from self.set_rpn(0x0000, (coarse, fine)) # 0x0000 = RPN for 'Pitch bend range'

    def set_tuning(self, semitones: float):
        coarse = round(semitones)
        fine = math.floor(remap(-1, 1, 0, 0x3fff, semitones - coarse))
        yield from self.address_rpn(0x0002) # 0x0001 = RPN for 'Coarse tuning'
        yield from self.set_rpn_value((coarse,None))
        yield from self.address_rpn(0x0001) # 0x0001 = RPN for 'Fine tuning'
        yield from self.set_rpn_value(fine)
        yield from self.address_rpn(0x3fff) # 0x3fff = "end of controller sequence"

    def set_pitchbend(self, semitones: float):
        assert abs(semitones) <= self.current_pitchbend_range
        param = math.floor(remap(-self.current_pitchbend_range, self.current_pitchbend_range, -8192, 8191, semitones))
        if not param == self.current_pitchbend:
            self.current_pitchbend = semitones
            yield mido.Message('pitchwheel', channel=self.channel, pitch=param)

    def note_on(self, semitones: float):
        assert self.current_coarse is None
        coarse = round(semitones)
        fine = semitones - coarse
        yield from self.set_pitchbend(fine)
        self.current_coarse = coarse
        yield mido.Message('note_on', channel=self.channel, note=coarse)
    
    def note_off(self):
        if self.current_coarse is not None:
            yield mido.Message('note_off', channel=self.channel, note=self.current_coarse)
            self.current_coarse = None
    
    def reset(self):
        yield from self.note_off()
        yield from self.set_pitchbend(0)
        yield from self.set_pitchbend_range(2)
