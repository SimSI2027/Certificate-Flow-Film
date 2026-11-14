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
# L2-CIN-01: the camera-following key and rim never sit inside an actor's body, and the rim is lifted over a solid that stands
# between the subject and it (cff.stage.rig). Each keep-out cylinder is the actor's footprint half-diagonal plus this margin, up
# to the actor's top plus the clearance. Per actor, not the ledger's single 3.5 m radius: that would also catch the camera-side
# key in the 14-24 s server close-ups.
RIG_KEEP_OUT_MARGIN_M = 0.5
RIG_KEEP_OUT_ABOVE_M = 1.0
RIG_KEEP_OUT_RAMP_M = 4.0  # outside the cylinder the lift falls linearly to nothing over this distance (a continuous light path)

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

# v1.3 interiors (blender/dressing.py): static set dressing inside the server chassis and the CA vaults, so the 14-24 s, 29-36 s,
# 73-76 s and 82-90 s close-ups read as machines, not grey boxes. Practical light strips motivate a soft ceiling key and, in the
# chassis, a cool back rim. Colours are existing tokens (pale pool tints and the rim blue), never a state colour (C-10).
# Nothing here animates. Powers are Blender watts for area lights.
CHASSIS_RIB_COUNT = 8
CHASSIS_RIB_Z = (0.3, 2.0)
# Emitters stay dim, so the practicals read as detail and the area lights carry the interior light. V3-CIN-01: the interior pops
# of the first v1.3 render (f477 5.0, f595 4.3, f600 4.4) were first blamed on these emitters (lamp 3.0, strips 0.8, LEDs 2.5); the
# next render popped at other frames (f671, f705, f719). The cause is shadow-pool overflow, fixed in blender/dressing.py.
CHASSIS_STRIP_EMISSION = 0.5
CHASSIS_LAMP_EMISSION = 1.0
CHASSIS_LED_COUNT = 5
CHASSIS_LED_EMISSION = 1.5
CHASSIS_TOP_W = 3.0
CHASSIS_RIM_W = 1.0
CHASSIS_ROUGHNESS_RANGE = (0.3, 0.6)  # brushed-metal variation on the chassis shell (noise-driven)
CHASSIS_NOISE_SCALE = 18.0
VAULT_RIB_COUNT = 6
VAULT_STRIP_EMISSION = 0.6
VAULT_TOP_W = 12.0

# Film grain at encode (tiers with ``grain``): temporal noise on the beauty layer only; captions and signs stay clean. Fixed seed, so the encode is deterministic.
GRAIN_STRENGTH = 3
GRAIN_STRENGTH_FALLBACK = 2  # if the Final MP4 exceeds GRAIN_MAX_MP4_MB at the first strength
GRAIN_MAX_MP4_MB = 120
GRAIN_SEED = 5201

# Compositor bloom (final and preview tiers).
BLOOM_THRESHOLD = 0.8
BLOOM_STRENGTH = 0.6
