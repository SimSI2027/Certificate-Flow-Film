"""Light-channel geometry: floor conduits, CA routes, trust links, light beams and the request seal ring."""

from __future__ import annotations

import itertools
import math

import bmesh

from blender.actors import artifacts
from blender.actors import primitives as p
from cff.stage import icons
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
    """A bowed chain of light: unit length along +X from its start (stretched to the link length when fully grown).

    The bow is in absolute metres on local Z (the link scales only along X), so the grown link arcs upward by
    ``TRUST_LINK_ARC_FRACTION`` of its length: a path of light, never a taut straight connector (C-01, CIN-S1R1-02).

    V5b: the path is drawn as interlocking chain links (the trust-chain symbol, ``cff.stage.icons``), alternately flat and
    upright, each turned along the bow. Links are laid out in metres and their X is divided by the full length, so they are
    true ovals once the link is grown; a thin core of light threads them so the path still reads at a distance.
    """
    _, sy, sz = o.size
    length = lo.dist(o.points[0], o.points[1]) if len(o.points) == 2 else 1.0
    rise = palette.TRUST_LINK_ARC_FRACTION * length

    def bow(x: float) -> tuple[float, float]:  # height and slope (metres per metre) of the bow at unit position x
        return rise * 4.0 * x * (1.0 - x), rise * 4.0 * (1.0 - 2.0 * x) / length

    n = palette.TRUST_LINK_SEGMENTS
    rings = []
    for i in range(n + 1):
        x = i / n
        z = bow(x)[0]
        hy, hz = sy / 2 * icons.CHAIN_CORE_FRACTION, sz / 2 * icons.CHAIN_CORE_FRACTION
        rings.append([bm.verts.new((x, y, z + dz)) for y, dz in ((-hy, -hz), (hy, -hz), (hy, hz), (-hy, hz))])
    for a, b in itertools.pairwise(rings):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])

    link_len, link_w, tube_r = sy * icons.CHAIN_LINK_LENGTH, sy * icons.CHAIN_LINK_WIDTH, sy * icons.CHAIN_LINK_TUBE
    pitch = link_len - 2.0 * tube_r - link_len * icons.CHAIN_LINK_OVERLAP
    count = max(1, int((length - link_len) / pitch) + 1)
    first = (length - (count - 1) * pitch) / 2
    steps = 20
    for k in range(count):
        centre_m = first + k * pitch
        cx = centre_m / length
        cz, slope = bow(cx)
        angle = math.atan(slope)
        ca, sa = math.cos(angle), math.sin(angle)
        upright = k % 2 == 1  # alternate links stand in the XZ plane, the others lie in the XY plane
        pts = []
        for j in range(steps):
            b = 2 * math.pi * j / steps
            half_straight = (link_len - link_w) / 2
            ex = (half_straight + link_w / 2 * abs(math.cos(b))) * (1.0 if math.cos(b) >= 0 else -1.0)  # a stadium: two arcs and two sides
            ew = link_w / 2 * math.sin(b)
            lx, ly, lz = (ex, 0.0, ew) if upright else (ex, ew, 0.0)
            rx, rz = lx * ca - lz * sa, lx * sa + lz * ca  # turn along the bow
            pts.append((centre_m + rx, ly, cz + rz))
        bm.verts.ensure_lookup_table()
        start = len(bm.verts)
        p.tube(bm, pts, tube_r, 6, closed=True)  # swept in metres, then X is divided by the full length
        bm.verts.ensure_lookup_table()
        for i in range(start, len(bm.verts)):
            bm.verts[i].co.x /= length


def beam(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A tapering beam of light, unit length along +Z from its start: wide at the container, narrow at the seal (CIN-S1R1-16)."""
    sx, _, _ = o.size
    p.cone(bm, sx / 2, sx / 7, 1.0, 16, (0.0, 0.0, 0.5), "Z")


def seal_ring(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The proof-of-possession seal ring that closes round the capsule (normal along +X). V5b: it carries the signature tag
    on top, the same signature symbol as the handshake proof (``cff.stage.icons``), so a sealed request reads as signed."""
    p.torus(bm, o.size[0] / 2, 0.045, (0.0, 0.0, 0.0), "X", 28, 6)  # a 4.5 cm tube so the sealing reads (V1-CIN-07)
    r = o.size[0] / 2
    artifacts.signature_tag(bm, 0.0, r + icons.SEAL_TAG_LIFT_M, icons.SEAL_TAG_SIZE_M, stem_from=r)


BUILDERS = {Kind.CHANNEL: channel, Kind.ROUTE: route, Kind.TRUST_LINK: trust_link, Kind.BEAM: beam, Kind.SEAL_RING: seal_ring}
