"""World layout (metres, Z up). Topology follows docs/STORYBOARD.md "World blocking"; distances are tuned here.

Actors face -Y (their fronts toward the viewer's side of the stage). The client sits south-west;
the two servers are in the middle; the AD node stands beside both servers' outbound ports;
the issuing CAs are further north; the root is on its own dais at the far end.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

Vec3 = tuple[float, float, float]
Seq3 = Sequence[float]  # any 3-sequence; keyframe values arrive as variable-length tuples


def add(a: Seq3, b: Seq3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Seq3, b: Seq3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a: Seq3, k: float) -> Vec3:
    return (a[0] * k, a[1] * k, a[2] * k)


def lerp(a: Seq3, b: Seq3, t: float) -> Vec3:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def dist(a: Seq3, b: Seq3) -> float:
    return math.dist(a, b)


def length(a: Seq3) -> float:
    return math.hypot(a[0], a[1], a[2])


def at_z(point: Vec3, z: float) -> Vec3:
    return (point[0], point[1], z)


def aim_x(start: Vec3, end: Vec3) -> Vec3:
    """XYZ Euler (degrees) that points the local +X axis from ``start`` toward ``end``."""
    dx, dy, dz = end[0] - start[0], end[1] - start[1], end[2] - start[2]
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = -math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return (0.0, pitch, yaw)


def aim_z(start: Vec3, end: Vec3) -> Vec3:
    """XYZ Euler (degrees) that points the local +Z axis from ``start`` toward ``end``."""
    dx, dy, dz = end[0] - start[0], end[1] - start[1], end[2] - start[2]
    total = math.sqrt(dx * dx + dy * dy + dz * dz)
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, dz / total))))
    return (0.0, tilt, math.degrees(math.atan2(dy, dx)))


# --- actor anchors -------------------------------------------------------------------------
CLIENT: Vec3 = (-12.0, -8.0, 0.0)
# V4: a realistic seated adult reaches about 0.45 m past the desk edge (x -11.1), so the laptop sits near the edge and the user's
# chair is pulled in; at the desk centre (x -12.0) the keyboard was 1.6 m from the user, out of any human reach.
LAPTOP: Vec3 = (-11.42, -8.0, 0.78)  # base centre; the screen faces +X
LAPTOP_LID_X_OFFSET = -0.2  # the idle screen glow sits on the lid, behind the base centre
USER: Vec3 = (-10.9, -8.0, 0.0)  # the chair; seated east of the laptop, facing west
RDP: Vec3 = (0.0, 0.0, 0.0)
WEB: Vec3 = (9.0, 2.0, 0.0)
AD: Vec3 = (4.0, 6.0, 0.0)
CA1: Vec3 = (-3.0, 14.0, 0.0)
CA2: Vec3 = (11.0, 14.0, 0.0)
ROOT: Vec3 = (4.0, 22.0, 0.0)  # plinth centre; the dais is at z = ROOT_DAIS_Z

# Backdrop (C-04, CIN-S1R1-13): a far ring of rack silhouettes, so wide shots have a background layer instead of a void.
# Set dressing only: no story role, no labels, never lit by a glow channel. Heights come from random.Random(BACKDROP_SEED).
BACKDROP_CENTRE: Vec3 = (2.0, 10.0, 0.0)
BACKDROP_RADIUS_M = 62.0
BACKDROP_COUNT = 56
BACKDROP_SEED = 20261107
BACKDROP_RACK_SIZE: Vec3 = (2.4, 1.2, 5.0)  # width, depth, base height (each rack is 0.7-1.6 x this tall)
KIOSK: Vec3 = (-8.0, 4.0, 0.0)

# --- sizes -----------------------------------------------------------------------------------
CHASSIS_SIZE: Vec3 = (1.4, 1.0, 2.2)
CA_VAULT_SIZE: Vec3 = (4.0, 3.2, 2.8)
AD_RADIUS = 0.8
AD_HEIGHT = 3.4
ROOT_DAIS_Z = 1.5
ROOT_PLINTH_SIZE: Vec3 = (2.4, 2.4, 4.5)
ROOT_VAULT_SIZE: Vec3 = (3.0, 2.4, 2.4)
ROOT_VAULT_Z = ROOT_DAIS_Z + ROOT_PLINTH_SIZE[2]  # underside of the vault
ROOT_DAIS_RADIUS = 5.0
CARD_SIZE: Vec3 = (0.7, 0.03, 0.45)  # width, thickness, height (card plane faces -Y)
CAPSULE_LENGTH = 0.38
CAPSULE_RADIUS = 0.1
KEY_SIZE = 0.26

# --- rack-relative anchors (add to RDP or WEB) ----------------------------------------------
FRONT_Y = -0.5  # chassis front face
LISTENER_PORT: Vec3 = (0.0, FRONT_Y - 0.03, 1.6)
TOP_PLATE: Vec3 = (0.0, 0.0, CHASSIS_SIZE[2] + 0.12)
KEY_FORM_PRIV: Vec3 = (-0.05, 0.0, 1.45)
KEY_FORM_PUB: Vec3 = (0.40, 0.0, 1.45)
CONTAINER: Vec3 = (-0.30, 0.10, 0.95)
CAPSULE_SPOT: Vec3 = (0.25, 0.10, 1.6)
CERT_SLOT: Vec3 = (0.30, 0.10, 0.95)
INTERMEDIATE_SLOT: Vec3 = (0.30, 0.10, 0.50)
RDP_PORT_SIDE = 1.0  # the RDP server's outbound port is on its +X face; the web server's on its -X face
WEB_PORT_SIDE = -1.0
PORT_Z = 1.3
PORT_OUT_DISTANCE = 0.38  # how far outside the chassis a waiting capsule hovers


def rel(base: Vec3, offset: Vec3) -> Vec3:
    return add(base, offset)


def port_surface(base: Vec3, side: float) -> Vec3:
    return (base[0] + side * (CHASSIS_SIZE[0] / 2), base[1], PORT_Z)


def port_wait(base: Vec3, side: float) -> Vec3:
    return (base[0] + side * (CHASSIS_SIZE[0] / 2 + PORT_OUT_DISTANCE), base[1], PORT_Z)


# --- network channels (floor conduits) and CA routes ----------------------------------------
FLOOR_Z = 0.06
CHANNEL_RDP: tuple[Vec3, ...] = (
    (-11.2, -7.0, FLOOR_Z),
    (-6.0, -4.8, FLOOR_Z),
    (-2.4, -3.0, FLOOR_Z),
    (0.0, -1.7, FLOOR_Z),
)
CHANNEL_WEB: tuple[Vec3, ...] = (
    (-11.2, -9.3, FLOOR_Z),
    (-6.0, -9.6, FLOOR_Z),
    (5.5, -8.8, FLOOR_Z),
    (9.0, -5.5, FLOOR_Z),
    (9.0, 0.9, FLOOR_Z),
)
ROUTE_CA1: tuple[Vec3, ...] = (
    (1.3, 0.0, FLOOR_Z),
    (0.2, 3.0, FLOOR_Z),
    (-1.8, 8.5, FLOOR_Z),
    (-3.0, 12.0, FLOOR_Z),
)
ROUTE_CA2: tuple[Vec3, ...] = (
    (7.7, 2.0, FLOOR_Z),
    (8.6, 6.0, FLOOR_Z),
    (10.0, 9.5, FLOOR_Z),
    (11.0, 12.0, FLOOR_Z),
)


def polyline_length(points: Sequence[Seq3]) -> float:
    return sum(dist(a, b) for a, b in zip(points, points[1:], strict=False))


def point_along(points: Sequence[Seq3], fraction: float) -> Vec3:
    """Point at a fraction (0..1) of the arc length of a polyline."""
    total = polyline_length(points)
    target = max(0.0, min(1.0, fraction)) * total
    walked = 0.0
    for a, b in zip(points, points[1:], strict=False):
        seg = dist(a, b)
        if walked + seg >= target and seg > 0:
            return lerp(a, b, (target - walked) / seg)
        walked += seg
    last = points[-1]
    return (last[0], last[1], last[2])


def reverse(points: tuple[Vec3, ...]) -> tuple[Vec3, ...]:
    return tuple(reversed(points))


# --- CA vault interiors (relative to the vault centre) --------------------------------------
CA_FRONT_Y = -CA_VAULT_SIZE[1] / 2  # open front
CA_CRADLE: Vec3 = (0.0, -0.9, 0.9)  # evaluation cradle
CA_MODULE: Vec3 = (-1.1, 0.7, 1.0)  # sealed key module
CA_PRESS: Vec3 = (1.0, 0.5, 1.0)
CA_PRESS_OUT: Vec3 = (1.0, -0.2, 0.9)  # where the stamped card appears
CA_CROWN: Vec3 = (0.0, 0.0, CA_VAULT_SIZE[2] + 0.45)

# --- root complex (absolute) -------------------------------------------------------------------
ROOT_VAULT_CENTRE: Vec3 = (ROOT[0], ROOT[1], ROOT_VAULT_Z + ROOT_VAULT_SIZE[2] / 2)
ROOT_SEAL: Vec3 = (ROOT[0], ROOT[1] - ROOT_VAULT_SIZE[1] / 2 - 0.02, ROOT_VAULT_CENTRE[2])
ROOT_READER: Vec3 = (ROOT[0] - 1.9, ROOT[1] - 2.6, ROOT_DAIS_Z + 0.55)
ROOT_PRESS: Vec3 = (ROOT[0], ROOT[1] - 2.6, ROOT_DAIS_Z + 0.55)
ROOT_MODULE: Vec3 = (ROOT[0] + 1.9, ROOT[1] - 2.6, ROOT_DAIS_Z + 0.45)
FOOTPRINT_COUNT = 8
WALKWAY: tuple[Vec3, ...] = (  # the footprint trail from Issuing CA 1's vault, up the dais edge, to the reader bay
    (-1.4, 12.4, 0.0),
    (-0.4, 14.6, 0.0),
    (0.6, 16.4, 0.0),
    (1.3, 17.6, ROOT_DAIS_Z + 0.02),
    (2.0, 18.6, ROOT_DAIS_Z + 0.02),
)

# --- client cluster ------------------------------------------------------------------------------
STACK_X_Y: tuple[float, float] = (-11.0, -7.4)
CRADLE_ROOT: Vec3 = (STACK_X_Y[0], STACK_X_Y[1], 2.55)
STACK_CERT: Vec3 = (STACK_X_Y[0], STACK_X_Y[1], 1.25)
STACK_INTERMEDIATE: Vec3 = (STACK_X_Y[0], STACK_X_Y[1], 1.9)
CHECK_LIST: Vec3 = (-9.5, -7.4, 1.0)  # first row of the validation list
CHECK_ROW_STEP = 0.36
HOVER_UNVERIFIED: Vec3 = (-10.5, -7.0, 1.7)
SCREEN_CENTRE: Vec3 = (-11.55, -8.0, 1.25)
HUD_DISTANCE = 3.0
