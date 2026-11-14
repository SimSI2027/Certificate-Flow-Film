"""Named easing presets and motion durations (Charter Section 9, criterion C-06).

Every keyframe is Bezier. Handles come from a named cubic-bezier preset (x1, y1, x2, y2), or from
``SMOOTH`` (Blender's auto-clamped handles, used where keys sample a path or a follow-move that is
already eased analytically). LINEAR appears only for the whitelisted constant-speed channels.
"""

from __future__ import annotations

from dataclasses import dataclass

from cff.story import timing


@dataclass(frozen=True)
class Easing:
    name: str
    x1: float
    y1: float
    x2: float
    y2: float


# Presets are standard cubic-bezier curves; OUT_BACK and SETTLE overshoot slightly (spring-like).
EASE_IN_OUT = Easing("EASE_IN_OUT", 0.65, 0.0, 0.35, 1.0)
EASE_OUT = Easing("EASE_OUT", 0.33, 1.0, 0.68, 1.0)
EASE_IN = Easing("EASE_IN", 0.32, 0.0, 0.67, 0.0)
CAMERA_GLIDE = Easing("CAMERA_GLIDE", 0.45, 0.0, 0.55, 1.0)  # gentler than EASE_IN_OUT: camera moves
OUT_BACK = Easing("OUT_BACK", 0.34, 1.45, 0.64, 1.0)  # entrance with a small overshoot
SETTLE = Easing("SETTLE", 0.3, 1.2, 0.5, 1.0)  # landing with a small settle

PRESETS: dict[str, Easing] = {
    e.name: e for e in (EASE_IN_OUT, EASE_OUT, EASE_IN, CAMERA_GLIDE, OUT_BACK, SETTLE)
}
SMOOTH = "SMOOTH"  # auto-clamped Bezier handles on analytically eased, densely sampled keys

# --- durations (seconds, all on frame boundaries) ------------------------------------------
ENTRANCE_S = 0.6
EXIT_S = 0.4  # 0.67 x the entrance (C-06: exits are 0.6-0.9 x)
LABEL_ENTRANCE_S = 0.3  # signs: quicker than a stage object, so short beats still hold them fully for 1.5 s
LABEL_EXIT_S = 0.2  # 0.67 x the entrance (C-06)
LABEL_LINGER_S = 0.3  # a windowed sign stays this long past its window, so its exit does not eat the hold
LABEL_ENTRANCE_SCALE = 0.85  # signs grow from this fraction of their size while they fade in (never opacity-only: C-06)
STAGGER_S = 0.1
IDLE_PERIOD_S = 2.0
IDLE_AMPLITUDE_FRACTION = 0.015  # <= 2% of object size (C-06)
SLIDE_S = 0.5  # short settling moves

# --- the user character (V4; keyed on the rig by blender.character from cff.stage.character) ------------------------------
BREATH_PERIOD_S = 4.0  # one breath (in and out): about 15 a minute, seated and calm
BREATH_ANGLE_DEG = 0.7  # chest pitch at the top of a breath; moves the head about 6 mm (<= 2% of the figure: C-06)
TYPING_STROKE_DOWN_S = 0.07  # a key press: the finger dips ...
TYPING_STROKE_UP_S = 0.1  # ... and lifts back
TYPING_STROKE_ANGLE_DEG = 8.0  # knuckle flex of a key press (12 put the fingertip pads up to 6 mm into the laptop base)
TYPING_INTERVAL_S = 0.14  # between strokes inside a burst (about 7 keys a second, two hands)
TYPING_BURST_S = (1.4, 3.4)  # a burst of typing lasts this long (seeded uniform) ...
TYPING_PAUSE_S = (0.7, 2.2)  # ... then the hands rest this long
TYPING_FINGER_GAP_S = 0.3  # the same finger never strikes twice within this time
HEAD_TURN_S = 0.8  # the head turns between gaze targets over this long (EASE_IN_OUT)
CHARACTER_EASE = "EASE_IN_OUT"  # strokes and head turns; breathing is SMOOTH like the other idle motion

# --- scale conventions ---------------------------------------------------------------------
HIDDEN_SCALE = 0.001  # an object that is not on stage yet or is gone for good
FULL_SCALE = 1.0

# --- key sampling ---------------------------------------------------------------------------
PATH_KEY_STEP_FRAMES = 3  # keys on analytically eased paths
CAMERA_KEY_STEP_FRAMES = 6  # keys on camera, target and focus tracks
CAMERA_SMOOTH_SIGMA_FRAMES = 16.0  # Gaussian lag on camera position and look-at: the subject leads, the camera follows
CAMERA_SMOOTH_REACH_SIGMAS = 3.0  # kernel half-width in sigmas

# LINEAR is allowed only on these channel names (constant-speed effects). None are used in the animatic.
LINEAR_WHITELIST: frozenset[str] = frozenset()


def preset(name: str) -> Easing:
    return PRESETS[name]


def peak_slope(easing: Easing, samples: int = 400) -> float:
    """Largest slope of the eased progress curve (1.0 would be constant speed)."""
    previous = 0.0
    best = 0.0
    for i in range(1, samples + 1):
        value = evaluate(easing, i / samples)
        best = max(best, (value - previous) * samples)
        previous = value
    return best


def entrance_frames() -> int:
    return round(ENTRANCE_S * timing.FPS)


def exit_frames() -> int:
    return round(EXIT_S * timing.FPS)


def label_entrance_frames() -> int:
    return round(LABEL_ENTRANCE_S * timing.FPS)


def label_exit_frames() -> int:
    return round(LABEL_EXIT_S * timing.FPS)


BISECTION_STEPS = 40


def _bezier(a: float, b: float, s: float) -> float:
    """Cubic Bezier from 0 to 1 with inner control values a, b: 3(1-s)^2 s a + 3(1-s) s^2 b + s^3."""
    u = 1.0 - s
    return 3 * u * u * s * a + 3 * u * s * s * b + s * s * s


def evaluate(easing: Easing, t: float) -> float:
    """Eased progress y for linear progress t in 0..1 (solves x(s) = t, returns y(s))."""
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(BISECTION_STEPS):
        mid = (lo + hi) / 2
        if _bezier(easing.x1, easing.x2, mid) < t:
            lo = mid
        else:
            hi = mid
    return _bezier(easing.y1, easing.y2, (lo + hi) / 2)
