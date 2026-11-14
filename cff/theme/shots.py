"""Named camera shots (Charter Section 8): one rig, eased moves, real lenses (24-50 mm), restrained f-stops.

Each beat has one shot. A shot describes where the camera ends the beat: it looks at ``look`` (object ids and/or
fixed points, averaged) from ``dist`` metres at azimuth ``az`` and elevation ``el`` (degrees; azimuth is measured
from +X toward +Y, so -90 is a camera south of its subject looking north). The camera starts each beat where the
previous one ended, so motion is continuous; only ``start`` shots (the two flashback cuts and the opening) differ.

``follow`` is the fraction of the beat over which the look-at point locks onto a moving subject (the subject
leads, the camera follows). ``bulge`` pulls the camera back (positive) or pushes it in (negative) mid-move.
Scenes and beats are never defined here, only camera intent.
"""

from __future__ import annotations

from dataclasses import dataclass

from cff.stage.layout import Vec3

Target = str | Vec3  # a stage object id or a fixed world point


@dataclass(frozen=True)
class Pose:
    look: tuple[Target, ...]
    az: float
    el: float
    dist: float
    lens: float
    fstop: float


@dataclass(frozen=True)
class Shot:
    name: str
    beat: str
    look: tuple[Target, ...]
    az: float
    el: float
    dist: float
    lens: float
    fstop: float
    follow: float = 1.0
    bulge: float = 0.0
    focus: tuple[Target, ...] = ()  # default: the look targets
    rack_to: tuple[Target, ...] = ()  # focus racks to these targets mid-beat
    start: Pose | None = None  # an explicit opening pose (the opening shot and the two cuts)
    lead_s: float = 0.0  # the move into this beat starts this long before the beat (the previous beat's move ends early)
    arrive: float = 1.0  # fraction of the move by which the pose (az, el, dist, look) is reached; the camera then holds it
    focus_pull: float | None = None  # fraction of the move over which the focus settles on the subject (default FOCUS_PULL_FRACTION)


# Camera limits (C-02) and lens-rate planning.
LENS_MAX_STEP_MM = 0.4  # planning margin under the 0.5 mm/frame limit
LENS_MIN_MM, LENS_MAX_MM = 24.0, 50.0
SENSOR_WIDTH_MM = 36.0
CLIP_START_M, CLIP_END_M = 0.1, 400.0
RACK_FROM, RACK_TO = 0.35, 0.75  # beat fractions over which a rack focus happens
FOCUS_PULL_FRACTION = 0.3  # the focus settles on a beat's subject within this fraction of the beat

# Fixed points the shots refer to (world metres).
USER_HEAD: Vec3 = (-10.96, -8.0, 1.27)  # V4: the seated character's head (chair at x -10.9, leaning 12 degrees to the desk)
LISTENER: Vec3 = (0.0, -0.5, 1.5)
PRESS1_OUT: Vec3 = (-2.0, 13.8, 1.1)
PRESS2_OUT: Vec3 = (12.0, 13.8, 1.1)
STACK_MID: Vec3 = (-10.6, -7.4, 1.7)
CA1_MODULE: Vec3 = (-4.1, 14.7, 1.3)
# The hero looks at the middle of the SW-NE topology from the south-east, so the user, both servers, both issuing
# CAs and the root lie across the 16:9 frame (V1-CIN-02; from az -105 the user and laptop fell below the frame).
WORLD_CENTRE: Vec3 = (-0.5, 4.0, 6.5)

