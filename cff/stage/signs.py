"""Sign layout: where each in-world label sits on every frame, how large it is, and when it is shown.

Every label is a sign anchored at a 3D point (its parent object plus an offset, or a fixed world point). Signs are
real text objects in the 3D world, turned to the camera, but they are held at one on-screen cap height
(``typography.SIGN_CAP_PX``) by scaling with depth, and they live in their own render pass (the SIGNS scene) so
geometry never hides them and depth of field never softens them (L-01, L-06; LEG-S1R1-03..11, CIN-S1R1-01).

On every frame a sign is shown only if all of these hold, otherwise it fades out:
- it exists (its window is open, or its parent is on stage);
- its anchor is in front of the lens by at least ``SIGN_NEAR_M`` (no sign ever fills the frame: CIN-S1R1-01);
- its plate lies inside the title-safe area (L-03);
- its plate clears a visible caption plate (L-05);
- its plate does not overlap a sign of higher priority (signs that must be read in the current beat come first).

Labels of one family (a check list, a tag stack, a card's fields) keep a minimum line pitch, in order, so a list never
prints one line on top of another (PKI-S1R1-03, LEG-S1R1-04).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache

from cff.stage import camera, caption_layout, choreography, labels
from cff.stage import layout as lo
from cff.stage.audit import POP_FRAME_WIDTH_FRACTION, beat_of_frame, is_visible
from cff.stage.labels import Placement
from cff.stage.layout import Vec3
from cff.stage.objects import BY_ID as BY_OBJECT
from cff.stage.objects import CATALOGUE, Kind
from cff.stage.tracks import LOCATION, Timeline
from cff.story import captions, timing
from cff.story import model as m
from cff.theme import motion, shots
from cff.theme import typography as ty

Rect = tuple[float, float, float, float]  # x0, y0, x1, y1 in 1080p pixels


@dataclass(frozen=True)
class SignFrame:
    frame: int
    alpha: float  # 0..1 after the eased fades
    origin: Vec3  # world position of the text origin (centre, or the left edge for left-aligned text)
    cap_m: float  # cap height in metres that gives SIGN_CAP_PX on screen at this depth
    rect: Rect  # the plate on screen at 1080p


@dataclass(frozen=True)
class SignPlan:
    label_id: str
    frames: dict[int, SignFrame]  # only frames on which the sign has any opacity

    def shown(self, frame: int) -> bool:
        f = self.frames.get(frame)
        return f is not None and f.alpha >= 1.0 - 1e-9


def _intersects(a: Rect, b: Rect, gap: float = 0.0) -> bool:
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def _inside_safe(r: Rect) -> bool:
    x0, y0, x1, y1 = ty.TITLE_SAFE_PX
    m = ty.SIGN_SAFE_MARGIN_PX - 1e-6  # nudged blocks land exactly on the margin
    return r[0] >= x0 + m and r[1] >= y0 + m and r[2] <= x1 - m and r[3] <= y1 - m


def anchor(timeline: Timeline, placement: Placement, frame: int) -> Vec3:
    if placement.parent is None:
        return placement.offset
    loc = timeline.value_at(placement.parent, LOCATION, frame)
    base = (loc[0], loc[1], loc[2]) if loc is not None else BY_OBJECT[placement.parent].home
    return lo.add(base, placement.offset)


def world_fade_frame() -> int:
    """First frame of the closing fade to black (E-09.3a): signs belong to the world and leave before it."""
    fade = next(e for e in m.MODEL.events if e.id == "E-09.3a")
    return timing.seconds_to_frame(fade.start_s)


def exists(timeline: Timeline, placement: Placement, frame: int) -> bool:
    if frame >= world_fade_frame() - round(motion.LABEL_EXIT_S * timing.FPS):
        return False
    if placement.window is not None:
        first, last = labels.window_frames(placement.window)
        return first <= frame < last + round(motion.LABEL_LINGER_S * timing.FPS)
    beats_allowed = labels.PLATE_BEATS.get(placement.label_id)
    if beats_allowed is not None and beat_of_frame().get(frame) not in beats_allowed:
        return False  # V1-LEG-04: a persistent plate shows only in the beats where it is read
    return placement.parent is None or is_visible(timeline, placement.parent, frame)


def caption_rects(frame: int, ahead: int = 0) -> list[Rect]:
    """Plates of the captions that have any opacity on ``frame`` (or will within ``ahead`` frames)."""
    return [caption_layout.plate_rect(c.id) for c in captions.CAPTIONS
            if any(f in caption_layout.caption_frames(c.id) for f in (frame, frame + ahead))]


CAPTION_LOOKAHEAD_FRAMES = 8  # the layout clears a caption's band this early, so a sign glides aside before it appears (V1-LEG-02)


def _unproject(state: camera.CamState, x_px: float, y_px: float, depth: float) -> Vec3:
    forward, right, up = camera._basis(state.position, state.look)
    half_w = shots.SENSOR_WIDTH_MM / 2
    nx = (x_px / ty.FRAME_W_PX - 0.5) * 2 * half_w / state.lens * depth
    ny = (0.5 - y_px / ty.FRAME_H_PX) * 2 * half_w / state.lens / (ty.FRAME_W_PX / ty.FRAME_H_PX) * depth
    return lo.add(state.position, lo.add(lo.mul(forward, depth), lo.add(lo.mul(right, nx), lo.mul(up, ny))))


def cap_m_at(state: camera.CamState, depth: float, cap_px: float = ty.SIGN_CAP_PX) -> float:
    return cap_px / ty.FRAME_W_PX * shots.SENSOR_WIDTH_MM / state.lens * depth


# Signs that are read together form a list: shown members keep this order, one line below the other, and the list
# moves as one block when it has to be nudged inside title-safe or above a caption. A member ending in "-" is a prefix.
# The four check lists are not here: each has one fixed place on screen (``fixed_list_positions``, V1-LEG-03).
LISTS: tuple[tuple[str, ...], ...] = (
    ("LBL-CA1", "LBL-CA1-INELIGIBLE"),
    ("LBL-CA2", "LBL-ELIG-"),
    ("LBL-HOST-WEB", "LBL-SITE-WEB", "LBL-TPL-WEB"),
    ("LBL-HOST-RDP", "LBL-TPL-RDP"),
    ("LBL-SELF", "LBL-UNVERIFIED"),
    ("LBL-CERT-RDP-",),
    ("LBL-CERT-WEB-",),
    ("LBL-AIA-",),
    ("LBL-AD", "LBL-DC"),
)


def _matches(label_id: str, member: str) -> bool:
    return label_id.startswith(member) if member.endswith("-") else label_id == member


def _list_key(label_id: str) -> tuple[int, int]:
    """(list number, position in the list); a label in no list is its own list."""
    for number, members in enumerate(LISTS):
        for position, member in enumerate(members):
            if _matches(label_id, member):
                return number, position
    return 1000 + labels.PLACEMENTS.index(labels.BY_ID[label_id]), 0


def family(label_id: str) -> int:
    return _list_key(label_id)[0]


@dataclass
class _Candidate:
    placement: Placement
    index: int
    origin_px: tuple[float, float]
    depth: float
    rect: Rect
    must: bool
    anchor_px: tuple[float, float] = (0.0, 0.0)  # where the anchor projects, before any layout move (V1-LEG-02)

    def __post_init__(self) -> None:
        if self.anchor_px == (0.0, 0.0):
            self.anchor_px = self.origin_px

    @property
    def offset_px(self) -> tuple[float, float]:
        """The layout move applied to the sign (nudges, clearing, list pitch): a change in it is a pop, not motion."""
        return (self.origin_px[0] - self.anchor_px[0], self.origin_px[1] - self.anchor_px[1])


def tick_width_px(label_id: str) -> float:
    """Extra plate width on the left of a check line, for its tick (V1-LEG-03); 0 for every other sign."""
    return labels.TICK_WIDTH_CAPS * ty.SIGN_CAP_PX if label_id in labels.CHECK_TICK_ROLES else 0.0


def plate_size_px(placement: Placement) -> tuple[float, float]:
    w, h = ty.sign_plate_size_px(placement.text)
    return w + tick_width_px(placement.label_id), h


def _rect_for(placement: Placement, x: float, y: float) -> tuple[Rect, tuple[float, float]]:
    w, h = plate_size_px(placement)
    margin = ty.SIGN_CAP_PX * ty.SIGN_PLATE_MARGIN_CAPS
    if placement.align == "LEFT":
        return (x, y - h / 2, x + w, y + h / 2), (x + margin + tick_width_px(placement.label_id), y)
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2), (x, y)


LIST_PITCH_EPSILON_PX = 1.0  # rows of a fixed list sit this much more than one gap apart (no rounding-edge overlap)


def _list_span(ids: tuple[str, ...]) -> tuple[int, int]:
    """(first entrance frame, last exit frame) over a check list's windowed rows."""
    spans = [labels.window_frames(w) for i in ids if (w := labels.BY_ID[i].window) is not None]
    return min(s[0] for s in spans), max(s[1] for s in spans)


