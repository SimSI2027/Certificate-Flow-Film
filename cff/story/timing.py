"""Named timing constants (Charter Section 7 and 9).

All durations, offsets and frame conversions live here. Times are seconds; frames are
derived through ``FPS``. Every time value must land exactly on a frame boundary.

Semantics (what happens) live in ``cff.story.model``; this module only says *when*.
"""

from __future__ import annotations

FPS = 30
FRAME_START = 1  # Blender's first frame
FRAME_EPSILON = 1e-6

# Film duration bounds (Charter: 100-120 s, target 105-115 s).
TOTAL_MIN_S = 100.0
TOTAL_MAX_S = 120.0
TARGET_MIN_S = 105.0
TARGET_MAX_S = 115.0

# Scene durations from Charter Section 7 (target total 109 s).
SCENE_DURATIONS_S: dict[str, float] = {
    "S1": 7.0,
    "S2": 7.0,
    "S3": 10.0,
    "S4": 14.0,
    "S5": 12.0,
    "S6": 20.0,
    "S7": 12.0,
    "S8": 11.0,
    "S9": 16.0,
}

# Beat durations, in story order. Beats are contiguous: each starts where the previous ends.
BEAT_DURATIONS_S: dict[str, float] = {
    "B-01.1": 3.0,
    "B-01.2": 4.0,
    "B-02.1": 2.0,
    "B-02.2": 3.0,
    "B-02.3": 2.0,
    "B-03.1": 2.0,
    "B-03.2": 2.5,
    "B-03.3": 2.5,
    "B-03.4": 3.0,
    "B-04.1": 3.0,
    "B-04.2": 2.0,
    "B-04.3": 4.0,
    "B-04.4": 3.0,
    "B-04.5": 2.0,
    "B-05.1": 3.5,
    "B-05.2": 5.0,
    "B-05.3": 3.5,
    "B-06.1": 3.0,
    "B-06.2": 4.0,
    "B-06.3": 2.0,
    "B-06.4": 5.0,
    "B-06.5": 3.0,
    "B-06.6": 3.0,
    "B-07.1": 3.0,
    "B-07.2": 3.0,
    "B-07.3": 3.5,
    "B-07.4": 2.5,
    "B-08.1": 3.5,
    "B-08.2": 4.5,
    "B-08.3": 3.0,
    "B-09.1": 5.0,
    "B-09.2": 6.0,
    "B-09.3": 5.0,
}

# Declared overlaps between beats (Charter 12: "no gaps or overlaps unless declared"). None.
DECLARED_BEAT_OVERLAPS: tuple[tuple[str, str], ...] = ()

# Beats that begin with the only permitted cut (C-02): into and out of the S5 flashback.
DECLARED_CUT_BEATS: tuple[str, ...] = ("B-05.2", "B-05.3")

# Event windows: event id -> (offset from its beat's start, duration), seconds.
EVENT_WINDOWS_S: dict[str, tuple[float, float]] = {
    # S1
    "E-01.1a": (0.6, 1.8),
    "E-01.2a": (0.0, 4.0),
    # S2
    "E-02.1a": (0.2, 1.2),
    "E-02.2a": (0.0, 1.5),
    "E-02.2b": (1.5, 0.8),
    "E-02.2c": (2.3, 0.6),
    "E-02.3a": (0.0, 1.6),
    # S3
    "E-03.1a": (0.2, 1.6),
    "E-03.2a": (0.0, 1.6),
    "E-03.3a": (0.0, 2.0),
    "E-03.4a": (0.3, 1.8),
    # S4
    "E-04.1a": (0.6, 0.8),
    "E-04.1b": (1.4, 1.4),
    "E-04.2a": (0.0, 2.0),
    "E-04.3a": (0.2, 0.7),
    "E-04.3b": (1.1, 0.7),
    "E-04.3c": (2.0, 0.7),
    "E-04.3d": (2.9, 0.7),
    "E-04.4a": (0.0, 0.8),
    "E-04.4b": (0.8, 1.8),
    "E-04.5a": (0.0, 1.2),
    "E-04.5b": (1.2, 0.7),
    "E-04.5c": (1.2, 0.7),
    # S5
    "E-05.1a": (1.2, 1.8),
    "E-05.2a": (0.2, 0.8),
    "E-05.2b": (1.0, 1.2),
    "E-05.2c": (2.2, 0.3),
    "E-05.2d": (2.5, 0.7),
    "E-05.2e": (3.2, 1.2),
    "E-05.2f": (4.4, 0.5),
    "E-05.3a": (0.3, 2.0),
    # S6
    "E-06.1a": (0.0, 0.7),
    "E-06.1b": (0.7, 0.8),
    "E-06.1c": (0.8, 0.8),
    "E-06.1d": (1.6, 0.3),
    "E-06.1e": (1.9, 0.4),
    "E-06.1f": (2.4, 0.5),
    "E-06.2a": (0.0, 1.2),
    "E-06.2b": (1.2, 1.2),
    "E-06.2c": (2.2, 1.4),
    "E-06.3a": (0.2, 1.4),
    "E-06.4a": (0.2, 0.6),
    "E-06.4b": (1.0, 0.6),
    "E-06.4c": (1.8, 0.6),
    "E-06.4d": (2.6, 0.6),
    "E-06.4e": (3.4, 0.6),
    "E-06.4f": (4.2, 0.8),
    "E-06.5a": (0.1, 1.0),
    "E-06.5b": (0.6, 1.0),
    "E-06.5c": (0.4, 1.6),
    "E-06.5d": (1.8, 0.8),
    "E-06.6a": (0.2, 1.6),
    # S7
    "E-07.1a": (1.0, 1.4),
    "E-07.2a": (0.0, 0.8),
    "E-07.2b": (0.8, 0.7),
    "E-07.2c": (1.5, 0.6),
    "E-07.2d": (2.1, 0.8),
    "E-07.3a": (0.5, 0.7),
    "E-07.3b": (1.2, 2.0),
    "E-07.4a": (0.0, 2.4),
    # S8
    "E-08.1a": (0.2, 0.6),
    "E-08.1b": (0.9, 0.6),
    "E-08.1c": (1.6, 0.6),
    "E-08.1d": (2.3, 0.9),
    "E-08.2a": (0.0, 0.7),
    "E-08.2b": (0.7, 1.4),
    "E-08.2c": (2.1, 1.4),
    "E-08.2d": (3.5, 0.9),
    "E-08.2e": (3.5, 0.9),
    "E-08.3a": (0.3, 2.0),
    # S9
    "E-09.1a": (0.0, 0.9),
    "E-09.1b": (0.9, 0.8),
    "E-09.1c": (1.0, 0.8),
    "E-09.1d": (1.8, 0.2),
    "E-09.1e": (2.0, 0.3),
    "E-09.1q": (2.3, 0.3),
    "E-09.1f": (2.6, 0.2),
    "E-09.1g": (2.8, 0.2),
    "E-09.1h": (3.0, 0.1),
    "E-09.1i": (3.0, 0.1),
    "E-09.1j": (3.0, 0.3),
    "E-09.1k": (3.3, 0.3),
    "E-09.1l": (3.6, 0.3),
    "E-09.1m": (3.2, 0.5),
    "E-09.1n": (3.3, 0.5),
    "E-09.1o": (3.9, 0.4),
    "E-09.1p": (4.4, 0.5),
    "E-09.2a": (0.5, 3.0),
    "E-09.2b": (0.8, 3.0),
    "E-09.3a": (1.5, 2.3),
}

