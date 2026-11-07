"""In-world signage: every model label as a dark plate with white text, turned to face the camera (L-06).

A label is an Empty (the animated root: it carries the appear/leave scale track) with a plate and a text child.
Persistent labels are children of their stage object; windowed tags stand free in the world or hang from one.
"""

from __future__ import annotations

import bpy

from blender import materials
from blender.common import LABEL_FONT, PROP_CAP, PROP_ID, PROP_KIND, PROP_LABEL, bundled_font, tag
from cff.stage import labels
from cff.stage.labels import Placement

TEXT_DEPTH_M = 0.004
PLATE_THICKNESS_M = 0.01
PLATE_GAP_M = 0.006


def _text_object(placement: Placement, collection: bpy.types.Collection) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"TXT-{placement.label_id}", "FONT")
    curve.body = placement.text
    curve.size = labels.cap_m(placement.label_id) * labels.TEXT_TO_EM
    curve.align_x = placement.align
    curve.align_y = "CENTER"
    curve.extrude = 0.0
    curve.font = bundled_font(LABEL_FONT)
    curve.materials.append(materials.label_material("text"))
    ob = bpy.data.objects.new(f"TXT-{placement.label_id}", curve)
    collection.objects.link(ob)
    return ob


def _plate(width: float, height: float, centre_x: float, collection: bpy.types.Collection, name: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"MESH-{name}")
    hx, hy, hz = width / 2, height / 2, PLATE_THICKNESS_M / 2
    corners = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz), (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    mesh.from_pydata(corners, [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    mesh.materials.append(materials.label_material("plate"))
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    ob.location = (centre_x, 0.0, -PLATE_GAP_M)
    return ob


def build_label(placement: Placement, collection: bpy.types.Collection, objects: dict[str, bpy.types.Object], camera: bpy.types.Object) -> bpy.types.Object:
    root = bpy.data.objects.new(placement.label_id, None)
    collection.objects.link(root)
    root.empty_display_size = 0.05
    if placement.parent is not None:
        root.parent = objects[placement.parent]
    root.location = placement.offset
    constraint = root.constraints.new("TRACK_TO")
    constraint.target = camera
    constraint.track_axis = "TRACK_Z"
    constraint.up_axis = "UP_Y"
    text = _text_object(placement, collection)
    text.parent = root
    text.location = (0.0, 0.0, TEXT_DEPTH_M)
    bpy.context.view_layer.update()
    width, height = text.dimensions.x, text.dimensions.y
    cap = labels.cap_m(placement.label_id)
    margin = cap * labels.PLATE_MARGIN_EM
    plate_w, plate_h = width + 2 * margin, max(height, cap * labels.TEXT_TO_EM) + 2 * margin
    plate_x = width / 2 if placement.align == "LEFT" else 0.0  # left-aligned text runs from the label origin to the right
    plate =_plate(plate_w, plate_h, plate_x, collection, f"PLATE-{placement.label_id}")
    plate.parent = root
    tag(root, **{PROP_ID: placement.label_id, PROP_KIND: "label", PROP_LABEL: placement.text, PROP_CAP: cap})
    tag(text, **{PROP_ID: f"TXT-{placement.label_id}", PROP_KIND: "label_text", PROP_LABEL: placement.text, PROP_CAP: cap})
    return root


def build_labels(collection: bpy.types.Collection, objects: dict[str, bpy.types.Object], camera: bpy.types.Object) -> dict[str, bpy.types.Object]:
    out: dict[str, bpy.types.Object] = {}
    for placement in labels.PLACEMENTS:
        out[placement.label_id] = build_label(placement, collection, objects, camera)
    return out
