"""V5a datacenter (amendment V5-A1): rows of racks round the stage, overhead cable trays over their hot aisles, cold-aisle
light fixtures, perforated raised-floor tiles, and every cable in the film (``cff.stage.hardware.CABLE_RUNS``).

Set dressing only: no story role, no label, nothing animated, never lit by a glow channel. Background racks are linked
duplicates of ``hardware.ROW_VARIANTS`` seeded rack meshes. The aisle lights are shadowless (V3-CIN-01: no shadow pages).
Cables are tagged ``cable`` with their owner, so ``root_no_cables`` can prove none reaches the Root CA.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import bmesh
import bpy
from mathutils import Matrix

from blender import finishes
from blender.actors import hardware
from blender.actors import primitives as p
from blender.actors import slots as s
from blender.common import PROP_ID, PROP_KIND, PROP_OWNER, linear, tag
from cff.stage import hardware as hw
from cff.stage import layout as lo
from cff.story.model import ColourRole
from cff.theme import look, palette

DATACENTER_KIND = "datacenter"
CABLE_KIND = "cable"
CABLE_RESOLUTION = 4
ROD_TOP_Z = 6.0
RUNG_PITCH_M = 0.3
ROD_PITCH_M = 1.8
UNLIT = (0.0, 0.0, 0.0, 1.0)


def _mesh(name: str, slot0: bpy.types.Material, build: Callable[[bmesh.types.BMesh], None]) -> bpy.types.Mesh:
    bm = bmesh.new()
    build(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(slot0)
    for mat in finishes.slot_materials(ColourRole.NEUTRAL):
        mesh.materials.append(mat)
    return mesh


def _object(name: str, data: bpy.types.ID, collection: bpy.types.Collection, kind: str = DATACENTER_KIND, owner: str = "") -> bpy.types.Object:
    ob = bpy.data.objects.new(name, data)
    collection.objects.link(ob)
    ob.color = UNLIT
    tag(ob, **{PROP_ID: name, PROP_KIND: kind, PROP_OWNER: owner})
    return ob


def build_rows(collection: bpy.types.Collection) -> int:
    variants = [_mesh(f"MESH-ROWRACK-{i}", finishes.powder_steel(), lambda bm, spec=spec: hardware.rack(bm, spec, "door", signal_frame=False))
                for i, spec in enumerate(hw.row_variants())]
    racks = hw.row_racks()
    for i, r in enumerate(racks):
        ob = _object(f"DC-RACK-{i:04d}", variants[r.variant], collection)
        ob.location = r.position
        ob.rotation_euler = (0.0, 0.0, math.radians(r.yaw_deg))
    return len(racks)


def _tray(bm: bmesh.types.BMesh, a: lo.Vec3, b: lo.Vec3) -> None:
    """A ladder tray from ``a`` to ``b`` (axis-aligned rows), its rungs, the cable bed in it and the hanger rods above."""
    length = lo.dist(a, b)
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    w = hw.TRAY_WIDTH_M
    nx, ny = -uy, ux

    def along(t0: float, t1: float, o0: float, o1: float, z0: float, z1: float, slot_index: int) -> None:
        xs = [a[0] + ux * t + nx * o for t in (t0, t1) for o in (o0, o1)]
        ys = [a[1] + uy * t + ny * o for t in (t0, t1) for o in (o0, o1)]
        hardware.span(bm, slot_index, min(xs), max(xs), min(ys), max(ys), z0, z1)

    z = a[2]
    for side in (-1, 1):
        along(0.0, length, side * w / 2 - 0.01, side * w / 2 + 0.01, z, z + 0.08, s.STEEL_LIGHT)
    for i in range(int(length / RUNG_PITCH_M)):
        t = i * RUNG_PITCH_M + RUNG_PITCH_M / 2
        along(t - 0.012, t + 0.012, -w / 2, w / 2, z, z + 0.02, s.STEEL_LIGHT)
    along(0.0, length, -w / 2 + 0.03, w / 2 - 0.03, z + 0.02, z + 0.07, s.CABLE)
    for i in range(int(length / ROD_PITCH_M) + 1):
        t = min(length, i * ROD_PITCH_M)
        for side in (-1, 1):
            along(t - 0.006, t + 0.006, side * (w / 2 + 0.03) - 0.006, side * (w / 2 + 0.03) + 0.006, z - 0.03, ROD_TOP_Z, s.STEEL_LIGHT)
        along(t - 0.02, t + 0.02, -w / 2 - 0.05, w / 2 + 0.05, z - 0.03, z, s.STEEL_LIGHT)


def build_trays(collection: bpy.types.Collection) -> int:
    for row in hw.ROWS:
        a, b = hw.row_tray(row)
        _object(f"DC-TRAY-{row.name}", _mesh(f"MESH-TRAY-{row.name}", finishes.powder_steel(), lambda bm, a=a, b=b: _tray(bm, a, b)), collection)
    return len(hw.ROWS)


def build_fixtures(collection: bpy.types.Collection) -> int:
    """Linear LED fixtures over every cold aisle (diffusers in slot 0), and one shadowless area light per aisle."""
    fx, fy, fz = hw.FIXTURE_SIZE
    diffuser = finishes.emitter("aisle", palette.AISLE_LIGHT_HEX, look.AISLE_LIGHT_EMISSION)

    def build(bm: bmesh.types.BMesh) -> None:
        for centre, yaw in hw.fixtures():
            first = len(bm.faces)
            with p.slot(bm, s.STEEL_LIGHT):
                p.box(bm, fx, fy, fz, centre)
                p.box(bm, 0.01, 0.01, ROD_TOP_Z - centre[2], (centre[0], centre[1], (centre[2] + ROD_TOP_Z) / 2))
            with p.slot(bm, s.SIGNAL):
                p.box(bm, fx - 0.04, fy - 0.04, 0.01, (centre[0], centre[1], centre[2] - fz / 2 - 0.004))
            if yaw:
                bm.faces.ensure_lookup_table()
                verts = {v for f in list(bm.faces)[first:] for v in f.verts}
                bmesh.ops.rotate(bm, verts=list(verts), cent=centre, matrix=Matrix.Rotation(math.radians(yaw), 3, "Z"))

    _object("DC-FIXTURES", _mesh("MESH-FIXTURES", diffuser, build), collection)
    for row in hw.ROWS:
        length = hw.ROW_PITCH_M * row.count
        data = bpy.data.lights.new(f"DC-AISLE-{row.name}", "AREA")
        data.shape = "RECTANGLE"
        data.size, data.size_y = length, hw.COLD_AISLE_M * 0.6
        data.energy = look.AISLE_LIGHT_W
        data.color = linear(palette.AISLE_LIGHT_HEX)
        data.use_shadow = False
        ob = _object(f"DC-AISLE-{row.name}", data, collection)
        c = hw.cold_aisle_centre(row, 0.5)
        ob.location = (c[0], c[1], hw.FIXTURE_Z - 0.1)
        ob.rotation_euler = (0.0, 0.0, math.atan2(row.along[1], row.along[0]))
    return len(hw.fixtures())


def build_tiles(collection: bpy.types.Collection) -> int:
    tiles = hw.perforated_tiles()
    half = look.FLOOR_TILE_M / 2 - 0.01

    def build(bm: bmesh.types.BMesh) -> None:
        for x, y, _ in tiles:
            p.box(bm, 2 * half, 2 * half, 0.004, (x, y, 0.002))

    _object("DC-PERFORATED-TILES", _mesh("MESH-PERFORATED-TILES", finishes.perforated_tile(), build), collection)
    return len(tiles)


def build_cables(collection: bpy.types.Collection) -> int:
    """Every cable in the film, as a round curve through its ``CableRun`` points."""
    mat = finishes.plain("cable", palette.CABLE_HEX, look.CABLE_ROUGHNESS)
    for run in hw.CABLE_RUNS:
        curve = bpy.data.curves.new(run.name, "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = hw.CABLE_RADIUS_M
        curve.bevel_resolution = 1
        curve.resolution_u = CABLE_RESOLUTION
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(len(run.points) - 1)
        for bp, point in zip(spline.bezier_points, run.points, strict=True):
            bp.co = point
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        curve.materials.append(mat)
        _object(run.name, curve, collection, CABLE_KIND, run.owner)
    return len(hw.CABLE_RUNS)


def build_datacenter(collection: bpy.types.Collection) -> dict[str, int]:
    return {
        "row_racks": build_rows(collection),
        "trays": build_trays(collection),
        "fixtures": build_fixtures(collection),
        "perforated_tiles": build_tiles(collection),
        "cables": build_cables(collection),
    }
