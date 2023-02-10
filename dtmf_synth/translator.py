
from __future__ import annotations
from typing import TypeVar
import numpy as np
import itertools
from .tone import *
from .phone_chords import dtmf
# Given: a "main" input note, and "chord" input notes
# - pick the DTMF tone pair that is optimal over a cost function that considers:
#   - distance from the main input note to one of the pair
#   - distance from the second of the pair to one of the chord notes


# Given two notes, "main" and "chord", select the DTMF tone that best approximates that pair of notes
# compute an error function based on:
# - delta from main tone to dtmf tone
# - delta from chord tone to dtmf tone
# - delta of main-chord interval to dtmf tone pair interval

K = TypeVar('K')

dtmf_all = dtmf.copy()
dtmf_all.update({k + "_r": list(reversed(v)) for k,v in dtmf.items()})

def best_pair(main: Tone, extras: list[Tone], pairs: dict[K,tuple[Tone,Tone]] = dtmf_all) -> tuple[K, tuple[Tone,Tone]]:
    """Finds the best matching DTMF tonepair for a given note and chord.
    Given a principal note `main`, a list of additional chord tone `extras', and a dictionary `pairs` whose values are pairs of tones,
      this method selects the chord tone from `extras` that is easiest to approximate,
      selects the best approximation to (`main`, `extra`) among `pairs`,
      and applies a tuning adjustment to the selected pair.
    The returned value is a tuple containing:
    - the dictionary key of the selected pair
    - the tuning-adjusted pair of notes
    """
    if not extras:
        # TODO return random matching DTMF
        raise NotImplementedError("TODO: return random matching DTMF when theres's no chord tones.")

    targets = [(main, extra) for extra in extras]
    tone_weights = [1,0.5]
    best_pair_for_target = [(target, best_match_for_chord(target, pairs, tone_weights)) for target in targets]
    target, k = min(best_pair_for_target, key = lambda k: tuned_loss(k[0], pairs[k[1]], tone_weights))
    
    tune = best_bulk_tune(target, pairs[k], tone_weights)

    tuned = tuple(tone - tune for tone in pairs[k])
    return k, tuned
    
def best_match_for_tuned_chord(chord: list[Tone], chords: dict[K, list[Tone,Tone]], tone_weights: list[float] |  np.ndarray = None, interval_weights: np.ndarray = None) -> K:
    return min(chords, key = lambda k: tuned_loss(chord, chords[k], tone_weights, interval_weights))

def best_match_for_chord(chord: list[Tone], chords: dict[K, list[Tone,Tone]], tone_weights: list[float] |  np.ndarray = None, interval_weights: np.ndarray = None) -> K:
    return min(chords, key = lambda k: loss(chord, chords[k], tone_weights, interval_weights))

def tuned_loss(chord_a: list[Tone], chord_b: list[Tone], tone_weights: list[float] |  np.ndarray = None, interval_weights: np.ndarray = None) -> float:
    tune = best_bulk_tune(chord_a, chord_b, tone_weights)
    tuned_a = [tone + tune for tone in chord_a]
    return loss(tuned_a, chord_b, tone_weights, interval_weights)

def loss(chord_a: list[Tone], chord_b: list[Tone], tone_weights: list[float] |  np.ndarray = None, interval_weights: np.ndarray = None) -> float:

    if tone_weights is None: tone_weights = np.ones_like(chord_a)
    if interval_weights is None: interval_weights = np.tri(len(chord_a), k=-1)

    assert len(chord_a) == len(chord_b)
    assert len(chord_a) == len(tone_weights)
    assert len(chord_a) == interval_weights.shape[0]
    assert len(chord_a) == interval_weights.shape[1]

    err_sq = 0

    for a, b, w in zip(chord_a, chord_b, tone_weights):
        err_sq += (a - b)**2 * w
    
    for (i, (ai, bi)), (j, (aj, bj)) in itertools.product(enumerate(zip(chord_a, chord_b)), repeat=2):
        interval_a = abs(ai-aj)
        interval_b = abs(bi-bj)
        err_sq += (interval_a - interval_b)**2 * interval_weights[i,j]
    
    return err_sq

def best_bulk_tune(chord_a: list[Tone], chord_b: list[Tone], tone_weights: list[float] | np.ndarray = None) -> float:

    if tone_weights is None: tone_weights = np.ones_like(chord_a)
    
    assert len(chord_a) == len(chord_b)
    assert len(chord_a) == len(tone_weights)
    
    weighted_sum = 0
    sum_of_weights = 0

    for a, b, w in zip(chord_a, chord_b, tone_weights):
        weighted_sum += (b - a) * w
        sum_of_weights += w
    
    return weighted_sum / sum_of_weights
