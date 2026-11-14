"""Focal-subject size audit (V1-CIN-01, Appendix A.1 of docs/AUDIT-v1.md).

For every beat: the median longer side (1080p px) of the projected bounds of the beat's focal objects over the beat
hold (start + 0.5 s .. end - 0.5 s), against the target in ``TARGET_PX``.
"""

from __future__ import annotations

import statistics
from functools import cache

from cff.stage import camera, caption_layout, choreography
from cff.stage.audit import HOLD_MARGIN_S
from cff.story import model as m
from cff.story import timing
from cff.theme import shots

DEFAULT_TARGET_PX = 150.0
TARGET_PX: dict[str, float] = {
    "B-01.2": 90.0, "B-04.2": 90.0, "B-07.4": 90.0,  # travel beats
    "B-05.3": 80.0, "B-08.3": 80.0,  # both ends of a trust link stay in frame
}
# Beats the audit does not size: the opening/closing wides and the hero (V1-CIN-02 has its own test), and the
# beats whose focal subject is a whole actor or the network (already large).
UNSIZED: frozenset[str] = frozenset({"B-09.2", "B-09.3"})
# Residuals recorded in docs/GAN-LEDGER.md (beat -> achieved px, rounded down to 5 px) when a target cannot be
# reached with camera audits green (session F2: each dist step that would gain more failed C-02/C-03, or moved the
# next beat's start pose so that a must-read sign went short).
RESIDUAL_PX: dict[str, float] = {
    "B-01.2": 75.0, "B-02.2": 95.0, "B-02.3": 95.0, "B-04.2": 65.0, "B-05.2": 50.0,
    "B-05.3": 35.0, "B-06.1": 60.0, "B-06.3": 50.0, "B-07.4": 60.0,
}


def longer_side(timeline: object, plan: camera.CameraPlan, obj_ids: tuple[str, ...], first: int, last: int) -> float:
    sides = []
    for f in range(first, last + 1):
        r = caption_layout.objects_rect(timeline, plan, obj_ids, f)  # type: ignore[arg-type]
        if r is not None and r[2] > r[0] and r[3] > r[1]:
            sides.append(max(r[2] - r[0], r[3] - r[1]))
    return statistics.median(sides) if sides else 0.0


@cache
def beat_sizes() -> dict[str, float]:
    tl = choreography.build_timeline()
    plan = camera.CameraPlan(tl)
    out: dict[str, float] = {}
    for beat in m.MODEL.beats:
        start, end = timing.beat_window(beat.id)
        first, last = timing.frame_range(start + HOLD_MARGIN_S, end - HOLD_MARGIN_S)
        out[beat.id] = longer_side(tl, plan, shots.focal_objects(beat.id, beat.focal), first, last)
    return out


def target(beat_id: str) -> float:
    return RESIDUAL_PX.get(beat_id, TARGET_PX.get(beat_id, DEFAULT_TARGET_PX))


def failing() -> dict[str, float]:
    return {b: px for b, px in beat_sizes().items() if b not in UNSIZED and px < target(b)}


def main() -> int:
    bad = failing()
    for beat_id, px in beat_sizes().items():
        mark = "   " if beat_id in UNSIZED else ("BAD" if beat_id in bad else "OK ")
        print(f"{mark} {beat_id}: {px:7.1f} px (target {target(beat_id):.0f})")
    print(f"focal audit: {len(bad)} beats under target")
    return 1 if bad else 0
