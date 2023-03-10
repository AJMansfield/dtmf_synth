
from __future__ import annotations
import mido
import math
from dataclasses import dataclass, field
from typing import Iterable, Generator

from .util import remap
from .tone import Tone
from .midi_constants import *

@dataclass
class ToneReader:
    channel: int = 0
    """The MIDI channel to interpret."""

    pitchwheel: float = 0
    """The current position of the pitch wheel."""

    rpn_addr_hi: int = 0x7f
    rpn_addr_lo: int = 0x7f
    @property
    def rpn_addr(self):
        """The currently-addressed registered parameter number."""
        return self.combine_hi_lo(self.rpn_addr_hi, self.rpn_addr_lo)
    
    pitchbend_range_coarse: int = 0x02 # in semitones
    pitchbend_range_fine: int = 0x00 # in cents
    @property
    def pitchbend_range(self) -> float:
        """The current Pitchbend Range parameter."""
        return self.pitchbend_range_coarse + self.pitchbend_range_fine/100

    @property
    def pitchbend(self) -> float:
        """The current pitchbend, based on the pitchbend range and pitchwheel position."""
        return self.pitchbend_range * self.pitchwheel

    tuning_coarse: int = 0x40
    tuning_fine_hi: int = 0x00
    tuning_fine_lo: int = 0x00
    @property
    def tuning(self) -> float:
        """The current tuning offset from A440."""
        # [40 00 00] = 0x100000 = A440
        # [41 00 00] = 0x104000 = 1 semitone up
        return remap(0x100000, 0x104000, 0, 1, (self.tuning_coarse << 14) | (self.tuning_fine_hi << 7) | (self.tuning_fine_lo))
    
    @property
    def note_adjustment(self):
        """The combined tuning and pitchbend adjustment."""
        return self.pitchbend + self.tuning

    notes_playing: list[int] = field(default_factory=list) # TODO implement correct multi note_on logic
    notes_meta: dict[int, dict] = field(default_factory=dict)
    def current_tones(self) -> list[Tone]:
        return [Tone(note=note + self.note_adjustment, meta=self.notes_meta[note]) for note in self.notes_playing]
    

    def split_hi_lo(self, word: int) -> tuple[int,int]:
        assert 0 <= word <= 0x3fff
        hi = word >> 7
        lo = word & 0x7f
        return hi, lo
    def combine_hi_lo(self, hi:int, lo:int) -> int:
        assert 0 <= hi <= 0x7f
        assert 0 <= lo <= 0x7f
        return hi << 7 | lo

    def messages_to_tones(self, messages: Iterable[mido.Message]) -> Generator[list[Tone], None, None]:
        last_tones = None
        
        for msg in messages:
            if msg.type == 'note_on' and msg.channel == self.channel:
                self.notes_playing.append(msg.note)
                self.notes_meta[msg.note]['velocity'] = msg.velocity
            elif msg.type == 'note_off' and msg.channel == self.channel:
                self.notes_meta[msg.note]['velocity'] = msg.velocity
                self.notes_playing.remove(msg.note)
            elif msg.type == 'polytouch' and msg.channel == self.channel:
                self.notes_meta[msg.note]['polytouch'] = msg.value
            elif msg.type == 'pitchwheel' and msg.channel == self.channel:
                self.pitchwheel = remap(-8192, 8191, -1, 1, msg.pitch)
            elif msg.type == 'control_change' and msg.channel == self.channel:
                if msg.control == CTRL_RPN_ADDR_HI:
                    self.rpn_addr_hi = msg.value
                elif msg.control == CTRL_RPN_ADDR_LO:
                    self.rpn_addr_lo = msg.value
                elif msg.control == CTRL_DATA_ENTRY_HI:
                    if self.rpn_addr == RPN_PITCHBEND_RANGE:
                        self.pitchbend_range_coarse = msg.value
                    elif self.rpn_addr == RPN_COARSE_TUNING:
                        self.tuning_coarse = msg.value
                    elif self.rpn_addr == RPN_FINE_TUNING:
                        self.tuning_fine_hi = msg.value
                elif msg.control == CTRL_DATA_ENTRY_LO:
                    if self.rpn_addr == RPN_PITCHBEND_RANGE:
                        self.pitchbend_range_fine = msg.value
                    elif self.rpn_addr == RPN_FINE_TUNING:
                        self.tuning_fine_lo = msg.value
            elif msg.type == 'reset':
                self.rpn_addr_hi = 0x7f
                self.rpn_addr_lo = 0x7f
                self.pitchwheel = 0
                self.notes_playing.clear()
                self.notes_meta.clear()
            
            tones = self.current_tones()
            if tones != last_tones:
                last_tones = tones
                yield tones

            