@cache
def fixed_list_positions() -> dict[str, tuple[float, float]]:
    """Check-list row -> (left x, centre y) on the 1080p frame, one fixed place per list for its whole life (V1-LEG-03).

    Appendix A.3 of docs/AUDIT-v1.md: a deterministic grid search over title-safe for the block that is blocked (by the
    focal subject, a capsule, card or private key, or a caption band) on the fewest frames, nearest the mean screen
    position of the list's first tick slot. Rows keep their slot even while earlier rows are not yet shown."""
    timeline = choreography.build_timeline()
    plan = camera.CameraPlan(timeline)
    beats = beat_of_frame()
    out: dict[str, tuple[float, float]] = {}
    pad, step = ty.SIGN_LIST_PAD_PX, ty.SIGN_LIST_STEP_PX
    m_px = ty.SIGN_SAFE_MARGIN_PX
    sx0, sy0, sx1, sy1 = ty.TITLE_SAFE_PX[0] + m_px, ty.TITLE_SAFE_PX[1] + m_px, ty.TITLE_SAFE_PX[2] - m_px, ty.TITLE_SAFE_PX[3] - m_px
    for ids in labels.CHECK_LISTS:
        sizes = [plate_size_px(labels.BY_ID[i]) for i in ids]
        w, row_h = max(s[0] for s in sizes), max(s[1] for s in sizes)
        h = len(ids) * row_h + (len(ids) - 1) * (ty.SIGN_GAP_PX + LIST_PITCH_EPSILON_PX)
        first, last = _list_span(ids)
        last += round(motion.LABEL_LINGER_S * timing.FPS)
        frames = [f for f in range(first, last + 1) if f in beats]
        forbidden: list[list[Rect]] = []
        ax = ay = 0.0
        for f in frames:
            rects = [(r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad) for r in _protected_rects(timeline, plan, beats[f], f)]
            c = ty.CAPTION_BAND_CLEARANCE_PX
            rects += [(0.0, r[1] - c, float(ty.FRAME_W_PX), r[3] + c) for r in caption_rects(f)]
            forbidden.append(rects)
            px, py, _ = camera.project(plan.state(f), anchor(timeline, labels.BY_ID[ids[0]], f))
            if math.isfinite(px):
                ax += px * ty.FRAME_W_PX / len(frames)
                ay += py * ty.FRAME_H_PX / len(frames)
        best: tuple[int, float, float, float] | None = None
        x = sx0
        while x + w <= sx1:
            y = sy0
            while y + h <= sy1:
                block = (x, y, x + w, y + h)
                blocked = sum(any(_intersects(block, r) for r in rects) for rects in forbidden)
                key = (blocked, math.hypot(x + w / 2 - ax, y + h / 2 - ay), y, x)
                if best is None or key < best:
                    best = key
                y += step
            x += step
        assert best is not None, ids
        x0, y0 = best[3], best[2]
        for row, label_id in enumerate(ids):
            out[label_id] = (x0, y0 + row_h / 2 + row * (row_h + ty.SIGN_GAP_PX + LIST_PITCH_EPSILON_PX))
    return out