# The stage objects that stand for each beat's focal subject (the model names concepts such as "CHAIN-RDP").
# Where the subject is born mid-beat (a stamped card, a sealed request), the machine that makes it is part of the
# subject: the camera is already looking at it, and the focus is already on it, when the subject appears.
FOCAL_OBJECTS: dict[str, tuple[str, ...]] = {
    "CH-RDP": ("PULSE-RDP-1",),
    "KP-RDP": ("KEY-RDP-PRIV", "KEY-RDP-PUB"),
    "CHAIN-RDP": ("CERT-RDP", "CERT-CA1-COPY-RDP", "CERT-ROOT"),
    "CHAIN-WEB": ("CERT-WEB", "CERT-CA2-COPY-WEB", "CERT-ROOT"),
    "SVC-AIA": ("AIA-RDP",),
    "SVC-CDP": ("CRL-CA1", "CRL-ROOT"),
    "ISSUING_CA1": ("EVAL-CA1",),
    "ISSUING_CA2": ("EVAL-CA2",),
}
FOCAL_BEAT_OBJECTS: dict[str, tuple[str, ...]] = {
    "B-01.2": ("PULSE-RDP-1",),
    "B-03.1": ("KC-RDP", "KEY-RDP-PRIV", "KEY-RDP-PUB"),
    "B-04.4": ("PRESSHEAD-CA1", "CERT-RDP"),
    "B-05.2": ("CARTRIDGE", "REQ-CA1"),
    "B-06.6": ("CH-RDP-S1", "SCREEN-RDP"),
    "B-07.2": ("KC-WEB", "REQ-WEB"),
    "B-08.2": ("PRESSHEAD-CA2", "CERT-WEB"),
}


def focal_objects(beat_id: str, focal: str) -> tuple[str, ...]:
    if beat_id in FOCAL_BEAT_OBJECTS:
        return FOCAL_BEAT_OBJECTS[beat_id]
    return FOCAL_OBJECTS.get(focal, (focal,))