# Captions (L-04). Each caption is anchored to a beat:
# caption id -> (anchor beat, offset of the full-opacity hold from the beat start, hold length).
# The fade-in happens before the hold and the fade-out after it; L-04 is measured on the hold.
CAPTION_FADE_IN_S = 0.4
CAPTION_FADE_OUT_S = 0.3  # exits slightly faster than entrances (C-06)
CAPTION_MIN_GAP_S = 0.2  # fully clear between one caption and the next (L-05)
CAPTION_MIN_HOLD_S = 2.5  # L-04
CAPTION_SECONDS_PER_WORD = 0.35  # L-04

CAPTION_WINDOWS_S: dict[str, tuple[str, float, float]] = {
    "CAP-S1": ("B-01.1", 1.0, 4.0),
    "CAP-S2": ("B-02.1", 1.0, 4.5),
    "CAP-S3a": ("B-03.1", 1.0, 4.5),
    "CAP-S3b": ("B-03.3", 2.2, 3.0),
    "CAP-S4": ("B-04.3", 0.0, 6.0),
    "CAP-S5a": ("B-05.2", 0.4, 4.0),
    "CAP-S5b": ("B-05.3", 0.6, 2.6),
    "CAP-S6a": ("B-06.2", 0.5, 9.5),
    "CAP-S6b": ("B-06.6", 0.2, 2.5),
    "CAP-S7": ("B-07.3", 0.0, 4.5),
    "CAP-S8": ("B-08.2", 0.0, 4.0),
    "CAP-S9a": ("B-09.2", 1.0, 4.0),
    "TITLE-S9": ("B-09.3", 0.5, 3.7),
}


def scene_of(beat_id: str) -> str:
    """'B-04.3' -> 'S4'."""
    return f"S{int(beat_id[2:4])}"


def beat_windows() -> dict[str, tuple[float, float]]:
    """Beat id -> (start_s, end_s), contiguous in story order."""
    windows: dict[str, tuple[float, float]] = {}
    cursor = 0.0
    for beat_id, duration in BEAT_DURATIONS_S.items():
        windows[beat_id] = (cursor, cursor + duration)
        cursor += duration
    return windows


def beat_window(beat_id: str) -> tuple[float, float]:
    return beat_windows()[beat_id]


def scene_windows() -> dict[str, tuple[float, float]]:
    windows: dict[str, tuple[float, float]] = {}
    cursor = 0.0
    for scene_id, duration in SCENE_DURATIONS_S.items():
        windows[scene_id] = (cursor, cursor + duration)
        cursor += duration
    return windows


def total_duration_s() -> float:
    return sum(BEAT_DURATIONS_S.values())


def event_window(event_id: str, beat_id: str) -> tuple[float, float]:
    """Absolute (start_s, end_s) of an event."""
    offset, duration = EVENT_WINDOWS_S[event_id]
    beat_start, _ = beat_window(beat_id)
    return beat_start + offset, beat_start + offset + duration


def is_on_frame(seconds: float) -> bool:
    frames = seconds * FPS
    return abs(frames - round(frames)) < FRAME_EPSILON


def seconds_to_frame(seconds: float) -> int:
    """Frame index at a time. Raises if the time is not on a frame boundary."""
    if not is_on_frame(seconds):
        raise ValueError(f"{seconds} s is not on a frame boundary at {FPS} fps")
    return FRAME_START + round(seconds * FPS)


def frame_end() -> int:
    """Last frame of the film (inclusive)."""
    return seconds_to_frame(total_duration_s()) - 1


def frame_range(start_s: float, end_s: float) -> tuple[int, int]:
    """Inclusive frame range covering [start_s, end_s)."""
    return seconds_to_frame(start_s), seconds_to_frame(end_s) - 1
