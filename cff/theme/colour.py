"""Colour maths for the L-07 palette checks (pure Python, no bpy).

sRGB <-> linear <-> CIE Lab, CIEDE2000 (Sharma, Wu and Dalal 2005 reference form),
Machado, Oliveira and Fernandes (2009) colour-vision-deficiency simulation at severity 1.0,
and WCAG 2.x contrast (used by L-02).
"""

from __future__ import annotations

import math

Rgb = tuple[float, float, float]
Matrix3 = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]

# Machado et al. 2009, severity 1.0, applied to LINEAR sRGB.
MACHADO_PROTANOPIA: Matrix3 = (
    (0.152286, 1.052583, -0.204868),
    (0.114503, 0.786281, 0.099216),
    (-0.003882, -0.048116, 1.051998),
)
MACHADO_DEUTERANOPIA: Matrix3 = (
    (0.367322, 0.860646, -0.227968),
    (0.280085, 0.672501, 0.047413),
    (-0.011820, 0.042940, 0.968881),
)
CVD_CONDITIONS: dict[str, Matrix3 | None] = {
    "normal": None,
    "deuteranopia": MACHADO_DEUTERANOPIA,
    "protanopia": MACHADO_PROTANOPIA,
}

# D65 white point and the sRGB -> XYZ matrix.
_WHITE = (0.95047, 1.0, 1.08883)
_SRGB_TO_XYZ: Matrix3 = (
    (0.4124564, 0.3575761, 0.1804375),
    (0.2126729, 0.7151522, 0.0721750),
    (0.0193339, 0.1191920, 0.9503041),
)
_SRGB_THRESHOLD = 0.04045
_LINEAR_THRESHOLD = 0.0031308
_LAB_EPSILON = 216 / 24389
_LAB_KAPPA = 24389 / 27


def hex_to_rgb(value: str) -> Rgb:
    """'#RRGGBB' -> sRGB floats in 0..1."""
    text = value.lstrip("#")
    if len(text) != 6:
        raise ValueError(f"expected #RRGGBB, got {value!r}")
    return (int(text[0:2], 16) / 255, int(text[2:4], 16) / 255, int(text[4:6], 16) / 255)


def srgb_to_linear(channel: float) -> float:
    if channel <= _SRGB_THRESHOLD:
        return channel / 12.92
    return float(((channel + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(channel: float) -> float:
    clipped = min(1.0, max(0.0, channel))
    if clipped <= _LINEAR_THRESHOLD:
        return clipped * 12.92
    return float(1.055 * clipped ** (1 / 2.4) - 0.055)


def rgb_to_linear(rgb: Rgb) -> Rgb:
    return (srgb_to_linear(rgb[0]), srgb_to_linear(rgb[1]), srgb_to_linear(rgb[2]))


def _mul(matrix: Matrix3, vec: Rgb) -> Rgb:
    return (
        matrix[0][0] * vec[0] + matrix[0][1] * vec[1] + matrix[0][2] * vec[2],
        matrix[1][0] * vec[0] + matrix[1][1] * vec[1] + matrix[1][2] * vec[2],
        matrix[2][0] * vec[0] + matrix[2][1] * vec[1] + matrix[2][2] * vec[2],
    )


def simulate_cvd(rgb: Rgb, matrix: Matrix3 | None) -> Rgb:
    """Apply a CVD matrix in linear light and return display sRGB."""
    if matrix is None:
        return rgb
    lin = _mul(matrix, rgb_to_linear(rgb))
    return (linear_to_srgb(lin[0]), linear_to_srgb(lin[1]), linear_to_srgb(lin[2]))


def _lab_f(t: float) -> float:
    return t ** (1 / 3) if t > _LAB_EPSILON else (_LAB_KAPPA * t + 16) / 116


def rgb_to_lab(rgb: Rgb) -> Rgb:
    x, y, z = _mul(_SRGB_TO_XYZ, rgb_to_linear(rgb))
    fx, fy, fz = _lab_f(x / _WHITE[0]), _lab_f(y / _WHITE[1]), _lab_f(z / _WHITE[2])
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e_2000(lab1: Rgb, lab2: Rgb) -> float:
    """CIEDE2000 colour difference (kL = kC = kH = 1)."""
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    c_bar7 = ((c1 + c2) / 2) ** 7
    g = 0.5 * (1 - math.sqrt(c_bar7 / (c_bar7 + 25**7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (b1 or a1p) else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (b2 or a2p) else 0.0
    d_lp, d_cp = l2 - l1, c2p - c1p
    if c1p * c2p == 0:
        d_hp = 0.0
    else:
        diff = h2p - h1p
        d_hp = diff - 360 if diff > 180 else diff + 360 if diff < -180 else diff
    d_hp_term = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(d_hp / 2))
    l_bar, c_bar = (l1 + l2) / 2, (c1p + c2p) / 2
    if c1p * c2p == 0:
        h_bar = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        h_bar = (h1p + h2p) / 2
    else:
        h_bar = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    t = (
        1
        - 0.17 * math.cos(math.radians(h_bar - 30))
        + 0.24 * math.cos(math.radians(2 * h_bar))
        + 0.32 * math.cos(math.radians(3 * h_bar + 6))
        - 0.20 * math.cos(math.radians(4 * h_bar - 63))
    )
    d_theta = 30 * math.exp(-(((h_bar - 275) / 25) ** 2))
    r_c = 2 * math.sqrt(c_bar**7 / (c_bar**7 + 25**7))
    s_l = 1 + 0.015 * (l_bar - 50) ** 2 / math.sqrt(20 + (l_bar - 50) ** 2)
    s_c = 1 + 0.045 * c_bar
    s_h = 1 + 0.015 * c_bar * t
    r_t = -math.sin(math.radians(2 * d_theta)) * r_c
    return math.sqrt(
        (d_lp / s_l) ** 2 + (d_cp / s_c) ** 2 + (d_hp_term / s_h) ** 2 + r_t * (d_cp / s_c) * (d_hp_term / s_h)
    )


def relative_luminance(rgb: Rgb) -> float:
    """WCAG 2.x relative luminance of display sRGB."""
    r, g, b = rgb_to_linear(rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(lum_a: float, lum_b: float) -> float:
    """WCAG 2.x contrast between two relative luminances."""
    hi, lo = max(lum_a, lum_b), min(lum_a, lum_b)
    return (hi + 0.05) / (lo + 0.05)