def list_blocked_frames() -> dict[str, int]:
    """First row of each check list -> frames on which its fixed place is blocked (recorded in the ledger)."""
    timeline = choreography.build_timeline()
    plan = camera.CameraPlan(timeline)
    beats = beat_of_frame()
    pos = fixed_list_positions()
    out: dict[str, int] = {}
    for ids in labels.CHECK_LISTS:
        rects = [_rect_for(labels.BY_ID[i], *pos[i])[0] for i in ids]
        block = (min(r[0] for r in rects), min(r[1] for r in rects), max(r[2] for r in rects), max(r[3] for r in rects))
        first, last = _list_span(ids)
        pad = ty.SIGN_LIST_PAD_PX
        n = 0
        for f in range(first, last + 1):
            if f not in beats:
                continue
            prot = [(r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad) for r in _protected_rects(timeline, plan, beats[f], f)]
            n += any(_intersects(block, r) for r in prot)
        out[ids[0]] = n
    return out


def _frame_candidates(timeline: Timeline, plan: camera.CameraPlan, frame: int, beat: str,
                      memory: dict[int, tuple[float, float]] | None = None) -> tuple[list[_Candidate], set[str]]:
    state = plan.state(frame)
    out: list[_Candidate] = []
    hidden: set[str] = set()
    fixed = fixed_list_positions()
    for index, placement in enumerate(labels.PLACEMENTS):
        if not exists(timeline, placement, frame):
            hidden.add(placement.label_id)
            continue
        if placement.screen_px is not None:  # fixed on-screen place (V1-PKI-02): never moved or cleared
            rect, origin = _rect_for(placement, *placement.screen_px)
            out.append(_Candidate(placement, index, origin, state.focus_distance, rect, True))
            continue
        if placement.label_id in fixed:  # a check-list row: one fixed place for the list's whole life (V1-LEG-03)
            rect, origin = _rect_for(placement, *fixed[placement.label_id])
            out.append(_Candidate(placement, index, origin, state.focus_distance, rect, True))
            continue
        px, py, depth = camera.project(state, anchor(timeline, placement, frame))
        if depth < ty.SIGN_NEAR_M or not math.isfinite(px):
            hidden.add(placement.label_id)
            continue
        relevant = placement.window is not None or beat in labels.LABELS[placement.label_id].must_read_beats
        if not relevant and depth > ty.SIGN_DEPTH_FACTOR * state.focus_distance:
            hidden.add(placement.label_id)  # a name far behind the subject of a close shot: it would show through walls
            continue
        x, y = px * ty.FRAME_W_PX, py * ty.FRAME_H_PX
        if not (0.0 <= x <= ty.FRAME_W_PX and 0.0 <= y <= ty.FRAME_H_PX):
            hidden.add(placement.label_id)  # the thing it names is off screen
            continue
        rect, origin = _rect_for(placement, x, y)
        must = beat in labels.LABELS[placement.label_id].must_read_beats
        out.append(_Candidate(placement, index, origin, depth, rect, must))
    # lists keep their order and a minimum pitch: each member sits at least one line below the previous one
    by_list: dict[int, list[_Candidate]] = {}
    for c in out:
        by_list.setdefault(family(c.placement.label_id), []).append(c)
    blocked = caption_rects(frame, CAPTION_LOOKAHEAD_FRAMES)
    protected: list[Rect] | None = None
    kept: list[_Candidate] = []
    # families in layout priority; a kept family that must be read now is protected from the families after it, so a
    # second list steps around it instead of being hidden by it (V1-LEG-02)
    for members in sorted(by_list.values(), key=lambda ms: min(_priority(c) for c in ms)):
        members.sort(key=lambda c: (_list_key(c.placement.label_id)[1], c.index))
        for prev, cur in zip(members, members[1:], strict=False):
            min_top = prev.rect[3] + ty.SIGN_GAP_PX
            if cur.rect[1] < min_top:
                _shift(cur, 0.0, min_top - cur.rect[1])
        if members[0].placement.screen_px is not None or members[0].placement.label_id in fixed:
            kept.extend(members)  # a fixed-position sign is never nudged or cleared
            continue
        if protected is None:  # names keep off the check lists' fixed places too (V1-LEG-03)
            protected = _protected_rects(timeline, plan, beat, frame) + [c.rect for c in out if c.placement.label_id in fixed]
        # every sign (V1-LEG-04: plates too) stands beside the focal subject and every visible capsule, card and private key,
        # never across them (CIN-S1R1-04, LEG-S1R2-03, LEG-S1R2-04, CIN-S1R2-02)
        _clear_of(members, protected, memory, family(members[0].placement.label_id))
        if _nudge_block(members, blocked):
            kept.extend(members)
            if any(c.must for c in members):
                protected.extend(c.rect for c in members)
        else:
            hidden.update(c.placement.label_id for c in members)
    return kept, hidden


