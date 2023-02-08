from __future__ import annotations
import dataclasses
from dataclasses import dataclass
from operator import attrgetter
import math
import numbers

__all__ = ["Tuning", "Tone"]

@dataclass
class Tuning:
    ref_freq: float = 440.0
    ref_note: int | float = 69 # A
    
    octave_factor: int | float = 2
    octave_count: int | float = 12

    def freq_for_note(self, note: int | float) -> float:
        return self.ref_freq * self.octave_factor ** ((note - self.ref_note) / self.octave_count)

    def note_for_freq(self, freq: int | float) -> float:
        return self.octave_count * math.log(freq / self.ref_freq, self.octave_factor) + self.ref_note
    
TUNING_12ET_A440 = Tuning()

class FreqConversionDescriptor:
    def __set_name__(self, owner, name:str):
        self._freq_name = "_" + name
        self._note_name = "_" + name.replace('freq', 'note')
        self._tuning_name = name.replace('freq', 'tuning')

    def __get__(self, obj, type):
        if obj is None:
            return None
        freq = getattr(obj, self._freq_name)
        if freq is None:
            note = getattr(obj, self._note_name) # type: float
            tuning = getattr(obj, self._tuning_name, TUNING_12ET_A440) # type: Tuning
            freq = tuning.freq_for_note(note)
        return freq

    def __set__(self, obj, value: float):
        if value is not None:
            setattr(obj, self._note_name, None)
        setattr(obj, self._freq_name, value)

class NoteConversionDescriptor:
    def __set_name__(self, owner, name:str):
        self._note_name = "_" + name
        self._freq_name = "_" + name.replace('note', 'freq')
        self._tuning_name = name.replace('note', 'tuning')

    def __get__(self, obj, type):
        if obj is None:
            return None
        note = getattr(obj, self._note_name)
        if note is None:
            freq = getattr(obj, self._freq_name) # type: float
            tuning = getattr(obj, self._tuning_name, TUNING_12ET_A440) # type: Tuning
            note = tuning.note_for_freq(freq)
        return note

    def __set__(self, obj, value: float):
        if value is not None:
            setattr(obj, self._freq_name, None)
        setattr(obj, self._note_name, value)


@dataclass
class Tone:
    freq: FreqConversionDescriptor = FreqConversionDescriptor()
    note: NoteConversionDescriptor = NoteConversionDescriptor()
    tuning: Tuning = TUNING_12ET_A440

    def __repr__(self): # skip default-valued fields, taken from https://stackoverflow.com/a/72161437/1324631
        nodef_f_vals = (
            (f.name, attrgetter(f.name)(self))
            for f in dataclasses.fields(self)
            if attrgetter(f.name)(self) != f.default
        )
        nodef_f_repr = ", ".join(f"{name}={value}" for name, value in nodef_f_vals)
        return f"{self.__class__.__name__}({nodef_f_repr})"
    
    def __add__(self, other):
        if isinstance(other, numbers.Real): 
            return Tone(note=self.note + other)
        else:
            return NotImplemented
    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, numbers.Real):
            return self + (-other)
        elif isinstance(other, Tone):
            return self.note - other.note
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, numbers.Real):
            return Tone(freq=self.freq * other)
        else:
            return NotImplemented
    
    def __truediv__(self, other):
        if isinstance(other, numbers.Real):
            return Tone(freq=self.freq / other)
        elif isinstance(other, Tone):
            return self.freq / other.freq
        else:
            return NotImplemented



    