SHOTS: tuple[Shot, ...] = (
    # S1
    Shot("desk-push", "B-01.1", (USER_HEAD,), -124, 5, 2.8, 50, 2.8, follow=0.25, bulge=3.8,
         start=Pose((USER_HEAD,), -150, 10, 3.4, 50, 2.8)),
    Shot("pulse-chase", "B-01.2", ("PULSE-RDP-1",), -128, 8, 7.0, 39, 4.0, follow=0.4, bulge=3.0),  # closer starts B-02.1 too near the RDP plate (V1-CIN-01 residual)
    # S2
    Shot("listener-low", "B-02.1", (LISTENER,), -94, 13, 6.2, 35, 2.8, follow=0.8, bulge=0.1),
    Shot("card-slide", "B-02.2", ("CERT-RDP-SELF",), -111, 14, 18.0, 42, 2.8, follow=0.25, bulge=6.0, rack_to=("CLIENT",)),  # card large (CIN-S1R1-06)
    Shot("badge-drop", "B-02.3", ("TPL-RDPAUTH",), -46, 28, 6.8, 39, 4.0, follow=0.6, bulge=0.6),
    # S3
    Shot("keys-push", "B-03.1", ("KEY-RDP-PRIV", "KEY-RDP-PUB"), -90, 4, 2.6, 50, 2.8),
    Shot("container-slide", "B-03.2", ("KC-RDP",), -100, 6, 2.2, 50, 2.0),
    Shot("capsule-rack", "B-03.3", ("KC-RDP", "REQ-RDP"), -82, 9, 2.7, 50, 2.8, follow=0.25, bulge=2.4, focus=("KC-RDP",), rack_to=("REQ-RDP",)),
    Shot("proof-pullback", "B-03.4", ("KC-RDP", "REQ-RDP"), -93, 5, 3.7, 50, 2.8, follow=0.25, bulge=1.5),
    # S4
    Shot("ad-shoulder", "B-04.1", ("PORT-RDP-OUT", "AD", "AD"), -108, 10, 10.5, 35, 4.0, bulge=1.5, focus=("AD",)),  # capsule at its port, AD apart (PKI-S1R1-02)
    Shot("capsule-chase", "B-04.2", ("REQ-RDP",), -95, 8, 4.6, 50, 4.0, follow=0.35, bulge=6.0),
    Shot("checks-orbit", "B-04.3", ("EVAL-CA1",), -69, 15, 3.5, 35, 2.8, follow=0.25),
    Shot("press-stamp", "B-04.4", (PRESS1_OUT,), -98, 9, 7.4, 50, 2.8, follow=0.25, bulge=2.7),
    Shot("card-return", "B-04.5", ("CERT-RDP",), -95, 6, 3.82, 35, 2.8, follow=0.8, bulge=12.3),  # V1-CIN-01
    # S5
    Shot("root-crane", "B-05.1", ("ROOT_CA",), -100, 14, 13.0, 28, 4.0, follow=0.6, bulge=8.0),
    Shot("flashback-glide", "B-05.2", ("CARTRIDGE",), -100, 12, 6.0, 50, 4.0, follow=0.25, bulge=9.0, focus=("CARTRIDGE",),
         start=Pose((CA1_MODULE,), -80, 8, 3.2, 35, 4.0)),
    Shot("issuer-link", "B-05.3", ("CERT-CA1", "ROOT_CA"), -106, 24, 46.4, 28, 4.0, follow=0.8, bulge=0.1, focus=("CERT-CA1",),
         start=Pose(("CERT-CA1", "ROOT_CA"), -100, 30, 16.0, 28, 4.0)),
    # S6
    # proof readable at film scale (PKI-S1R1-06, V1-PKI-04; dist 4.5 / follow 0.7 failed C-03, so 5.25 / 0.6, then V1-CIN-01 steps)
    Shot("present-follow", "B-06.1", ("CERT-RDP",), -10, 8, 4.46, 44, 4.0, follow=0.6, bulge=0.15),
    Shot("chain-boom", "B-06.2", (STACK_MID,), 79, 24, 11.2, 35, 2.8, follow=0.4, bulge=1.4),
    Shot("aia-push", "B-06.3", ("AIA-RDP",), 53, 4, 4.4, 50, 2.8, follow=0.8, rack_to=((-9.8, -7.4, 1.7),)),
    Shot("checks-crane", "B-06.4", (STACK_MID,), 45, 25, 8.5, 35, 2.8, follow=0.6, bulge=0.4),
    Shot("revocation-pan", "B-06.5", ("CRL-CA1", "CRL-ROOT"), -44, 12, 11.0, 32, 4.0, follow=0.25, bulge=11.0),  # fetches larger (CIN-S1R1-06, V1-PKI-05)
    # V1-CIN-05: dist 5.0 breaks C-02 on the move into B-07.1 (f2091+); 8.5 at 50 mm is the closest passing framing
    Shot("green-glide", "B-06.6", ("SCREEN-RDP",), -20, 14, 8.5, 50, 2.8),
    # S7
    Shot("web-glide", "B-07.1", ("WEB_SERVER",), -73, 8, 11.0, 35, 4.0, follow=0.15, bulge=12.0),
    Shot("web-keys", "B-07.2", ("KC-WEB",), -67, 6, 6.1, 50, 2.8, follow=0.4, bulge=-3.0),
    Shot("eligibility-wide", "B-07.3", ("AD", (4.0, 10.0, 2.0)), -90, 24, 17.0, 28, 4.0, focus=("AD",)),
    Shot("web-capsule-chase", "B-07.4", ("REQ-WEB",), -95, 8, 3.91, 50, 4.0, follow=0.35, bulge=0.75),  # V1-CIN-01
    # S8
    Shot("checks-orbit-2", "B-08.1", ("EVAL-CA2",), -77, 11, 3.4, 35, 2.8, bulge=-0.2),
    Shot("tls-stamp", "B-08.2", ("CERT-WEB",), -94, 5, 3.8, 35, 2.8, follow=0.8, bulge=8.8),
    # V1-CIN-01 (dist) and V1-CIN-06 (bulge 1.8 -> 4.8: the white flash at 90 s drops from a 12.2 to a 4.2 luma step; 5.8 is worse)
    Shot("same-root", "B-08.3", ("CERT-CA2", "ROOT_CA"), -32, 18, 26.22, 28, 4.0, follow=0.35, bulge=4.8, focus=("CERT-CA2",)),
    # S9
    Shot("browser-arc", "B-09.1", (STACK_MID,), -80, 8, 6.0, 35, 2.8, follow=0.4, bulge=5.5),  # V1-PKI-04
    # V1-CIN-02, v1.3: the pull-back starts 0.8 s before the beat, reaches the pose in 27% of its move and racks to the root early
    # (C-02 is relative to the focus distance), so the whole topology is in frame from 98.5 s (was about 101 s)
    Shot("hero", "B-09.2", (WORLD_CENTRE,), -45, 30, 42.0, 24, 5.6, follow=0.7, focus=("ROOT_CA",), lead_s=0.8, arrive=0.27, focus_pull=0.08),
    Shot("close", "B-09.3", (WORLD_CENTRE,), -41, 32, 44.0, 24, 5.6, focus=("ROOT_CA",)),
)

BY_BEAT: dict[str, Shot] = {s.beat: s for s in SHOTS}
