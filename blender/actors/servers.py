"""Server racks: the open-front chassis, its hinged panel, ports and the key container with lid, lock and clamps."""

from __future__ import annotations

import bmesh

from blender.actors import hardware
from blender.actors import primitives as p
from blender.actors import slots as s
from cff.stage import hardware as hw
from cff.stage.objects import Kind, StageObject


def chassis(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """V5a: a double-width rack cabinet (two 19-inch columns of 1U/2U devices against the back) with an open front; the hinged
    perforated door (``panel``) closes it. The story bay in front of the devices stays clear (``cff.stage.hardware``)."""
    hardware.rack(bm, hw.HERO_RACKS[o.id], "open")


def panel(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The rack's front door. Origin on the hinge edge (left, bottom); the leaf extends along +X and +Z. A steel frame (the
    glow channel), a perforated steel insert, a handle with a lock and the door's status light."""
    sx, sy, sz = o.size
    y0, y1 = -sy / 2, sy / 2
    border = 0.05
    hardware.span(bm, s.SIGNAL, 0.0, sx, y0, y1, 0.0, border)
    hardware.span(bm, s.SIGNAL, 0.0, sx, y0, y1, sz - border, sz)
    hardware.span(bm, s.SIGNAL, 0.0, border, y0, y1, border, sz - border)
    hardware.span(bm, s.SIGNAL, sx - border, sx, y0, y1, border, sz - border)
    hardware.span(bm, s.PERFORATED, border, sx - border, -0.006, 0.006, border, sz - border)
    hardware.span(bm, s.STEEL, border, sx - border, -0.01, 0.01, sz * 0.5 - 0.02, sz * 0.5 + 0.02)  # mid stiffener
    hardware.span(bm, s.STEEL_LIGHT, sx - 0.11, sx - 0.085, y0 - 0.02, y0, sz * 0.42, sz * 0.6)  # handle
    hardware.span(bm, s.BEZEL, sx - 0.113, sx - 0.082, y0 - 0.024, y0 - 0.02, sz * 0.5, sz * 0.52)  # lock
    for z in (0.2, sz * 0.5, sz - 0.3):
        hardware.span(bm, s.STEEL_LIGHT, -0.012, 0.012, y0 - 0.01, y1, z, z + 0.08)  # hinges
    with p.slot(bm, s.SIGNAL):
        p.cylinder(bm, 0.018, 0.012, 10, (sx - 0.14, y0 - 0.006, sz - 0.14), "Y")  # status light


def port(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A network port block: a dark housing, a glowing jack frame (the glow channel) and the jack opening."""
    sx, sy, sz = o.size
    hardware.span(bm, s.BEZEL, -sx / 2, sx / 2, -sy / 2, sy / 2, -sz / 2, sz / 2)
    hardware.span(bm, s.SIGNAL, -sx * 0.36, sx * 0.36, -sy / 2 - 0.006, -sy / 2, -sz * 0.3, sz * 0.3)
    hardware.span(bm, s.VENT, -sx * 0.24, sx * 0.24, -sy / 2 - 0.008, -sy / 2 - 0.006, -sz * 0.2, sz * 0.12)
    hardware.span(bm, s.VENT, -sx * 0.1, sx * 0.1, -sy / 2 - 0.008, -sy / 2 - 0.006, sz * 0.12, sz * 0.2)  # latch notch


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