PROTECTED_KINDS = (Kind.CAPSULE, Kind.CARD, Kind.KEY_PRIVATE)  # what a tag or check list must never cover
PROTECTED_OBJECTS = tuple(o.id for o in CATALOGUE if o.kind in PROTECTED_KINDS)


def _protected_rects(timeline: Timeline, plan: camera.CameraPlan, beat: str, frame: int) -> list[Rect]:
    """Screen bounds of the beat's focal subject and of every visible capsule, card and private key on ``frame``."""
    out: list[Rect] = []
    focal = caption_layout.focal_rect(timeline, plan, beat, frame) if beat else None
    if focal is not None:
        out.append(focal)
    for obj in PROTECTED_OBJECTS:
        rect = caption_layout.objects_rect(timeline, plan, (obj,), frame)
        if rect is not None:
            out.append(rect)
    return out


def _block(members: list[_Candidate]) -> Rect:
    return (min(c.rect[0] for c in members), min(c.rect[1] for c in members), max(c.rect[2] for c in members), max(c.rect[3] for c in members))


GLIDE_BACK_SCALES = (0.0, 0.25, 0.5, 0.75, 0.9, 1.0)  # fractions of the last move tried, nearest the anchor first


def _clear_of(members: list[_Candidate], protected: list[Rect], memory: dict[int, tuple[float, float]] | None = None, key: int = 0) -> None:
    """Move a list, as one block, the shortest way off every protected rect it covers, staying inside title-safe.

    Candidate moves put the block just right of, left of, above or below each rect it crosses; the shortest move that
    leaves the block inside title-safe and clear of all protected rects wins. If none exists the list stays (and the
    caption and title-safe rules still apply). With ``memory`` (one dict per pass, frames in ascending order) the move
    nearest the family's previous move wins instead, so the choice does not flip sides from frame to frame (V1-LEG-02)."""
    gap = ty.SIGN_GAP_PX * 2
    x0, y0, x1, y1 = _block(members)
    m = ty.SIGN_SAFE_MARGIN_PX
    sx0, sy0, sx1, sy1 = ty.TITLE_SAFE_PX[0] + m, ty.TITLE_SAFE_PX[1] + m, ty.TITLE_SAFE_PX[2] - m, ty.TITLE_SAFE_PX[3] - m
    previous = memory.get(key) if memory is not None else None
    if memory is not None and previous is not None:
        # sticky: keep the last move, easing it back toward the anchor, while the block stays clear and inside title-safe
        for scale in GLIDE_BACK_SCALES:
            dx, dy = previous[0] * scale, previous[1] * scale
            if math.hypot(dx - previous[0], dy - previous[1]) > ty.SIGN_JUMP_PX:
                continue
            moved = (x0 + dx, y0 + dy, x1 + dx, y1 + dy)
            inside = sx0 <= moved[0] and sy0 <= moved[1] and moved[2] <= sx1 and moved[3] <= sy1
            if inside and not any(_intersects(moved, p, gap) for p in protected):
                memory[key] = (dx, dy)
                for c in members:
                    _shift(c, dx, dy)
                return
    # try to clear everything; if the frame is too crowded for that, clear the focal subject alone (the first rect)
    for rects in (protected, protected[:1]):
        hit = [p for p in rects if _intersects((x0, y0, x1, y1), p, gap)]
        if not hit:
            if memory is not None:
                memory.pop(key, None)
            return
        options: list[tuple[float, float]] = []
        for p in hit:
            options += [(p[2] + gap - x0, 0.0), (p[0] - gap - x1, 0.0), (0.0, p[1] - gap - y1), (0.0, p[3] + gap - y0)]
        good = []
        for dx, dy in options:
            moved = (x0 + dx, y0 + dy, x1 + dx, y1 + dy)
            inside = sx0 <= moved[0] and sy0 <= moved[1] and moved[2] <= sx1 and moved[3] <= sy1
            if inside and not any(_intersects(moved, p) for p in rects):
                good.append((dx, dy))
        if good:
            if previous is not None:
                pdx, pdy = previous
                dx, dy = min(good, key=lambda d: math.hypot(d[0] - pdx, d[1] - pdy))
            else:
                dx, dy = min(good, key=lambda d: math.hypot(*d))
            if memory is not None:
                memory[key] = (dx, dy)
            for c in members:
                _shift(c, dx, dy)
            return


