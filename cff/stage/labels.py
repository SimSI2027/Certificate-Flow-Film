"""In-world labels: where each model label hangs, how big it is and when it is on screen.

Every ``cff.story.model.Label`` is placed exactly once (a test enforces it). Labels are physical signage: a dark
plate with white text, hung from a stage object (or a fixed world point) and turned to face the camera (L-06).
Persistent labels (host plates, CA nameplates, template badges, card fields, check captions on ticks) belong to
their parent and appear and leave with it; windowed labels (tags) pop in and out with their own scale track.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from cff.stage import camera, choreography
from cff.stage import layout as lo
from cff.stage.layout import Vec3
from cff.stage.objects import BY_ID as BY_OBJECT
from cff.stage.tracks import LOCATION, SCALE, Timeline
from cff.story import model as m
from cff.story import timing
from cff.theme import motion, shots

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
PLATE_OPACITY = 0.82
APPEAR_LEAD_FRAMES = 3  # staggering between consecutive windowed labels


@dataclass(frozen=True)
class Window:
    beat: str
    start_s: float  # offset from the beat start
    end_s: float | None = None  # None: to the end of the beat


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


def _check_placements() -> list[Placement]:
    """Check captions hang to the right of their tick, so they appear with it."""
    out: list[Placement] = []
    right = (0.2, 0.0, 0.0)
    for ca_actor, tag, beat in ((m.ISSUING_CA1, "CA1", "B-04.3"), (m.ISSUING_CA2, "CA2", "B-08.1")):
        for index, check in enumerate(_CA_CHECK_ORDER):
            out.append(Placement(f"LBL-{ca_actor}-{check}", f"TICK-{tag}-{'abcd'[index]}", right, CAP_CHECK, "LEFT"))
        del beat
    rdp_checks = [e.check.name for e in m.MODEL.events if e.id.startswith("E-06.4") and e.check is not None]
    for index, rdp_check in enumerate(rdp_checks):
        out.append(Placement(f"LBL-CHAIN-RDP-{rdp_check}", f"TICK-RDP-{'abcdef'[index]}", right, CAP_CHECK, "LEFT"))
    web_events = ("E-09.1j", "E-09.1k", "E-09.1l", "E-09.1o")
    by_id = {e.id: e for e in m.MODEL.events}
    for index, event_id in enumerate(web_events):
        web_check = by_id[event_id].check
        assert web_check is not None
        out.append(Placement(f"LBL-CHAIN-WEB-{web_check.name}", f"TICK-WEB-{'abcd'[index]}", right, CAP_CHECK, "LEFT"))
    return out


def _build() -> tuple[Placement, ...]:
    ca1_front = lo.add(lo.CA1, (0.0, lo.CA_FRONT_Y - 0.4, 0.0))
    ca2_front = lo.add(lo.CA2, (0.0, lo.CA_FRONT_Y - 0.4, 0.0))
    elig_x = lo.CA2[0]  # the four eligibility tags stack above Issuing CA 2
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
        Placement("LBL-UNVERIFIED", m.CLIENT, (0.0, 0.0, 1.0), CAP_TAG * 1.2, window=Window("B-02.2", 1.1, 2.9)),
        Placement("LBL-FLASHBACK", "CARTRIDGE", (0.0, 0.0, 0.7), CAP_TAG * 1.4, window=Window("B-05.2", 0.1, 4.9)),
        Placement("LBL-ROOT-STORE", "TS-CLIENT-ROOT", (0.0, 0.0, 0.55), CAP_TAG, window=Window("B-06.2", 1.9)),
        Placement("LBL-AIA-1", None, lo.add(lo.STACK_CERT, (1.15, -0.2, 0.45)), CAP_TAG, window=Window("B-06.3", 0.1)),
        Placement("LBL-AIA-2", None, lo.add(lo.STACK_CERT, (1.15, -0.2, 0.12)), CAP_TAG, window=Window("B-06.3", 0.2)),
        Placement("LBL-OCSP", "TICK-RDP-f", (0.2, 0.0, -0.3), CAP_TAG, "LEFT", Window("B-06.5", 0.3, 2.5)),
        Placement("LBL-CA1-INELIGIBLE", None, lo.add(ca1_front, (0.0, 0.0, lo.CA_VAULT_SIZE[2] + 0.5)), CAP_WIDE_TAG, window=Window("B-07.3", 1.0)),
        Placement("LBL-CA2-NOTE", "TICK-CA2-c", (0.2, 0.0, -0.32), CAP_CHECK, "LEFT", Window("B-08.1", 1.4)),
    ]
    elig = ("LBL-ELIG-TEMPLATE_PUBLISHED", "LBL-ELIG-ENROLLMENT_POLICY", "LBL-ELIG-PERMISSIONS", "LBL-ELIG-CA_AVAILABLE")
    for index, label_id in enumerate(elig):
        placements.append(Placement(label_id, None, (elig_x, ca2_front[1] - 0.4, lo.CA_VAULT_SIZE[2] + 1.3 - index * 0.55), CAP_WIDE_TAG, "CENTER",
                                    Window("B-07.3", 0.9 + 0.2 * index)))
    placements += _check_placements()
    return tuple(placements)


PLACEMENTS: tuple[Placement, ...] = _build()
BY_ID: dict[str, Placement] = {p.label_id: p for p in PLACEMENTS}


def window_frames(window: Window) -> tuple[int, int]:
    """(first frame of the entrance, first frame of the exit)."""
    start = timing.beat_window(window.beat)[0] + window.start_s
    end = timing.beat_window(window.beat)[1] if window.end_s is None else timing.beat_window(window.beat)[0] + window.end_s
    return timing.seconds_to_frame(start), timing.seconds_to_frame(end)


def add_label_tracks(timeline: Timeline) -> None:
    """Scale tracks for windowed labels: eased entrance, a faster exit (C-06), hidden otherwise."""
    hidden: tuple[float, ...] = (motion.HIDDEN_SCALE,) * 3
    shown: tuple[float, ...] = (motion.FULL_SCALE,) * 3
    enter, leave = motion.label_entrance_frames(), motion.label_exit_frames()
    stagger = 0
    for placement in PLACEMENTS:
        if placement.window is None:
            continue
        first, last = window_frames(placement.window)
        first += stagger % (APPEAR_LEAD_FRAMES + 1)
        stagger += 1
        timeline.key(placement.label_id, SCALE, timing.FRAME_START, hidden, "EASE_IN_OUT")
        timeline.key(placement.label_id, SCALE, first, hidden, "OUT_BACK")
        timeline.key(placement.label_id, SCALE, first + enter, shown, "EASE_IN_OUT")
        timeline.key(placement.label_id, SCALE, last - leave, shown, "EASE_IN")
        timeline.key(placement.label_id, SCALE, last, hidden, "EASE_IN_OUT")


def is_windowed(label_id: str) -> bool:
    return BY_ID[label_id].window is not None


# --- sizing from the camera plan --------------------------------------------------------------------------------------------------------------
# Signage is sized so it stays readable in the beats that need it: a label that must be read from a wide shot gets a
# larger plate. Each label's cap height is raised until it reaches TARGET_CAP_PX (1080p) at the SIZING_PERCENTILE of the
# camera distances during its must-read frames; labels of one family (a check list, a tag stack) share the largest size.
TARGET_CAP_PX = 26.0  # above the 18 px of L-01 so the measured minimum clears it
SIZING_PERCENTILE = 0.7
MAX_CAP_M = 0.6
FAMILIES: tuple[str, ...] = ("LBL-ISSUING_CA1-", "LBL-ISSUING_CA2-", "LBL-CHAIN-RDP-", "LBL-CHAIN-WEB-", "LBL-ELIG-", "LBL-CERT-RDP-", "LBL-CERT-WEB-",
                             "LBL-AIA-", "LBL-HOST-WEB", "LBL-SITE-WEB")
REFERENCE_WIDTH_PX = 1920.0


# Must-read labels that are still below the L-01 / L-03 / L-06 measurement in the animatic (reported, ratcheted: no label
# outside this set may fail, and scene_checks fails if a listed label now passes, so the list never rots). The Stage 1
# rounds clear it by retiming ticks and by framing: most of these appear too late in their beat to be on screen 1.5 s.
LABELS_OPEN: frozenset[str] = frozenset()


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


def _family(label_id: str) -> str:
    return next((f for f in FAMILIES if label_id.startswith(f)), label_id)


@cache
def effective_caps() -> dict[str, float]:
    """Cap height in metres per label after sizing against the camera plan."""
    timeline = choreography.build_timeline()
    plan = camera.CameraPlan(timeline)
    needed: dict[str, float] = {}
    for placement in PLACEMENTS:
        frames = must_read_frames(placement.label_id)
        values: list[float] = []
        for frame in frames:
            state = plan.state(frame)
            if placement.parent is None:
                position = placement.offset
            else:
                loc = timeline.value_at(placement.parent, LOCATION, frame)
                base = (loc[0], loc[1], loc[2]) if loc is not None else BY_OBJECT[placement.parent].home
                position = lo.add(base, placement.offset)
            depth = lo.dist(state.position, position)
            values.append(TARGET_CAP_PX * depth * shots.SENSOR_WIDTH_MM / (state.lens * REFERENCE_WIDTH_PX))
        values.sort()
        wanted = values[min(len(values) - 1, int(SIZING_PERCENTILE * len(values)))] if values else 0.0
        needed[placement.label_id] = min(MAX_CAP_M, max(placement.cap_m, wanted))
    families: dict[str, float] = {}
    for label_id, cap in needed.items():
        families[_family(label_id)] = max(families.get(_family(label_id), 0.0), cap)
    return {label_id: families[_family(label_id)] for label_id in needed}


def cap_m(label_id: str) -> float:
    return effective_caps()[label_id]
