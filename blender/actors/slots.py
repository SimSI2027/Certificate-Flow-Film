"""Material slots of the detailed hardware meshes (V5a). Slot 0 is always the object's stage material: it carries the glow
channel (``Object Info > Color``) and the role colour, so every PKI signal still lights the parts that carry it. The other slots
are static physical finishes (``blender.finishes``); a builder puts faces in a slot with ``primitives.slot``."""

from __future__ import annotations

SIGNAL = 0
STEEL = 1
STEEL_LIGHT = 2
BEZEL = 3
CADDY = 4
VENT = 5
ALUMINIUM = 6
PERFORATED = 7
LED = 8
ACCENT_LED = 9
GLASS = 10
CABLE = 11
CONCRETE = 12
TILE = 13
DESK = 14
FABRIC = 15
UI_TITLE = 16
UI_DESKTOP = 17
UI_TASKBAR = 18
UI_ICON = 19

# V5b: the PKI symbol meshes (``cff.stage.icons``) use their own, shorter slot list: slot 0 is the stage material as above.
ICON_INK = 1  # the symbol's ink strokes (palette.ICON_INK_HEX, static, never a state colour)
ICON_SEAL = 2  # a card's seal disc in its issuer's role colour (stage material, so it takes the glow channel)
ICON_NAMES: tuple[str, ...] = ("signal", "ink", "seal")

NAMES: tuple[str, ...] = (
    "signal", "steel", "steel_light", "bezel", "caddy", "vent", "aluminium", "perforated", "led", "accent_led", "glass", "cable",
    "concrete", "tile", "desk", "fabric", "ui_title", "ui_desktop", "ui_taskbar", "ui_icon",
)
