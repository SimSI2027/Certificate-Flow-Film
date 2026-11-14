"""The SIGNS pass: every in-world label as a 3D text sign in its own scene, rendered over the beauty pass (Charter 8, 10).

Signs are Blender text objects on dark plates, placed in world space at their anchors and held parallel to the image
plane (they copy the camera's rotation), so the plate lands on screen exactly where the sign plan put it; a sign
turned to the camera's position was skewed off-axis and could leave title-safe (LEG-S1R2-05). Their own scene has a
twin of the beauty camera without depth of field, and no other geometry, so no object can hide a sign and focus never
softens one (L-06). ``cff.stage.signs`` plans every frame: world position, the scale that holds the sign at
``SIGN_CAP_PX`` on screen, and the eased opacity; this module only keys it.

Plates and glyphs render in two view layers (``PLATES``, ``TEXT``) and the scene's compositor lays the text over the
plates. Both use blended alpha, so fades are smooth (no dithered stipple: LEG-S1R2-02, CIN-S1R2-15), and a plate can
never sort over its own text. Signs never overlap each other (the plan keeps them apart), so the split is exact.
The pass renders with a transparent film and the Standard view transform, like the caption layer.
"""

from __future__ import annotations

import math

import bpy

from blender import camera_rig, materials
from blender.animation import FCurveWriter
from blender.common import PROP_CAP, PROP_ID, PROP_KIND, PROP_LABEL, bundled_font, tag
from blender.render_settings import apply_tier
from cff.stage import labels, signs
from cff.stage.camera import CameraPlan
from cff.story.model import ColourRole
from cff.theme import motion, palette
from cff.theme import typography as ty
from cff.theme.render import Tier

SIGNS_SCENE = "SIGNS"
SIGN_CAMERA_PREFIX = "SIGN-"
PLATES_LAYER = "PLATES"
TEXT_LAYER = "TEXT"
PLATES_COLLECTION = "SIGN-PLATES"
TEXT_COLLECTION = "SIGN-TEXT"
TEXT_LIFT_CAPS = 0.03  # text sits this far in front of its plate (in cap heights)


def _plate(name: str, width: float, height: float, centre_x: float, collection: bpy.types.Collection) -> bpy.types.Object:
    """A plate quad in the sign's plane; its origin is the sign's origin (the offset is in the mesh)."""
    mesh = bpy.data.meshes.new(f"MESH-{name}")
    hx, hy = width / 2, height / 2
    mesh.from_pydata([(centre_x - hx, -hy, 0.0), (centre_x + hx, -hy, 0.0), (centre_x + hx, hy, 0.0), (centre_x - hx, hy, 0.0)], [], [(0, 1, 2, 3)])
    mesh.materials.append(materials.sign_plate_material())
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    return ob


PROP_TICK_PHASE = "cff_tick_phase"  # "pending" parts show until the tick resolves, "resolved" parts from then on
# Tick geometry in sign units (1 unit = cap height; text origin at x = 0), V1-LEG-03.
TICK_CENTRE = (-1.1, 0.0)
TICK_RING_RADII = (0.42, 0.55)
TICK_RING_SEGMENTS = 24
TICK_MARK_WIDTH = 0.12
TICK_MARK_STROKES = (((-1.35, 0.02), (-1.15, -0.22)), ((-1.15, -0.22), (-0.80, 0.26)))
TICK_DOT_RADIUS = 0.14


def _tick_part(name: str, kind: str, hex_colour: str, phase: str, parent: bpy.types.Object, collection: bpy.types.Collection) -> None:
    cx, cy = TICK_CENTRE
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    if kind == "ring":
        r0, r1 = TICK_RING_RADII
        for i in range(TICK_RING_SEGMENTS):
            a = 2 * math.pi * i / TICK_RING_SEGMENTS
            verts += [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), 0.0), (cx + r1 * math.cos(a), cy + r1 * math.sin(a), 0.0)]
        n = TICK_RING_SEGMENTS
        faces = [(2 * i, 2 * ((i + 1) % n), 2 * ((i + 1) % n) + 1, 2 * i + 1) for i in range(n)]
    elif kind == "dot":
        verts = [(cx + TICK_DOT_RADIUS * math.cos(2 * math.pi * i / TICK_RING_SEGMENTS), cy + TICK_DOT_RADIUS * math.sin(2 * math.pi * i / TICK_RING_SEGMENTS), 0.0)
                 for i in range(TICK_RING_SEGMENTS)]
        faces = [tuple(range(TICK_RING_SEGMENTS))]
    else:  # the check mark: two flat strokes
        for (x0, y0), (x1, y1) in TICK_MARK_STROKES:
            length = math.hypot(x1 - x0, y1 - y0)
            nx, ny = -(y1 - y0) / length * TICK_MARK_WIDTH / 2, (x1 - x0) / length * TICK_MARK_WIDTH / 2
            base = len(verts)
            verts += [(x0 + nx, y0 + ny, 0.0), (x0 - nx, y0 - ny, 0.0), (x1 - nx, y1 - ny, 0.0), (x1 + nx, y1 + ny, 0.0)]
            faces.append((base, base + 1, base + 2, base + 3))
    mesh = bpy.data.meshes.new(f"MESH-{name}")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(materials.sign_tick_material(hex_colour))
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    ob.parent = parent
    ob.location = (0.0, 0.0, TEXT_LIFT_CAPS)
    ob[PROP_TICK_PHASE] = phase


