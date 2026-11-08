"""Planned-film legibility audit (pure Python, from the sign plan and the caption layout).

- L-06: every must-read label is fully shown (inside title-safe, clear of captions and of other signs, at the fixed
  sign cap height) for >= 1.5 s, or its whole must-read window if shorter, inside its must-read beats.
- L-05: no caption plate intersects the focal subject's projected bounds.
"""

from __future__ import annotations

from dataclasses import dataclass

from cff.stage import caption_layout, labels, signs
from cff.story import timing

MUST_READ_HOLD_S = 1.5


@dataclass(frozen=True)
class LabelResult:
    label_id: str
    shown: int
    needed: int

    @property
    def ok(self) -> bool:
        return self.shown >= self.needed


def label_results() -> list[LabelResult]:
    out: list[LabelResult] = []
    for placement in labels.PLACEMENTS:
        frames = labels.must_read_frames(placement.label_id)
        if not frames:
            continue
        needed = min(len(frames), round(MUST_READ_HOLD_S * timing.FPS))
        out.append(LabelResult(placement.label_id, signs.shown_frames(placement.label_id, frames), needed))
    return out


def main() -> int:
    bad = [r for r in label_results() if not r.ok]
    for r in label_results():
        print(f"{'OK ' if r.ok else 'BAD'} {r.label_id}: shown {r.shown} of needed {r.needed}")
        if not r.ok:
            for reason, count in sorted(signs.hidden_reasons(r.label_id, labels.must_read_frames(r.label_id)).items(), key=lambda kv: -kv[1]):
                print(f"      {count:4d} frames: {reason}")
    overlaps = caption_layout.focal_overlaps()
    for caption_id, frames in overlaps.items():
        print(f"L-05 {caption_id} ({caption_layout.bands()[caption_id]}): {len(frames)} frames over the focal subject, {frames[0]}..{frames[-1]}")
    print(f"legibility audit: {len(bad)} labels short, {len(overlaps)} captions over the focal subject")
    return 1 if bad or overlaps else 0
