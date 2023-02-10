from __future__ import annotations
import itertools
from .tone import Tone

dtmf_l: list[Tone] = [
    Tone(freq=697),
    Tone(freq=770),
    Tone(freq=852),
    Tone(freq=941),
]
dtmf_h: list[Tone] = [
    Tone(freq=1209),
    Tone(freq=1336),
    Tone(freq=1477),
    Tone(freq=1633),
]
dtmf_keypad: list[str] = [
    "123A",
    "456B",
    "789C",
    "*0#D",
]
dtmf_lh: dict[str, tuple[Tone, Tone]] = {"key_" + dtmf_keypad[i][j] + "_lh": (low, high) for ((i,low), (j,high)) in itertools.product(enumerate(dtmf_l), enumerate(dtmf_h)) }
dtmf_hl: dict[str, tuple[Tone, Tone]] = {"key_" + dtmf_keypad[i][j] + "_hl": (high, low) for ((i,low), (j,high)) in itertools.product(enumerate(dtmf_l), enumerate(dtmf_h)) }
dtmf: dict[str, tuple[Tone, Tone]] = {**dtmf_lh, **dtmf_hl}

def get_dtmf(key: str, low_tone_first: bool = True) -> tuple[Tone, Tone]:
    if key in dtmf:
        return dtmf[key]
    else:
        suffix = '_lh' if low_tone_first else '_hl'
        lookup = 'key_' + key + suffix
        return dtmf[lookup]

dial_US = [Tone(freq=350), Tone(freq=440)]
busy_US = [Tone(freq=480), Tone(freq=620)]
ring_US = [Tone(freq=440), Tone(freq=480)]

dial_UK = [Tone(freq=350), Tone(freq=450)]
dial_EU = [Tone(freq=425)]
dial_FR = [Tone(freq=440)]
dial_JP = [Tone(freq=400)]