def _ticks(placement: labels.Placement, root: bpy.types.Object, collection: bpy.types.Collection) -> None:
    """The tick that belongs to a check line, on the line's plate (V1-LEG-03)."""
    role = labels.CHECK_TICK_ROLES.get(placement.label_id)
    if role is None:
        return
    colour = palette.role_hex(role)
    lid = placement.label_id
    if lid in labels.PENDING_TICKS:  # waits in pending amber with a dot, then resolves green
        pending = palette.role_hex(ColourRole.PENDING)
        _tick_part(f"TICK-RING-P-{lid}", "ring", pending, "pending", root, collection)
        _tick_part(f"TICK-DOT-{lid}", "dot", pending, "pending", root, collection)
        _tick_part(f"TICK-RING-{lid}", "ring", colour, "resolved", root, collection)
        _tick_part(f"TICK-MARK-{lid}", "mark", colour, "resolved", root, collection)
        return
    _tick_part(f"TICK-RING-{lid}", "ring", colour, "always", root, collection)
    _tick_part(f"TICK-MARK-{lid}", "mark", colour, "always", root, collection)


def _sign(placement: labels.Placement, board: dict[str, bpy.types.Collection], camera: bpy.types.Object) -> bpy.types.Object:
    """A sign built at a cap height of 1 m: the root's scale is the cap height in metres."""
    root = bpy.data.objects.new(placement.label_id, None)
    board[TEXT_COLLECTION].objects.link(root)
    root.empty_display_size = 0.5
    constraint = root.constraints.new("COPY_ROTATION")  # parallel to the image plane: local +Z points back at the lens
    constraint.target = camera
    curve = bpy.data.curves.new(f"TXT-{placement.label_id}", "FONT")
    curve.body = placement.text
    curve.size = ty.em_per_cap(ty.LABEL_FONT)
    curve.align_x = placement.align
    curve.align_y = "CENTER"
    curve.font = bundled_font(ty.LABEL_FONT)
    curve.materials.append(materials.caption_material("text"))
    text = bpy.data.objects.new(f"TXT-{placement.label_id}", curve)
    board[TEXT_COLLECTION].objects.link(text)
    text.parent = root
    text.location = (0.0, 0.0, TEXT_LIFT_CAPS)
    width, height = ty.sign_plate_size_px(placement.text, 1.0)
    margin = ty.SIGN_PLATE_MARGIN_CAPS
    tick = labels.TICK_WIDTH_CAPS if placement.label_id in labels.CHECK_TICK_ROLES else 0.0  # the plate widens left for the tick
    centre = width / 2 - margin - tick / 2 if placement.align == "LEFT" else 0.0
    plate = _plate(f"PLATE-{placement.label_id}", width + tick, height, centre, board[PLATES_COLLECTION])
    plate.parent = root
    _ticks(placement, root, board[TEXT_COLLECTION])
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
    resolve = labels.tick_resolve_frame(plan.label_id)
    for frame in sorted(plan.frames):
        f = plan.frames[frame]
        grow = motion.LABEL_ENTRANCE_SCALE + (1.0 - motion.LABEL_ENTRANCE_SCALE) * f.alpha  # entrances grow and fade (C-06)
        loc.key("location", frame, f.origin, smooth=True)
        loc.key("scale", frame, (f.cap_m * grow,) * 3, smooth=True)
        for child, writer in zip(root.children, fades, strict=True):
            phase = child.get(PROP_TICK_PHASE, "always")
            gate = 1.0
            if resolve is not None and phase == "pending":
                gate = 1.0 if frame < resolve else 0.0
            elif resolve is not None and phase == "resolved":
                gate = 1.0 if frame >= resolve else 0.0
            writer.key("color", frame, (1.0, 1.0, 1.0, f.alpha * gate), smooth=True)
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
    scene.collection.children.link(rig)
    board = {name: bpy.data.collections.new(name) for name in (PLATES_COLLECTION, TEXT_COLLECTION)}
    for collection in board.values():
        scene.collection.children.link(collection)
    camera = camera_rig.build_rig(scene, rig, plan, use_dof=False, prefix=SIGN_CAMERA_PREFIX)
    planned = signs.plan_signs()
    for placement in labels.PLACEMENTS:
        _key_sign(_sign(placement, board, camera), planned[placement.label_id])
    _split_layers(scene)
    return scene


def _split_layers(scene: bpy.types.Scene) -> None:
    """Two view layers (plates only, text only) and a compositor that lays the text over the plates."""
    text_layer = scene.view_layers[0]
    text_layer.name = TEXT_LAYER
    plates_layer = scene.view_layers.new(PLATES_LAYER)
    text_layer.update()  # a scene made in background has no layer collections until its layer is updated
    text_layer.layer_collection.children[PLATES_COLLECTION].exclude = True
    plates_layer.layer_collection.children[TEXT_COLLECTION].exclude = True
    group = bpy.data.node_groups.new("CFF-Signs-Comp", "CompositorNodeTree")
    group.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    scene.compositing_node_group = group
    nodes, links = group.nodes, group.links
    under, over = nodes.new("CompositorNodeRLayers"), nodes.new("CompositorNodeRLayers")
    for node, layer in ((under, PLATES_LAYER), (over, TEXT_LAYER)):
        node.scene = scene
        node.layer = layer
    stack = nodes.new("CompositorNodeAlphaOver")
    links.new(under.outputs["Image"], stack.inputs["Background"])
    links.new(over.outputs["Image"], stack.inputs["Foreground"])
    out = nodes.new("NodeGroupOutput")
    links.new(stack.outputs["Image"], out.inputs["Image"])
