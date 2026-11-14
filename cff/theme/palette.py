"""Central colour language and look parameters (Charter Section 8).

Every colour in the film is a token here. Role colours map one-to-one onto
``cff.story.model.ColourRole``. The eight key role colours (L-07) were tuned with a seeded
hill-climb against CIEDE2000 under normal vision, deuteranopia and protanopia
(Machado et al. 2009, severity 1.0); ``tests/test_palette.py`` and ``python -m tools palette``
re-check them.
"""

from __future__ import annotations

from cff.story.model import ColourRole

# --- role colours (display sRGB hex) -----------------------------------------------------
ROLE_HEX: dict[ColourRole, str] = {
    ColourRole.ROOT: "#FFCB30",  # warm gold
    ColourRole.ISSUING_CA1: "#19D5FF",  # cyan
    ColourRole.ISSUING_CA2: "#8A63FF",  # violet
    ColourRole.REQUEST: "#F7FAFF",  # bright neutral white
    ColourRole.VALIDATED: "#26B985",  # green
    ColourRole.PENDING: "#D95C00",  # amber
    ColourRole.REVOCATION: "#D9A24F",  # restrained amber: a calmer, lighter variant of pending (dE00 >= 11.7 from it, incl. CVD)
    ColourRole.INELIGIBLE: "#8E939C",  # muted grey
    ColourRole.DIRECTORY: "#215C86",  # steel blue
    ColourRole.NEUTRAL: "#4A5568",  # chassis and furniture grey-blue
}

# The 8 key role colours of L-07 (revocation amber is the one allowed close pair).
KEY_ROLES: tuple[ColourRole, ...] = (
    ColourRole.ROOT,
    ColourRole.ISSUING_CA1,
    ColourRole.ISSUING_CA2,
    ColourRole.REQUEST,
    ColourRole.VALIDATED,
    ColourRole.PENDING,
    ColourRole.INELIGIBLE,
    ColourRole.DIRECTORY,
)
L07_MIN_DELTA_E = 15.0
L07_REVOCATION_MIN_DELTA_E = 5.0

# --- world and furniture tokens ----------------------------------------------------------
WORLD_HEX = "#050A14"  # near-black navy environment
FLOOR_HEX = "#0A1424"
GRID_HEX = "#1C3354"
CARD_PALE_HEX = "#C9D4E3"  # the pale self-signed card
TEXT_HEX = "#FFFFFF"  # caption and label text
PLATE_HEX = "#0B1220"  # label plate and caption backing
SKIN_HEX = "#8A93A6"  # stylized figure (no realistic human)
SCREEN_HEX = "#7FB4E8"  # laptop session window
BACKDROP_HEX = "#18263C"  # far rack silhouettes: a step above the floor, far below any role colour
PLATE_OPACITY = 0.92  # caption plates: even over a white background, white text keeps >= 4.5:1 (L-02)
SIGN_PLATE_OPACITY = 1.0  # sign plates are solid while held (they must draw under their blended glyphs)

# Trust links are light, not cable (AR-01, C-01): a gradient from the issuer's colour to the subject CA's colour along
# the link, whose glow channel carries only intensity. Emission stays low enough that AgX keeps the hue (PKI-S1R1-05).
TRUST_LINK_STOPS: dict[str, tuple[ColourRole, ColourRole]] = {
    "gold_to_cyan": (ColourRole.ROOT, ColourRole.ISSUING_CA1),
    "gold_to_violet": (ColourRole.ROOT, ColourRole.ISSUING_CA2),
    "cyan": (ColourRole.ISSUING_CA1, ColourRole.ISSUING_CA1),
    "violet": (ColourRole.ISSUING_CA2, ColourRole.ISSUING_CA2),
}
TRUST_LINK_EMISSION = 1.2  # was 1.8: links read white, not gold-to-cyan/violet, at distance (V1-COL-01)
TRUST_LINK_REST = 0.4  # glow level a link settles to once introduced (it stays readable without dominating later shots)
TRUST_LINK_ARC_FRACTION = 0.12  # a link bows upward by this fraction of its length (a path of light, not a taut wire)
TRUST_LINK_SEGMENTS = 24

# --- glow and light levels ---------------------------------------------------------------
GLOW_OFF = 0.0
GLOW_SOFT = 0.35
GLOW_ACTIVE = 1.0
GLOW_PEAK = 1.6
EMISSION_STRENGTH = 1.8  # emission strength at glow level 1.0 (3.0 -> 2.4: CIN-S1R1-12; 2.4 -> 1.8: role hues held at distance, V1-COL-01)
FLASHBACK_SATURATION = 0.3  # compositor saturation inside the S5 flashback
FLASHBACK_VIGNETTE = 0.55

# World ambient stays far below the key light (C-05: <= 20% of key illuminance at the subject).
WORLD_STRENGTH = 0.02
KEY_LIGHT_POWER_W = 900.0
RIM_LIGHT_POWER_W = 1050.0  # a visible rim on every focal subject (CIN-S1R1-12)
KEY_LIGHT_HEX = "#FFE9D2"
RIM_LIGHT_HEX = "#9CC4FF"
HAZE_HEX = "#9CC4FF"  # v1.2 look (docs/LOOK-PLAN-v1.2.md): haze, horizon glow and pool light tints; never a state colour (C-10)
HORIZON_HEX = "#2B5C9E"
POOL_NEUTRAL_HEX = "#CFE0FF"
POOL_CA1_HEX = "#8CEBFF"
POOL_CA2_HEX = "#C4B1FF"
POOL_ROOT_HEX = "#FFE08A"
AMBIENT_TO_KEY_MAX = 0.20


def role_hex(role: ColourRole) -> str:
    return ROLE_HEX[role]


# V1-CIN-03 step 1: an issuing CA's vault takes its role colour at this HSV value, so the evaluation interiors (B-04.3,
# B-08.1) stop reading as a flat, over-bright box (about 2x the luma of the beats around them).
VAULT_VALUE_SCALE = 0.45
VAULT_DIMMED_ROLES: tuple[ColourRole, ...] = (ColourRole.ISSUING_CA1, ColourRole.ISSUING_CA2)


def value_scaled_hex(hex_colour: str, scale: float) -> str:
    """``hex_colour`` with its HSV value multiplied by ``scale`` (hue and saturation kept)."""
    import colorsys  # noqa: PLC0415

    r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v * scale)
    return "#" + "".join(f"{round(c * 255):02X}" for c in (r2, g2, b2))
