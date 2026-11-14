"""Which beauty frames a client-cluster change touches (Session V4: realistic user character, laptop within reach).

``snapshot`` records the camera plan and the client-cluster bounds BEFORE a change; ``compute`` rebuilds both AFTER the
change and returns every frame on which

* the camera plan differs from the snapshot (any look, angle, distance, lens, f-stop or focus value), or
* any part of the client-cluster region (old and new bounds, grown by ``SHADOW_MARGIN_M`` for shadows the character casts
  onto the desk and floor) projects inside the frame (grown by ``FRAME_MARGIN``) in front of the camera,

dilated by ``DILATE_FRAMES`` because Blender interpolates the camera between keys. Nothing here is guessed: the
projection is ``cff.stage.camera.project``, the same model the planned-film audits use.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

from cff.stage import camera, choreography
from cff.stage.objects import BY_ID
from cff.story import model as m
from cff.story import timing
from tools import frames, toolchain

ROOT = toolchain.ROOT
BASELINE = ROOT / "qa" / "v4" / "camera-baseline.json"
RESULT = ROOT / "qa" / "v4" / "beauty-rerender.json"

CLUSTER_IDS: tuple[str, ...] = ("DESK", m.CLIENT, m.USER, "SCREEN-IDLE")
CHARACTER_EXTENT = ((-0.9, 0.9), (-0.6, 0.6), (0.0, 1.7))  # around the user's home: a seated adult reaching a desk, with margin
SHADOW_MARGIN_M = 1.0
FRAME_MARGIN = 0.1  # fraction of the frame added on every side
DILATE_FRAMES = 3
GRID = 7  # sample points per box edge
CAMERA_TOLERANCE = 1e-6

Box = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]


def _object_box(obj_id: str) -> Box:
    o = BY_ID[obj_id]
    x, y, z = o.home
    sx, sy, sz = o.size
    half = max(sx, sy) / 2  # yaw-independent footprint
    if obj_id == m.USER:
        (ax, bx), (ay, by), (az, bz) = CHARACTER_EXTENT
        return ((x + ax, x + bx), (y + ay, y + by), (z + az, z + bz))
    return ((x - half, x + half), (y - half, y + half), (z - sz, z + sz))


def cluster_box() -> Box:
    boxes = [_object_box(i) for i in CLUSTER_IDS]
    return tuple((min(b[k][0] for b in boxes), max(b[k][1] for b in boxes)) for k in range(3))  # type: ignore[return-value]


def _union(a: Box, b: Box) -> Box:
    return tuple((min(a[k][0], b[k][0]), max(a[k][1], b[k][1])) for k in range(3))  # type: ignore[return-value]


def _grow(box: Box, margin: float) -> Box:
    return tuple((lo_ - margin, hi + margin) for lo_, hi in box)  # type: ignore[return-value]


def _state_row(s: camera.CamState) -> list[float]:
    return [*s.look, s.az, s.el, s.dist, s.lens, s.fstop, *s.focus]


def _plan() -> camera.CameraPlan:
    return camera.CameraPlan(choreography.build_timeline())


def snapshot(path: Path = BASELINE) -> Path:
    plan = _plan()
    payload = {"cluster_box": cluster_box(), "camera": {str(f): _state_row(plan.state(f)) for f in plan.frames()}}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8", newline="\n")
    return path


def _points(box: Box) -> list[tuple[float, float, float]]:
    xs, ys, zs = ([lo_ + (hi - lo_) * i / (GRID - 1) for i in range(GRID)] for lo_, hi in box)
    return list(itertools.product(xs, ys, zs))


def _in_view(state: camera.CamState, points: list[tuple[float, float, float]], box: Box) -> bool:
    pos = state.position
    if all(box[k][0] <= pos[k] <= box[k][1] for k in range(3)):
        return True
    for p in points:
        x, y, depth = camera.project(state, p)
        if depth > 0 and -FRAME_MARGIN <= x <= 1 + FRAME_MARGIN and -FRAME_MARGIN <= y <= 1 + FRAME_MARGIN:
            return True
    return False


def compute(baseline: Path = BASELINE) -> dict[str, object]:
    data = json.loads(baseline.read_text(encoding="utf-8"))
    old_box: Box = tuple(tuple(axis) for axis in data["cluster_box"])  # type: ignore[assignment]
    region = _grow(_union(old_box, cluster_box()), SHADOW_MARGIN_M)
    points = _points(region)
    plan = _plan()
    camera_changed, in_view = set(), set()
    for f in plan.frames():
        old = data["camera"].get(str(f))
        new = _state_row(plan.state(f))
        if old is None or any(abs(a - b) > CAMERA_TOLERANCE for a, b in zip(old, new, strict=True)):
            camera_changed.add(f)
        if _in_view(plan.state(f), points, region):
            in_view.add(f)
    first, last = timing.FRAME_START, timing.frame_end()
    core = camera_changed | in_view
    dilated = sorted({g for f in core for g in range(f - DILATE_FRAMES, f + DILATE_FRAMES + 1) if first <= g <= last})
    return {
        "region": region,
        "camera_changed": frames.ranges(sorted(camera_changed)),
        "cluster_in_view": frames.ranges(sorted(in_view)),
        "frames": dilated,
        "ranges": frames.ranges(dilated),
        "count": len(dilated),
        "of": last - first + 1,
    }


def write(result: dict[str, object], path: Path = RESULT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    slim = {k: v for k, v in result.items() if k != "frames"}
    path.write_text(json.dumps(slim, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path
