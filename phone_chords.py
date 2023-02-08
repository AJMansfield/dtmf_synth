from tone import Tone
import itertools

chords = dict() # type: dict[str, list[Tone]]

dtmf_low = [
    Tone(freq=697),
    Tone(freq=770),
    Tone(freq=852),
    Tone(freq=941),
]
dtmf_high = [
    Tone(freq=1209),
    Tone(freq=1336),
    Tone(freq=1477),
    Tone(freq=1633),
]
dtmf_keys = [
    "123A",
    "456B",
    "789C",
    "*0#D",
]
dtmf = {"key_" + dtmf_keys[i][j]: [low, high] for ((i,low), (j,high)) in itertools.product(enumerate(dtmf_low), enumerate(dtmf_high)) }

dial_US = [Tone(freq=350), Tone(freq=440)]
busy_US = [Tone(freq=480), Tone(freq=620)]
ring_US = [Tone(freq=440), Tone(freq=480)]

dial_UK = [Tone(freq=350), Tone(freq=450)]
dial_EU = [Tone(freq=425)]
dial_FR = [Tone(freq=440)]
dial_JP = [Tone(freq=400)]
