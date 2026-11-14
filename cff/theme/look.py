"""Look constants for the v1.2 materials and lighting pass (docs/LOOK-PLAN-v1.2.md). Colours live in cff.theme.palette."""

from __future__ import annotations

from cff.stage import layout as lo
from cff.stage.layout import Vec3

# Haze: a thin world volume. Only tiers with ``volumetrics`` get it.
HAZE_DENSITY = 0.004
HAZE_DENSITY_MIN, HAZE_DENSITY_MAX, HAZE_DENSITY_STEP = 0.0025, 0.006, 0.0005
HAZE_ANISOTROPY = 0.4
VOLUME_START_M, VOLUME_END_M = 0.5, 150.0
VOLUME_TILE_SIZE = "4"
VOLUME_SAMPLES = 96
VOLUME_SAMPLE_DISTRIBUTION = 0.8
VOLUME_RAY_DEPTH = 8

# Horizon glow: seen by the camera only, so the ambient light on the stage does not change (C-05).
HORIZON_STRENGTH = 1.2
HORIZON_POWER = 6.0

# Key and rim: softer shadows, weaker floor highlights, a soft glow in the haze instead of a hard dot.
KEY_RADIUS_M = 1.5
RIM_RADIUS_M = 4.0
KEY_SPECULAR = 0.2
RIM_SPECULAR = 0.2

# Pool lights: one static spot above each actor. They never animate.
POOL_HEIGHT_M = 12.0
POOL_OFFSET_Y_M = -1.5
POOL_CONE_DEG = 50.0
POOL_BLEND = 0.7
POOL_RADIUS_M = 0.5
POOL_WATTS = 4000.0
POOL_SPECULAR = 0.3
POOLS: tuple[tuple[str, Vec3, str, float], ...] = (  # name, actor anchor, palette token name, relative power
    ("client", lo.CLIENT, "POOL_NEUTRAL_HEX", 1.0),
    ("rdp", lo.RDP, "POOL_NEUTRAL_HEX", 1.0),
    ("web", lo.WEB, "POOL_NEUTRAL_HEX", 1.0),
    ("ad", lo.AD, "RIM_LIGHT_HEX", 0.8),
    ("ca1", lo.CA1, "POOL_CA1_HEX", 1.6),
    ("ca2", lo.CA2, "POOL_CA2_HEX", 1.6),
    ("root", lo.ROOT, "POOL_ROOT_HEX", 3.0),
)

# Materials.
NEUTRAL_METALLIC = 0.35
NEUTRAL_ROUGHNESS = 0.45
ROLE_ROUGHNESS = 0.4
BACKDROP_METALLIC = 0.6
BACKDROP_ROUGHNESS = 0.5
FLOOR_ROUGHNESS = 0.4

# Compositor bloom (final and preview tiers).
BLOOM_THRESHOLD = 0.8
BLOOM_STRENGTH = 0.6
