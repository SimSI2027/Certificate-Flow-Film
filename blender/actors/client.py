"""The client cluster: desk, laptop, the user's chair, the session windows and the Trusted Root cradle."""

from __future__ import annotations

import bmesh

from blender.actors import hardware
from blender.actors import primitives as p
from cff.stage.objects import Kind, StageObject


def desk(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """V5a: an office desk (laminate top, steel C-frame legs, modesty panel)."""
    hardware.desk(bm, o.size)


def laptop(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """V5a: a thin modern laptop, no logo (``hardware.laptop``). Width runs along Y, depth along X; the screen faces +X."""
    hardware.laptop(bm, o.size)


def figure(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The user's office chair (local +X faces the desk). The person sitting on it is the V4 character (``blender.character``)."""
    hardware.office_chair(bm)


def screen(bm: bmesh.types.BMesh, o: StageObject) -> None:
    if o.variant == "idle":  # V5a: the laptop's own display, showing the RDP client's connection dialog
        hardware.screen_ui(bm, o.size)
        return
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
