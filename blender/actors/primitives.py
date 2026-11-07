"""Mesh primitives on a ``bmesh.BMesh``. Every shape in the film is built from these (no external models).

Axis arguments name the local axis the shape runs along. All sizes are full extents in metres.
"""

from __future__ import annotations

import math

import bmesh
from mathutils import Matrix, Vector

Pt = tuple[float, float, float]
AXIS_ROTATION = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.radians(90), 4, "Y"), "Y": Matrix.Rotation(math.radians(-90), 4, "X")}


def _place(centre: Pt, axis: str = "Z", scale: Pt = (1.0, 1.0, 1.0)) -> Matrix:
    return Matrix.Translation(Vector(centre)) @ AXIS_ROTATION[axis] @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))


def box(bm: bmesh.types.BMesh, sx: float, sy: float, sz: float, centre: Pt = (0.0, 0.0, 0.0)) -> None:
    bmesh.ops.create_cube(bm, size=1.0, matrix=_place(centre, "Z", (sx, sy, sz)))


def box_span(bm: bmesh.types.BMesh, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> None:
    box(bm, x1 - x0, y1 - y0, z1 - z0, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cylinder(bm: bmesh.types.BMesh, radius: float, depth: float, segments: int = 16, centre: Pt = (0.0, 0.0, 0.0), axis: str = "Z") -> None:
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=depth, matrix=_place(centre, axis))


def cone(bm: bmesh.types.BMesh, r1: float, r2: float, depth: float, segments: int = 16, centre: Pt = (0.0, 0.0, 0.0), axis: str = "Z") -> None:
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=r1, radius2=r2, depth=depth, matrix=_place(centre, axis))


def sphere(bm: bmesh.types.BMesh, radius: float, centre: Pt = (0.0, 0.0, 0.0), segments: int = 10, rings: int = 6, scale: Pt = (1.0, 1.0, 1.0)) -> None:
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius, matrix=_place(centre, "Z", scale))


def icosphere(bm: bmesh.types.BMesh, radius: float, centre: Pt = (0.0, 0.0, 0.0), subdivisions: int = 1) -> None:
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=radius, matrix=_place(centre))


def torus(bm: bmesh.types.BMesh, major: float, minor: float, centre: Pt = (0.0, 0.0, 0.0), axis: str = "Z", segments: int = 28, minor_segments: int = 8) -> None:
    """A ring of tube radius ``minor`` around a circle of radius ``major``; ``axis`` is the ring's normal."""
    matrix = _place(centre, axis)
    rings: list[list[bmesh.types.BMVert]] = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        ring = []
        for j in range(minor_segments):
            b = 2 * math.pi * j / minor_segments
            r = major + minor * math.cos(b)
            ring.append(bm.verts.new(matrix @ Vector((r * math.cos(a), r * math.sin(a), minor * math.sin(b)))))
        rings.append(ring)
    for i in range(segments):
        for j in range(minor_segments):
            bm.faces.new((rings[i][j], rings[(i + 1) % segments][j], rings[(i + 1) % segments][(j + 1) % minor_segments], rings[i][(j + 1) % minor_segments]))


def prism(bm: bmesh.types.BMesh, outline: list[tuple[float, float]], depth: float, centre: Pt = (0.0, 0.0, 0.0), axis: str = "Y") -> None:
    """A convex or simple polygon (x, z pairs) extruded ``depth`` along ``axis`` (default Y: the polygon sits in XZ)."""
    matrix = _place(centre, "Z")
    half = depth / 2
    lower = [bm.verts.new(matrix @ Vector((x, -half, z))) for x, z in outline]
    upper = [bm.verts.new(matrix @ Vector((x, half, z))) for x, z in outline]
    bm.faces.new(lower[::-1])
    bm.faces.new(upper)
    count = len(outline)
    for i in range(count):
        bm.faces.new((lower[i], lower[(i + 1) % count], upper[(i + 1) % count], upper[i]))
    del axis


def arc_of_boxes(bm: bmesh.types.BMesh, radius: float, span_deg: float, count: int, tile: tuple[float, float, float], centre: Pt = (0.0, 0.0, 0.0)) -> None:
    """A curved rail made of ``count`` boxes laid on an arc in the XY plane, opening toward -Y."""
    for i in range(count):
        a = math.radians(-90 - span_deg / 2 + span_deg * i / max(1, count - 1))
        m = Matrix.Translation(Vector((centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a), centre[2]))) @ Matrix.Rotation(a + math.pi / 2, 4, "Z")
        bmesh.ops.create_cube(bm, size=1.0, matrix=m @ Matrix.Diagonal((tile[0], tile[1], tile[2], 1.0)))
