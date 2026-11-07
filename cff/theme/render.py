"""Render tiers (Charter Section 11) and the look switches each tier turns on.

``animatic`` is the Stage 1 grey-box tier: 960x540, low samples, no motion blur, no volumetrics.
"""

from __future__ import annotations

from dataclasses import dataclass

from cff.story import timing


@dataclass(frozen=True)
class Tier:
    name: str
    width: int
    height: int
    taa_samples: int
    motion_blur: bool
    volumetrics: bool
    bloom: bool
    grain: bool
    shadows: bool
    raytracing: bool


TIERS: dict[str, Tier] = {
    "animatic": Tier("animatic", 960, 540, 32, False, False, False, False, True, False),
    "preview": Tier("preview", 1280, 720, 32, False, True, True, False, True, False),
    "final": Tier("final", 1920, 1080, 96, True, True, True, True, True, True),
}

CHUNK_FRAMES = 300  # long renders run in background chunks of this many frames (Charter 3.7)
FPS = timing.FPS
SENSOR_WIDTH_MM = 36.0
CAPTION_PIXELS_PER_UNIT = 100.0  # the caption scene's orthographic camera: 1 Blender unit = 100 px at 1920x1080
CAPTION_REFERENCE_WIDTH_PX = 1920
CAPTION_REFERENCE_HEIGHT_PX = 1080


def tier(name: str) -> Tier:
    return TIERS[name]


def chunks(first: int, last: int, size: int = CHUNK_FRAMES) -> list[tuple[int, int]]:
    """Inclusive frame ranges covering first..last in blocks of ``size`` frames."""
    return [(start, min(start + size - 1, last)) for start in range(first, last + 1, size)]
