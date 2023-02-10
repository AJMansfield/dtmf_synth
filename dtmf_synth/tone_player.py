
from __future__ import annotations
import mido
import math
from dataclasses import dataclass

from .util import remap
from .tone import Tone
from .midi_constants import *

@dataclass
class TonePlayer:
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
        yield mido.Message('control_change', channel=self.channel, control=CTRL_RPN_ADDR_LO, value=lo) # 0x64 = control for 'RPN lo byte'
        yield mido.Message('control_change', channel=self.channel, control=CTRL_RPN_ADDR_HI, value=hi) # 0x65 = control for 'RPN hi byte'
    
    def set_rpn_value(self, param_value: int | tuple[int, int|None]):
        try:
            hi, lo = param_value
        except TypeError:
            hi, lo = self.split_hi_lo(param_value)

        assert 0 <= hi <= 127
        assert 0 <= lo <= 127 or lo is None

        yield mido.Message('control_change', channel=self.channel, control=CTRL_DATA_ENTRY_HI, value=hi) # 0x06 = control for 'Data Entry (Coarse)'
        if lo is not None:
            yield mido.Message('control_change', channel=self.channel, control=CTRL_DATA_ENTRY_LO, value=lo) # 0x26 = control for 'Data Entry (Fine)'

    def set_rpn(self, param_num: int, param_value: int | tuple[int, int|None]):
        yield from self.address_rpn(param_num)
        yield from self.set_rpn_value(param_value)
        yield from self.address_rpn(RPN_NONE)
    
    def set_pitchbend_range(self, semitones: float):
        self.current_pitchbend_range = semitones
        coarse = math.floor(semitones)
        fine = math.floor((semitones - coarse) * 100)
        yield from self.set_rpn(RPN_PITCHBEND_RANGE, (coarse, fine))

    def set_tuning(self, semitones: float):
        value = math.floor(remap(0, 1, 0x100000, 0x200000, semitones))
        coarse = value >> 14
        fine_hi = (value >> 7) & 0x7f
        fine_lo = value & 0x7f
        yield from self.address_rpn(RPN_COARSE_TUNING)
        yield from self.set_rpn_value((coarse, None))
        yield from self.address_rpn(RPN_FINE_TUNING)
        yield from self.set_rpn_value((fine_hi, fine_lo))
        yield from self.address_rpn(RPN_NONE)

    def set_pitchbend(self, semitones: float):
        assert abs(semitones) <= self.current_pitchbend_range
        param = math.floor(remap(-self.current_pitchbend_range, self.current_pitchbend_range, -0x2000, 0x1fff, semitones))
        if not param == self.current_pitchbend:
            self.current_pitchbend = semitones
            yield mido.Message('pitchwheel', channel=self.channel, pitch=param)

    def note_on(self, tone: Tone):
        assert self.current_coarse is None
        semitones = tone.note
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
