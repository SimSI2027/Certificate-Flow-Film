"""V5b iconography: one recognisable symbol per PKI concept, the same symbol wherever the concept appears.

Pure data and maths (no ``bpy``). The Blender builders in ``blender/actors/artifacts.py`` and ``blender/actors/network.py``
draw these symbols; ``blender/checks/scene_checks.py`` measures their silhouettes against C-11 with the maths below.

All symbols are drawn originally in code from primitives (no imported icon set, so no third-party licence applies),
use only palette tokens, and carry no vendor mark.

Symbol vocabulary (concept -> symbol -> where it appears):
- certificate: a document (ink header and text lines) with a ribbon seal in the ISSUER's colour, ribbon tails below
  the card edge -> every issued card (end-entity cards, issuing CA cards and their copies).
- CA certificate: the certificate symbol plus a shield badge standing above the top-left corner -> issuing CA cards,
  their copies and the root card. End-entity cards never carry it.
- self-signed: a seal ring that closes on itself (it loops past its start), no ribbon -> the root card (gold) and the
  RDP server's pale self-signed card. Issued cards never carry it.
- private key: a key locked in a padlock (locked, anchored) -> every private key (server, CA and root keys).
- public key: an open key (ring bow, no lock) -> every public key, and as the small emblem on every card (a certificate
  binds a public key).
- signature: one autograph stroke -> the proof-of-possession seal on a request, the CA request's seal and the
  handshake proof (all three are private-key signatures).
- request (CSR): the capsule; once sealed it carries the signature tag.
- CRL: a hanging list document with one entry struck through.
- trust chain: interlocking chain links of light -> every trust link and validated trust path.
- validation: check marks (the check-line ticks of the SIGNS pass).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from cff.stage.objects import BY_ID, CATALOGUE, Kind
from cff.story import model as m
from cff.story.model import ColourRole

Pt2 = tuple[float, float]
Tri2 = tuple[Pt2, Pt2, Pt2]

# --- which card shows which marks -------------------------------------------------------------------------------------------

CARD_BODY_HEIGHT_FRACTION = 0.64  # the card body; the CA badge rises above it and the ribbon tails hang below, inside the box
CARD_BADGE_ROOM_FRACTION = 0.08  # the strip of the box above the body, where only the CA badge rises
CARD_FOLD_FRACTION = 0.34  # the folded top-right corner, as a fraction of the body height (the universal document outline)
SELF_SEAL_RADIUS_M = 0.162  # the self-closing seal keeps the V1-PKI-06 size (0.36 x the old 0.45 m card), overhanging the body's foot
SELF_SEAL_TUBE_FRACTION = 0.11  # its ink ring, as a fraction of its radius (18 mm, above V1-PKI-06's 12 mm)
PROOF_NOTCH_FRACTION = 0.6  # depth of the proof banner's swallowtail notches, as a fraction of its height
CARD_CA_VARIANTS = frozenset({"ca_cert", "copy", "root_cert"})  # cards that carry the CA badge
CARD_SELF_SIGNED_VARIANTS = frozenset({"self_signed", "root_cert"})  # cards that carry the self-closing seal
CARD_ISSUED_VARIANTS = frozenset({"end_entity", "ca_cert", "copy"})  # cards that carry the issuer's ribbon seal


def _model_cert(card_id: str) -> m.Certificate:
    return next(c for c in m.MODEL.certificates if c.id == card_id)


def issuer_role(card_id: str) -> ColourRole:
    """The colour of a card's seal: the role of the certificate that signed it (its issuer). Self-signed cards seal themselves."""
    cert = _model_cert(card_id)
    issuer = cert.issuer_cert
    return BY_ID[issuer].role


def card_marks(card_id: str) -> frozenset[str]:
    """The marks a card shows: ``ca_badge``, ``self_seal``, ``ribbon_seal``; always ``document`` and ``public_key``."""
    variant = BY_ID[card_id].variant
    marks = {"document", "public_key"}
    if variant in CARD_CA_VARIANTS:
        marks.add("ca_badge")
    if variant in CARD_SELF_SIGNED_VARIANTS:
        marks.add("self_seal")
    if variant in CARD_ISSUED_VARIANTS:
        marks.add("ribbon_seal")
    return frozenset(marks)


def cards() -> tuple[str, ...]:
    return tuple(o.id for o in CATALOGUE if o.kind is Kind.CARD)


# --- signature marks -------------------------------------------------------------------------------------------------------

SIGNED_REQUEST_VARIANTS = frozenset({"ca_request"})  # a capsule that is sealed as it appears carries its own signature tag
SIGNATURE_KINDS = frozenset({Kind.SEAL_RING, Kind.PROOF})  # every seal ring and handshake proof carries the stroke
SEAL_TAG_SIZE_M = 0.1  # the signature tag on a seal ring: 17 x 8.5 cm
SEAL_TAG_LIFT_M = 0.09  # its centre above the ring's top

# Kinds drawn with ink (and, for cards, the issuer seal): they take the icon slot list (``blender.actors.slots.ICON_NAMES``).
ICON_KINDS = frozenset({Kind.CARD, Kind.KEY_PRIVATE, Kind.KEY_PUBLIC, Kind.CAPSULE, Kind.SCROLL, Kind.SEAL_RING, Kind.PROOF})

