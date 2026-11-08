"""The caption layer: a separate scene with an orthographic camera and a transparent film (Charter 10).

Captions never share a scene with the 3D world, so depth of field, bloom and motion blur never soften them.
Each caption fades and rises with the named motion presets; exactly one is visible at a time (L-05).
"""

from __future__ import annotations

import bpy

from blender import materials
from blender.animation import FCurveWriter
from blender.common import CAPTION_FONT, PROP_CAP, PROP_ID, PROP_KIND, PROP_LABEL, bundled_font, tag
from blender.render_settings import apply_tier
from cff.stage import caption_layout
from cff.story import captions, timing
from cff.story.captions import Caption, CaptionKind
from cff.theme import render
from cff.theme import typography as ty
from cff.theme.render import Tier

CAPTION_SCENE = "CAPTIONS"
UNIT_PX = render.CAPTION_PIXELS_PER_UNIT
ORTHO_WIDTH_UNITS = render.CAPTION_REFERENCE_WIDTH_PX / UNIT_PX
RISE_UNITS = 0.16
PLATE_MARGIN_UNITS = ty.CAPTION_PLATE_MARGIN_PX / UNIT_PX
TEXT_TO_EM = ty.em_per_cap(ty.CAPTION_FONT)  # measured glyph ratio (cff.theme.typography), re-measured by check_fonts
CAMERA_Z_UNITS = 10.0


def caption_cap_units(caption: Caption) -> float:
    return (ty.TITLE_CAP_PX if caption.kind is CaptionKind.TITLE else ty.CAPTION_CAP_PX) / UNIT_PX


def caption_centre_y_units(caption: Caption) -> float:
    """Top or bottom band, whichever keeps the plate clear of the focal subject (cff.stage.caption_layout, L-05)."""
    return (render.CAPTION_REFERENCE_HEIGHT_PX / 2 - caption_layout.centre_y_px(caption.id)) / UNIT_PX


def _plate(scene: bpy.types.Scene, width: float, height: float, name: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"MESH-{name}")
    hx, hy = width / 2, height / 2
    mesh.from_pydata([(-hx, -hy, 0.0), (hx, -hy, 0.0), (hx, hy, 0.0), (-hx, hy, 0.0)], [], [(0, 1, 2, 3)])
    mesh.materials.append(materials.caption_material("plate"))
    ob = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(ob)
    return ob


def build_caption_scene(tier: Tier) -> bpy.types.Scene:
    scene = bpy.data.scenes.new(CAPTION_SCENE)
    apply_tier(scene, tier, transparent=True)
    scene.render.use_motion_blur = False
    scene.eevee.use_shadows = False
    cam_data = bpy.data.cameras.new("CAPCAM")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ORTHO_WIDTH_UNITS
    cam_data.clip_start, cam_data.clip_end = 0.1, 100.0
    cam = bpy.data.objects.new("CAPCAM", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (0.0, 0.0, CAMERA_Z_UNITS)
    scene.camera = cam
    tag(cam, **{PROP_ID: "CAPCAM", PROP_KIND: "caption_camera"})

    for caption in captions.CAPTIONS:
        _build_caption(scene, caption)
    return scene


def _build_caption(scene: bpy.types.Scene, caption: Caption) -> None:
    cap_units = caption_cap_units(caption)
    curve = bpy.data.curves.new(f"TXT-{caption.id}", "FONT")
    curve.body = caption.text
    curve.size = cap_units * TEXT_TO_EM
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.font = bundled_font(CAPTION_FONT)
    curve.materials.append(materials.caption_material("text"))
    text = bpy.data.objects.new(f"TXT-{caption.id}", curve)
    scene.collection.objects.link(text)
    scene.view_layers[0].update()
    width, height = text.dimensions.x, text.dimensions.y
    del height  # the plate height is fixed per size, so every plate in a band lines up
    plate = _plate(scene, width + 2 * PLATE_MARGIN_UNITS, cap_units * TEXT_TO_EM + 1.4 * PLATE_MARGIN_UNITS, f"PLATE-{caption.id}")
    root = bpy.data.objects.new(f"CAP-{caption.id}", None)
    scene.collection.objects.link(root)
    for child, depth in ((plate, 0.0), (text, 0.01)):
        child.parent = root
        child.location = (0.0, 0.0, depth)
    y = caption_centre_y_units(caption)
    root.location = (0.0, y, 0.0)
    tag(root, **{PROP_ID: caption.id, PROP_KIND: "caption", PROP_LABEL: caption.text, PROP_CAP: cap_units})
    # alpha lives on the colour of each child (the material reads Object Info > Alpha); the rise is on the root
    fade_in, hold_start, hold_end, vanish = (timing.seconds_to_frame(s) for s in (caption.appear_s, caption.hold_start_s, caption.hold_end_s, caption.vanish_s))
    root_writer = FCurveWriter(root, f"{caption.id}-root")
    root_writer.key("location", timing.FRAME_START, (0.0, y - RISE_UNITS, 0.0), ease="EASE_IN_OUT")
    root_writer.key("location", fade_in, (0.0, y - RISE_UNITS, 0.0), ease="EASE_OUT")
    root_writer.key("location", hold_start, (0.0, y, 0.0), ease="EASE_IN_OUT")
    root_writer.key("location", hold_end, (0.0, y, 0.0), ease="EASE_IN")
    root_writer.key("location", vanish, (0.0, y + RISE_UNITS * 0.5, 0.0), ease="EASE_IN_OUT")
    root_writer.finish()
    for child in (plate, text):
        writer = FCurveWriter(child, f"{caption.id}-{child.name}")
        for frame, alpha, ease in ((timing.FRAME_START, 0.0, "EASE_IN_OUT"), (fade_in, 0.0, "EASE_OUT"), (hold_start, 1.0, "EASE_IN_OUT"), (hold_end, 1.0, "EASE_IN"), (vanish, 0.0, "EASE_IN_OUT")):
            writer.key("color", frame, (1.0, 1.0, 1.0, alpha), ease=ease)
        writer.finish()