def _shift(c: _Candidate, dx: float, dy: float) -> None:
    c.rect = (c.rect[0] + dx, c.rect[1] + dy, c.rect[2] + dx, c.rect[3] + dy)
    c.origin_px = (c.origin_px[0] + dx, c.origin_px[1] + dy)


def _nudge_block(members: list[_Candidate], blocked: list[Rect]) -> bool:
    """Move a list as one block inside title-safe and clear of visible captions; False if it cannot fit near its anchor."""
    m = ty.SIGN_SAFE_MARGIN_PX
    sx0, sy0, sx1, sy1 = ty.TITLE_SAFE_PX[0] + m, ty.TITLE_SAFE_PX[1] + m, ty.TITLE_SAFE_PX[2] - m, ty.TITLE_SAFE_PX[3] - m
    for b in blocked:  # keep out of the caption plate's band: above a bottom caption, below a top one
        if b[1] > ty.FRAME_H_PX / 2:
            sy1 = min(sy1, b[1] - ty.CAPTION_BAND_CLEARANCE_PX)
        else:
            sy0 = max(sy0, b[3] + ty.CAPTION_BAND_CLEARANCE_PX)
    x0, y0 = min(c.rect[0] for c in members), min(c.rect[1] for c in members)
    x1, y1 = max(c.rect[2] for c in members), max(c.rect[3] for c in members)
    if x1 - x0 > sx1 - sx0 or y1 - y0 > sy1 - sy0:
        return False
    dx = (sx0 - x0) if x0 < sx0 else (sx1 - x1) if x1 > sx1 else 0.0
    dy = (sy0 - y0) if y0 < sy0 else (sy1 - y1) if y1 > sy1 else 0.0
    if math.hypot(dx, dy) > ty.SIGN_MAX_NUDGE_PX:
        return False
    for c in members:
        _shift(c, dx, dy)
    return True


