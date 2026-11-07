"""Keyframe tracks (pure data) and their evaluation.

A ``Timeline`` holds, per (object, channel), a frame-ordered list of keys. Channels:
``location`` (x, y, z in metres), ``rotation`` (x, y, z Euler degrees), ``scale`` (x, y, z) and
``glow`` (linear r, g, b, alpha: the emission tint and opacity read by the materials).
Each key carries the name of the easing used for the segment that leaves it (``cff.theme.motion``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from cff.theme import motion

Value = tuple[float, ...]

LOCATION = "location"
ROTATION = "rotation"
SCALE = "scale"
GLOW = "glow"
CHANNELS: tuple[str, ...] = (LOCATION, ROTATION, SCALE, GLOW)
CHANNEL_WIDTH: dict[str, int] = {LOCATION: 3, ROTATION: 3, SCALE: 3, GLOW: 4}


@dataclass(frozen=True)
class Key:
    frame: int
    value: Value
    ease: str  # a motion.PRESETS name or motion.SMOOTH; applies to the segment after this key


@dataclass
class Timeline:
    """All keyframe tracks of the film."""

    tracks: dict[tuple[str, str], dict[int, Key]] = field(default_factory=dict)

    def key(self, obj: str, channel: str, frame: int, value: Value, ease: str = "EASE_IN_OUT") -> None:
        if len(value) != CHANNEL_WIDTH[channel]:
            raise ValueError(f"{obj}.{channel}: expected {CHANNEL_WIDTH[channel]} values, got {value}")
        if ease != motion.SMOOTH and ease not in motion.PRESETS:
            raise ValueError(f"unknown easing {ease!r}")
        self.tracks.setdefault((obj, channel), {})[frame] = Key(frame, value, ease)

    def keys(self, obj: str, channel: str) -> list[Key]:
        return [k for _, k in sorted(self.tracks.get((obj, channel), {}).items())]

    def objects(self) -> list[str]:
        return sorted({obj for obj, _ in self.tracks})

    def has(self, obj: str, channel: str) -> bool:
        return (obj, channel) in self.tracks

    def value_at(self, obj: str, channel: str, frame: float) -> Value | None:
        keys = self.keys(obj, channel)
        if not keys:
            return None
        return evaluate_keys(keys, frame)


def _hermite(p0: float, p1: float, m0: float, m1: float, t: float) -> float:
    t2, t3 = t * t, t * t * t
    return (2 * t3 - 3 * t2 + 1) * p0 + (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) * p1 + (t3 - t2) * m1


def _slopes(frames: list[int], values: list[float]) -> list[float]:
    """Auto-clamped style slopes: central differences, zero at local extremes and at the ends."""
    count = len(values)
    slopes = [0.0] * count
    for i in range(1, count - 1):
        before = (values[i] - values[i - 1]) / (frames[i] - frames[i - 1])
        after = (values[i + 1] - values[i]) / (frames[i + 1] - frames[i])
        if before * after <= 0:
            slopes[i] = 0.0
        else:
            span = frames[i + 1] - frames[i - 1]
            slopes[i] = (values[i + 1] - values[i - 1]) / span
            limit = 3 * min(abs(before), abs(after))
            slopes[i] = math.copysign(min(abs(slopes[i]), limit), slopes[i])
    return slopes


def evaluate_keys(keys: list[Key], frame: float) -> Value:
    """Value of a key list at a (possibly fractional) frame, mirroring the Bezier handles used in Blender."""
    if frame <= keys[0].frame:
        return keys[0].value
    if frame >= keys[-1].frame:
        return keys[-1].value
    index = max(i for i, k in enumerate(keys) if k.frame <= frame)
    k0, k1 = keys[index], keys[index + 1]
    t = (frame - k0.frame) / (k1.frame - k0.frame)
    if k0.ease == motion.SMOOTH:
        out: list[float] = []
        span = k1.frame - k0.frame
        for axis in range(len(k0.value)):
            frames = [k.frame for k in keys]
            values = [k.value[axis] for k in keys]
            slopes = _slopes(frames, values)
            out.append(_hermite(values[index], values[index + 1], slopes[index] * span, slopes[index + 1] * span, t))
        return tuple(out)
    eased = motion.evaluate(motion.preset(k0.ease), t) if k0.ease in motion.PRESETS else t
    return tuple(a + (b - a) * eased for a, b in zip(k0.value, k1.value, strict=True))
