"""The user character (Session V4, amendment V4-A2): what it is made of, how it sits, and how it moves.

Pure Python (no ``bpy``). ``blender/make_character.py`` generates ``assets/character.blend`` from the generation inputs
here (once, with the MPFB add-on); ``blender/character.py`` loads that file at build time, poses the rig from the seated-pose
geometry here and keys it from the motion plans here. Timing comes from ``cff.story.timing`` and the timeline, easing and
durations from ``cff.theme.motion``. No wall-clock logic; the typing rhythm uses ``random.Random(TYPING_SEED)``.

Frames: positions are in the user object's local frame (``USER_LOCAL``): +X is the way the user faces (toward the laptop),
+Y is the user's left, +Z is up, the origin is the chair's floor point (``layout.USER``).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from cff.stage import choreography
from cff.stage.tracks import SCALE
from cff.story import model, timing
from cff.theme import motion

# --- the asset -------------------------------------------------------------------------------------------------------------
ASSET_PATH = "assets/character.blend"  # relative to the repository root
ASSET_MAX_BYTES = 20 * 1024 * 1024
COLLECTION = "CHARACTER"
RIG = "CHAR-rig"


@dataclass(frozen=True)
class Part:
    """One mesh of the character: its object name, the MakeHuman asset it comes from (None: the body), and its MPFB type."""

    name: str
    source: str | None
    asset_type: str
    texture_px: int  # the packed diffuse texture is scaled to this size (0: no texture kept)


PARTS: tuple[Part, ...] = (
    Part("CHAR-body", None, "Basemesh", 0),
    Part("CHAR-eyes", "eyes/low-poly/low-poly.mhclo", "Eyes", 256),
    Part("CHAR-brows", "eyebrows/eyebrow001/eyebrow001.mhclo", "Eyebrows", 256),
    Part("CHAR-hair", "hair/short02/short02.mhclo", "Hair", 1024),
    Part("CHAR-clothes", "clothes/male_casualsuit01/male_casualsuit01.mhclo", "Clothes", 1024),
    Part("CHAR-shoes", "clothes/shoes02/shoes02.mhclo", "Clothes", 512),
)
PART_BY_NAME: dict[str, Part] = {p.name: p for p in PARTS}

# MPFB macro sliders (0..1): an adult man of about 33, average build. Race weights are left at MPFB's even mix; the skin
# colour is a theme token, not a texture.
MACROS: dict[str, float] = {
    "gender": 1.0,
    "age": 0.56,
    "muscle": 0.5,
    "weight": 0.55,
    "proportions": 0.5,
    "height": 0.5,
    "cupsize": 0.5,
    "firmness": 0.5,
}
RIG_NAME = "default"  # MPFB's standard rig (CC0 weights)

# --- the seated pose (USER_LOCAL metres and degrees) -------------------------------------------------------------------------
# The MakeHuman figure faces -Y in its own space; the rig is turned +90 degrees about Z under the user object, so it faces +X.
RIG_YAW_DEG = 90.0
HIP_JOINT = (-0.08, 0.0, 0.56)  # mid-point of the two hip joints: 8.5 cm above the seat top (0.475), over the seat's front half
SPINE_BONES = ("spine05", "spine04", "spine03", "spine02")
SPINE_LEAN_DEG = (3.0, 3.0, 3.0, 3.0)  # 12 degrees forward in all, toward the desk
THIGH_DECLINE_DEG = 8.0
KNEE_SPREAD = 0.08  # lateral component of the thigh direction (knees slightly apart)
SHIN_FORWARD_DEG = 10.0
# The hands: on the laptop's keyboard. Offsets are in the laptop's own frame (+X toward the user, +Z up from the base centre).
KEYBOARD_HOME = (-0.02, 0.0, 0.045)  # home-row centre, 2 cm above the base top (0.025): the wrist and gaze reference
KEYBOARD_TOP_Z = 0.025  # the laptop base's top surface, in the laptop's frame
FINGER_PAD_M = 0.006  # the fingertip bone runs through the finger's middle; the pad is this much below it
FINGERTIP_REST_Z = 0.048  # resting middle fingertip bones 2.3 cm over the keys, so a keystroke dip (about 1.4 cm) never enters them
HAND_SPREAD = 0.1  # each hand's fingertip target this far left / right of the home-row centre
WRIST_BACK = 0.13  # the wrist rests this far behind its fingertips (toward the user) ...
WRIST_LIFT = 0.025  # ... and this much higher
ELBOW_POLE = (-0.3, 0.6, -1.0)  # elbows point down, back and out (Y mirrored per side)
FINGER_CURL_DEG = (10.0, 18.0, 14.0)  # resting curl of the three finger segments (knuckle, middle, tip)
THUMB_CURL_DEG = 8.0
HEAD_SHARE = (0.15, 0.15, 0.2, 0.5)  # how a head turn is shared by neck01, neck02, neck03 and head
GAZE_TARGETS = ("keyboard", "laptop", "session")  # keyboard home row, the laptop screen (SCREEN-IDLE), the session window


# --- motion plans ----------------------------------------------------------------------------------------------------------------
TYPING_SEED = 20261114  # documented seed: the typing rhythm (bursts, pauses, which finger strikes)
FINGERS = ("finger2", "finger3", "finger4", "finger5")  # index to little finger; the thumbs rest on the space bar
SIDES = ("L", "R")


def _frames(seconds: float) -> int:
    return max(1, round(seconds * timing.FPS))


def _event_frames(event_id: str) -> tuple[int, int]:
    event = next(e for e in model.MODEL.events if e.id == event_id)
    return timing.seconds_to_frame(event.start_s), timing.seconds_to_frame(event.end_s)


def session_windows() -> list[tuple[int, int]]:
    """When the RDP session window and the browser window are open, read from the timeline (the single source)."""
    timeline = choreography.build_timeline()
    out: list[tuple[int, int]] = []
    for screen in ("SCREEN-RDP", "SCREEN-WEB"):
        keys = timeline.keys(screen, SCALE)
        shown = [k.frame for k in keys if k.value[0] > motion.HIDDEN_SCALE]
        hidden_after = [k.frame for k in keys if k.value[0] <= motion.HIDDEN_SCALE and shown and k.frame > shown[0]]
        if shown:
            out.append((shown[0], hidden_after[0] if hidden_after else timing.frame_end()))
    return out


@dataclass(frozen=True)
class GazeKey:
    frame: int
    target: str
    ease: str


def gaze_keys() -> list[GazeKey]:
    """Head turns, all tied to the story: the user types the server's name looking at the keyboard, looks up at the laptop
    screen when it wakes (E-01.1a), and turns up to each session window while it is open."""
    turn = _frames(motion.HEAD_TURN_S)
    wake, _ = _event_frames("E-01.1a")
    changes: list[tuple[int, str]] = [(wake, "laptop")]
    for opened, closed in session_windows():
        changes += [(opened, "session"), (closed, "laptop")]
    keys = [GazeKey(timing.FRAME_START, "keyboard", motion.CHARACTER_EASE)]
    for wanted, target in sorted(changes):
        start = max(wanted, keys[-1].frame + 1)
        keys.append(GazeKey(start, keys[-1].target, motion.CHARACTER_EASE))
        keys.append(GazeKey(start + turn, target, motion.CHARACTER_EASE))
    return [k for k in keys if k.frame <= timing.frame_end()]


@dataclass(frozen=True)
class Stroke:
    bone: str  # e.g. "finger3-1.L"
    frame: int


def typing_strokes() -> list[Stroke]:
    """Bursts of key presses with pauses between them, over the whole film (seeded, so every build is identical)."""
    rng = random.Random(TYPING_SEED)
    interval, gap = _frames(motion.TYPING_INTERVAL_S), _frames(motion.TYPING_FINGER_GAP_S)
    span = _frames(motion.TYPING_STROKE_DOWN_S) + _frames(motion.TYPING_STROKE_UP_S)
    last_strike: dict[str, int] = {}
    strokes: list[Stroke] = []
    frame, end = timing.FRAME_START + interval, timing.frame_end() - span - 1
    while frame < end:
        burst_end = min(end, frame + _frames(rng.uniform(*motion.TYPING_BURST_S)))
        while frame < burst_end:
            bone = f"{rng.choice(FINGERS)}-1.{rng.choice(SIDES)}"
            if frame - last_strike.get(bone, -gap) >= gap:
                strokes.append(Stroke(bone, frame))
                last_strike[bone] = frame
            frame += interval
        frame += _frames(rng.uniform(*motion.TYPING_PAUSE_S))
    return strokes


def finger_keys() -> dict[str, list[tuple[int, float]]]:
    """Per finger bone: (frame, extra knuckle flex in degrees) keys; 0 is the resting curl."""
    down, up = _frames(motion.TYPING_STROKE_DOWN_S), _frames(motion.TYPING_STROKE_UP_S)
    out: dict[str, list[tuple[int, float]]] = {f"{f}-1.{s}": [(timing.FRAME_START, 0.0)] for f in FINGERS for s in SIDES}
    for stroke in typing_strokes():
        keys = out[stroke.bone]
        if stroke.frame <= keys[-1][0]:
            continue
        keys += [(stroke.frame, 0.0), (stroke.frame + down, motion.TYPING_STROKE_ANGLE_DEG), (stroke.frame + down + up, 0.0)]
    return out


def breath_keys() -> list[tuple[int, float]]:
    """(frame, chest pitch in degrees): out at 0, in at BREATH_ANGLE_DEG, every half period (SMOOTH keys, like the idle motion)."""
    half = _frames(motion.BREATH_PERIOD_S / 2)
    keys, frame, inhale = [(timing.FRAME_START, 0.0)], timing.FRAME_START, True
    while frame + half <= timing.frame_end():
        frame += half
        keys.append((frame, motion.BREATH_ANGLE_DEG if inhale else 0.0))
        inhale = not inhale
    return keys


def head_breath_displacement_m() -> float:
    """How far breathing moves the head: chest pitch times the chest-to-head lever (spine02 to the head top, about 0.5 m)."""
    return math.radians(motion.BREATH_ANGLE_DEG) * 0.5
