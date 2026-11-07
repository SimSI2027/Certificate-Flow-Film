"""Authorities and the directory: issuing CA vaults and their machinery, the root vault on its plinth, AD, the kiosk."""

from __future__ import annotations

import bmesh

from blender.actors import primitives as p
from cff.stage.objects import Kind, StageObject


def ca_vault(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """An open-front vault hall: floor, back wall, side walls and roof (the front faces -Y)."""
    sx, sy, sz = o.size
    wall = 0.14
    p.box(bm, sx, sy, 0.12, (0.0, 0.0, 0.06))
    p.box(bm, sx, wall, sz, (0.0, sy / 2 - wall / 2, sz / 2))
    for side in (-1, 1):
        p.box(bm, wall, sy, sz, (side * (sx / 2 - wall / 2), 0.0, sz / 2))
    p.box(bm, sx, sy, wall, (0.0, 0.0, sz - wall / 2))
    for side in (-1, 1):  # front pilasters
        p.box(bm, 0.2, 0.2, sz, (side * (sx / 2 - 0.1), -sy / 2 + 0.1, sz / 2))


def trim(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A glowing frame round the vault opening (centred; the object sits at the opening)."""
    sx, _, sz = o.size
    bar = 0.1
    p.box(bm, sx, 0.06, bar, (0.0, 0.0, sz / 2 - bar / 2))
    p.box(bm, sx, 0.06, bar, (0.0, 0.0, -sz / 2 + bar / 2))
    for side in (-1, 1):
        p.box(bm, bar, 0.06, sz, (side * (sx / 2 - bar / 2), 0.0, 0.0))


def eval_cradle(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.cylinder(bm, sx / 2, 0.08, 20, (0.0, 0.0, -sz / 2 + 0.04))
    p.arc_of_boxes(bm, sx * 0.62, 150.0, 7, (0.1, 0.08, 0.08), (0.0, sy * 0.1, -sz / 2 + 0.12))


def key_module(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    p.box(bm, sx * 1.04, sy * 1.04, 0.06, (0.0, 0.0, sz * 0.22))  # sealed bands
    p.box(bm, sx * 1.04, sy * 1.04, 0.06, (0.0, 0.0, -sz * 0.22))
    p.box(bm, sx * 0.5, 0.02, sz * 0.18, (0.0, -sy / 2 - 0.005, 0.0))  # status window


def press(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A signing press: bed, two posts and a crossbar; the head (separate object) moves between them."""
    sx, sy, sz = o.size
    p.box(bm, sx, sy, 0.2, (0.0, 0.0, -sz / 2 + 0.1))
    for side in (-1, 1):
        p.box(bm, 0.1, 0.1, sz + 0.5, (side * (sx / 2 - 0.05), sy / 2 - 0.1, 0.1))
    p.box(bm, sx, 0.16, 0.1, (0.0, sy / 2 - 0.1, 0.6))
    p.box(bm, 0.5, 0.5, 0.06, (0.0, -0.05, -sz / 2 + 0.23))  # anvil


def press_head(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    p.cone(bm, sx * 0.3, sx * 0.1, sz * 1.2, 8, (0.0, 0.0, -sz * 0.7))


def link_rod(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    p.sphere(bm, sy * 0.9, (-sx / 2, 0.0, 0.0), 8, 5)
    p.sphere(bm, sy * 0.9, (sx / 2, 0.0, 0.0), 8, 5)


def crown(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    for x in (-0.38, 0.0, 0.38):
        p.cone(bm, 0.08, 0.02, 0.3, 6, (x, 0.0, sz / 2 + 0.15))


def root_vault(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A sealed, windowless vault with a heavy frame. No openings, nothing attached: only trust links reach it."""
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    edge = 0.14
    for z in (-1, 1):
        p.box(bm, sx + 0.1, sy + 0.1, edge, (0.0, 0.0, z * (sz / 2)))
    for x in (-1, 1):
        p.box(bm, edge, sy + 0.1, sz + 0.1, (x * (sx / 2), 0.0, 0.0))


def plinth(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.cone(bm, sx * 0.62, sx * 0.48, sz, 4, (0.0, 0.0, sz / 2))
    p.box(bm, sx * 1.35, sy * 1.35, 0.18, (0.0, 0.0, 0.09))


def dais(bm: bmesh.types.BMesh, o: StageObject) -> None:
    radius, _, height = o.size
    p.cylinder(bm, radius, height, 40, (0.0, 0.0, height / 2))
    p.cylinder(bm, radius * 0.84, 0.12, 40, (0.0, 0.0, height + 0.06))


def seal(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The root's self-signed seal: a ring that closes on itself, facing -Y. Static: never animated closed."""
    p.torus(bm, o.size[0] * 0.5, o.size[2] * 0.7, (0.0, 0.0, 0.0), "Y", 32, 8)
    p.cylinder(bm, o.size[0] * 0.18, o.size[2] * 1.2, 16, (0.0, 0.0, 0.0), "Y")


def reader(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, _, sz = o.size
    p.cylinder(bm, sx / 2, sz, 16)
    p.box(bm, sx * 0.9, 0.06, 0.05, (0.0, 0.0, sz / 2 + 0.01))


def ad_column(bm: bmesh.types.BMesh, o: StageObject) -> None:
    radius, _, height = o.size
    p.cylinder(bm, radius, height, 6, (0.0, 0.0, height / 2))
    p.cylinder(bm, radius * 1.35, 0.14, 6, (0.0, 0.0, 0.07))
    p.cone(bm, radius, radius * 0.45, 0.35, 6, (0.0, 0.0, height + 0.175))


def ring(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """An Enrollment Services ring round the AD column."""
    p.torus(bm, o.size[0] / 2, o.size[2], (0.0, 0.0, 0.0), "Z", 30, 8)


def kiosk(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx * 0.5, sy * 0.5, sz * 0.7, (0.0, 0.0, sz * 0.35))
    p.prism(bm, [(-sx / 2, 0.0), (sx / 2, 0.0), (sx / 2, 0.45), (-sx / 2, 0.25)], sy, (0.0, 0.0, sz * 0.7))
    p.box(bm, sx * 1.2, sy * 1.2, 0.08, (0.0, 0.0, 0.04))


BUILDERS = {
    Kind.CA_VAULT: ca_vault,
    Kind.TRIM: trim,
    Kind.EVAL_CRADLE: eval_cradle,
    Kind.MODULE: key_module,
    Kind.PRESS: press,
    Kind.PRESS_HEAD: press_head,
    Kind.LINK_ROD: link_rod,
    Kind.CROWN: crown,
    Kind.ROOT_VAULT: root_vault,
    Kind.PLINTH: plinth,
    Kind.DAIS: dais,
    Kind.SEAL: seal,
    Kind.READER: reader,
    Kind.AD_COLUMN: ad_column,
    Kind.RING: ring,
    Kind.KIOSK: kiosk,
}
