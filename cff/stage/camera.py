"""The camera plan: one rig, planned in pure Python and audited against C-02 / C-03.

For every frame the plan gives the look-at point, the camera position, the focus point, the lens and the f-stop.
Blender keys exactly these values (camera, look-at empty, focus empty), so the audit here predicts the render.

Continuity: each beat starts from the previous beat's end state. Only the opening shot and the two flashback
cuts (``Shot.start``) are allowed to break that.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cff.stage import layout as lo
from cff.stage.layout import Vec3
from cff.stage.objects import BY_ID
from cff.stage.tracks import LOCATION, Timeline
from cff.story import model as m
from cff.story import timing
from cff.theme import motion, shots
from cff.theme.shots import Pose, Shot, Target

GLIDE = motion.CAMERA_GLIDE
GLIDE_PEAK = motion.peak_slope(GLIDE)


@dataclass(frozen=True)
class CamState:
    frame: int
    look: Vec3
    az: float
    el: float
    dist: float
    lens: float
    fstop: float
    focus: Vec3

    @property
    def position(self) -> Vec3:
        return offset_position(self.look, self.az, self.el, self.dist)

    @property
    def focus_distance(self) -> float:
        return lo.dist(self.position, self.focus)


def offset_position(look: Vec3, az: float, el: float, dist: float) -> Vec3:
    a, e = math.radians(az), math.radians(el)
    return (look[0] + dist * math.cos(e) * math.cos(a), look[1] + dist * math.cos(e) * math.sin(a), look[2] + dist * math.sin(e))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_angle(a: float, b: float, t: float) -> float:
    delta = (b - a + 180.0) % 360.0 - 180.0
    return a + delta * t


def ease(t: float) -> float:
    return motion.evaluate(GLIDE, max(0.0, min(1.0, t)))


class CameraPlan:
    def __init__(self, timeline: Timeline) -> None:
        self.timeline = timeline
        self.states: dict[int, CamState] = {}
        self.cut_frames: list[int] = []
        self.beat_first: dict[str, int] = {}
        self._build()

    # --- target evaluation -------------------------------------------------------------
    def point(self, target: Target, frame: int) -> Vec3:
        if not isinstance(target, str):
            return target
        value = self.timeline.value_at(target, LOCATION, frame)
        if value is not None:
            return (value[0], value[1], value[2])
        return BY_ID[target].home

    def centre(self, targets: tuple[Target, ...], frame: int) -> Vec3:
        pts = [self.point(t, frame) for t in targets]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts))

    # --- plan --------------------------------------------------------------------------
    def _pose_state(self, pose: Pose, frame: int) -> CamState:
        look = self.centre(pose.look, frame)
        return CamState(frame, look, pose.az, pose.el, pose.dist, pose.lens, pose.fstop, look)

    def _build(self) -> None:
        prev: CamState | None = None
        beats = list(timing.BEAT_DURATIONS_S)
        for index, beat_id in enumerate(beats):
            shot = shots.BY_BEAT[beat_id]
            first, last = timing.frame_range(*timing.beat_window(beat_id))
            self.beat_first[beat_id] = first
            if shot.start is not None:
                start = self._pose_state(shot.start, first)
                if prev is not None:
                    self.cut_frames.append(first)
            else:
                if prev is None:
                    raise ValueError("the opening shot needs an explicit start pose")
                start = prev
            span = last - first + 1
            lens_frames = min(1.0, math.ceil(GLIDE_PEAK * abs(shot.lens - start.lens) / shots.LENS_MAX_STEP_MM) / span) if shot.lens != start.lens else 1.0
            for frame in range(first, last + 2):  # last + 1 is the next beat's first frame (end state)
                t = (frame - first) / span
                state = self._state(shot, start, first, frame, t, lens_frames)
                if frame <= last:
                    self.states[frame] = state
                else:
                    prev = state
            if index == len(beats) - 1 and prev is not None:
                self.states[last + 1] = prev

    def _state(self, shot: Shot, start: CamState, first: int, frame: int, t: float, lens_t: float) -> CamState:
        w = ease(t / shot.follow) if shot.follow > 0 else 1.0
        e = ease(t)
        target = self.centre(shot.look, frame)
        look = lo.lerp(start.look, target, w)
        bump = math.sin(math.pi * min(1.0, t))
        dist = _lerp(start.dist, shot.dist, e) + shot.bulge * bump
        lens = _lerp(start.lens, shot.lens, ease(t / lens_t) if lens_t > 0 else 1.0)
        focus_targets = shot.focus or shot.look
        focus_now = self.centre(focus_targets, frame)
        if shot.rack_to:
            r = max(0.0, min(1.0, (t - shots.RACK_FROM) / (shots.RACK_TO - shots.RACK_FROM)))
            focus_now = lo.lerp(focus_now, self.centre(shot.rack_to, frame), ease(r))
        focus = lo.lerp(start.focus, focus_now, w)
        return CamState(frame, look, _lerp_angle(start.az, shot.az, e), _lerp(start.el, shot.el, e), dist, lens,
                        _lerp(start.fstop, shot.fstop, e), focus)

    # --- accessors ---------------------------------------------------------------------
    def state(self, frame: int) -> CamState:
        return self.states[frame]

    def frames(self) -> list[int]:
        return sorted(self.states)

    def key_frames(self) -> list[int]:
        """Frames that carry camera keys: every PATH_KEY_STEP frames, plus every frame around a cut."""
        step = motion.PATH_KEY_STEP_FRAMES
        frames = set(range(timing.FRAME_START, timing.frame_end() + 1, step)) | {timing.frame_end()}
        for cut in self.cut_frames:
            frames |= set(range(cut - step, cut + step))
        frames |= set(self.beat_first.values())
        return sorted(f for f in frames if f in self.states)


# --- projection and audits ---------------------------------------------------------------------


def _basis(position: Vec3, look: Vec3) -> tuple[Vec3, Vec3, Vec3]:
    forward = lo.sub(look, position)
    n = lo.length(forward)
    forward = (forward[0] / n, forward[1] / n, forward[2] / n)
    right = (forward[1], -forward[0], 0.0)
    rn = math.hypot(right[0], right[1]) or 1.0
    right = (right[0] / rn, right[1] / rn, 0.0)
    up = (
        right[1] * forward[2] - right[2] * forward[1],
        right[2] * forward[0] - right[0] * forward[2],
        right[0] * forward[1] - right[1] * forward[0],
    )
    return forward, right, (-up[0], -up[1], -up[2]) if up[2] < 0 else up


def project(state: CamState, point: Vec3, aspect: float = 16 / 9) -> tuple[float, float, float]:
    """(x, y, depth) with x, y in 0..1 across the frame (y downwards); depth is along the view axis."""
    position = state.position
    forward, right, up = _basis(position, state.look)
    rel = lo.sub(point, position)
    depth = rel[0] * forward[0] + rel[1] * forward[1] + rel[2] * forward[2]
    if depth <= 1e-6:
        return (math.inf, math.inf, depth)
    x = rel[0] * right[0] + rel[1] * right[1] + rel[2] * right[2]
    y = rel[0] * up[0] + rel[1] * up[1] + rel[2] * up[2]
    half_w = shots.SENSOR_WIDTH_MM / 2
    f = state.lens
    px = 0.5 + (x / depth) * f / (2 * half_w)
    py = 0.5 - (y / depth) * f / (2 * half_w) * aspect
    return (px, py, depth)


def view_angle_deg(a: CamState, b: CamState) -> float:
    fa = lo.sub(a.look, a.position)
    fb = lo.sub(b.look, b.position)
    dot = sum(x * y for x, y in zip(fa, fb, strict=True)) / (lo.length(fa) * lo.length(fb))
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))


CUT_TRANSLATION_FRACTION = 0.10  # C-02: a cut is > 10% of the focus distance ...
CUT_ROTATION_DEG = 5.0  # ... or > 5 degrees between consecutive frames
MAX_TRANSLATION_FRACTION = 0.04  # C-02
MAX_ROTATION_DEG = 2.0
MAX_LENS_STEP_MM = 0.5
MAX_SPEED_CHANGE_FRACTION = 0.25
FOCAL_BOX = (0.15, 0.85)
FOCUS_TOLERANCE = 0.10


@dataclass(frozen=True)
class FrameStep:
    frame: int
    translation: float
    translation_fraction: float
    rotation_deg: float
    lens_step: float


def steps(plan: CameraPlan) -> list[FrameStep]:
    out: list[FrameStep] = []
    frames = plan.frames()
    for a, b in zip(frames, frames[1:], strict=False):
        sa, sb = plan.state(a), plan.state(b)
        move = lo.dist(sa.position, sb.position)
        out.append(FrameStep(b, move, move / max(sb.focus_distance, 1e-6), view_angle_deg(sa, sb), abs(sb.lens - sa.lens)))
    return out


def is_cut(step: FrameStep) -> bool:
    return step.translation_fraction > CUT_TRANSLATION_FRACTION or step.rotation_deg > CUT_ROTATION_DEG


def subject_ids() -> dict[str, str]:
    """Beat id -> the object id that is its focal subject (from the story model)."""
    return {beat.id: beat.focal for beat in m.MODEL.beats}
