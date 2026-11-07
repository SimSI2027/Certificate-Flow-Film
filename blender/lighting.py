"""Lighting blocking: a warm key and a cool rim that travel with the camera, plus a faint static top light.

The key stands off to the camera's upper left; the rim sits behind the subject, on the far side, so it is always
more than 120 degrees from the camera direction around the subject (C-05). Power scales with the square of the
camera distance so wide shots stay lit; the world itself contributes far less than 20% of the key (C-05).
"""

from __future__ import annotations

import math

import bpy

from blender.animation import FCurveWriter
from blender.common import PROP_ID, PROP_KIND, linear, tag
from cff.stage import layout as lo
from cff.stage.camera import CameraPlan
from cff.theme import palette

KEY_NAME = "LIGHT-key"
RIM_NAME = "LIGHT-rim"
TOP_NAME = "LIGHT-top"
REFERENCE_DISTANCE_M = 4.0
DISTANCE_CLAMP_M = (3.0, 46.0)
KEY_OFFSET = (-0.30, 0.35)  # (right, up) in camera distances
RIM_OFFSET = (0.35, 0.40)
RIM_BEHIND = 0.85
SPOT_MIN_RADIUS_M = 5.0
SPOT_RADIUS_PER_DISTANCE = 0.5
SPOT_BLEND = 0.6
TOP_LIGHT_ENERGY = 1.2
TOP_LIGHT_ANGLE_DEG = 18.0
TOP_LIGHT_TILT_DEG = 35.0
LIGHT_KEY_STEP = 6


def _spot(name: str, hex_colour: str, collection: bpy.types.Collection, look: bpy.types.Object) -> bpy.types.Object:
    data = bpy.data.lights.new(name, "SPOT")
    data.color = linear(hex_colour)
    data.shadow_soft_size = 0.3
    data.spot_blend = SPOT_BLEND
    ob = bpy.data.objects.new(name, data)
    collection.objects.link(ob)
    constraint = ob.constraints.new("TRACK_TO")
    constraint.target = look
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    tag(ob, **{PROP_ID: name, PROP_KIND: "light"})
    return ob


def build_lights(collection: bpy.types.Collection, look: bpy.types.Object, plan: CameraPlan) -> None:
    top_data = bpy.data.lights.new(TOP_NAME, "SUN")
    top_data.energy = TOP_LIGHT_ENERGY
    top_data.angle = math.radians(TOP_LIGHT_ANGLE_DEG)
    top_data.color = linear(palette.RIM_LIGHT_HEX)
    top = bpy.data.objects.new(TOP_NAME, top_data)
    top.rotation_euler = (math.radians(TOP_LIGHT_TILT_DEG), 0.0, math.radians(-30.0))
    collection.objects.link(top)
    tag(top, **{PROP_ID: TOP_NAME, PROP_KIND: "light"})

    key = _spot(KEY_NAME, palette.KEY_LIGHT_HEX, collection, look)
    rim = _spot(RIM_NAME, palette.RIM_LIGHT_HEX, collection, look)
    writers = {n: FCurveWriter(o, f"{n}-rig") for n, o in ((KEY_NAME, key), (RIM_NAME, rim))}
    data_writers = {n: FCurveWriter(o.data, f"{n}-data") for n, o in ((KEY_NAME, key), (RIM_NAME, rim))}
    frames = sorted(set(range(plan.frames()[0], plan.frames()[-1] + 1, LIGHT_KEY_STEP)) | set(plan.key_frames()))
    for frame in frames:
        state = plan.state(frame)
        position = state.position
        forward = lo.sub(state.look, position)
        distance = min(max(lo.length(forward), DISTANCE_CLAMP_M[0]), DISTANCE_CLAMP_M[1])
        unit = lo.mul(forward, 1.0 / max(lo.length(forward), 1e-6))
        right = (unit[1], -unit[0], 0.0)
        norm = math.hypot(right[0], right[1]) or 1.0
        right = (right[0] / norm, right[1] / norm, 0.0)
        up = (0.0, 0.0, 1.0)
        key_pos = lo.add(position, lo.add(lo.mul(right, KEY_OFFSET[0] * distance), lo.mul(up, KEY_OFFSET[1] * distance)))
        rim_pos = lo.add(state.look, lo.add(lo.mul(unit, RIM_BEHIND * distance), lo.add(lo.mul(right, RIM_OFFSET[0] * distance), lo.mul(up, RIM_OFFSET[1] * distance))))
        scale = (distance / REFERENCE_DISTANCE_M) ** 2
        radius = max(SPOT_MIN_RADIUS_M, SPOT_RADIUS_PER_DISTANCE * distance)
        for name, light_pos, watts in ((KEY_NAME, key_pos, palette.KEY_LIGHT_POWER_W), (RIM_NAME, rim_pos, palette.RIM_LIGHT_POWER_W)):
            writers[name].key("location", frame, light_pos, smooth=True)
            data_writers[name].key("energy", frame, (watts * scale,), smooth=True)
            reach = lo.dist(light_pos, state.look)
            data_writers[name].key("spot_size", frame, (min(math.radians(120.0), 2.0 * math.atan2(radius, max(reach, 1e-3))),), smooth=True)
    for writer in (*writers.values(), *data_writers.values()):
        writer.finish()
