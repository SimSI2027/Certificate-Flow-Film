"""The client cluster: desk, laptop, the stylized user, the session windows and the Trusted Root cradle."""

from __future__ import annotations

import math

import bmesh
from mathutils import Matrix, Vector

from blender.actors import primitives as p
from cff.stage.objects import Kind, StageObject


def desk(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, 0.06, (0.0, 0.0, sz - 0.03))
    for x in (-1, 1):
        for y in (-1, 1):
            p.box(bm, 0.06, 0.06, sz - 0.06, (x * (sx / 2 - 0.06), y * (sy / 2 - 0.06), (sz - 0.06) / 2))


def laptop(bm: bmesh.types.BMesh, o: StageObject) -> None:
    width, depth, height = o.size  # width runs along Y, depth along X; the screen faces +X
    p.box(bm, depth, width, 0.025, (0.0, 0.0, 0.0125))
    lid = Matrix.Translation(Vector((-depth / 2 + 0.01, 0.0, 0.025 + height / 2 - 0.02))) @ Matrix.Rotation(math.radians(-12), 4, "Y")
    bmesh_box(bm, lid, (0.015, width, height - 0.04))
    p.box(bm, 0.012, width - 0.06, height - 0.1, (-depth / 2 + 0.028, 0.0, 0.025 + height / 2 - 0.02))


def bmesh_box(bm: bmesh.types.BMesh, matrix: Matrix, size: tuple[float, float, float]) -> None:
    bmesh.ops.create_cube(bm, size=1.0, matrix=matrix @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))


def figure(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The user's chair (local +X faces the desk). The person sitting on it is the V4 character (``blender.character``)."""
    p.box(bm, 0.5, 0.44, 0.05, (-0.12, 0.0, 0.45))  # seat
    p.box(bm, 0.05, 0.42, 0.48, (-0.36, 0.0, 0.74))  # back
    for x in (-0.33, 0.09):
        for y in (-0.19, 0.19):
            p.box(bm, 0.04, 0.04, 0.43, (x, y, 0.215))  # legs


def screen(bm: bmesh.types.BMesh, o: StageObject) -> None:
    p.box(bm, *o.size)
    if o.variant in ("session", "browser"):
        sx, sy, sz = o.size
        p.box(bm, sx * 0.94, sy * 2.0, 0.05 * sz / 0.56, (0.0, -sy, sz * 0.46))  # window title bar


def root_cradle(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy * 2.2, 0.05, (0.0, 0.0, -sz / 2 + 0.025))
    for side in (-1, 1):
        p.box(bm, 0.05, sy * 2.2, sz, (side * (sx / 2 - 0.025), 0.0, 0.0))
    p.box(bm, sx, 0.02, sz, (0.0, sy * 1.0, 0.0))


BUILDERS = {Kind.DESK: desk, Kind.LAPTOP: laptop, Kind.FIGURE: figure, Kind.SCREEN: screen, Kind.CRADLE: root_cradle}
