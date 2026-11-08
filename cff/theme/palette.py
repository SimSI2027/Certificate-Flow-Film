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
PLATE_OPACITY = 0.92  # label and caption plates: even over a white background, white text keeps >= 4.5:1 (L-02)

# Trust links are light, not cable (AR-01, C-01): a gradient from the issuer's colour to the subject CA's colour along
# the link, whose glow channel carries only intensity. Emission stays low enough that AgX keeps the hue (PKI-S1R1-05).
TRUST_LINK_STOPS: dict[str, tuple[ColourRole, ColourRole]] = {
    "gold_to_cyan": (ColourRole.ROOT, ColourRole.ISSUING_CA1),
    "gold_to_violet": (ColourRole.ROOT, ColourRole.ISSUING_CA2),
    "cyan": (ColourRole.ISSUING_CA1, ColourRole.ISSUING_CA1),
    "violet": (ColourRole.ISSUING_CA2, ColourRole.ISSUING_CA2),
}
TRUST_LINK_EMISSION = 1.8
TRUST_LINK_REST = 0.4  # glow level a link settles to once introduced (it stays readable without dominating later shots)
TRUST_LINK_ARC_FRACTION = 0.12  # a link bows upward by this fraction of its length (a path of light, not a taut wire)
TRUST_LINK_SEGMENTS = 24

# --- glow and light levels ---------------------------------------------------------------
GLOW_OFF = 0.0
GLOW_SOFT = 0.35
GLOW_ACTIVE = 1.0
GLOW_PEAK = 1.6
EMISSION_STRENGTH = 2.4  # emission strength at glow level 1.0 (lowered from 3.0: less emissive wash, CIN-S1R1-12)
FLASHBACK_SATURATION = 0.3  # compositor saturation inside the S5 flashback
FLASHBACK_VIGNETTE = 0.55

# World ambient stays far below the key light (C-05: <= 20% of key illuminance at the subject).
WORLD_STRENGTH = 0.02
KEY_LIGHT_POWER_W = 900.0
RIM_LIGHT_POWER_W = 1050.0  # a visible rim on every focal subject (CIN-S1R1-12)
KEY_LIGHT_HEX = "#FFE9D2"
RIM_LIGHT_HEX = "#9CC4FF"
AMBIENT_TO_KEY_MAX = 0.20


def role_hex(role: ColourRole) -> str:
    return ROLE_HEX[role]
