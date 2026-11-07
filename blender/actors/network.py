"""Light-channel geometry: floor conduits, CA routes, trust links, light beams and the request seal ring."""

from __future__ import annotations

import bmesh

from blender.actors import primitives as p
from cff.stage.objects import Kind, StageObject


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
    """A bar of light, unit length along +X from its start (stretched to the link length when fully grown)."""
    _, sy, sz = o.size
    p.box_span(bm, 0.0, 1.0, -sy / 2, sy / 2, -sz / 2, sz / 2)


def beam(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A beam of light, unit length along +Z from its start."""
    sx, sy, _ = o.size
    p.box_span(bm, -sx / 2, sx / 2, -sy / 2, sy / 2, 0.0, 1.0)


def seal_ring(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The proof-of-possession seal ring that closes round the capsule (normal along +X)."""
    p.torus(bm, o.size[0] / 2, 0.02, (0.0, 0.0, 0.0), "X", 28, 6)


BUILDERS = {Kind.CHANNEL: channel, Kind.ROUTE: route, Kind.TRUST_LINK: trust_link, Kind.BEAM: beam, Kind.SEAL_RING: seal_ring}
