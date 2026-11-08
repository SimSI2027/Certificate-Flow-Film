"""Light-channel geometry: floor conduits, CA routes, trust links, light beams and the request seal ring."""

from __future__ import annotations

import itertools
import math

import bmesh

from blender.actors import primitives as p
from cff.stage import layout as lo
from cff.stage.objects import Kind, StageObject
from cff.theme import palette


def channel(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A floor conduit segment; origin at its start, running along +X."""
    sx, sy, sz = o.size
    p.box_span(bm, 0.0, sx, -sy / 2, sy / 2, 0.0, sz)
    p.box_span(bm, 0.0, sx, -sy / 2 - 0.03, -sy / 2, 0.0, sz * 0.6)  # raised edges
    p.box_span(bm, 0.0, sx, sy / 2, sy / 2 + 0.03, 0.0, sz * 0.6)


def route(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box_span(bm, 0.0, sx, -sy / 2, sy / 2, 0.0, sz)


def trust_link(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A bowed path of light: unit length along +X from its start (stretched to the link length when fully grown).

    The bow is in absolute metres on local Z (the link scales only along X), so the grown link arcs upward by
    ``TRUST_LINK_ARC_FRACTION`` of its length: a path of light, never a taut straight connector (C-01, CIN-S1R1-02).
    """
    _, sy, sz = o.size
    rise = palette.TRUST_LINK_ARC_FRACTION * (lo.dist(o.points[0], o.points[1]) if len(o.points) == 2 else 1.0)
    n = palette.TRUST_LINK_SEGMENTS
    rings = []
    for i in range(n + 1):
        x = i / n
        z = rise * 4.0 * x * (1.0 - x)
        taper = 0.55 + 0.45 * math.sin(math.pi * x) if 0.0 < x < 1.0 else 0.55
        hy, hz = sy / 2 * taper, sz / 2 * taper
        rings.append([bm.verts.new((x, y, z + dz)) for y, dz in ((-hy, -hz), (hy, -hz), (hy, hz), (-hy, hz))])
    for a, b in itertools.pairwise(rings):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def beam(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A beam of light, unit length along +Z from its start."""
    sx, sy, _ = o.size
    p.box_span(bm, -sx / 2, sx / 2, -sy / 2, sy / 2, 0.0, 1.0)


def seal_ring(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The proof-of-possession seal ring that closes round the capsule (normal along +X)."""
    p.torus(bm, o.size[0] / 2, 0.02, (0.0, 0.0, 0.0), "X", 28, 6)


BUILDERS = {Kind.CHANNEL: channel, Kind.ROUTE: route, Kind.TRUST_LINK: trust_link, Kind.BEAM: beam, Kind.SEAL_RING: seal_ring}
