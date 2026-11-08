"""Type: fonts, measured cap-height ratios and the caption and sign sizes (L-01, L-03, L-05).

Cap ratios are measured, not assumed: the height of the evaluated 'H' glyph mesh per unit of Blender font size,
for the fonts bundled with Blender 5.2 (``blender/checks/scene_checks.py: check_fonts`` re-measures them on every
verify, so a different build cannot silently change text sizes). Stage 1 round 1 found the old assumed ratio (0.72)
made every caption and label about 30% smaller than planned (LEG-S1R1-03).
"""

from __future__ import annotations

LABEL_FONT = "DejaVuSansMono.woff2"  # in-world names: monospace with a distinct 1, I and 0
CAPTION_FONT = "Inter.woff2"  # captions: proportional, narrow enough for the longest line

CAP_RATIO: dict[str, float] = {CAPTION_FONT: 0.5087, LABEL_FONT: 0.5198}  # cap height / font size
CAP_RATIO_TOLERANCE = 0.01
MONO_ADVANCE_EM = 0.4276  # DejaVu Sans Mono advance per character, in Blender font sizes (measured: 36 characters span 15.39)
INTER_MEAN_ADVANCE_EM = 0.38  # upper bound of Inter's mean advance per character of caption text (measured 0.324 on CAP-S6a)
SIGN_TEXT_HEIGHT_CAPS = 1.45  # ascender-to-descender height of a sign line, in cap heights (measured 'Hg': 0.673 size = 1.30 caps)


def em_per_cap(font: str) -> float:
    """Blender font size per unit of cap height."""
    return 1.0 / CAP_RATIO[font]


# --- frame geometry at the 1080p reference --------------------------------------------------------------------------------------------
FRAME_W_PX = 1920.0
FRAME_H_PX = 1080.0
TITLE_SAFE_PX = (96.0, 54.0, 1824.0, 1026.0)  # x0, y0, x1, y1 (L-03)

# --- captions -------------------------------------------------------------------------------------------------------------------------
CAPTION_CAP_PX = 34.0  # >= 30 px at 1080p (L-01), measured from the glyphs
TITLE_CAP_PX = 52.0
CAPTION_CENTRE_Y_PX = 950.0  # bottom band: distance from the top of the frame (the plate and its rise stay inside title-safe)
CAPTION_TOP_CENTRE_Y_PX = 128.0  # top band, used when the focal subject would sit under the bottom band (L-05)
CAPTION_PLATE_MARGIN_PX = 34.0
CAPTION_PLATE_HEIGHT_PX = CAPTION_CAP_PX * (1.0 / CAP_RATIO[CAPTION_FONT]) + 1.4 * CAPTION_PLATE_MARGIN_PX
CAPTION_BAND_CLEARANCE_PX = 12.0  # signs keep this far from a visible caption plate

# --- signs (in-world labels) ----------------------------------------------------------------------------------------------------------
SIGN_CAP_PX = 22.0  # every sign is held at this cap height on screen (>= 18 px at 1080p, L-01)
SIGN_PLATE_MARGIN_CAPS = 0.45  # plate padding around the text, in cap heights
SIGN_GAP_PX = 6.0  # minimum gap between two visible sign plates (also the gap between the lines of a list)
SIGN_MAX_NUDGE_PX = 420.0  # a sign (or a list) may be moved this far to fit inside title-safe; farther, it fades out
SIGN_NEAR_M = 1.2  # a sign nearer the lens than this fades out (CIN-S1R1-01)
SIGN_DEPTH_FACTOR = 2.5  # a persistent name farther than this x the focus distance is not shown (unless it must be read now)
SIGN_SAFE_MARGIN_PX = 4.0  # signs keep this far inside title-safe
SIGN_MIN_RUN_FRAMES = 12  # a sign is never shown or hidden for less than this (no flicker)


def sign_plate_size_px(text: str, cap_px: float = SIGN_CAP_PX) -> tuple[float, float]:
    """(width, height) in 1080p pixels of a sign plate holding ``text`` (single line, monospace)."""
    em = cap_px / CAP_RATIO[LABEL_FONT]
    margin = cap_px * SIGN_PLATE_MARGIN_CAPS
    return len(text) * MONO_ADVANCE_EM * em + 2 * margin, cap_px * SIGN_TEXT_HEIGHT_CAPS + 2 * margin
