"""The camera-following key and rim lights, planned in pure Python. ``blender/lighting.py`` keys exactly these positions.

The key stands off to the camera's upper left; the rim sits behind the subject, on the far side (C-05). Neither may sit
inside an actor's solid body: a light inside a tower or a plinth is cut off in one frame when it crosses the surface, which
showed as single-frame luma pops of 8.0 at f746 (inside the AD tower) and 10.6 at f1376 (inside the root plinth), finding
L2-CIN-01. ``keep_out`` pushes a light radially out of each solid's keep-out cylinder before it is keyed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cff.stage import layout as lo
from cff.stage.camera import CamState
from cff.stage.layout import Vec3
from cff.theme import look

REFERENCE_DISTANCE_M = 4.0
DISTANCE_CLAMP_M = (3.0, 46.0)
KEY_OFFSET = (-0.30, 0.35)  # (right, up) in camera distances
RIM_OFFSET = (0.35, 0.40)
RIM_BEHIND = 0.85


@dataclass(frozen=True)
class Solid:
    """A vertical keep-out cylinder round an actor's solid body: no rig light below ``top`` + clearance within ``radius``."""

    name: str
    centre: tuple[float, float]
    radius: float
    top: float


def _half_diagonal(width: float, depth: float) -> float:
    return math.hypot(width, depth) / 2


SOLIDS: tuple[Solid, ...] = tuple(
    Solid(name, (anchor[0], anchor[1]), body + look.RIG_KEEP_OUT_MARGIN_M, top)
    for name, anchor, body, top in (
        ("desk", lo.CLIENT, _half_diagonal(1.8, 1.2), 0.76),
        ("rdp", lo.RDP, _half_diagonal(lo.CHASSIS_SIZE[0], lo.CHASSIS_SIZE[1]), lo.TOP_PLATE[2]),
        ("web", lo.WEB, _half_diagonal(lo.CHASSIS_SIZE[0], lo.CHASSIS_SIZE[1]), lo.TOP_PLATE[2]),
        ("ad", lo.AD, lo.AD_RADIUS, lo.AD_HEIGHT),  # the 0.35 m cap is inside RIG_KEEP_OUT_ABOVE_M
        ("ca1", lo.CA1, _half_diagonal(lo.CA_VAULT_SIZE[0], lo.CA_VAULT_SIZE[1]), lo.CA_CROWN[2]),
        ("ca2", lo.CA2, _half_diagonal(lo.CA_VAULT_SIZE[0], lo.CA_VAULT_SIZE[1]), lo.CA_CROWN[2]),
        ("root", lo.ROOT, _half_diagonal(lo.ROOT_VAULT_SIZE[0], lo.ROOT_VAULT_SIZE[1]), lo.ROOT_VAULT_Z + lo.ROOT_VAULT_SIZE[2]),
        ("root-dais", lo.ROOT, lo.ROOT_DAIS_RADIUS, lo.ROOT_DAIS_Z),
    )
)


def inside(point: Vec3, solid: Solid) -> bool:
    return math.hypot(point[0] - solid.centre[0], point[1] - solid.centre[1]) < solid.radius and point[2] < solid.top + look.RIG_KEEP_OUT_ABOVE_M


def clearance(x: float, y: float, solid: Solid) -> float:
    """The lowest height a rig light may have at (x, y) for ``solid``: its top plus the clearance inside the cylinder, falling
    linearly to nothing over ``RIG_KEEP_OUT_RAMP_M`` outside it."""
    d = math.hypot(x - solid.centre[0], y - solid.centre[1])
    ramp = look.RIG_KEEP_OUT_RAMP_M
    weight = 1.0 if d <= solid.radius else max(0.0, 1.0 - (d - solid.radius) / ramp)
    return (solid.top + look.RIG_KEEP_OUT_ABOVE_M) * weight