def _visible_set(timeline: Timeline, plan: camera.CameraPlan, frame: int, beat: str, why: dict[str, str] | None = None,
                 memory: dict[int, tuple[float, float]] | None = None) -> dict[str, _Candidate]:
    candidates, _ = _frame_candidates(timeline, plan, frame, beat, memory)
    blocked = caption_rects(frame, CAPTION_LOOKAHEAD_FRAMES)
    accepted: dict[str, _Candidate] = {}
    for c in sorted(candidates, key=_priority):  # check-list rows hold their fixed place first; names step aside (V1-LEG-03)
        label_id = c.placement.label_id
        if not _inside_safe(c.rect):
            if why is not None:
                why[label_id] = f"outside title-safe {tuple(round(v) for v in c.rect)}"
            continue
        if any(_intersects(c.rect, b, ty.CAPTION_BAND_CLEARANCE_PX) for b in blocked):
            if why is not None:
                why[label_id] = "caption"
            continue
        clash = next((a for a in accepted.values() if _intersects(c.rect, a.rect, ty.SIGN_GAP_PX)), None)
        if clash is not None:
            if why is not None:
                why[label_id] = f"overlaps {clash.placement.label_id}"
            continue
        accepted[label_id] = c
    return accepted


def hidden_reasons(label_id: str, frames: list[int]) -> dict[str, int]:
    """Why a sign is not fully shown on ``frames`` (diagnostics for the legibility audit)."""
    timeline = choreography.build_timeline()
    plan = camera.CameraPlan(timeline)
    beats = beat_of_frame()
    placement = labels.BY_ID[label_id]
    sign = plan_signs()[label_id]
    out: dict[str, int] = {}
    for frame in frames:
        if sign.shown(frame):
            continue
        why: dict[str, str] = {}
        visible = _visible_set(timeline, plan, frame, beats.get(frame, ""), why)
        if label_id in visible:
            reason = "fading or too short a run"
        elif label_id in why:
            reason = why[label_id].split(" (")[0] if why[label_id].startswith("outside") else why[label_id]
        elif not exists(timeline, placement, frame):
            reason = "not on stage"
        else:
            reason = "behind or too near the lens"
        out[reason] = out.get(reason, 0) + 1
    return out


