"""Caption placement: the band each caption sits in, and the focal subject's projected bounds (L-05).

A caption sits in the bottom band unless the beat's focal subject would cross the bottom plate while the caption has
any opacity; then it takes the top band (if that is clear on more frames). Both bands lie inside title-safe.
The focal bounds are the projected corners of each focal object's box (``StageObject.size`` about its centre,
turned by its yaw), unioned over the beat's focal objects (``cff.theme.shots.focal_objects``).
"""

from __future__ import annotations

import math
from functools import cache

from cff.stage import camera, choreography
from cff.stage import layout as lo
from cff.stage.audit import beat_of_frame, is_visible, position_at
from cff.stage.objects import BY_ID as BY_OBJECT
from cff.stage.tracks import SCALE, Timeline
from cff.story import captions, timing
from cff.story import model as m
from cff.theme import shots
from cff.theme import typography as ty

Rect = tuple[float, float, float, float]
BOTTOM, TOP = "bottom", "top"


def caption_frames(caption_id: str) -> range:
    caption = captions.caption(caption_id)
    return range(timing.seconds_to_frame(caption.appear_s), timing.seconds_to_frame(caption.vanish_s) + 1)


def plate_width_px(caption_id: str) -> float:
    caption = captions.caption(caption_id)
    cap = ty.TITLE_CAP_PX if caption.kind is captions.CaptionKind.TITLE else ty.CAPTION_CAP_PX
    em = cap / ty.CAP_RATIO[ty.CAPTION_FONT]
    return len(caption.text) * ty.INTER_MEAN_ADVANCE_EM * em + 2 * ty.CAPTION_PLATE_MARGIN_PX


def _rect_at(caption_id: str, centre_y: float) -> Rect:
    w = plate_width_px(caption_id)
    h = ty.CAPTION_PLATE_HEIGHT_PX
    cx = ty.FRAME_W_PX / 2
    return (cx - w / 2, centre_y - h / 2, cx + w / 2, centre_y + h / 2)


def _corners(obj_id: str, centre: lo.Vec3, scale: tuple[float, ...]) -> list[lo.Vec3]:
    o = BY_OBJECT[obj_id]
    sx, sy, sz = (o.size[i] * abs(scale[i]) / 2 for i in range(3))
    yaw = math.radians(o.yaw)
    c, s = math.cos(yaw), math.sin(yaw)
    out = []
    for dx in (-sx, sx):
        for dy in (-sy, sy):
            for dz in (-sz, sz):
                out.append((centre[0] + dx * c - dy * s, centre[1] + dx * s + dy * c, centre[2] + dz))
    return out


def focal_rect(timeline: Timeline, plan: camera.CameraPlan, beat_id: str, frame: int) -> Rect | None:
    """Projected bounds (1080p pixels) of the beat's focal objects on ``frame``; None if none is visible or in front."""
    beat = next(b for b in m.MODEL.beats if b.id == beat_id)
    return objects_rect(timeline, plan, shots.focal_objects(beat_id, beat.focal), frame)


def objects_rect(timeline: Timeline, plan: camera.CameraPlan, obj_ids: tuple[str, ...] | list[str], frame: int) -> Rect | None:
    """Projected bounds (1080p pixels) of the visible objects among ``obj_ids`` on ``frame``; None if none is visible."""
    state = plan.state(frame)
    xs: list[float] = []
    ys: list[float] = []
    for obj_id in obj_ids:
        if obj_id not in BY_OBJECT or not is_visible(timeline, obj_id, frame):
            continue
        scale = timeline.value_at(obj_id, SCALE, frame) or (1.0, 1.0, 1.0)
        for corner in _corners(obj_id, position_at(timeline, obj_id, frame), scale):
            px, py, depth = camera.project(state, corner)
            if depth <= 0 or not math.isfinite(px):
                continue
            xs.append(px * ty.FRAME_W_PX)
            ys.append(py * ty.FRAME_H_PX)
    if not xs:
        return None
    return (max(0.0, min(xs)), max(0.0, min(ys)), min(ty.FRAME_W_PX, max(xs)), min(ty.FRAME_H_PX, max(ys)))


def _hits(a: Rect, b: Rect) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


@cache
def bands() -> dict[str, str]:
    timeline = choreography.build_timeline()
    plan = camera.CameraPlan(timeline)
    beats = beat_of_frame()
    out: dict[str, str] = {}
    for caption in captions.CAPTIONS:
        if caption.kind is captions.CaptionKind.TITLE:
            out[caption.id] = BOTTOM
            continue
        hits = {BOTTOM: 0, TOP: 0}
        for frame in caption_frames(caption.id):
            if frame not in beats:
                continue
            focal = focal_rect(timeline, plan, beats[frame], frame)
            if focal is None:
                continue
            for band, y in ((BOTTOM, ty.CAPTION_CENTRE_Y_PX), (TOP, ty.CAPTION_TOP_CENTRE_Y_PX)):
                hits[band] += _hits(focal, _rect_at(caption.id, y))
        out[caption.id] = TOP if hits[BOTTOM] > 0 and hits[TOP] < hits[BOTTOM] else BOTTOM
    return out


def centre_y_px(caption_id: str) -> float:
    caption = captions.caption(caption_id)
    if caption.kind is captions.CaptionKind.TITLE:
        return ty.FRAME_H_PX / 2
    return ty.CAPTION_TOP_CENTRE_Y_PX if bands()[caption_id] == TOP else ty.CAPTION_CENTRE_Y_PX


def plate_rect(caption_id: str) -> Rect:
    return _rect_at(caption_id, centre_y_px(caption_id))


def focal_overlaps() -> dict[str, list[int]]:
    """Caption id -> frames on which its plate intersects the focal subject's projected bounds (L-05 audit)."""
    timeline = choreography.build_timeline()
    plan = camera.CameraPlan(timeline)
    beats = beat_of_frame()
    out: dict[str, list[int]] = {}
    for caption in captions.CAPTIONS:
        if caption.kind is captions.CaptionKind.TITLE:
            continue
        rect = plate_rect(caption.id)
        bad = [f for f in caption_frames(caption.id) if f in beats and (fr := focal_rect(timeline, plan, beats[f], f)) is not None and _hits(fr, rect)]
        if bad:
            out[caption.id] = bad
    return out
