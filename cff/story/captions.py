"""Caption text, timing and word counts (Charter Section 7 and 10; criteria L-04, L-05).

Text lives here; timing comes from ``cff.story.timing.CAPTION_WINDOWS_S``. Names come from
``cff.config.names``. ``captions.vtt`` and ``transcript.md`` are generated from this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from cff.config import names as n
from cff.story import timing

WORD_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9'.\-]*")


class CaptionKind(StrEnum):
    CAPTION = "caption"
    TITLE = "title"


def word_count(text: str) -> int:
    """Words for L-04: tokens that contain a letter or digit (dashes and punctuation excluded)."""
    return len(WORD_PATTERN.findall(text))


def min_hold_s(text: str) -> float:
    """L-04 minimum on-screen time: max(2.5 s, 0.35 s per word)."""
    return max(timing.CAPTION_MIN_HOLD_S, timing.CAPTION_SECONDS_PER_WORD * word_count(text))


@dataclass(frozen=True)
class Caption:
    id: str
    text: str
    kind: CaptionKind = CaptionKind.CAPTION

    @property
    def anchor_beat(self) -> str:
        return timing.CAPTION_WINDOWS_S[self.id][0]

    @property
    def scene(self) -> str:
        return timing.scene_of(self.anchor_beat)

    @property
    def hold_start_s(self) -> float:
        beat, offset, _ = timing.CAPTION_WINDOWS_S[self.id]
        return timing.beat_window(beat)[0] + offset

    @property
    def hold_end_s(self) -> float:
        return self.hold_start_s + timing.CAPTION_WINDOWS_S[self.id][2]

    @property
    def hold_s(self) -> float:
        return self.hold_end_s - self.hold_start_s

    @property
    def appear_s(self) -> float:
        """Fade-in starts."""
        return self.hold_start_s - timing.CAPTION_FADE_IN_S

    @property
    def vanish_s(self) -> float:
        """Fade-out ends; the caption is fully gone."""
        return self.hold_end_s + timing.CAPTION_FADE_OUT_S

    @property
    def words(self) -> int:
        return word_count(self.text)

    @property
    def required_hold_s(self) -> float:
        return min_hold_s(self.text)


CAPTIONS: tuple[Caption, ...] = (
    Caption("CAP-S1", "Secure RDP connection"),
    Caption("CAP-S2", "The RDP server needs a trusted identity"),
    Caption("CAP-S3a", "The private key stays on the server"),
    Caption("CAP-S3b", "The request is signed, not the key sent"),
    Caption("CAP-S4", f"{n.ISSUING_CA1_ROLE} verifies, then signs"),
    Caption("CAP-S5a", f"The {n.ROOT_CA_ROLE} signs the issuing CA certificate"),
    Caption("CAP-S5b", f"The {n.ROOT_CA_ROLE} is the trust anchor"),
    Caption("CAP-S6a", "The client validates the whole chain"),
    Caption("CAP-S6b", "Trusted RDP connection established"),
    Caption("CAP-S7", "Different templates can use different issuing CAs"),
    Caption("CAP-S8", f"{n.ISSUING_CA2_ROLE} signs the TLS certificate"),
    Caption("CAP-S9a", "Different issuing paths. One trusted root."),
    Caption("TITLE-S9", f"{n.FILM_TITLE} — {n.FILM_SUBTITLE}", CaptionKind.TITLE),
)


def caption(caption_id: str) -> Caption:
    return next(c for c in CAPTIONS if c.id == caption_id)


def captions_in_order() -> list[Caption]:
    return sorted(CAPTIONS, key=lambda c: c.appear_s)
