"""The one camera rig: a camera with a look-at empty and an animated focus empty, keyed from the camera plan.

Per frame the plan gives camera position, look-at point, focus point, lens and f-stop. Keys sit every
``CAMERA_KEY_STEP_FRAMES`` plus every frame next to a cut; the two cuts are CONSTANT between their frames.
"""

from __future__ import annotations

import bpy

from blender.animation import FCurveWriter
from blender.common import PROP_ID, PROP_KIND, tag
from cff.stage.camera import CameraPlan
from cff.theme import shots

CAMERA_NAME = "CAM"
LOOK_NAME = "CAM_LOOK"
FOCUS_NAME = "CAM_FOCUS"


def build_rig(scene: bpy.types.Scene, collection: bpy.types.Collection, plan: CameraPlan, use_dof: bool, prefix: str = "") -> bpy.types.Object:
    """The rig keyed from the plan. ``prefix`` names a twin rig (the SIGNS pass uses one without depth of field)."""
    cam_data = bpy.data.cameras.new(prefix + CAMERA_NAME)
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = shots.SENSOR_WIDTH_MM
    cam_data.clip_start = shots.CLIP_START_M
    cam_data.clip_end = shots.CLIP_END_M
    cam_data.type = "PERSP"
    camera = bpy.data.objects.new(prefix + CAMERA_NAME, cam_data)
    look = bpy.data.objects.new(prefix + LOOK_NAME, None)
    focus = bpy.data.objects.new(prefix + FOCUS_NAME, None)
    for ob in (camera, look, focus):
        collection.objects.link(ob)
        tag(ob, **{PROP_ID: ob.name, PROP_KIND: "camera_rig"})
    look.empty_display_size = focus.empty_display_size = 0.2
    constraint = camera.constraints.new("TRACK_TO")
    constraint.target = look
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    cam_data.dof.use_dof = use_dof
    cam_data.dof.focus_object = focus
    scene.camera = camera

    writers = {
        "camera": FCurveWriter(camera, "CAM-rig"),
        "look": FCurveWriter(look, "LOOK-rig"),
        "focus": FCurveWriter(focus, "FOCUS-rig"),
        "data": FCurveWriter(cam_data, "CAMDATA-rig"),
    }
    cut_frames = set(plan.cut_frames)
    for frame in plan.key_frames():
        state = plan.state(frame)
        hold_to_next = (frame + 1) in cut_frames  # the key before a cut holds its value (the cut is a jump)
        writers["camera"].key("location", frame, state.position, smooth=True, constant=hold_to_next)
        writers["look"].key("location", frame, state.look, smooth=True, constant=hold_to_next)
        writers["focus"].key("location", frame, state.focus, smooth=True, constant=hold_to_next)
        writers["data"].key("lens", frame, (state.lens,), smooth=True, constant=hold_to_next)
        writers["data"].key("dof.aperture_fstop", frame, (state.fstop,), smooth=True, constant=hold_to_next)
    for writer in writers.values():
        writer.finish()
    return camera
