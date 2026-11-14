"""The film's small, travelling shapes (C-11): capsule, card, keys, badge, tick, CRL scroll, AIA indicator, proof.

V5b iconography (``cff.stage.icons``): every PKI concept has one symbol, drawn the same way wherever it appears. The symbols
are original, built here from primitives; ink strokes go to ``slots.ICON_INK`` and a card's issuer seal to ``slots.ICON_SEAL``.
Every mark stays inside the object's declared ``size`` box, so caption clearance and focal bounds still measure the symbol.
"""

from __future__ import annotations

import math

import bmesh

from blender.actors import primitives as p
from blender.actors import slots as s
from cff.stage import icons
from cff.stage import layout as lo
from cff.stage.objects import Kind, StageObject

INK_DEPTH_M = 0.008  # how far an ink stroke stands proud of the face it is printed on


def _front(t: float, lift: float = 0.0) -> float:
    """The Y of a mark printed on a face at -t/2 (faces look down -Y), raised ``lift`` further toward the camera."""
    return -t / 2 - INK_DEPTH_M / 2 - lift


def _bar(bm: bmesh.types.BMesh, x0: float, x1: float, z: float, height: float, y: float) -> None:
    p.box(bm, x1 - x0, INK_DEPTH_M, height, ((x0 + x1) / 2, y, z))


def signature(bm: bmesh.types.BMesh, cx: float, cz: float, width: float, height: float, y: float, stroke: float) -> None:
    """The signature symbol: one looping autograph stroke in the XZ plane at depth ``y`` (the same stroke on every
    private-key signature: a request's seal, the CA request and the handshake proof)."""
    loops, steps = 4, 64
    pts = []
    for i in range(steps + 1):
        u = i / steps
        envelope = math.sin(math.pi * min(1.0, u * 1.25)) if u < 0.8 else 1.0 - (u - 0.8) * 2.5
        x = cx + width * (u - 0.5) + 0.075 * width * math.cos(2 * math.pi * loops * u)
        z = cz + height / 2 * envelope * math.sin(2 * math.pi * loops * u) * (0.75 + 0.25 * math.sin(3.1 * u))
        pts.append((x, y, z))
    p.tube(bm, pts, stroke, 5)


def _rosette(bm: bmesh.types.BMesh, r: float, cx: float, cz: float, y: float) -> None:
    outline = [((r * (1.16 if k % 2 else 1.0)) * math.cos(math.pi * k / 12) + cx, (r * (1.16 if k % 2 else 1.0)) * math.sin(math.pi * k / 12) + cz)
               for k in range(24)]
    p.prism(bm, outline, INK_DEPTH_M, (0.0, y, 0.0))


def ribbon_seal(bm: bmesh.types.BMesh, r: float, cx: float, cz: float, t: float, bottom: float) -> None:
    """The issuer's seal: a rosette disc in the issuer's colour with an ink rim, and two ribbon tails hanging to ``bottom``."""
    with p.slot(bm, s.ICON_SEAL):
        _rosette(bm, r, cx, cz, _front(t))
        p.cylinder(bm, r * 0.78, INK_DEPTH_M, 20, (cx, _front(t, INK_DEPTH_M), cz), "Y")
        for side in (-1.0, 1.0):  # tails: a strip from under the disc to the box edge, with a V-notched end
            top_x, top_z = cx + side * r * 0.35, cz - r * 0.4
            end_x, end_z = cx + side * r * 0.95, bottom
            half = r * 0.24
            nx, nz = (end_z - top_z), -(end_x - top_x)
            norm = math.hypot(nx, nz)
            nx, nz = nx / norm * half, nz / norm * half
            notch = (end_x - (end_x - top_x) * 0.18, end_z - (end_z - top_z) * 0.18)
            outline = [(top_x - nx, top_z - nz), (top_x + nx, top_z + nz), (end_x + nx, end_z + nz), notch, (end_x - nx, end_z - nz)]
            if side < 0:
                outline.reverse()
            p.prism(bm, outline, INK_DEPTH_M, (0.0, _front(t), 0.0))
    with p.slot(bm, s.ICON_INK):
        p.torus(bm, r * 0.9, r * 0.09, (cx, _front(t, INK_DEPTH_M * 1.5), cz), "Y", 28, 5)


