"""Writing keyframes: slotted-action F-curves from the pure-Python ``Timeline``.

Blender 5.x actions hold F-curves in channelbags (layer -> strip -> channelbag per slot); the legacy
``action.fcurves`` is gone, so every curve is created through ``channelbag.fcurves``. Handles come from the named
easing presets in ``cff.theme.motion`` (FREE handles shaped as a cubic-bezier), or auto-clamped for SMOOTH keys.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass, field

import bpy

from cff.stage.tracks import CHANNEL_WIDTH, GLOW, LOCATION, ROTATION, SCALE, Timeline
from cff.theme import motion

DATA_PATHS = {LOCATION: "location", ROTATION: "rotation_euler", SCALE: "scale", GLOW: "color"}
SLOT_TYPES = ((bpy.types.Camera, "CAMERA"), (bpy.types.Light, "LIGHT"), (bpy.types.NodeTree, "NODETREE"))


@dataclass
class _Key:
    frame: float
    value: float
    ease: str
    constant: bool


@dataclass
class FCurveWriter:
    """Collects keys for one ID block, then writes its action in one pass."""

    id_block: bpy.types.ID
    name: str
    curves: dict[tuple[str, int], list[_Key]] = field(default_factory=dict)

    def key(self, data_path: str, frame: float, values: Sequence[float], ease: str = motion.SMOOTH, smooth: bool = False, constant: bool = False) -> None:
        easing = motion.SMOOTH if smooth else ease
        for index, value in enumerate(values):
            self.curves.setdefault((data_path, index), []).append(_Key(float(frame), float(value), easing, constant))

    def finish(self) -> None:
        if not self.curves:
            return
        action = bpy.data.actions.new(f"ACT-{self.name}")
        slot_type = next((t for cls, t in SLOT_TYPES if isinstance(self.id_block, cls)), "OBJECT")
        slot = action.slots.new(id_type=slot_type, name=self.name)
        layer = action.layers.new("L")
        strip = layer.strips.new(type="KEYFRAME")
        bag = strip.channelbag(slot, ensure=True)
        for (data_path, index), keys in self.curves.items():
            _write_curve(bag, data_path, index, keys)
        self.id_block.animation_data_create()
        self.id_block.animation_data.action = action
        self.id_block.animation_data.action_slot = slot


def _write_curve(bag: bpy.types.ActionChannelbag, data_path: str, index: int, keys: list[_Key]) -> None:
    keys = sorted(keys, key=lambda k: k.frame)
    for a, b in itertools.pairwise(keys):
        if not b.frame > a.frame:
            raise ValueError(f"{data_path}[{index}]: keys not strictly ordered at frame {b.frame}")
    for key in keys:
        if not (math.isfinite(key.value) and math.isfinite(key.frame)):
            raise ValueError(f"{data_path}[{index}]: non-finite key at frame {key.frame}")
    fcurve = bag.fcurves.new(data_path, index=index)
    points = fcurve.keyframe_points
    points.add(len(keys))
    for point, key in zip(points, keys, strict=True):
        point.co = (key.frame, key.value)
        point.interpolation = "CONSTANT" if key.constant else "BEZIER"
        point.handle_left_type = "AUTO_CLAMPED"
        point.handle_right_type = "AUTO_CLAMPED"
    for i, (a, b) in enumerate(itertools.pairwise(keys)):
        if a.ease == motion.SMOOTH or a.constant:
            continue
        easing = motion.preset(a.ease)
        span, rise = b.frame - a.frame, b.value - a.value
        left, right = points[i], points[i + 1]
        left.handle_right_type = "FREE"
        right.handle_left_type = "FREE"
        left.handle_right = (a.frame + easing.x1 * span, a.value + easing.y1 * rise)
        right.handle_left = (a.frame + easing.x2 * span, a.value + easing.y2 * rise)
    fcurve.update()


def write_timeline(timeline: Timeline, objects: dict[str, bpy.types.Object]) -> int:
    """Create one action per animated object. Returns the number of keyframes written."""
    total = 0
    for obj_id in timeline.objects():
        writer = FCurveWriter(objects[obj_id], obj_id)
        for channel in (LOCATION, ROTATION, SCALE, GLOW):
            for key in timeline.keys(obj_id, channel):
                values = tuple(math.radians(v) for v in key.value) if channel == ROTATION else key.value
                writer.key(DATA_PATHS[channel], key.frame, values, ease=key.ease, smooth=key.ease == motion.SMOOTH)
                total += CHANNEL_WIDTH[channel]
        writer.finish()
    return total
