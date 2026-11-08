"""The SIGNS pass: every in-world label as a 3D text sign in its own scene, rendered over the beauty pass (Charter 8, 10).

Signs are Blender text objects on dark plates, placed in world space at their anchors and turned to the camera
(physical signage). Their own scene has a twin of the beauty camera without depth of field, and no other geometry,
so no object can hide a sign and focus never softens one (L-06). ``cff.stage.signs`` plans every frame: world
position, the scale that holds the sign at ``SIGN_CAP_PX`` on screen, and the eased opacity; this module only keys it.
The pass renders with a transparent film and the Standard view transform, like the caption layer.
"""

from __future__ import annotations

import bpy

from blender import camera_rig, materials
from blender.animation import FCurveWriter
from blender.common import PROP_CAP, PROP_ID, PROP_KIND, PROP_LABEL, bundled_font, tag
from blender.render_settings import apply_tier
from cff.stage import labels, signs
from cff.stage.camera import CameraPlan
from cff.theme import motion
from cff.theme import typography as ty
from cff.theme.render import Tier

SIGNS_SCENE = "SIGNS"
SIGN_CAMERA_PREFIX = "SIGN-"
TEXT_LIFT_CAPS = 0.03  # text sits this far in front of its plate (in cap heights), so blended sorting is unambiguous


def _plate(name: str, width: float, height: float, centre_x: float, collection: bpy.types.Collection) -> bpy.types.Object:
    """The plate's origin stays at the sign's origin (the offset is in the mesh), so blended sorting always puts the text,
    lifted towards the camera, in front of its plate; an offset origin let the plate sort over left-aligned text."""
    mesh = bpy.data.meshes.new(f"MESH-{name}")
    hx, hy = width / 2, height / 2
    mesh.from_pydata([(centre_x - hx, -hy, 0.0), (centre_x + hx, -hy, 0.0), (centre_x + hx, hy, 0.0), (centre_x - hx, hy, 0.0)], [], [(0, 1, 2, 3)])
    mesh.materials.append(materials.sign_plate_material())
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    return ob


def _sign(placement: labels.Placement, collection: bpy.types.Collection, camera: bpy.types.Object) -> bpy.types.Object:
    """A sign built at a cap height of 1 m: the root's scale is the cap height in metres."""
    root = bpy.data.objects.new(placement.label_id, None)
    collection.objects.link(root)
    root.empty_display_size = 0.5
    constraint = root.constraints.new("TRACK_TO")
    constraint.target = camera
    constraint.track_axis = "TRACK_Z"
    constraint.up_axis = "UP_Y"
    curve = bpy.data.curves.new(f"TXT-{placement.label_id}", "FONT")
    curve.body = placement.text
    curve.size = ty.em_per_cap(ty.LABEL_FONT)
    curve.align_x = placement.align
    curve.align_y = "CENTER"
    curve.font = bundled_font(ty.LABEL_FONT)
    curve.materials.append(materials.caption_material("text"))
    text = bpy.data.objects.new(f"TXT-{placement.label_id}", curve)
    collection.objects.link(text)
    text.parent = root
    text.location = (0.0, 0.0, TEXT_LIFT_CAPS)
    width, height = ty.sign_plate_size_px(placement.text, 1.0)
    margin = ty.SIGN_PLATE_MARGIN_CAPS
    plate = _plate(f"PLATE-{placement.label_id}", width, height, width / 2 - margin if placement.align == "LEFT" else 0.0, collection)
    plate.parent = root
    tag(root, **{PROP_ID: placement.label_id, PROP_KIND: "sign", PROP_LABEL: placement.text, PROP_CAP: 1.0})
    tag(text, **{PROP_ID: f"TXT-{placement.label_id}", PROP_KIND: "sign_text", PROP_LABEL: placement.text})
    return root


def _key_sign(root: bpy.types.Object, plan: signs.SignPlan) -> int:
    loc = FCurveWriter(root, f"{plan.label_id}-sign")
    fades = [FCurveWriter(child, f"{plan.label_id}-{child.name}") for child in root.children]
    if not plan.frames:
        root.scale = (motion.HIDDEN_SCALE,) * 3
        for child in root.children:
            child.color = (1.0, 1.0, 1.0, 0.0)
        return 0
    for frame in sorted(plan.frames):
        f = plan.frames[frame]
        grow = motion.LABEL_ENTRANCE_SCALE + (1.0 - motion.LABEL_ENTRANCE_SCALE) * f.alpha  # entrances grow and fade (C-06)
        loc.key("location", frame, f.origin, smooth=True)
        loc.key("scale", frame, (f.cap_m * grow,) * 3, smooth=True)
        for writer in fades:
            writer.key("color", frame, (1.0, 1.0, 1.0, f.alpha), smooth=True)
    loc.finish()
    for writer in fades:
        writer.finish()
    return len(plan.frames)


def build_signs_scene(tier: Tier, plan: CameraPlan) -> bpy.types.Scene:
    scene = bpy.data.scenes.new(SIGNS_SCENE)
    apply_tier(scene, tier, transparent=True)
    scene.render.use_motion_blur = False
    scene.eevee.use_shadows = False
    rig = bpy.data.collections.new("SIGN-RIG")
    board = bpy.data.collections.new("SIGNS")
    scene.collection.children.link(rig)
    scene.collection.children.link(board)
    camera = camera_rig.build_rig(scene, rig, plan, use_dof=False, prefix=SIGN_CAMERA_PREFIX)
    planned = signs.plan_signs()
    for placement in labels.PLACEMENTS:
        _key_sign(_sign(placement, board, camera), planned[placement.label_id])
    return scene