def _pop_px() -> float:
    return POP_FRAME_WIDTH_FRACTION * ty.FRAME_W_PX * GLIDE_STEP_FRACTION


def _runs(frames: list[int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for f in frames:
        if out and f == out[-1][1] + 1:
            out[-1] = (out[-1][0], f)
        else:
            out.append((f, f))
    return out


def _hops(by_frame: dict[int, _Candidate]) -> list[int]:
    """Frames on which a sign steps farther than the C-06 pop limit from the frame before (Appendix A.2, V1-LEG-02).
    Layout moves glide at ``SIGN_JUMP_PX`` per frame (``_glide_all``); only a forced step is left (a caption or a sign
    of higher priority leaves no gliding path, or the list rides a fast card)."""
    return [f for f in sorted(by_frame) if (p := by_frame.get(f - 1)) is not None
            and math.hypot(by_frame[f].rect[0] - p.rect[0], by_frame[f].rect[1] - p.rect[1]) > _pop_px()]


GLIDE_STEP_FRACTION = 0.99  # glide and pop limits are kept just under their thresholds, so rounding never crosses them
GLIDE_BACKOFF = 0.05  # the glide step shrinks in these fractions until the whole on-screen step is under the pop limit


def _glide_step(c: _Candidate, prev: _Candidate) -> _Candidate:
    """``c`` with its layout move rate-limited to ``SIGN_JUMP_PX`` from ``prev`` (the sign as shown on the frame before),
    the whole on-screen step kept under the pop limit when the anchor allows, and the plate kept inside title-safe."""
    pop = _pop_px()
    shown = prev.offset_px
    ddx, ddy = c.offset_px[0] - shown[0], c.offset_px[1] - shown[1]
    step = math.hypot(ddx, ddy)
    k = min(1.0, GLIDE_STEP_FRACTION * ty.SIGN_JUMP_PX / step) if step > 0 else 1.0
    ax, ay = c.anchor_px[0] - prev.anchor_px[0], c.anchor_px[1] - prev.anchor_px[1]
    while k > 0 and math.hypot(ax + ddx * k, ay + ddy * k) > pop and math.hypot(ax, ay) <= pop:
        k = max(0.0, k - GLIDE_BACKOFF)
    g = _Candidate(c.placement, c.index, c.origin_px, c.depth, c.rect, c.must, c.anchor_px)
    dx, dy = shown[0] + ddx * k - c.offset_px[0], shown[1] + ddy * k - c.offset_px[1]
    if dx or dy:
        _shift(g, dx, dy)
        m_px = ty.SIGN_SAFE_MARGIN_PX
        sx0, sy0, sx1, sy1 = ty.TITLE_SAFE_PX[0] + m_px, ty.TITLE_SAFE_PX[1] + m_px, ty.TITLE_SAFE_PX[2] - m_px, ty.TITLE_SAFE_PX[3] - m_px
        cx = (sx0 - g.rect[0]) if g.rect[0] < sx0 else (sx1 - g.rect[2]) if g.rect[2] > sx1 else 0.0
        cy = (sy0 - g.rect[1]) if g.rect[1] < sy0 else (sy1 - g.rect[3]) if g.rect[3] > sy1 else 0.0
        if cx or cy:
            _shift(g, cx, cy)
    return g


def _priority(c: _Candidate) -> tuple[bool, bool, tuple[int, int], int]:
    return (not c.must, c.placement.label_id not in fixed_list_positions(), _list_key(c.placement.label_id), c.index)


def _glide_all(per_label: dict[str, dict[int, _Candidate]], frames: list[int]) -> dict[str, dict[int, _Candidate]]:
    """One pass, frames ascending, signs in layout priority (V1-LEG-02). Each sign tries its glided place (a layout move
    slides at ``SIGN_JUMP_PX`` per frame instead of popping), then its laid-out place; the first that is inside
    title-safe, clear of captions and of every sign already placed wins. Otherwise the sign sits the frame out."""
    out: dict[str, dict[int, _Candidate]] = {label_id: {} for label_id in per_label}
    for frame in frames:
        present = sorted((c for by_frame in per_label.values() if (c := by_frame.get(frame)) is not None), key=_priority)
        blocked = caption_rects(frame)
        accepted: list[Rect] = []
        # a list glides as one block: its first member with a previous frame sets the slide for every member
        slide: dict[int, tuple[float, float]] = {}
        for c in present:
            fam = family(c.placement.label_id)
            prev = out[c.placement.label_id].get(frame - 1)
            if fam not in slide and prev is not None:
                g = _glide_step(c, prev)
                slide[fam] = (g.rect[0] - c.rect[0], g.rect[1] - c.rect[1])
        for c in present:
            label_id = c.placement.label_id
            dx, dy = slide.get(family(label_id), (0.0, 0.0))
            options: tuple[_Candidate, ...] = (c,)
            if dx or dy:
                g = _Candidate(c.placement, c.index, c.origin_px, c.depth, c.rect, c.must, c.anchor_px)
                _shift(g, dx, dy)
                options = (g, c)
            for option in options:
                if (_inside_safe(option.rect) and not any(_intersects(option.rect, b, ty.CAPTION_BAND_CLEARANCE_PX) for b in blocked)
                        and not any(_intersects(option.rect, a, ty.SIGN_GAP_PX) for a in accepted)):
                    accepted.append(option.rect)
                    out[label_id][frame] = option
                    break
    return out


@cache
def plan_signs() -> dict[str, SignPlan]:
    """The sign plan for the whole film (deterministic: no randomness)."""
    timeline = choreography.build_timeline()
    plan = camera.CameraPlan(timeline)
    beats = beat_of_frame()
    per_label: dict[str, dict[int, _Candidate]] = {p.label_id: {} for p in labels.PLACEMENTS}
    memory: dict[int, tuple[float, float]] = {}  # one pass, frames ascending: each family remembers its last move
    for frame in plan.frames():
        for label_id, cand in _visible_set(timeline, plan, frame, beats.get(frame, ""), memory=memory).items():
            per_label[label_id][frame] = cand
    enter = motion.label_entrance_frames()
    leave = motion.label_exit_frames()
    out: dict[str, SignPlan] = {}
    for label_id, by_frame in _glide_all(per_label, plan.frames()).items():
        frames: dict[int, SignFrame] = {}
        dips: dict[int, float] = {}  # a forced hop larger than the pop limit is hidden by a short dip (V1-LEG-02)
        for hop in _hops(by_frame):
            for i, a in enumerate(ty.SIGN_HOP_DIP):
                f = hop - len(ty.SIGN_HOP_DIP) // 2 + i
                dips[f] = min(dips.get(f, 1.0), a)
        for first, last in _runs(sorted(by_frame)):
            if last - first + 1 < ty.SIGN_MIN_RUN_FRAMES:
                continue  # too short to read: never flashed
            for frame in range(first, last + 1):
                c = by_frame[frame]
                into, outof = frame - first, last - frame
                alpha = dips.get(frame, 1.0)
                if into < enter:
                    alpha = min(alpha, motion.evaluate(motion.EASE_OUT, into / enter))
                if outof < leave:
                    alpha = min(alpha, motion.evaluate(motion.EASE_IN, outof / leave))
                state = plan.state(frame)
                origin = _unproject(state, c.origin_px[0], c.origin_px[1], c.depth)
                frames[frame] = SignFrame(frame, alpha, origin, cap_m_at(state, c.depth), c.rect)
        out[label_id] = SignPlan(label_id, frames)
    return out


def shown_frames(label_id: str, frames: list[int]) -> int:
    sign = plan_signs()[label_id]
    return sum(1 for f in frames if sign.shown(f))