def keep_out(point: Vec3) -> Vec3:
    """``point`` lifted over every keep-out cylinder it lies in or near.

    A lift, not a sideways push: a radial push swings a light round the axis when its path passes near it (2.4 m in one
    frame at f1372), and pushing along the view direction jumps by a chord length where the path enters. The required
    height is a continuous function of (x, y), so a smooth camera move gives a smooth light path.
    """
    x, y, z = point
    return (x, y, max([z, *(clearance(x, y, s) for s in SOLIDS)]))


def _ramp(value: float) -> float:
    return max(0.0, min(1.0, value / look.RIG_KEEP_OUT_RAMP_M))


def unblock(camera: Vec3, subject: Vec3, light: Vec3) -> Vec3:
    """``light`` lifted until the camera's line to it clears the top of every solid that stands beyond the subject.

    The rim's haze glow sat low behind the root tower and came out from behind it in one frame (f1535, step 6.7; L2-CIN-01).
    A solid that holds the subject (an interior) is not lifted over: there the rim is meant to be behind the subject. The
    weights fall linearly with the solid's distance from the line and with how far beyond the subject it stands, so the
    lift is continuous.
    """
    vx, vy = light[0] - camera[0], light[1] - camera[1]
    span = math.hypot(vx, vy)
    if span < 1e-6:
        return light
    ux, uy = vx / span, vy / span
    beyond_subject = (subject[0] - camera[0]) * ux + (subject[1] - camera[1]) * uy  # metres along the line
    z = light[2]
    for solid in SOLIDS:
        along = (solid.centre[0] - camera[0]) * ux + (solid.centre[1] - camera[1]) * uy
        if along <= beyond_subject or along >= span:
            continue  # only a solid between the subject and the light can hide the light
        off = math.hypot(camera[0] + ux * along - solid.centre[0], camera[1] + uy * along - solid.centre[1])
        holds_subject = 1.0 - _ramp(math.hypot(subject[0] - solid.centre[0], subject[1] - solid.centre[1]) - solid.radius)
        weight = _ramp(along - beyond_subject) * _ramp(span - along) * (1.0 - holds_subject) * (1.0 if off <= solid.radius else 1.0 - _ramp(off - solid.radius))
        if weight <= 0.0:
            continue
        s = along / span
        needed = camera[2] + (solid.top + look.RIG_KEEP_OUT_ABOVE_M - camera[2]) / s
        z = max(z, light[2] + weight * max(0.0, needed - light[2]))
    return (light[0], light[1], z)


@dataclass(frozen=True)
class RigFrame:
    key: Vec3
    rim: Vec3
    distance: float  # the clamped camera distance that scales power and spot size

    @property
    def power_scale(self) -> float:
        return (self.distance / REFERENCE_DISTANCE_M) ** 2


def raw_positions(state: CamState) -> tuple[Vec3, Vec3, float]:
    """Key and rim positions before the keep-out, and the clamped camera distance."""
    position = state.position
    forward = lo.sub(state.look, position)
    distance = min(max(lo.length(forward), DISTANCE_CLAMP_M[0]), DISTANCE_CLAMP_M[1])
    unit = lo.mul(forward, 1.0 / max(lo.length(forward), 1e-6))
    right = (unit[1], -unit[0], 0.0)
    norm = math.hypot(right[0], right[1]) or 1.0
    right = (right[0] / norm, right[1] / norm, 0.0)
    up = (0.0, 0.0, 1.0)
    key_pos = lo.add(position, lo.add(lo.mul(right, KEY_OFFSET[0] * distance), lo.mul(up, KEY_OFFSET[1] * distance)))
    rim_pos = lo.add(state.look, lo.add(lo.mul(unit, RIM_BEHIND * distance), lo.add(lo.mul(right, RIM_OFFSET[0] * distance), lo.mul(up, RIM_OFFSET[1] * distance))))
    return key_pos, rim_pos, distance


def rig_frame(state: CamState) -> RigFrame:
    key_pos, rim_pos, distance = raw_positions(state)
    return RigFrame(keep_out(key_pos), unblock(state.position, state.look, keep_out(rim_pos)), distance)
