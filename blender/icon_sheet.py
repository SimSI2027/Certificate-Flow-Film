"""Render the PKI symbol legend (V5b iconography): every symbol, front on, in its film materials, on one 1920x1080 still.

Usage: blender -b --factory-startup --python-exit-code 1 -P blender/icon_sheet.py -- --out <legend.png>

Each object is built with the film's own builder and materials (``blender.world.build_actor``), shown at full size and lit
at a modest glow, so the sheet shows exactly the geometry the film renders. It is a review aid (``qa\\v5b``), not a film frame.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy
from mathutils import Matrix

from blender import world
from blender.common import ROOT, engine_id, linear, linear4, option, script_args
from blender.render_settings import set_view_transform
from cff.stage.objects import BY_ID, Kind
from cff.story.model import ColourRole
from cff.theme import palette

GLOW = 0.3  # the glow channel's value on every symbol (a lit, resting object)
CELL_M = 1.25  # grid pitch
LINK_SCALE = 0.3  # the trust link is shown uniformly scaled down, so its chain links keep their proportions
SEAL_CLOSED = 0.75  # the request's seal ring shown closed round its capsule
ROWS: tuple[tuple[str, ...], ...] = (
    ("CERT-RDP", "CERT-CA1", "CERT-CA1-COPY-RDP", "CERT-ROOT", "CERT-RDP-SELF"),
    ("KEY-RDP-PRIV", "KEY-CA1-PRIV", "KEY-ROOT-PRIV", "KEY-RDP-PUB", "AIA-RDP"),
    ("REQ-RDP", "REQ-CA1", "HS-RDP", "CRL-CA1", "TL-CA1"),
)
COMPANIONS = {"REQ-RDP": ("SEAL-RDP",), "REQ-CA1": ("BAND-CA1",)}


def _glow(ob: bpy.types.Object, role: ColourRole) -> None:
    r, g, b = linear(palette.role_hex(role))
    ob.color = (r * GLOW, g * GLOW, b * GLOW, 1.0)


def main() -> None:
    args = script_args()
    out = Path(option(args, "out", str(ROOT / "qa" / "v5b" / "icon-legend.png")) or "")
    scene = bpy.context.scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob)
    col = bpy.data.collections.new("ICONS")
    scene.collection.children.link(col)
    for r, row in enumerate(ROWS):
        for c, oid in enumerate(row):
            x, z = (c - (len(row) - 1) / 2) * CELL_M * 1.3, -(r - 1) * CELL_M
            for part in (oid, *COMPANIONS.get(oid, ())):
                o = BY_ID[part]
                ob = world.build_actor(o, col)
                ob.rotation_euler = (0.0, 0.0, 0.0)
                ob.scale = o.full
                ob.location = (x, 0.0, z)
                if o.kind is Kind.TRUST_LINK:
                    ob.scale = tuple(v * LINK_SCALE for v in o.full)
                    ob.location = (x - o.full[0] * LINK_SCALE / 2, 0.0, z - 0.2)
                if o.kind is Kind.SEAL_RING:
                    ob.scale = (SEAL_CLOSED,) * 3
                scale = 1.6 if o.kind in {Kind.KEY_PRIVATE, Kind.KEY_PUBLIC, Kind.AIA} else 1.0
                ob.scale = tuple(v * scale for v in ob.scale)
                _glow(ob, o.role if o.role is not ColourRole.NEUTRAL else ColourRole.REQUEST)
    cam_data = bpy.data.cameras.new("CAM")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = CELL_M * 6.8
    cam = bpy.data.objects.new("CAM", cam_data)
    scene.collection.objects.link(cam)
    cam.matrix_world = Matrix.Translation((0.0, -10.0, 0.0)) @ Matrix.Rotation(math.radians(90.0), 4, "X")
    scene.camera = cam
    for name, rot, energy in (("KEY", (55.0, 0.0, -25.0), 3.0), ("FILL", (70.0, 0.0, 40.0), 1.2)):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        light.data.energy = energy
        light.rotation_euler = tuple(math.radians(a) for a in rot)
        scene.collection.objects.link(light)
    scene.world = bpy.data.worlds.new("W")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = linear4(palette.BACKDROP_HEX)
    scene.render.engine = engine_id()
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.eevee.taa_render_samples = 32
    set_view_transform(scene, "AgX")
    scene.render.filepath = str(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print("ICON-SHEET", out)


main()
