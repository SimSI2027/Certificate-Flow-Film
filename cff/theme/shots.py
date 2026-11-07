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


# Camera limits (C-02) and lens-rate planning.
LENS_MAX_STEP_MM = 0.4  # planning margin under the 0.5 mm/frame limit
LENS_MIN_MM, LENS_MAX_MM = 24.0, 50.0
SENSOR_WIDTH_MM = 36.0
CLIP_START_M, CLIP_END_M = 0.1, 400.0
RACK_FROM, RACK_TO = 0.35, 0.75  # beat fractions over which a rack focus happens

# Fixed points the shots refer to (world metres).
USER_HEAD: Vec3 = (-10.4, -8.0, 1.3)
LISTENER: Vec3 = (0.0, -0.5, 1.5)
PRESS1_OUT: Vec3 = (-2.0, 13.8, 1.1)
PRESS2_OUT: Vec3 = (12.0, 13.8, 1.1)
STACK_MID: Vec3 = (-10.6, -7.4, 1.7)
CA1_MODULE: Vec3 = (-4.1, 14.7, 1.3)
WORLD_CENTRE: Vec3 = (-1.0, 7.0, 3.5)

SHOTS: tuple[Shot, ...] = (
    # S1
    Shot("desk-push", "B-01.1", (USER_HEAD,), -138, 10, 3.1, 50, 2.8,
         start=Pose((USER_HEAD,), -150, 10, 3.4, 50, 2.8)),
    Shot("pulse-chase", "B-01.2", ("PULSE-RDP-1",), -128, 8, 7.0, 35, 4.0, follow=0.4, bulge=3.0),
    # S2
    Shot("listener-low", "B-02.1", (LISTENER,), -105, 8, 5.2, 35, 2.8),
    Shot("card-slide", "B-02.2", ("CERT-RDP-SELF",), 25, 10, 11.0, 35, 2.8, follow=0.5, bulge=4.0, rack_to=("CLIENT",)),
    Shot("badge-drop", "B-02.3", ("TPL-RDPAUTH",), -80, 35, 5.0, 35, 4.0, follow=0.6),
    # S3
    Shot("keys-push", "B-03.1", ("KEY-RDP-PRIV", "KEY-RDP-PUB"), -90, 4, 2.6, 50, 2.8),
    Shot("container-slide", "B-03.2", ("KC-RDP",), -100, 6, 2.2, 50, 2.0),
    Shot("capsule-rack", "B-03.3", ("KC-RDP", "REQ-RDP"), -80, 6, 2.5, 50, 2.8, focus=("KC-RDP",), rack_to=("REQ-RDP",)),
    Shot("proof-pullback", "B-03.4", ("KC-RDP", "REQ-RDP"), -80, 8, 3.4, 50, 2.8),
    # S4
    Shot("ad-shoulder", "B-04.1", ("AD",), -124, 8, 11.5, 35, 4.0, bulge=1.5),
    Shot("capsule-chase", "B-04.2", ("REQ-RDP",), -95, 8, 4.6, 35, 4.0, follow=0.35, bulge=6.0),
    Shot("checks-orbit", "B-04.3", ("EVAL-CA1",), -85, 10, 3.4, 35, 2.8),
    Shot("press-stamp", "B-04.4", (PRESS1_OUT,), -100, 8, 3.0, 50, 2.8),
    Shot("card-return", "B-04.5", ("CERT-RDP",), -95, 6, 2.8, 35, 2.8, follow=0.3, bulge=9.0),
    # S5
    Shot("root-crane", "B-05.1", ("ROOT_CA",), -100, 14, 13.0, 28, 4.0, bulge=6.0),
    Shot("flashback-glide", "B-05.2", ("CARTRIDGE",), -100, 12, 6.0, 35, 4.0, follow=0.25, bulge=9.0,
         start=Pose((CA1_MODULE,), -80, 8, 3.2, 35, 4.0)),
    Shot("issuer-link", "B-05.3", ("CERT-CA1", "ROOT_CA"), -105, 18, 24.0, 28, 4.0, focus=("CERT-CA1",),
         start=Pose(("CERT-CA1", "ROOT_CA"), -100, 30, 16.0, 28, 4.0)),
    # S6
    Shot("present-follow", "B-06.1", ("CERT-RDP",), 40, 8, 6.0, 35, 4.0, follow=0.5, bulge=8.0),
    Shot("chain-boom", "B-06.2", (STACK_MID,), 35, 20, 5.0, 35, 2.8),
    Shot("aia-push", "B-06.3", ("AIA-RDP",), 30, 10, 3.6, 50, 2.8, rack_to=((-9.8, -7.4, 1.7),)),
    Shot("checks-crane", "B-06.4", (STACK_MID,), 40, 24, 5.5, 35, 2.8),
    Shot("revocation-pan", "B-06.5", ("CRL-CA1", "CRL-ROOT"), 20, 12, 6.0, 28, 4.0, follow=0.8, bulge=9.0),
    Shot("green-glide", "B-06.6", ("SCREEN-RDP",), 25, 5, 3.4, 35, 2.8, bulge=4.0),
    # S7
    Shot("web-glide", "B-07.1", ("WEB_SERVER",), -115, 10, 6.0, 35, 4.0, bulge=10.0),
    Shot("web-keys", "B-07.2", ("KC-WEB",), -85, 8, 4.5, 50, 2.8, bulge=-1.8),
    Shot("eligibility-wide", "B-07.3", ("AD", (4.0, 10.0, 2.0)), -90, 24, 17.0, 28, 4.0, focus=("AD",)),
    Shot("web-capsule-chase", "B-07.4", ("REQ-WEB",), -95, 8, 4.6, 35, 4.0, follow=0.35, bulge=6.0),
    # S8
    Shot("checks-orbit-2", "B-08.1", ("EVAL-CA2",), -80, 10, 3.4, 35, 2.8),
    Shot("tls-stamp", "B-08.2", ("CERT-WEB",), -95, 6, 3.4, 35, 2.8, follow=0.35, bulge=9.0),
    Shot("same-root", "B-08.3", ("CERT-CA2", "ROOT_CA"), -100, 22, 24.0, 28, 4.0, focus=("CERT-CA2",)),
    # S9
    Shot("browser-arc", "B-09.1", (STACK_MID,), 35, 14, 6.5, 35, 2.8, bulge=6.0),
    Shot("hero", "B-09.2", (WORLD_CENTRE,), -105, 28, 40.0, 24, 5.6, focus=("ROOT_CA",)),
    Shot("close", "B-09.3", (WORLD_CENTRE,), -101, 30, 42.0, 24, 5.6, focus=("ROOT_CA",)),
)

BY_BEAT: dict[str, Shot] = {s.beat: s for s in SHOTS}
