"""
A tool for translating a MIDI sequence into a series of DTMF tones that closely approximate it.

In this module, a "tone" is the abstract entity representing a sound with a particular frequency or pitch.
"freq" is used to refer to a tone's numerical frequency in Hz.
"note" is used to refer to a tone's log-scale tuning, equivalent to MIDI note indices.
"""