def self_seal(bm: bmesh.types.BMesh, r: float, cx: float, cz: float, t: float) -> None:
    """The self-signed seal: an ink ring that runs past its own start and tucks inside it (a seal that closes on itself)."""
    with p.slot(bm, s.ICON_SEAL):
        p.cylinder(bm, r * 0.72, INK_DEPTH_M, 20, (cx, _front(t), cz), "Y")
    steps = 44
    start, turn = math.radians(110.0), 2 * math.pi + math.radians(70.0)
    pts = []
    for i in range(steps + 1):
        u = i / steps
        a = start - turn * u  # clockwise as seen by the camera
        radius = r * (1.0 - 0.2 * max(0.0, (u - 0.78) / 0.22))  # the last part spirals inward, inside the ring's start
        pts.append((cx + radius * math.cos(a), _front(t, INK_DEPTH_M * 1.5), cz + radius * math.sin(a)))
    with p.slot(bm, s.ICON_INK):
        p.tube(bm, pts, r * icons.SELF_SEAL_TUBE_FRACTION, 6)


def ca_badge(bm: bmesh.types.BMesh, bw: float, bh: float, cx: float, top: float, t: float) -> None:
    """The CA symbol: a shield (ink rim, body-colour field, ink stud) whose top sits at ``top``."""
    def shield(scale: float) -> list[tuple[float, float]]:
        hw, hh = bw / 2 * scale, bh / 2 * scale
        cz = top - bh / 2
        return [(cx - hw, cz + hh), (cx + hw, cz + hh), (cx + hw, cz - hh * 0.1), (cx + hw * 0.45, cz - hh * 0.72), (cx, cz - hh),
                (cx - hw * 0.45, cz - hh * 0.72), (cx - hw, cz - hh * 0.1)]
    with p.slot(bm, s.ICON_INK):
        p.prism(bm, shield(1.0), INK_DEPTH_M, (0.0, _front(t), 0.0))
    p.prism(bm, shield(0.68), INK_DEPTH_M, (0.0, _front(t, INK_DEPTH_M), 0.0))
    with p.slot(bm, s.ICON_INK):
        p.cylinder(bm, bw * 0.1, INK_DEPTH_M, 10, (cx, _front(t, INK_DEPTH_M * 2), top - bh * 0.42), "Y")


def open_key(bm: bmesh.types.BMesh, k: float, cx: float, cz: float, y: float, depth: float) -> None:
    """The public-key symbol: an open key (a ring bow, a shaft, two teeth, no lock), ``k`` wide, in the XZ plane."""
    ring_r, tube = k * 0.15, k * 0.055
    bow_x = cx - k * 0.5 + ring_r + tube
    p.torus(bm, ring_r, tube, (bow_x, y, cz), "Y", 20, 6)
    shaft0 = bow_x + ring_r
    p.box(bm, cx + k * 0.48 - shaft0, depth, k * 0.085, ((shaft0 + cx + k * 0.48) / 2, y, cz))
    for x in (0.31, 0.43):
        p.box(bm, k * 0.07, depth, k * 0.14, (cx + k * x, y, cz - k * 0.1))


