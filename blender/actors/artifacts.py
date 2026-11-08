"""The film's small, travelling shapes (C-11): capsule, card, keys, badge, tick, CRL scroll, AIA indicator, proof."""

from __future__ import annotations

import math

import bmesh

from blender.actors import primitives as p
from cff.stage import layout as lo
from cff.stage.objects import Kind, StageObject


def capsule(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A request capsule: a pill lying along +X."""
    length, radius, _ = o.size
    p.cylinder(bm, radius, length - 2 * radius, 14, (0.0, 0.0, 0.0), "X")
    p.sphere(bm, radius, (length / 2 - radius, 0.0, 0.0), 12, 7)
    p.sphere(bm, radius, (-(length / 2 - radius), 0.0, 0.0), 12, 7)


def card(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A certificate card facing -Y: body, header strip, issuer seal (not on a self-signed card) and a key emblem."""
    w, t, h = o.size
    p.box(bm, w, t, h)
    p.box(bm, w * 0.9, 0.012, h * 0.16, (0.0, -t / 2 - 0.004, h * 0.34))  # header strip
    if o.variant == "self_signed":
        p.torus(bm, h * 0.18, 0.012, (0.0, -t / 2 - 0.01, 0.02), "Y", 24, 6)  # a faint seal looping back on itself
        return
    p.cylinder(bm, h * 0.15, 0.014, 18, (-w * 0.26, -t / 2 - 0.008, -0.02), "Y")  # issuer seal
    p.torus(bm, 0.035, 0.01, (w * 0.28, -t / 2 - 0.01, -h * 0.28), "Y", 14, 5)  # public-key emblem
    p.box(bm, 0.07, 0.012, 0.016, (w * 0.34, -t / 2 - 0.01, -h * 0.28))
    if o.variant == "end_entity":
        for x in (-0.06, 0.06):  # AIA and CDP ports
            p.box(bm, 0.05, 0.016, 0.03, (x, -t / 2 - 0.008, -h * 0.38))
    if o.variant == "root_cert":
        p.cone(bm, 0.07, 0.02, 0.12, 6, (w * 0.0, -t / 2 - 0.02, -h * 0.12), "Y")


def private_key(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A solid round head with a keyhole, a toothed shaft and a padlock shackle (the lock motif)."""
    s = o.size[0]
    p.cylinder(bm, s * 0.34, s * 0.14, 18, (-s * 0.3, 0.0, 0.0), "Y")
    p.box(bm, s * 0.62, s * 0.08, s * 0.1, (s * 0.2, 0.0, 0.0))
    for x in (0.28, 0.4):
        p.box(bm, s * 0.07, s * 0.08, s * 0.2, (s * x, 0.0, -s * 0.12))
    p.torus(bm, s * 0.14, s * 0.035, (-s * 0.3, 0.0, s * 0.28), "Y", 16, 5)
    p.box(bm, s * 0.3, s * 0.1, s * 0.12, (-s * 0.3, 0.0, s * 0.16))


def public_key(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """An open, notched token: a flat hexagonal plate with three notches on its rim. No bow, no shaft, no teeth.

    Stage 1 round 1 (LEG-S1R1-02) showed that a key-shaped public key is read as the private key, so this shape shares
    nothing with a key's silhouette (C-11: private vs public IoU <= 0.6).
    """
    s = o.size[0]
    p.cylinder(bm, s * 0.42, s * 0.08, 6, (0.0, 0.0, 0.0), "Y")
    for angle in (90.0, 210.0, 330.0):  # notches stand proud of three alternate faces
        a = math.radians(angle)
        p.box(bm, s * 0.12, s * 0.08, s * 0.12, (math.cos(a) * s * 0.42, 0.0, math.sin(a) * s * 0.42))


def badge(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    p.cylinder(bm, sy * 0.5, sz * 1.1, 12, (-sx / 2, 0.0, 0.0), "Z")
    p.cylinder(bm, sy * 0.5, sz * 1.1, 12, (sx / 2, 0.0, 0.0), "Z")
    p.torus(bm, 0.06, 0.012, (0.0, 0.0, sz / 2 + 0.01), "Z", 12, 5)


def tile(bm: bmesh.types.BMesh, o: StageObject) -> None:
    p.box(bm, *o.size)


def proof(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A flat signature impression: a thin plate with a scribbled stroke. Unlike any key shape (C-11)."""
    sx, sy, sz = o.size
    p.box(bm, sx, sy * 0.4, sz)
    for i in range(7):
        x = -sx * 0.4 + i * sx * 0.133
        p.box(bm, sx * 0.1, sy * 0.4, sz * 0.12, (x, -sy * 0.4, math.sin(i * 1.3) * sz * 0.28))


def scroll(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A CRL scroll: a rolled cylinder with end flanges."""
    length, radius, _ = o.size
    p.cylinder(bm, radius * 0.5, length, 14, (0.0, 0.0, 0.0), "X")
    for side in (-1, 1):
        p.cylinder(bm, radius * 0.78, length * 0.08, 14, (side * length / 2, 0.0, 0.0), "X")


def aia(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, _sz = o.size
    p.cylinder(bm, sx / 2, sy, 6, (0.0, 0.0, 0.0), "Y")
    p.cylinder(bm, sx * 0.18, sy * 1.6, 8, (0.0, -sy * 0.15, 0.0), "Y")


def tick(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A check slot: a ring that holds a check mark (resolved) or a waiting dot (pending)."""
    sx, _, _ = o.size
    p.torus(bm, sx * 0.46, sx * 0.07, (0.0, 0.0, 0.0), "Y", 24, 6)
    if o.variant == "pending":
        p.sphere(bm, sx * 0.13, (0.0, 0.0, 0.0), 8, 5)
        return
    p.box(bm, sx * 0.22, 0.03, sx * 0.1, (-sx * 0.12, 0.0, -sx * 0.05))
    p.box(bm, sx * 0.48, 0.03, sx * 0.1, (sx * 0.1, 0.0, sx * 0.07))
    bm.verts.ensure_lookup_table()


def pulse(bm: bmesh.types.BMesh, o: StageObject) -> None:
    p.icosphere(bm, o.size[0] / 2, (0.0, 0.0, 0.0), 2)


def query(bm: bmesh.types.BMesh, o: StageObject) -> None:
    p.sphere(bm, o.size[0] / 2, (0.0, 0.0, 0.0), 4, 2)  # an octahedron: a diamond, not a sphere


def band(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The CA=true band: a ring round the capsule."""
    p.torus(bm, lo.CAPSULE_RADIUS + 0.012, 0.016, (0.0, 0.0, 0.0), "X", 20, 6)


def cartridge(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    p.box(bm, sx * 0.3, sy * 1.02, sz * 0.4, (sx * 0.34, 0.0, sz * 0.1))
    p.box(bm, sx * 0.18, sy * 0.5, sz * 0.5, (-sx * 0.58, 0.0, 0.0))  # contact tab


def footprint(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy * 0.58, sz, (0.0, sy * 0.2, 0.0))
    p.box(bm, sx * 0.7, sy * 0.3, sz, (0.0, -sy * 0.32, 0.0))


BUILDERS = {
    Kind.CAPSULE: capsule,
    Kind.CARD: card,
    Kind.KEY_PRIVATE: private_key,
    Kind.KEY_PUBLIC: public_key,
    Kind.BADGE: badge,
    Kind.TILE: tile,
    Kind.PROOF: proof,
    Kind.SCROLL: scroll,
    Kind.AIA: aia,
    Kind.TICK: tick,
    Kind.PULSE: pulse,
    Kind.QUERY: query,
    Kind.BAND: band,
    Kind.CARTRIDGE: cartridge,
    Kind.FOOTPRINT: footprint,
}
