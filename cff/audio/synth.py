"""Deterministic cue synthesis and mixing (Charter 10). Pure Python, standard library only, seeded.

Each cue kind is a short mono float buffer at ``SAMPLE_RATE``. ``mix`` places every cue at its exact sample offset on top of a
slowly moving low bed. Nothing here reads the clock; the only randomness is ``random.Random(SEED_*)``.
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

from cff.audio import cues as cue_sheet_module

SAMPLE_RATE = 48000
SEED_WHOOSH = 5101  # filtered-noise cues (documented in docs\AUDIO.md)
SEED_CLICK = 5102
SEED_SEAL = 5103
PEAK_CEILING = 0.89  # the pre-loudnorm mix is scaled to this peak so the int16 write never clips
WHOOSH_GAIN = 1.4  # low-passed noise is quiet; this brings it to about unity
A3_HZ = 220.0
BED_LOW_HZ = 55.0
BED_FIFTH_HZ = 82.5
BED_LFO_HZ = 0.07


def _n(seconds: float) -> int:
    return round(seconds * SAMPLE_RATE)


def _db(db: float) -> float:
    return 10 ** (db / 20)


def _env(i: int, n: int, attack: float, release: float) -> float:
    t = i / SAMPLE_RATE
    end = (n - i) / SAMPLE_RATE
    return min(1.0, t / attack if attack > 0 else 1.0) * min(1.0, end / release if release > 0 else 1.0)


def _tone(freq: float, seconds: float, attack: float, release: float, decay: float = 0.0) -> list[float]:
    n = _n(seconds)
    return [math.sin(2 * math.pi * freq * i / SAMPLE_RATE) * _env(i, n, attack, release) * math.exp(-decay * i / SAMPLE_RATE) for i in range(n)]


def _add(dst: list[float], src: list[float], at: int = 0, gain: float = 1.0) -> None:
    for i, v in enumerate(src):
        if 0 <= at + i < len(dst):
            dst[at + i] += v * gain


def pulse() -> list[float]:
    out = _tone(A3_HZ * 2, 0.35, 0.02, 0.25, decay=6.0)
    _add(out, _tone(A3_HZ * 3, 0.35, 0.02, 0.25, decay=9.0), gain=0.35)
    return out


def whoosh() -> list[float]:
    rng = random.Random(SEED_WHOOSH)
    n = _n(0.7)
    out: list[float] = []
    low = 0.0
    for i in range(n):
        t = i / n
        coeff = 0.02 + 0.30 * math.sin(math.pi * t)  # the filter opens and closes: a rising-falling sweep
        low += coeff * (rng.uniform(-1, 1) - low)
        out.append(low * math.sin(math.pi * t) ** 2 * WHOOSH_GAIN)
    return out


def click() -> list[float]:
    rng = random.Random(SEED_CLICK)
    out = [rng.uniform(-1, 1) * math.exp(-i / (SAMPLE_RATE * 0.004)) * 0.6 for i in range(_n(0.05))]
    out += [0.0] * (_n(0.25) - len(out))
    _add(out, _tone(1250.0, 0.25, 0.001, 0.15, decay=18.0), gain=0.5)
    return out


def seal() -> list[float]:
    rng = random.Random(SEED_SEAL)
    out = _tone(110.0, 0.7, 0.004, 0.4, decay=7.0)
    _add(out, _tone(A3_HZ * 4, 0.6, 0.01, 0.4, decay=5.0), at=_n(0.02), gain=0.3)
    _add(out, [rng.uniform(-1, 1) * math.exp(-i / (SAMPLE_RATE * 0.02)) * 0.3 for i in range(_n(0.08))])
    return out


def tick() -> list[float]:
    return _tone(A3_HZ * 4, 0.09, 0.002, 0.06, decay=25.0)


def deny() -> list[float]:
    out = _tone(A3_HZ, 0.35, 0.01, 0.2, decay=4.0)
    _add(out, _tone(A3_HZ * 0.75, 0.45, 0.01, 0.3, decay=4.0), at=_n(0.18))
    return out


def chord() -> list[float]:
    """A major triad, the trust-resolve chord."""
    out = [0.0] * _n(3.0)
    for ratio, gain in ((1.0, 0.5), (1.25, 0.4), (1.5, 0.4), (2.0, 0.25)):
        _add(out, _tone(A3_HZ * ratio, 3.0, 0.15, 1.4, decay=0.6), gain=gain)
    return out


def mark() -> list[float]:
    out = _tone(A3_HZ * 3, 1.6, 0.01, 1.0, decay=2.2)
    _add(out, _tone(A3_HZ * 1.5, 1.6, 0.01, 1.0, decay=1.8), gain=0.6)
    return out


KINDS = {"pulse": pulse, "whoosh": whoosh, "click": click, "seal": seal, "tick": tick, "deny": deny, "chord": chord, "mark": mark}


def bed(seconds: float) -> list[float]:
    n = _n(seconds)
    fade_in, fade_out = cue_sheet_module.BED_FADE_IN_S, cue_sheet_module.BED_FADE_OUT_S
    out: list[float] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        lfo = 0.75 + 0.25 * math.sin(2 * math.pi * BED_LFO_HZ * t)
        v = math.sin(2 * math.pi * BED_LOW_HZ * t) + 0.6 * math.sin(2 * math.pi * BED_FIFTH_HZ * t + 1.0 * lfo)
        out.append(v * lfo * min(1.0, t / fade_in) * min(1.0, (seconds - t) / fade_out) * 0.5)
    return out


def mix() -> list[float]:
    """The full mono mix, scaled so its peak is ``PEAK_CEILING``."""
    total = cue_sheet_module.duration_s()
    out = bed(total)
    scale = _db(cue_sheet_module.BED_GAIN_DB)
    out = [v * scale for v in out]
    kinds = {name: build() for name, build in KINDS.items()}
    for cue in cue_sheet_module.cue_sheet():
        _add(out, kinds[cue.kind], at=_n(cue.time_s), gain=_db(cue_sheet_module.CUE_GAIN_DB[cue.kind]) * 0.5)
    peak = max(abs(v) for v in out) or 1.0
    return [v * PEAK_CEILING / peak for v in out]


def write_wav(samples: list[float], path: Path) -> Path:
    """Write mono samples as a 16-bit PCM WAV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, round(v * 32767)))) for v in samples))
    return path