def capsule(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A request capsule: a pill lying along +X. A CA request is sealed as it appears, so it carries the signature tag."""
    length, radius, _ = o.size
    p.cylinder(bm, radius, length - 2 * radius, 14, (0.0, 0.0, 0.0), "X")
    p.sphere(bm, radius, (length / 2 - radius, 0.0, 0.0), 12, 7)
    p.sphere(bm, radius, (-(length / 2 - radius), 0.0, 0.0), 12, 7)
    if o.variant in icons.SIGNED_REQUEST_VARIANTS:
        signature_tag(bm, length * 0.26, radius * 1.45, radius)


def signature_tag(bm: bmesh.types.BMesh, cx: float, cz: float, size: float, stem_from: float = 0.0) -> None:
    """A small tag on a stem, standing on a sealed request: the request's signature (proof of possession)."""
    tw, th, tt = size * 1.7, size * 0.85, size * 0.12
    p.box(bm, size * 0.12, tt, cz - th / 2 - stem_from, (cx, 0.0, (cz - th / 2 + stem_from) / 2))  # stem
    p.box(bm, tw, tt, th, (cx, 0.0, cz))
    with p.slot(bm, s.ICON_INK):
        signature(bm, cx, cz, tw * 0.8, th * 0.6, _front(tt), size * 0.07)


def card(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """A certificate card facing -Y: a document (ink header and text lines) with the marks of ``icons.card_marks``.

    - issued cards: the ribbon seal in the issuer's colour, tails hanging to the box edge;
    - CA cards (issuing CAs, their copies, the root): the shield badge standing above the top-left corner;
    - self-signed cards (root, the RDP server's first card): the seal that closes on itself, no ribbon;
    - every card: the open-key emblem of the public key it binds; end-entity cards also the validity bar and the AIA and CDP
      ports (PKI-S1R1-08).
    """
    w, t, h = o.size
    hb = h * icons.CARD_BODY_HEIGHT_FRACTION
    top = h / 2 - h * icons.CARD_BADGE_ROOM_FRACTION
    bottom = top - hb
    marks = icons.card_marks(o.id)
    fold = hb * icons.CARD_FOLD_FRACTION  # the document's folded top-right corner
    p.prism(bm, [(-w / 2, bottom), (w / 2, bottom), (w / 2, top - fold), (w / 2 - fold, top), (-w / 2, top)], t)
    with p.slot(bm, s.ICON_INK):
        p.prism(bm, [(w / 2 - fold, top - fold), (w / 2, top - fold), (w / 2 - fold, top)], INK_DEPTH_M, (0.0, _front(t), 0.0))  # the fold
        header_x0 = -w * 0.2 if "ca_badge" in marks else -w * 0.42
        _bar(bm, header_x0, w / 2 - fold - w * 0.06, top - hb * 0.14, hb * 0.1, _front(t))
        line_x1 = 0.0 if "self_seal" in marks else w * 0.06
        rows = (-0.12, -0.27) if o.variant == "end_entity" else (-0.04, -0.18, -0.32)  # CA cards: rows start below the badge
        for z in rows:
            _bar(bm, -w * 0.42, line_x1, top - hb * 0.32 + hb * z, hb * 0.045, _front(t))
        open_key(bm, w * 0.2, -w * 0.31, bottom + hb * 0.16, _front(t), INK_DEPTH_M)
    if o.variant == "end_entity":
        p.box(bm, w * 0.48, INK_DEPTH_M * 2, hb * 0.07, (-w * 0.18, _front(t, INK_DEPTH_M), top - hb * 0.32))  # validity bar
        p.box(bm, w * 0.29, INK_DEPTH_M * 3, hb * 0.07, (-w * 0.275, _front(t, INK_DEPTH_M * 1.5), top - hb * 0.32))  # its elapsed part
        for x in (-0.09, 0.0):  # AIA and CDP ports
            p.box(bm, 0.07, 0.02, 0.05, (x, -t / 2 - 0.01, bottom + hb * 0.16))
    if "ca_badge" in marks:
        ca_badge(bm, w * 0.2, h * icons.CARD_BADGE_ROOM_FRACTION + hb * 0.3, -w * 0.33, h / 2, t)
    seal_r = hb * 0.27
    seal_x, seal_z = w * 0.27, bottom + hb * 0.42
    if "ribbon_seal" in marks:
        ribbon_seal(bm, seal_r, seal_x, seal_z, t, -h / 2)
    if "self_seal" in marks:  # V1-PKI-06 size: the seal overhangs the body's foot, where an issued card hangs its ribbon
        r = icons.SELF_SEAL_RADIUS_M
        self_seal(bm, r, w / 2 - r - 0.005, bottom + r * 0.75, t)


def private_key(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The private-key symbol: a key locked in a padlock (locked and anchored). The body and the key are the role colour;
    the keyhole is ink."""
    k = o.size[0]
    lx, lz, lw, lh, ld = -k * 0.2, -k * 0.06, k * 0.5, k * 0.42, k * 0.2
    p.box(bm, lw, ld, lh, (lx, 0.0, lz))  # padlock body
    shackle = [(lx + k * 0.15 * math.cos(math.pi * i / 16), 0.0, lz + lh / 2 + k * 0.15 * math.sin(math.pi * i / 16)) for i in range(17)]
    p.tube(bm, [(shackle[0][0], 0.0, lz + lh / 2 - k * 0.02), *shackle, (shackle[-1][0], 0.0, lz + lh / 2 - k * 0.02)], k * 0.05, 8)
    shaft0, shaft1, sz = lx + lw / 2, k * 0.48, lz - k * 0.02
    p.box(bm, shaft1 - shaft0, k * 0.09, k * 0.09, ((shaft0 + shaft1) / 2, 0.0, sz))  # the key, held in the lock
    for x in (0.3, 0.42):
        p.box(bm, k * 0.07, k * 0.09, k * 0.15, (k * x, 0.0, sz - k * 0.1))
    with p.slot(bm, s.ICON_INK):  # keyhole
        p.cylinder(bm, k * 0.055, INK_DEPTH_M, 12, (lx, -ld / 2 - INK_DEPTH_M / 2, lz + k * 0.05), "Y")
        p.box(bm, k * 0.045, INK_DEPTH_M, k * 0.12, (lx, -ld / 2 - INK_DEPTH_M / 2, lz - k * 0.03))


def public_key(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The public-key symbol: an open key (ring bow, shaft, teeth) and no lock. It is long and open where the private key is
    compact and locked, so the two silhouettes stay apart (C-11: IoU <= 0.6, measured by the ``silhouettes`` check)."""
    k = o.size[0]
    open_key(bm, k, 0.0, 0.0, 0.0, k * 0.1)


def badge(bm: bmesh.types.BMesh, o: StageObject) -> None:
    sx, sy, sz = o.size
    p.box(bm, sx, sy, sz)
    p.cylinder(bm, sy * 0.5, sz * 1.1, 12, (-sx / 2, 0.0, 0.0), "Z")
    p.cylinder(bm, sy * 0.5, sz * 1.1, 12, (sx / 2, 0.0, 0.0), "Z")
    p.torus(bm, 0.06, 0.012, (0.0, 0.0, sz / 2 + 0.01), "Z", 12, 5)


def tile(bm: bmesh.types.BMesh, o: StageObject) -> None:
    p.box(bm, *o.size)


def proof(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The handshake proof: a signature impression, a thin plate carrying the signature symbol (the same stroke as a request's
    seal: both are private-key signatures) above an ink baseline. Unlike any key shape (C-11)."""
    sx, sy, sz = o.size
    t = sy * 0.4
    notch = sz * icons.PROOF_NOTCH_FRACTION  # swallowtail ends: a signed ribbon, not a card
    p.prism(bm, [(-sx / 2, sz / 2), (sx / 2, sz / 2), (sx / 2 - notch, 0.0), (sx / 2, -sz / 2), (-sx / 2, -sz / 2), (-sx / 2 + notch, 0.0)], t)
    with p.slot(bm, s.ICON_INK):
        signature(bm, 0.0, sz * 0.06, sx * 0.56, sz * 0.55, _front(t), sz * 0.06)
        _bar(bm, -sx * 0.36, sx * 0.36, -sz * 0.34, sz * 0.05, _front(t))


def scroll(bm: bmesh.types.BMesh, o: StageObject) -> None:
    """The CRL symbol: a hanging list document (a top roll, the sheet, a curled foot) with ink entries, one struck through.

    ``size`` is (width, depth, height). It stands tall where the certificate card is wide, so the two documents never share a
    silhouette (C-11)."""
    w, d, h = o.size
    roll_r = d / 2
    p.cylinder(bm, roll_r, w, 16, (0.0, 0.0, h / 2 - roll_r), "X")  # top roll
    for side in (-1.0, 1.0):  # roll knobs
        p.sphere(bm, roll_r * 0.75, (side * w / 2, 0.0, h / 2 - roll_r), 10, 6)
    sheet_w, sheet_t = w * 0.86, d * 0.2
    sheet_top, sheet_bottom = h / 2 - roll_r, -h / 2 + roll_r * 0.6
    p.box(bm, sheet_w, sheet_t, sheet_top - sheet_bottom, (0.0, 0.0, (sheet_top + sheet_bottom) / 2))
    p.cylinder(bm, roll_r * 0.6, sheet_w, 14, (0.0, -roll_r * 0.2, sheet_bottom), "X")  # curled foot
    x0, x1 = -sheet_w * 0.38, sheet_w * 0.38
    with p.slot(bm, s.ICON_INK):
        _bar(bm, x0, x1, sheet_top - h * 0.12, h * 0.05, _front(sheet_t))  # header
        rows = 5
        pitch = (sheet_top - sheet_bottom - h * 0.3) / (rows - 1)
        for i in range(rows):
            z = sheet_top - h * 0.24 - i * pitch
            p.box(bm, sheet_w * 0.07, INK_DEPTH_M, sheet_w * 0.07, (x0 + sheet_w * 0.035, _front(sheet_t), z))  # entry bullet
            _bar(bm, x0 + sheet_w * 0.12, x1 - (sheet_w * 0.12 if i % 2 else 0.0), z, h * 0.022, _front(sheet_t))
            if i == 2:  # the revoked entry: a heavy stroke through it, past both ends
                strike = h * 0.03
                p.tube(bm, [(x0 - sheet_w * 0.05, _front(sheet_t, INK_DEPTH_M), z - h * 0.012),
                            (x1 + sheet_w * 0.05, _front(sheet_t, INK_DEPTH_M), z + h * 0.012)], strike, 6)


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
