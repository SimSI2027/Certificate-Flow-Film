"""Server racks: the open-front chassis, its hinged panel, ports and the key container with lid, lock and clamps."""

from __future__ import annotations

import bmesh

from blender.actors import primitives as p
from cff.stage.objects import Kind, StageObject

WALL = 0.06


def chassis(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """An open-front shell standing on its base; the hinged panel closes the front."""
    sx, sy, sz = o.size
    p.box(bm, sx, sy, 0.08, (0.0, 0.0, 0.04))
    p.box(bm, sx, sy, 0.08, (0.0, 0.0, sz - 0.04))
    p.box(bm, sx, WALL, sz, (0.0, sy / 2 - WALL / 2, sz / 2))
    for side in (-1, 1):
        p.box(bm, WALL, sy, sz, (side * (sx / 2 - WALL / 2), 0.0, sz / 2))
    p.box(bm, sx - 0.1, 0.02, 0.07, (0.0, sy / 2 - WALL - 0.02, 0.35))  # interior shelf rail
    p.box(bm, sx + 0.1, sy + 0.1, 0.06, (0.0, 0.0, 0.03))  # plinth


def panel(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """Origin on the hinge edge (left, bottom); the leaf extends along +X and +Z."""
    sx, sy, sz = o.size
    p.box_span(bm, 0.0, sx, -sy / 2, sy / 2, 0.0, sz)
    for i in range(6):  # vents
        p.box_span(bm, 0.12, sx - 0.12, -sy / 2 - 0.012, -sy / 2, 0.25 + i * 0.12, 0.29 + i * 0.12)
    p.cylinder(bm, 0.03, 0.02, 8, (sx - 0.14, -sy / 2 - 0.012, sz - 0.14), "Y")  # status light


def port(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    p.cylinder(bm, sx * 0.32, sy * 1.6, 8, (0.0, -sy * 0.3, 0.0), "Y")


def container(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    for x in (-1, 1):
        for z in (-1, 1):
            p.box(bm, 0.05, sy + 0.02, 0.05, (x * (sx / 2 - 0.025), 0.0, z * (sz / 2 - 0.025)))


def lid(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """Origin on the hinge (left edge, top of the container); closed it lies along +X."""
    sx, sy, sz = o.size
    p.box_span(bm, 0.0, sx, -sy / 2, sy / 2, -sz / 2, sz / 2)


def lock(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.cylinder(bm, sx / 2, sy, 14, (0.0, 0.0, 0.0), "Y")
    p.box(bm, sx * 0.14, sy * 1.4, sz * 0.5, (0.0, -sy * 0.2, 0.0))  # keyhole bar, turns with the lock


def clamp(bm: bmesh.types.BMesh, o: StageObject) -> None:
    p.box(bm, *o.size)
    p.box(bm, o.size[0] * 0.5, o.size[1] * 1.2, o.size[2] * 1.4, (0.0, 0.0, 0.0))


BUILDERS = {
    Kind.CHASSIS: chassis,
    Kind.PANEL: panel,
    Kind.PORT: port,
    Kind.CONTAINER: container,
    Kind.CONTAINER_LID: lid,
    Kind.LOCK: lock,
    Kind.CLAMP: clamp,
}
