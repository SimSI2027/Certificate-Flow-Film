"""In-world labels: where each model label hangs, how big it is and when it is on screen.

Every ``cff.story.model.Label`` is placed exactly once (a test enforces it). Labels are physical signage: a dark
plate with white text, hung from a stage object (or a fixed world point) and turned to face the camera (L-06).
Persistent labels (host plates, CA nameplates, template badges, card fields) exist while their parent is on stage;
windowed labels (tags, check lists) exist inside their window. ``cff.stage.signs`` decides, frame by frame, where each
sign sits on screen, its size and whether it is shown.
"""

from __future__ import annotations

from dataclasses import dataclass

from cff.stage import layout as lo
from cff.stage.layout import Vec3
from cff.story import model as m
from cff.story import timing

# Cap heights in metres (the height of a capital letter). L-06 asks >= 18 px at 1080p; scene_checks measures it.
CAP_PLATE_SMALL = 0.05
CAP_PLATE = 0.12
CAP_NAMEPLATE = 0.11
CAP_TAG = 0.11
CAP_CHECK = 0.115
CAP_WIDE_TAG = 0.26  # eligibility tags read from the wide B-07.3 shot
CAP_ROOT_PLATE = 0.3
CAP_FIELD = 0.05
TEXT_TO_EM = 1.0 / 0.72  # Blender font size (em) per metre of cap height, for the bundled font
PLATE_MARGIN_EM = 0.45  # plate padding around the text, in cap heights
APPEAR_LEAD_FRAMES = 3  # staggering between consecutive windowed labels


@dataclass(frozen=True)
class Window:
    beat: str
    start_s: float  # offset from the beat start
    end_s: float | None = None  # None: to the end of the beat (or of ``until``)
    until: str | None = None  # a later beat whose end closes the window (a check list held while its last check resolves)


@dataclass(frozen=True)
class Placement:
    label_id: str
    parent: str | None  # stage object id; None: ``offset`` is a world position
    offset: Vec3
    cap_m: float
    align: str = "CENTER"
    window: Window | None = None  # None: persistent with its parent

    @property
    def text(self) -> str:
        return LABELS[self.label_id].text


LABELS: dict[str, m.Label] = {label.id: label for label in m.MODEL.labels}

_CA_CHECK_ORDER = tuple(c.name for c in m.CaCheck)


# A check list is written out as soon as its first check begins, so every line is readable while the ticks resolve one by
# one (L-06: each line holds >= 1.5 s); the list closes with its last beat (never left over into the flashback: PKI-S1R1-04).
LIST_LEAD_S = 0.3  # the list appears this long before its first check event


def _list_window(beat: str, first_event: str, until: str | None = None) -> Window:
    start = next(e.start_s for e in m.MODEL.events if e.id == first_event) - timing.beat_window(beat)[0] - LIST_LEAD_S
    return Window(beat, max(0.1, round(start * timing.FPS) / timing.FPS), until=until)


def _check_placements() -> list[Placement]:
    """Check lines hang to the right of their tick slot."""
    out: list[Placement] = []
    right = (0.2, 0.0, 0.0)
    for ca_actor, tag, beat, first in ((m.ISSUING_CA1, "CA1", "B-04.3", "E-04.3a"), (m.ISSUING_CA2, "CA2", "B-08.1", "E-08.1a")):
        window = _list_window(beat, first)
        for index, check in enumerate(_CA_CHECK_ORDER):
            out.append(Placement(f"LBL-{ca_actor}-{check}", f"TICK-{tag}-{'abcd'[index]}", right, CAP_CHECK, "LEFT", window))
    rdp_checks = [e.check.name for e in m.MODEL.events if e.id.startswith("E-06.4") and e.check is not None]
    rdp_window = _list_window("B-06.4", "E-06.4a", until="B-06.5")
    for index, rdp_check in enumerate(rdp_checks):
        out.append(Placement(f"LBL-CHAIN-RDP-{rdp_check}", f"TICK-RDP-{'abcdef'[index]}", right, CAP_CHECK, "LEFT", rdp_window))
    web_events = ("E-09.1j", "E-09.1k", "E-09.1l", "E-09.1o")
    by_id = {e.id: e for e in m.MODEL.events}
    web_window = _list_window("B-09.1", "E-09.1j")
    for index, event_id in enumerate(web_events):
        web_check = by_id[event_id].check
        assert web_check is not None
        out.append(Placement(f"LBL-CHAIN-WEB-{web_check.name}", f"TICK-WEB-{'abcd'[index]}", right, CAP_CHECK, "LEFT", web_window))
    return out