# --- trust chain: chain links of light, in multiples of the link's width (``size[1]``) ------------------------------------------

CHAIN_LINK_LENGTH = 4.2  # centreline length of one oval link
CHAIN_LINK_WIDTH = 2.0  # centreline width
CHAIN_LINK_TUBE = 0.36  # tube radius
CHAIN_LINK_OVERLAP = 0.08  # extra overlap (fraction of the link length) so neighbours visibly interlock
CHAIN_CORE_FRACTION = 0.3  # the thin core of light that threads the links

# --- C-11 silhouettes ------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Shape:
    """One C-11 shape. A shape the film always shows as an assembly is measured as that assembly at its rest pose (catalogue
    home, full scale, rotation): the CA vault with its crown, the key container with its lid, lock and clamps, the root vault
    on its plinth (the spec names it "root vault (on a cable-free plinth)")."""

    name: str  # the C-11 name
    object_ids: tuple[str, ...]  # the catalogue objects whose meshes make the silhouette
    view: str  # "FRONT" (world XZ: what the camera sees of a card, key or capsule) or "TOP" (world XY: floor conduits, badges)


C11_SHAPES: tuple[Shape, ...] = (
    Shape("request capsule", ("REQ-RDP",), "FRONT"),
    Shape("certificate card", ("CERT-RDP",), "FRONT"),
    Shape("public key", ("KEY-RDP-PUB",), "FRONT"),
    Shape("private key", ("KEY-RDP-PRIV",), "FRONT"),
    Shape("key container", ("KC-RDP", "KCLID-RDP", "LOCK-RDP", "CLAMP-RDP-L", "CLAMP-RDP-R"), "FRONT"),
    Shape("template badge", ("TPL-RDPAUTH",), "TOP"),
    Shape("CA vault", (m.ISSUING_CA1, "CROWN-CA1"), "FRONT"),
    Shape("root vault", (m.ROOT_CA, "ROOT-PLINTH"), "FRONT"),
    Shape("trust link", ("TL-CA1",), "FRONT"),
    Shape("network channel", ("CH-RDP-S1",), "TOP"),
    Shape("validation tick", ("TICK-RDP-a",), "FRONT"),
    Shape("CRL scroll fetch", ("CRL-CA1",), "FRONT"),
    Shape("AIA indicator", ("AIA-RDP",), "FRONT"),
    Shape("handshake proof", ("HS-RDP",), "FRONT"),
)
PAIR_IOU_MAX = 0.75
STRICT_IOU_MAX = 0.6
STRICT_PAIRS: tuple[tuple[str, str], ...] = (
    ("private key", "public key"),
    ("handshake proof", "private key"),
    ("handshake proof", "public key"),
)
GRID_CELLS = 400  # cells per side of the common raster (the normalised shapes span at most GRID_HALF_EXTENT either way)
GRID_HALF_EXTENT = 2.6


def normalise(tris: Sequence[Tri2]) -> list[Tri2]:
    """Scale uniformly so the bounding box has unit area, and centre the box on the origin (C-11 measurement)."""
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        raise ValueError("a silhouette needs a non-degenerate bounding box")
    s = 1.0 / (w * h) ** 0.5
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return [tuple(((p[0] - cx) * s, (p[1] - cy) * s) for p in t) for t in tris]  # type: ignore[misc]


def rasterise(tris: Iterable[Tri2], cells: int = GRID_CELLS, half: float = GRID_HALF_EXTENT) -> set[int]:
    """Cells (row * cells + column) whose centre lies inside any triangle, on a square grid over [-half, half]^2."""
    step = 2 * half / cells
    filled: set[int] = set()
    for (ax, ay), (bx, by), (cx, cy) in tris:
        area = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
        if abs(area) < 1e-15:
            continue
        c0 = max(0, int((min(ax, bx, cx) + half) / step))
        c1 = min(cells - 1, int((max(ax, bx, cx) + half) / step))
        r0 = max(0, int((min(ay, by, cy) + half) / step))
        r1 = min(cells - 1, int((max(ay, by, cy) + half) / step))
        for r in range(r0, r1 + 1):
            py = -half + (r + 0.5) * step
            for c in range(c0, c1 + 1):
                px = -half + (c + 0.5) * step
                w0 = (bx - ax) * (py - ay) - (px - ax) * (by - ay)
                w1 = (cx - bx) * (py - by) - (px - bx) * (cy - by)
                w2 = (ax - cx) * (py - cy) - (px - cx) * (ay - cy)
                if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0):
                    filled.add(r * cells + c)
    return filled


def iou(a: set[int], b: set[int]) -> float:
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def limit(a: str, b: str) -> float:
    return STRICT_IOU_MAX if (a, b) in STRICT_PAIRS or (b, a) in STRICT_PAIRS else PAIR_IOU_MAX


def pair_report(silhouettes: dict[str, set[int]]) -> list[tuple[str, str, float, float]]:
    """Every pair (a, b, IoU, limit), worst margin first."""
    names = list(silhouettes)
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            out.append((a, b, iou(silhouettes[a], silhouettes[b]), limit(a, b)))
    return sorted(out, key=lambda row: row[3] - row[2])
