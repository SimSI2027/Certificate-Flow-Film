"""Authorities and the directory: issuing CA vaults and their machinery, the root vault on its plinth, AD, the kiosk."""

from __future__ import annotations

import bmesh

from blender.actors import hardware
from blender.actors import primitives as p
from blender.actors import slots as s
from cff.stage import hardware as hw
from cff.stage.objects import Kind, StageObject


def ca_vault(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """V5a: a secured CA enclosure with an open front (-Y). Its walls are steel panels painted in the CA's identity colour (the
    glow channel), panelled inside; the floor is raised-floor tile; four CA server racks stand along the back wall, the CA's own
    server the accent 2U in the middle two. The key module (HSM), cradle and press stand in front of the racks."""
    sx, sy, sz = o.size
    wall = 0.14
    with p.slot(bm, s.SIGNAL):
        p.box(bm, sx, wall, sz, (0.0, sy / 2 - wall / 2, sz / 2))
        for side in (-1, 1):
            p.box(bm, wall, sy, sz, (side * (sx / 2 - wall / 2), 0.0, sz / 2))
        p.box(bm, sx, sy, wall, (0.0, 0.0, sz - wall / 2))
    hardware.span(bm, s.STEEL, -sx / 2, sx / 2, -sy / 2, sy / 2, 0.0, 0.1)
    hardware.span(bm, s.TILE, -sx / 2 + wall, sx / 2 - wall, -sy / 2, sy / 2 - wall, 0.1, 0.12)
    for side in (-1, 1):  # front pilasters and the roof fascia
        hardware.span(bm, s.STEEL_LIGHT, side * (sx / 2 - 0.2), side * sx / 2, -sy / 2, -sy / 2 + 0.2, 0.0, sz)
    hardware.span(bm, s.STEEL_LIGHT, -sx / 2, sx / 2, -sy / 2, -sy / 2 + 0.2, sz - 0.22, sz)
    inner_x, inner_y = sx / 2 - wall, sy / 2 - wall
    for i in range(1, 5):  # interior panel seams on the side walls and the roof
        y = -sy / 2 + 0.2 + (inner_y + sy / 2 - 0.2) * i / 5
        for side in (-1, 1):
            hardware.span(bm, s.VENT, side * inner_x, side * (inner_x - 0.004), y - 0.006, y + 0.006, 0.12, sz - wall)
        hardware.span(bm, s.VENT, -inner_x, inner_x, y - 0.006, y + 0.006, sz - wall - 0.004, sz - wall)
    for x, spec in hw.vault_racks(o.role):  # cabinet fronts at VAULT_RACK_FACE_Y, backs against the back wall
        hardware.rack(bm, spec, "door", ox=x, oy=hw.VAULT_RACK_FACE_Y + spec.depth / 2, oz=0.12)


def trim(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A glowing frame round the vault opening (centred; the object sits at the opening)."""
    sx, _, sz = o.size
    bar = 0.1
    p.box(bm, sx, 0.06, bar, (0.0, 0.0, sz / 2 - bar / 2))
    p.box(bm, sx, 0.06, bar, (0.0, 0.0, -sz / 2 + bar / 2))
    for side in (-1, 1):
        p.box(bm, bar, 0.06, sz, (side * (sx / 2 - bar / 2), 0.0, 0.0))


def eval_cradle(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The request-evaluation cradle: a steel turntable base and a curved rail that carries the glow channel."""
    sx, sy, sz = o.size
    with p.slot(bm, s.STEEL):
        p.cylinder(bm, sx / 2, 0.06, 32, (0.0, 0.0, -sz / 2 + 0.03))
    with p.slot(bm, s.STEEL_LIGHT):
        p.cylinder(bm, sx / 2 - 0.03, 0.02, 32, (0.0, 0.0, -sz / 2 + 0.07))
    with p.slot(bm, s.SIGNAL):
        p.arc_of_boxes(bm, sx * 0.62, 150.0, 9, (0.08, 0.06, 0.07), (0.0, sy * 0.1, -sz / 2 + 0.12))


def key_module(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """V5a: an HSM-style key module (``hardware.hsm``); its display and tamper bands carry the glow channel."""
    hardware.hsm(bm, o.size)


def press(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A signing press: a steel bed, two machined posts and a crossbar; the head (separate object) moves between them."""
    sx, sy, sz = o.size
    with p.slot(bm, s.SIGNAL):
        p.box(bm, sx, sy, 0.2, (0.0, 0.0, -sz / 2 + 0.1))
    hardware.span(bm, s.STEEL, -sx / 2 + 0.02, sx / 2 - 0.02, -sy / 2 + 0.02, sy / 2 - 0.02, -sz / 2 + 0.2, -sz / 2 + 0.22)
    with p.slot(bm, s.STEEL_LIGHT):
        for side in (-1, 1):
            p.cylinder(bm, 0.045, sz + 0.5, 16, (side * (sx / 2 - 0.05), sy / 2 - 0.1, 0.1))
            p.box(bm, 0.12, 0.12, 0.06, (side * (sx / 2 - 0.05), sy / 2 - 0.1, -sz / 2 + 0.23))
        p.box(bm, 0.5, 0.5, 0.06, (0.0, -0.05, -sz / 2 + 0.25))  # anvil
    with p.slot(bm, s.STEEL):
        p.box(bm, sx, 0.16, 0.1, (0.0, sy / 2 - 0.1, 0.6))


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
    """V5a: the Root CA is an offline, air-gapped machine in a locked gold cage (``hardware.root_cage``). Nothing is attached
    to it and no cable reaches it: only trust links (light) leave it."""
    hardware.root_cage(bm, o.size)


def plinth(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A cast-concrete plinth (CC0 concrete) with a gold band below its top; the base flange fills the declared footprint."""
    sx, sy, sz = o.size
    with p.slot(bm, s.CONCRETE):
        p.cone(bm, sx * 0.62, sx * 0.48, sz - 0.24, 4, (0.0, 0.0, 0.18 + (sz - 0.24) / 2))
        p.box(bm, sx * hw.PLINTH_FOOT_SCALE, sy * hw.PLINTH_FOOT_SCALE, 0.18, (0.0, 0.0, 0.09))
        p.cone(bm, sx * 0.5, sx * 0.5, 0.06, 4, (0.0, 0.0, sz - 0.03))  # cap slab under the cage
    with p.slot(bm, s.SIGNAL):
        p.cone(bm, sx * 0.5, sx * 0.5, 0.06, 4, (0.0, 0.0, sz - 0.12))  # gold band


def dais(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A concrete platform with a raised-floor deck and a gold edge ring (the glow channel)."""
    radius, _, height = o.size
    with p.slot(bm, s.CONCRETE):
        p.cylinder(bm, radius, height, 64, (0.0, 0.0, height / 2))
    with p.slot(bm, s.SIGNAL):
        p.cylinder(bm, radius * 0.86, hw.DAIS_RIM_M * 0.5, 64, (0.0, 0.0, height + hw.DAIS_RIM_M * 0.25))
    with p.slot(bm, s.TILE):
        p.cylinder(bm, radius * 0.84, hw.DAIS_RIM_M, 64, (0.0, 0.0, height + hw.DAIS_RIM_M / 2))


def seal(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The root's self-signed seal: a ring that closes on itself, facing -Y. Static: never animated closed."""
    p.torus(bm, o.size[0] * 0.5, o.size[2] * 0.7, (0.0, 0.0, 0.0), "Y", 32, 8)
    p.cylinder(bm, o.size[0] * 0.18, o.size[2] * 1.2, 16, (0.0, 0.0, 0.0), "Y")


def reader(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The offline media reader on its pedestal: steel column, a dark reader head with a glowing slot (the glow channel)."""
    sx, _, sz = o.size
    with p.slot(bm, s.STEEL):
        p.cylinder(bm, sx / 2, sz - 0.12, 24, (0.0, 0.0, -0.06))
    with p.slot(bm, s.BEZEL):
        p.box(bm, sx * 0.9, sx * 0.7, 0.12, (0.0, 0.0, sz / 2 - 0.06))
    with p.slot(bm, s.SIGNAL):
        p.box(bm, sx * 0.9, 0.06, 0.05, (0.0, 0.0, sz / 2 + 0.01))


def ad_column(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """V5a: the AD/DC node is a 42U rack cabinet with a closed perforated door; its frame and the domain controller's bezel
    stripe carry the steel-blue directory identity (the glow channel)."""
    hardware.rack(bm, hw.HERO_RACKS[o.id], "door")


def ring(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """An Enrollment Services ring round the AD column."""
    p.torus(bm, o.size[0] / 2, o.size[2], (0.0, 0.0, 0.0), "Z", 30, 8)


def kiosk(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """V5a: the PKI HTTP publication point is a half-height rack with its web server; the frame carries the glow channel."""
    hardware.rack(bm, hw.HERO_RACKS[o.id], "door")


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