def _build() -> tuple[Placement, ...]:
    placements: list[Placement] = [
        # --- persistent plates ------------------------------------------------------------------
        Placement("LBL-HOST-CLIENT", m.CLIENT, (-0.05, 0.0, 0.6), CAP_PLATE),
        Placement("LBL-HOST-RDP", m.RDP_SERVER, (0.0, lo.FRONT_Y - 0.15, 2.55), CAP_PLATE),
        Placement("LBL-HOST-WEB", m.WEB_SERVER, (0.0, lo.FRONT_Y - 0.15, 2.7), CAP_PLATE),
        Placement("LBL-SITE-WEB", m.WEB_SERVER, (0.0, lo.FRONT_Y - 0.15, 2.4), CAP_PLATE),
        Placement("LBL-AD", m.AD, (0.0, -1.3, lo.AD_HEIGHT + 0.45), CAP_NAMEPLATE * 0.8),
        Placement("LBL-DC", m.AD, (0.0, -1.3, lo.AD_HEIGHT + 0.05), CAP_PLATE_SMALL),
        Placement("LBL-PKI", m.PKI_HTTP, (0.0, -0.6, 1.85), CAP_PLATE),
        Placement("LBL-ROOT", m.ROOT_CA, (0.0, -lo.ROOT_VAULT_SIZE[1] / 2 - 0.5, -lo.ROOT_VAULT_SIZE[2] / 2 - 0.45), CAP_ROOT_PLATE),
        Placement("LBL-CA1", "EVAL-CA1", (0.0, -0.15, 0.95), CAP_NAMEPLATE),  # hangs over the evaluation cradle
        Placement("LBL-CA2", "EVAL-CA2", (0.0, -0.15, 0.95), CAP_NAMEPLATE),
        Placement("LBL-TPL-RDP", "TPL-RDPAUTH", (0.0, 0.0, 0.26), CAP_PLATE),
        Placement("LBL-TPL-WEB", "TPL-WEBTLS", (0.0, 0.0, 0.26), CAP_PLATE),
        # --- card fields: floated in front of the card so they stay readable ----------------------
        Placement("LBL-SELF", "CERT-RDP-SELF", (0.0, -0.12, -0.38), CAP_FIELD * 1.6),
        Placement("LBL-CERT-RDP-SAN", "CERT-RDP", (0.0, -0.12, -0.36), CAP_FIELD * 1.4),
        Placement("LBL-CERT-RDP-EKU", "CERT-RDP", (0.0, -0.12, -0.52), CAP_FIELD * 1.3),
        Placement("LBL-CERT-WEB-SAN", "CERT-WEB", (0.0, -0.12, -0.36), CAP_FIELD * 1.4),
        Placement("LBL-CERT-WEB-EKU", "CERT-WEB", (0.0, -0.12, -0.52), CAP_FIELD * 1.3),
        Placement("LBL-REQ-CA1", "REQ-CA1", (0.0, 0.0, 0.34), CAP_TAG * 0.9),
        # --- windowed tags ---------------------------------------------------------------------------
        Placement("LBL-CONNECT", "SCREEN-IDLE", (0.0, 0.0, 0.35), CAP_TAG, window=Window("B-01.1", 0.3)),  # on the client's screen (PKI-S1R1-07)
        Placement("LBL-UNVERIFIED", m.CLIENT, (0.0, 0.0, 1.0), CAP_TAG * 1.2, window=Window("B-02.2", 0.7)),
        Placement("LBL-FLASHBACK", "CARTRIDGE", (0.0, 0.0, 0.7), CAP_TAG * 1.4, window=Window("B-05.2", 0.1, 4.9)),
        Placement("LBL-ROOT-STORE", "TS-CLIENT-ROOT", (0.0, 0.0, 0.55), CAP_TAG, window=Window("B-06.2", 1.6)),
        Placement("LBL-AIA-1", None, lo.add(lo.STACK_CERT, (1.15, -0.2, 0.45)), CAP_TAG, window=Window("B-06.3", 0.1)),
        Placement("LBL-AIA-2", None, lo.add(lo.STACK_CERT, (1.15, -0.2, 0.12)), CAP_TAG, window=Window("B-06.3", 0.2)),
        Placement("LBL-OCSP", "TICK-RDP-f", (0.2, 0.0, -0.3), CAP_TAG, "LEFT", Window("B-06.5", 0.3, 2.4)),
        Placement("LBL-CA1-INELIGIBLE", "EVAL-CA1", (0.0, -0.15, 0.95), CAP_WIDE_TAG, window=Window("B-07.3", 0.6)),  # under CA 1's nameplate
        Placement("LBL-CA2-NOTE", "TICK-CA2-c", (0.2, 0.0, -0.32), CAP_CHECK, "LEFT", Window("B-08.1", 1.4)),
    ]
    elig = ("LBL-ELIG-TEMPLATE_PUBLISHED", "LBL-ELIG-ENROLLMENT_POLICY", "LBL-ELIG-PERMISSIONS", "LBL-ELIG-CA_AVAILABLE")
    for index, label_id in enumerate(elig):  # stacked under CA 2's nameplate (cff.stage.signs.LISTS keeps the order)
        placements.append(Placement(label_id, "EVAL-CA2", (0.0, -0.15, 0.95), CAP_WIDE_TAG, "CENTER", Window("B-07.3", 0.5 + 0.1 * index)))
    placements += _check_placements()
    return tuple(placements)


PLACEMENTS: tuple[Placement, ...] = _build()
BY_ID: dict[str, Placement] = {p.label_id: p for p in PLACEMENTS}


def window_frames(window: Window) -> tuple[int, int]:
    """(first frame of the entrance, first frame of the exit)."""
    start = timing.beat_window(window.beat)[0] + window.start_s
    end = timing.beat_window(window.until or window.beat)[1] if window.end_s is None else timing.beat_window(window.beat)[0] + window.end_s
    return timing.seconds_to_frame(start), timing.seconds_to_frame(end)


def is_windowed(label_id: str) -> bool:
    return BY_ID[label_id].window is not None


def must_read_frames(label_id: str) -> list[int]:
    window = BY_ID[label_id].window
    frames: set[int] = set()
    for beat in LABELS[label_id].must_read_beats:
        first, last = timing.frame_range(*timing.beat_window(beat))
        frames.update(range(first, last + 1))
    if window is not None:
        a, b = window_frames(window)
        frames = {f for f in frames if a <= f < b}
    return sorted(frames)
