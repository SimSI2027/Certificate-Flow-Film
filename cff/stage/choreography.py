"""Story events -> keyframe tracks.

Every on-screen model event is handled exactly once by a ``Choreographer`` method that reads its window from
``cff.story.timing`` through the model (``Choreographer.event``). A test asserts that no on-screen event is left
unhandled. Positions come from ``cff.stage.layout``; colours from ``cff.theme.palette``; easings from
``cff.theme.motion``. Nothing here depends on Blender.

Conventions
- An object that is not on stage keeps scale HIDDEN_SCALE; ``show`` is its entrance, ``hide`` its (faster) exit.
- ``glow`` is the emission tint and opacity: (linear r, g, b, alpha). Black means unlit.
- Network travel (pulses, presented certificates, proofs, CRL fetches) is baked onto Bezier keys every
  PATH_KEY_STEP_FRAMES with the eased progress, and uses SMOOTH (auto-clamped) handles.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from cff.stage import layout as lo
from cff.stage.layout import Vec3
from cff.stage.objects import BY_ID, CATALOGUE
from cff.stage.tracks import GLOW, LOCATION, ROTATION, SCALE, Timeline, Value
from cff.story import model as m
from cff.story import timing
from cff.story.model import ColourRole, Event
from cff.theme import colour, motion, palette

FRAME_LAST = timing.frame_end()
OFF_GLOW: Value = (0.0, 0.0, 0.0, 1.0)
HIDDEN: Value = (motion.HIDDEN_SCALE,) * 3
SHOWN: Value = (motion.FULL_SCALE,) * 3
GHOST_ALPHA = 0.45  # translucent copies of a certificate (the response chain copy)
DIM_LEVEL = 0.12  # a certificate dimmed on its crown
PULSE_LIFT = 0.25  # pulses ride this high above the floor conduit
TRAVEL_LIFT = 1.1  # cards travelling along a channel float this high
TRAVEL_BEHIND_S = 0.1  # a second object leaves this long after the first
SETTLE_BOUNCE = 0.04
HOLD_EASE = "EASE_IN_OUT"


def role_rgb(role: ColourRole) -> tuple[float, float, float]:
    return colour.rgb_to_linear(colour.hex_to_rgb(palette.role_hex(role)))


def glow_value(role: ColourRole, level: float, alpha: float = 1.0) -> Value:
    r, g, b = role_rgb(role)
    return (r * level, g * level, b * level, alpha)


def hex_glow(hex_colour: str, level: float, alpha: float = 1.0) -> Value:
    r, g, b = colour.rgb_to_linear(colour.hex_to_rgb(hex_colour))
    return (r * level, g * level, b * level, alpha)


def frame_of(seconds: float) -> int:
    return timing.seconds_to_frame(seconds)


class Choreographer:
    def __init__(self) -> None:
        self.tl = Timeline()
        self.handled: set[str] = set()
        self._events = {e.id: e for e in m.MODEL.events}
        self._last: dict[tuple[str, str], tuple[int, Value]] = {}

    # ------------------------------------------------------------------ frame helpers
    def beat(self, beat_id: str, offset_s: float = 0.0) -> int:
        return frame_of(timing.beat_window(beat_id)[0] + offset_s)

    def event(self, event_id: str) -> tuple[int, int]:
        """(first frame, frame after the last) of a model event; marks it handled."""
        self.handled.add(event_id)
        ev: Event = self._events[event_id]
        return frame_of(ev.start_s), frame_of(ev.end_s)

    # ------------------------------------------------------------------ track primitives
    def _initial(self, obj_id: str, channel: str) -> Value:
        o = BY_ID[obj_id]
        if channel == LOCATION:
            return o.home
        if channel == ROTATION:
            return o.rotation
        if channel == SCALE:
            return SHOWN if o.on_stage else HIDDEN
        return OFF_GLOW

    def current(self, obj_id: str, channel: str) -> Value:
        last = self._last.get((obj_id, channel))
        return last[1] if last else self._initial(obj_id, channel)

    def _set(self, obj_id: str, channel: str, frame: int, value: Value, ease: str = HOLD_EASE) -> None:
        last = self._last.get((obj_id, channel))
        if last is None and frame > timing.FRAME_START:
            initial = self._initial(obj_id, channel)
            self.tl.key(obj_id, channel, timing.FRAME_START, initial, HOLD_EASE)
            self._last[(obj_id, channel)] = (timing.FRAME_START, initial)
        elif last is not None and frame < last[0]:
            raise ValueError(f"{obj_id}.{channel}: key at {frame} is before the previous key at {last[0]}")
        self.tl.key(obj_id, channel, frame, value, ease)
        self._last[(obj_id, channel)] = (frame, value)

    def _hold(self, obj_id: str, channel: str, frame: int) -> None:
        """Make sure the track holds its current value up to ``frame`` (a key at ``frame``)."""
        last = self._last.get((obj_id, channel))
        if last is not None and last[0] > frame:
            raise ValueError(f"{obj_id}.{channel}: operation at {frame} overlaps an earlier one that runs to {last[0]}")
        if last is None or last[0] < frame:
            self._set(obj_id, channel, frame, self.current(obj_id, channel), HOLD_EASE)

    def key_to(self, obj_id: str, channel: str, f0: int, f1: int, value: Value, ease: str = "EASE_IN_OUT") -> None:
        """Hold until f0, then ease to ``value`` at f1."""
        self._hold(obj_id, channel, f0)
        self._set(obj_id, channel, f1, value, HOLD_EASE)
        self._set_ease(obj_id, channel, f0, ease)

    def _set_ease(self, obj_id: str, channel: str, frame: int, ease: str) -> None:
        keys = self.tl.tracks[(obj_id, channel)]
        old = keys[frame]
        keys[frame] = type(old)(old.frame, old.value, ease)

    # ------------------------------------------------------------------ vocabulary
    def init_glow(self, obj_id: str, value: Value) -> None:
        self._set(obj_id, GLOW, timing.FRAME_START, value, HOLD_EASE)

    def show(self, obj_id: str, f0: int, dur: int | None = None, rise: Vec3 = (0.0, 0.0, -0.3), ease: str = "OUT_BACK",
             glow: Value | None = None, at: Vec3 | None = None) -> None:
        """Entrance: scale, location and glow animate together (C-06: never opacity only)."""
        o = BY_ID[obj_id]
        dur = motion.entrance_frames() if dur is None else dur
        full = o.full
        home = at if at is not None else self.current(obj_id, LOCATION)
        self._hold(obj_id, SCALE, f0)
        self._set(obj_id, SCALE, f0, HIDDEN, ease)
        self._set(obj_id, SCALE, f0 + dur, full, HOLD_EASE)
        self._hold(obj_id, LOCATION, f0)
        self._set(obj_id, LOCATION, f0, lo.add(home, rise), "EASE_OUT")
        self._set(obj_id, LOCATION, f0 + dur, home, HOLD_EASE)
        if glow is not None:
            self._hold(obj_id, GLOW, f0)
            self._set(obj_id, GLOW, f0, self._dark(glow), "EASE_OUT")
            self._set(obj_id, GLOW, f0 + dur, glow, HOLD_EASE)

    def hide(self, obj_id: str, f0: int, dur: int | None = None, sink: Vec3 = (0.0, 0.0, -0.15)) -> None:
        """Exit: shorter than the entrance (C-06)."""
        dur = motion.exit_frames() if dur is None else dur
        here = self.current(obj_id, LOCATION)
        self._hold(obj_id, SCALE, f0)
        self._set(obj_id, SCALE, f0, self.current(obj_id, SCALE), "EASE_IN")
        self._set(obj_id, SCALE, f0 + dur, HIDDEN, HOLD_EASE)
        self._hold(obj_id, LOCATION, f0)
        self._set(obj_id, LOCATION, f0, here, "EASE_IN")
        self._set(obj_id, LOCATION, f0 + dur, lo.add(here, sink), HOLD_EASE)
        if (obj_id, GLOW) in self._last:
            self._hold(obj_id, GLOW, f0)
            cur = self.current(obj_id, GLOW)
            self._set(obj_id, GLOW, f0, cur, "EASE_IN")
            self._set(obj_id, GLOW, f0 + dur, self._dark(cur), HOLD_EASE)

    def grow(self, obj_id: str, f0: int, f1: int, glow: Value) -> None:
        """A beam or trust link extends along its own axis while it lights up."""
        full = BY_ID[obj_id].full
        thin = (motion.HIDDEN_SCALE if full[0] != 1.0 else 1.0, 1.0, motion.HIDDEN_SCALE if full[2] != 1.0 else 1.0)
        self._hold(obj_id, SCALE, f0)
        self._set(obj_id, SCALE, f0, thin, "EASE_OUT")
        self._set(obj_id, SCALE, f1, full, HOLD_EASE)
        self._hold(obj_id, GLOW, f0)
        self._set(obj_id, GLOW, f0, self._dark(glow), "EASE_OUT")
        self._set(obj_id, GLOW, f1, glow, HOLD_EASE)

    @staticmethod
    def _dark(glow: Value) -> Value:
        return (0.0, 0.0, 0.0, glow[3])

    def glow_to(self, obj_id: str, f0: int, f1: int, glow: Value, ease: str = "EASE_IN_OUT") -> None:
        self.key_to(obj_id, GLOW, f0, f1, glow, ease)

    def glow_pulse(self, obj_id: str, f0: int, f1: int, peak: Value, rest: Value | None = None) -> None:
        mid = (f0 + f1) // 2
        rest = rest if rest is not None else self.current(obj_id, GLOW)
        self.key_to(obj_id, GLOW, f0, mid, peak, "EASE_OUT")
        self.key_to(obj_id, GLOW, mid, f1, rest, "EASE_IN")

    def go(self, obj_id: str, f0: int, f1: int, dest: Vec3, ease: str = "EASE_IN_OUT") -> None:
        self.key_to(obj_id, LOCATION, f0, f1, dest, ease)

    def go_z(self, obj_id: str, f0: int, f1: int, dz: float, ease: str = "EASE_IN_OUT") -> None:
        here = self.current(obj_id, LOCATION)
        self.go(obj_id, f0, f1, (here[0], here[1], here[2] + dz), ease)

    def turn(self, obj_id: str, f0: int, f1: int, euler: Vec3, ease: str = "EASE_IN_OUT") -> None:
        self.key_to(obj_id, ROTATION, f0, f1, euler, ease)

    def settle(self, obj_id: str, f0: int, f1: int, dest: Vec3) -> None:
        """Arrive at ``dest`` and land with a small bounce (spring-like settle)."""
        mid = f0 + (f1 - f0) * 2 // 3
        self.go(obj_id, f0, mid, lo.add(dest, (0.0, 0.0, SETTLE_BOUNCE)), "EASE_OUT")
        self.go(obj_id, mid, f1, dest, "SETTLE")

    def travel(self, obj_id: str, f0: int, f1: int, points: Sequence[lo.Seq3], ease: str = "EASE_IN_OUT") -> Callable[[float], int]:
        """Move along a polyline with eased progress, baked onto SMOOTH Bezier keys.

        Returns a function mapping an arc-length fraction to the frame the object reaches it.
        """
        self._hold(obj_id, LOCATION, f0)
        easing = motion.preset(ease)
        step = motion.PATH_KEY_STEP_FRAMES
        frames: list[int] = [*range(f0, f1, step), f1]
        progress: list[float] = []
        for frame in frames:
            t = (frame - f0) / (f1 - f0)
            progress.append(motion.evaluate(easing, t))
            self._set(obj_id, LOCATION, frame, lo.point_along(points, progress[-1]), motion.SMOOTH)
        self._set_ease(obj_id, LOCATION, f1, "EASE_IN_OUT")

        def frame_at(fraction: float) -> int:
            for frame, p in zip(frames, progress, strict=True):
                if p >= fraction - 1e-9:
                    return frame
            return f1

        return frame_at

    def light_path(self, prefix: str, count: int, points: tuple[Vec3, ...], frame_at: Callable[[float], int], glow: Value, lead: int = 0) -> None:
        """Light consecutive channel or route segments as a traveller reaches each one."""
        total = lo.polyline_length(points)
        walked = 0.0
        ramp = 6
        for i in range(1, count + 1):
            seg = lo.dist(points[i - 1], points[i])
            start = max(timing.FRAME_START, frame_at(walked / total) - lead)
            self.glow_to(f"{prefix}-S{i}", start, start + ramp, glow, "EASE_OUT")
            walked += seg

    def dim_path(self, prefix: str, count: int, f0: int, f1: int, reverse: bool = False) -> None:
        order = range(count, 0, -1) if reverse else range(1, count + 1)
        span = max(1, (f1 - f0) // max(1, count))
        for n, i in enumerate(order):
            start = f0 + n * span
            self.glow_to(f"{prefix}-S{i}", start, min(f1, start + span + 3), OFF_GLOW, "EASE_IN")

    def recolour_path(self, prefix: str, count: int, f0: int, f1: int, glow: Value, reverse: bool = False) -> None:
        order = list(range(count, 0, -1)) if reverse else list(range(1, count + 1))
        span = max(1, (f1 - f0) // max(1, count))
        for n, i in enumerate(order):
            start = f0 + n * span
            self.glow_to(f"{prefix}-S{i}", start, min(f1, start + span + 3), glow, "EASE_IN_OUT")

    # ------------------------------------------------------------------ build
    def build(self) -> Timeline:
        for step in (self.initial, self.s1, self.s2, self.s3, self.s4, self.s5, self.s6, self.s7, self.s8, self.s9, self.idle):
            step()
        return self.tl

    def initial(self) -> None:
        """Resting glow of objects that are lit from the first frame."""
        R = ColourRole
        for obj_id, value in (
            ("CERT-ROOT", glow_value(R.ROOT, 0.45)),
            ("CERT-CA1", glow_value(R.ISSUING_CA1, DIM_LEVEL)),
            ("CERT-CA2", glow_value(R.ISSUING_CA2, DIM_LEVEL)),
            ("TRIM-CA1", glow_value(R.ISSUING_CA1, 0.25)),
            ("TRIM-CA2", glow_value(R.ISSUING_CA2, 0.25)),
            (m.AD, glow_value(R.DIRECTORY, 0.3)),
            (m.PKI_HTTP, hex_glow(palette.TEXT_HEX, 0.1)),
            ("KEY-CA1-PRIV", glow_value(R.ISSUING_CA1, 0.3)),
            ("KEY-CA2-PRIV", glow_value(R.ISSUING_CA2, 0.3)),
            ("MODULE-CA1", glow_value(R.ISSUING_CA1, 0.15)),
            ("MODULE-CA2", glow_value(R.ISSUING_CA2, 0.15)),
        ):
            self.init_glow(obj_id, value)

    # ------------------------------------------------------------------ S1
    def s1(self) -> None:
        R = ColourRole
        # B-01.1: the screen wakes while the user opens the connection by the server's FQDN.
        f0, f1 = self.event("E-01.1a")
        self.glow_to("SCREEN-IDLE", f0, f1, hex_glow(palette.SCREEN_HEX, 0.55), "EASE_OUT")
        # B-01.2: an amber pulse leaves the laptop, drops into the floor channel and runs to the rack.
        f0, f1 = self.event("E-01.2a")
        amber = glow_value(R.PENDING, palette.GLOW_ACTIVE)
        path = (lo.add(lo.CHANNEL_RDP[0], (-0.3, 0.0, 0.7)), *[lo.at_z(p, lo.FLOOR_Z + PULSE_LIFT) for p in lo.CHANNEL_RDP],
                lo.add(lo.RDP, (0.0, lo.FRONT_Y - 0.6, 0.55)))
        self.show("PULSE-RDP-1", f0, 12, rise=(0.0, 0.0, 0.0), glow=glow_value(R.PENDING, palette.GLOW_PEAK), at=path[0])
        frame_at = self.travel("PULSE-RDP-1", f0 + 12, f1, path)
        self.light_path("CH-RDP", len(lo.CHANNEL_RDP) - 1, path[1:], frame_at, amber)

    # ------------------------------------------------------------------ S2
    def s2(self) -> None:
        R = ColourRole
        amber = glow_value(R.PENDING, palette.GLOW_ACTIVE)
        port_listen = lo.add(lo.RDP, lo.LISTENER_PORT)
        # B-02.1: the pulse reaches the listener, which lights amber.
        f0, f1 = self.event("E-02.1a")
        self.go("PULSE-RDP-1", f0, f1, lo.add(port_listen, (0.0, -0.1, 0.0)), "EASE_IN_OUT")
        self.glow_to("PORT-RDP-LISTEN", f0, f1, amber, "EASE_OUT")
        # B-02.2: a pale self-signed card rises at the listener and slides along the channel to the laptop.
        f0, f1 = self.event("E-02.2a")
        card_start = lo.add(port_listen, (0.0, -0.35, 0.15))
        self.show("CERT-RDP-SELF", f0, 12, rise=(0.0, 0.0, -0.3), glow=hex_glow(palette.CARD_PALE_HEX, 0.35), at=card_start)
        slide = (card_start, *[lo.at_z(p, TRAVEL_LIFT) for p in reversed(lo.CHANNEL_RDP)], lo.HOVER_UNVERIFIED)
        self.travel("CERT-RDP-SELF", f0 + 12, f1, slide)
        f0b, f1b = self.event("E-02.2b")  # the client cannot verify: the card hovers, not accepted
        self.glow_pulse("CERT-RDP-SELF", f0b, f1b, hex_glow(palette.CARD_PALE_HEX, 0.6))
        # the user does not accept: the attempt closes, the card fades and the pulse dies out of the channel
        f0c, f1c = self.event("E-02.2c")
        self.hide("CERT-RDP-SELF", f0c)
        self.dim_path("CH-RDP", len(lo.CHANNEL_RDP) - 1, f0c, f1c, reverse=True)
        self.glow_to("PORT-RDP-LISTEN", f0c, f1c, OFF_GLOW, "EASE_IN")
        self.hide("PULSE-RDP-1", f0c)
        # B-02.3: policy refresh; the RDPAuth badge drops from the AD node's direction onto the server's top plate.
        f0, f1 = self.event("E-02.3a")
        top = lo.add(lo.RDP, lo.TOP_PLATE)
        start = lo.add(lo.AD, (-0.5, -0.4, lo.AD_HEIGHT + 0.4))
        self.show("TPL-RDPAUTH", f0, 12, rise=(0.0, 0.0, 0.0), glow=hex_glow(palette.TEXT_HEX, 0.4), at=start)
        mid = lo.add(lo.lerp(start, top, 0.5), (0.0, 0.0, 0.9))
        self.travel("TPL-RDPAUTH", f0 + 12, f1 - 8, (start, mid, lo.add(top, (0.0, 0.0, 0.2))), "EASE_IN_OUT")
        self.settle("TPL-RDPAUTH", f1 - 8, f1, top)

    # ------------------------------------------------------------------ S3 / S7.2 shared echo
    def key_ceremony(self, tag: str, base: Vec3, e_form: str, e_store: str, e_request: str, e_proof: str, compress: bool) -> None:
        """Key pair forms, private key anchored, request assembled, proof of possession. Used for RDP and web."""
        R = ColourRole
        white = glow_value(R.REQUEST, palette.GLOW_ACTIVE)
        soft_white = hex_glow(palette.TEXT_HEX, 0.7)
        panel, container, lid = f"PANEL-{tag}", f"KC-{tag}", f"KCLID-{tag}"
        priv, pub = f"KEY-{tag}-PRIV", f"KEY-{tag}-PUB"
        req, tile = f"REQ-{tag}", f"TILE-{tag}"
        # Durations in frames: the echo at the web server (S7) is compressed to fit its shorter event windows.
        ent, swing, slide = (9, 18, 18) if compress else (18, 24, 30)
        beam_d, ring_d, close_d = (6, 6, 9) if compress else (15, 12, 12)
        # keys form: the front panel swings open to a cutaway interior
        f0, _f1 = self.event(e_form)
        self.turn(panel, f0, f0 + swing, (0.0, 0.0, -110.0))
        self.show(container, f0 + 6, ent, rise=(0.0, 0.0, -0.2), ease="OUT_BACK")
        self.show(lid, f0 + 6, ent, rise=(0.0, 0.0, -0.2))
        self.turn(lid, f0 + 6, f0 + 6 + 12, (0.0, -100.0, 0.0))
        k0 = f0 + (9 if compress else 15)
        self.show(priv, k0, ent, rise=(0.0, 0.0, 0.2), glow=soft_white)
        self.show(pub, k0 + 6, ent, rise=(0.0, 0.0, 0.2), glow=soft_white)
        # the private key settles into its container; lid closes; lock turns; anchors engage
        f0, _ = self.event(e_store)
        inside = lo.add(base, (lo.CONTAINER[0], lo.CONTAINER[1], lo.CONTAINER[2] + 0.02))
        self.travel(priv, f0, f0 + slide, (self.current(priv, LOCATION), lo.add(inside, (0.0, 0.0, 0.3)), inside))
        close = f0 + slide
        self.turn(lid, close, close + 9, (0.0, 0.0, 0.0), "EASE_IN_OUT")
        self.show(f"LOCK-{tag}", close + 6, 12, rise=(0.0, 0.0, 0.0))
        self.turn(f"LOCK-{tag}", close + 18, close + 30, (0.0, 90.0, 0.0), "EASE_IN_OUT")
        for side, sign in (("L", -1.0), ("R", 1.0)):
            clamp = f"CLAMP-{tag}-{side}"
            self.show(clamp, close + 12, 12, rise=(sign * 0.15, 0.0, 0.0))
            self.go(clamp, close + 24, close + 36, lo.add(self.current(clamp, LOCATION), (-sign * 0.1, 0.0, 0.0)), "EASE_IN_OUT")
        # the public key and the request information enter the glass capsule; the private key stays put
        f0, _ = self.event(e_request)
        capsule_at = lo.add(base, lo.CAPSULE_SPOT)
        self.show(req, f0, ent, rise=(0.0, 0.0, -0.2), glow=glow_value(R.REQUEST, 0.35), at=capsule_at)
        enter0 = f0 + 6
        tile_at = lo.add(base, (0.0, 0.4, 1.95))
        self.travel(pub, enter0, enter0 + 12, (self.current(pub, LOCATION), lo.add(capsule_at, (0.0, 0.0, 0.1)), capsule_at))
        self.hide(pub, enter0 + 12, 9, sink=(0.0, 0.0, 0.0))
        self.show(tile, enter0, 9, rise=(0.0, 0.0, 0.0), glow=white, at=tile_at)
        self.travel(tile, enter0 + 9, enter0 + 21, (tile_at, lo.add(capsule_at, (0.0, 0.1, 0.1)), capsule_at))
        self.hide(tile, enter0 + 21, 9, sink=(0.0, 0.0, 0.0))
        # proof of possession: a beam rises from the container; the seal ring closes round the capsule
        f0, _ = self.event(e_proof)
        self.glow_pulse(container, f0, f0 + beam_d + ring_d + close_d, white)
        self.grow(f"BEAM-{tag}", f0, f0 + beam_d, white)
        ring = f"SEAL-{tag}"
        ring_end = f0 + beam_d + ring_d
        self.show(ring, f0 + beam_d, ring_d, rise=(0.0, 0.0, 0.0), glow=white, at=capsule_at)
        self.key_to(ring, SCALE, ring_end, ring_end + close_d, (0.7, 0.7, 0.7), "EASE_IN_OUT")
        self.glow_to(req, ring_end, ring_end + close_d, white)
        self.hide(f"BEAM-{tag}", ring_end, sink=(0.0, 0.0, 0.0))

    def s3(self) -> None:
        self.key_ceremony("RDP", lo.RDP, "E-03.1a", "E-03.2a", "E-03.3a", "E-03.4a", compress=False)

    # ------------------------------------------------------------------ S4
    def lit_ring_and_route(self, ring: str, other_ring: str, route: str, count: int, role: ColourRole, f0: int, f1: int) -> None:
        self.show(ring, f0, rise=(0.0, 0.0, 0.3), glow=glow_value(role, palette.GLOW_ACTIVE))
        self.show(other_ring, f0 + 3, rise=(0.0, 0.0, 0.3), glow=glow_value(ColourRole.INELIGIBLE, 0.15))
        span = max(3, (f1 - f0 - 12) // count)
        for i in range(1, count + 1):
            start = f0 + 12 + (i - 1) * span
            self.glow_to(f"{route}-S{i}", start, start + 6, glow_value(role, palette.GLOW_ACTIVE), "EASE_OUT")

    def s4(self) -> None:
        R = ColourRole
        cyan = glow_value(R.ISSUING_CA1, palette.GLOW_ACTIVE)
        # B-04.1: the sealed capsule moves to the outbound port and waits; a separate query pulse goes to AD and back.
        beat0 = self.beat("B-04.1")
        wait = lo.port_wait(lo.RDP, lo.RDP_PORT_SIDE)
        capsule_at = self.current("REQ-RDP", LOCATION)
        self.travel("REQ-RDP", beat0, beat0 + 18, (capsule_at, lo.add(lo.RDP, (0.45, 0.05, 1.45)), wait))
        f0, f1 = self.event("E-04.1a")
        ad_front = lo.add(lo.AD, (-0.9, -0.7, 1.8))
        q_start = lo.add(wait, (0.0, 0.25, 0.1))
        self.show("QUERY-RDP", f0, 9, rise=(0.0, 0.0, 0.0), glow=glow_value(R.DIRECTORY, palette.GLOW_ACTIVE), at=q_start)
        self.travel("QUERY-RDP", f0 + 9, f1, (q_start, lo.lerp(q_start, ad_front, 0.5), ad_front))
        f0b, f1b = self.event("E-04.1b")
        self.travel("QUERY-RDP", f0b, f0b + 24, (ad_front, lo.lerp(q_start, ad_front, 0.5), q_start))
        self.hide("QUERY-RDP", f0b + 24, 9, sink=(0.0, 0.0, 0.0))
        self.lit_ring_and_route("RING-AD-1", "RING-AD-2", "ROUTE-CA1", len(lo.ROUTE_CA1) - 1, R.ISSUING_CA1, f0b, f1b)
        # B-04.2: the capsule launches along the cyan route into Issuing CA 1's antechamber.
        f0, f1 = self.event("E-04.2a")
        cradle = lo.add(lo.CA1, lo.CA_CRADLE)
        route = tuple(lo.at_z(p, 0.55) for p in lo.ROUTE_CA1)
        self.travel("REQ-RDP", f0, f1, (wait, lo.add(wait, (0.4, 0.4, -0.6)), *route[1:], lo.add(cradle, (0.0, -0.6, 0.5)), lo.add(cradle, (0.0, 0.0, 0.42))))
        # B-04.3: four checks resolve one after another with cyan ticks.
        self.glow_to("EVAL-CA1", self.beat("B-04.3"), self.beat("B-04.3", 0.7), glow_value(R.ISSUING_CA1, 0.3), "EASE_OUT")
        for letter, ev_id in zip("abcd", ("E-04.3a", "E-04.3b", "E-04.3c", "E-04.3d"), strict=True):
            self.tick(f"TICK-CA1-{letter}", self.event(ev_id), cyan)
        # B-04.4: the request is consumed at the press; CA 1's sealed key drives the press, which stamps the RDP certificate.
        f0, f1 = self.event("E-04.4a")
        press = lo.add(lo.CA1, lo.CA_PRESS)
        self.travel("REQ-RDP", f0, f1, (self.current("REQ-RDP", LOCATION), lo.add(press, (-0.3, -0.5, 0.9)), lo.add(press, (0.0, 0.0, 0.7))))
        self.hide("REQ-RDP", f1, 9, sink=(0.0, 0.0, -0.1))
        f0, f1 = self.event("E-04.4b")
        self.glow_to("MODULE-CA1", f0, f0 + 6, cyan, "EASE_OUT")
        self.glow_to("KEY-CA1-PRIV", f0, f0 + 6, cyan, "EASE_OUT")
        self.glow_to("LINK-CA1", f0 + 3, f0 + 12, cyan, "EASE_OUT")
        head = lo.add(press, (0.0, 0.0, 0.85))
        self.go("PRESSHEAD-CA1", f0 + 9, f0 + 18, lo.add(head, (0.0, 0.0, -0.35)), "EASE_IN")
        out = lo.add(lo.CA1, lo.CA_PRESS_OUT)
        self.show("CERT-RDP", f0 + 18, 15, rise=(0.0, 0.0, -0.2), glow=glow_value(R.ISSUING_CA1, 0.9), at=out)
        self.go("PRESSHEAD-CA1", f0 + 18, f0 + 30, head, "EASE_OUT")
        self.glow_to("LINK-CA1", f0 + 24, f1, OFF_GLOW, "EASE_IN")
        self.glow_to("MODULE-CA1", f0 + 24, f1, glow_value(R.ISSUING_CA1, 0.3), "EASE_IN")  # the sealed module stays shut
        # B-04.5: the card returns along the cyan route and locks beside the private key; the CA's certificate copy follows.
        f0, f1 = self.event("E-04.5a")
        f0b, f1b = self.event("E-04.5b")
        slot = lo.add(lo.RDP, lo.CERT_SLOT)
        back = (out, lo.add(cradle, (0.0, -0.7, 0.5)), *tuple(lo.at_z(p, 0.8) for p in reversed(lo.ROUTE_CA1))[:-1], wait, lo.add(slot, (0.5, 0.0, 0.0)))
        self.travel("CERT-RDP", f0, f1, back, "EASE_IN_OUT")
        self.go("CERT-RDP", f0b, f1b, slot, "SETTLE")
        self.glow_to("CERT-RDP", f0b, f1b, glow_value(R.ISSUING_CA1, 1.1))
        # the original stays on the crown; a translucent copy travels with the card into the intermediate slot
        f0c, f1c = self.event("E-04.5c")
        crown = lo.add(lo.CA1, (0.0, 0.0, lo.CA_CROWN[2] + 0.42))
        ghost = glow_value(R.ISSUING_CA1, 0.8, GHOST_ALPHA)
        self.show("CERT-CA1-COPY-RDP", f0, 12, rise=(0.0, 0.0, 0.0), glow=ghost, at=crown)
        copy_back = (crown, lo.add(cradle, (0.0, -0.9, 0.9)), *tuple(lo.at_z(p, 1.2) for p in reversed(lo.ROUTE_CA1))[:-1], wait, lo.add(lo.RDP, (0.9, 0.0, 0.55)))
        self.travel("CERT-CA1-COPY-RDP", f0 + 12, f1, copy_back, "EASE_IN_OUT")
        self.go("CERT-CA1-COPY-RDP", f0c, f1c, lo.add(lo.RDP, lo.INTERMEDIATE_SLOT), "SETTLE")
        # the route and AD rings go dark again
        self.dim_path("ROUTE-CA1", len(lo.ROUTE_CA1) - 1, f1c, f1c + 12, reverse=True)
        self.hide("RING-AD-1", f1c)
        self.hide("RING-AD-2", f1c)

    def tick(self, tick_id: str, window: tuple[int, int], glow: Value) -> None:
        """A check slot: a ring appears, then resolves with a pop and light."""
        f0, f1 = window
        dim = (glow[0] * 0.25, glow[1] * 0.25, glow[2] * 0.25, 1.0)
        self.show(tick_id, f0, 9, rise=(0.0, 0.0, -0.1), glow=dim)
        self.glow_to(tick_id, f0 + 9, max(f1, f0 + 12), glow, "EASE_OUT")
        self.key_to(tick_id, SCALE, f0 + 9, f0 + 15, (1.25, 1.25, 1.25), "EASE_OUT")
        self.key_to(tick_id, SCALE, f0 + 15, f0 + 21, SHOWN, "SETTLE")

    # ------------------------------------------------------------------ S5
    def s5(self) -> None:
        R = ColourRole
        gold = glow_value(R.ROOT, palette.GLOW_ACTIVE)
        # B-05.1: the root complex rises on its own plinth; the sweep reveals the existing self-signed seal.
        b0 = self.beat("B-05.1")
        rise = (0.0, 0.0, -7.0)
        for n, oid in enumerate(("ROOT-DAIS", "ROOT-PLINTH", m.ROOT_CA, "READER-ROOT", "PRESS-ROOT", "PRESSHEAD-ROOT")):
            self.show(oid, b0 + n * 3, 36, rise=rise, ease="EASE_OUT", glow=glow_value(R.ROOT, 0.12) if oid in {m.ROOT_CA, "ROOT-DAIS", "ROOT-PLINTH"} else None)
        for oid in ("MODULE-ROOT", "KEY-ROOT-PRIV"):  # the dark key module and its key appear on the dais bay once the complex has landed
            self.show(oid, b0 + 60, 18, rise=(0.0, 0.0, -0.25), ease="EASE_OUT")
        f0, f1 = self.event("E-05.1a")
        self.show("SEAL-ROOT", f0 - 12, 12, rise=(0.0, 0.0, 0.0), glow=glow_value(R.ROOT, 0.1))
        self.glow_to("SEAL-ROOT", f0, f1, gold, "EASE_IN_OUT")
        # CA 1's present-day certificate steps aside while the flashback re-forms it (single object, see S5.2)
        self.hide("CERT-CA1", self.beat("B-05.1", 3.0))
        # B-05.2: offline ceremony, a desaturated flashback (compositor), inside CA 1's vault and out to the root dais.
        ca1_mod = lo.add(lo.CA1, lo.CA_MODULE)
        seal_at = lo.add(ca1_mod, (0.0, -0.55, 0.35))
        f0, f1 = self.event("E-05.2a")
        cyan = glow_value(R.ISSUING_CA1, palette.GLOW_ACTIVE)
        self.show("REQ-CA1", f0, 12, rise=(0.0, 0.0, -0.2), glow=glow_value(R.REQUEST, 0.6), at=seal_at)
        self.show("BAND-CA1", f0 + 3, 9, rise=(0.0, 0.0, 0.0), glow=cyan, at=seal_at)
        self.glow_pulse("MODULE-CA1", f0, f1, cyan, rest=glow_value(R.ISSUING_CA1, 0.3))
        self.grow("BEAM-CA1", f0 + 3, f0 + 12, cyan)
        self.hide("BEAM-CA1", f0 + 18, sink=(0.0, 0.0, 0.0))
        self.glow_to("REQ-CA1", f0 + 12, f1, glow_value(R.REQUEST, palette.GLOW_ACTIVE))
        f0, f1 = self.event("E-05.2b")
        cart0 = lo.add(lo.WALKWAY[0], (0.0, 0.0, 0.85))
        self.show("CARTRIDGE", self.beat("B-05.2", 0.1), 12, rise=(0.0, 0.0, 0.0), glow=hex_glow(palette.TEXT_HEX, 0.5), at=cart0)
        walk = tuple(lo.add(p, (0.0, 0.0, 0.85)) for p in lo.WALKWAY)
        reader = lo.add(lo.ROOT_READER, (0.0, 0.0, 0.62))
        out_path = (*walk, reader)
        self.travel("REQ-CA1", f0 - 12, f0, (seal_at, lo.add(cart0, (0.0, 0.0, 0.12))), "EASE_IN_OUT")
        self.travel("BAND-CA1", f0 - 12, f0, (seal_at, lo.add(cart0, (0.0, 0.0, 0.12))), "EASE_IN_OUT")
        frame_at = self.travel("CARTRIDGE", f0, f1, out_path)
        self.travel("REQ-CA1", f0, f1, tuple(lo.add(p, (0.0, 0.0, 0.12)) for p in out_path))
        self.travel("BAND-CA1", f0, f1, tuple(lo.add(p, (0.0, 0.0, 0.12)) for p in out_path))
        for i in range(lo.FOOTPRINT_COUNT):
            self.show(f"FOOT-{i + 1:02d}", frame_at((i + 0.3) / (lo.FOOTPRINT_COUNT + 1) * 0.92) - 2, 9, rise=(0.0, 0.0, 0.0), glow=hex_glow(palette.TEXT_HEX, 0.35))
        f0, f1 = self.event("E-05.2c")  # consumed at the root's reader
        self.hide("REQ-CA1", f0, 9, sink=(0.0, 0.0, 0.0))
        self.hide("BAND-CA1", f0, 9, sink=(0.0, 0.0, 0.0))
        f0, f1 = self.event("E-05.2d")  # the root's sealed key drives its press, which stamps CA 1's CA certificate
        self.glow_to("MODULE-ROOT", f0, f0 + 9, gold, "EASE_OUT")
        self.glow_to("KEY-ROOT-PRIV", f0, f0 + 9, gold, "EASE_OUT")
        head = lo.add(lo.ROOT_PRESS, (0.0, 0.0, 0.85))
        self.glow_to("PRESSHEAD-ROOT", f0, f0 + 9, gold, "EASE_OUT")
        self.go("PRESSHEAD-ROOT", f0 + 3, f0 + 12, lo.add(head, (0.0, 0.0, -0.35)), "EASE_IN")
        out = lo.add(lo.ROOT_PRESS, (0.0, -0.7, 0.45))
        self.show("CERT-CA1", f0 + 12, 9, rise=(0.0, 0.0, -0.2), glow=glow_value(R.ISSUING_CA1, 0.9), at=out)
        self.go("PRESSHEAD-ROOT", f0 + 12, f1, head, "EASE_OUT")
        f0, f1 = self.event("E-05.2e")  # the cartridge carries the certificate back
        crown = lo.add(lo.CA1, (0.0, 0.0, lo.CA_CROWN[2] + 0.42))
        back = tuple(reversed(out_path))
        self.travel("CARTRIDGE", f0, f1, back)
        self.travel("CERT-CA1", f0, f1, (out, *tuple(lo.add(p, (0.0, 0.0, 0.3)) for p in back[1:])))
        self.glow_to("MODULE-ROOT", f0, f0 + 9, OFF_GLOW, "EASE_IN")
        self.glow_to("KEY-ROOT-PRIV", f0, f0 + 9, OFF_GLOW, "EASE_IN")
        self.glow_to("PRESSHEAD-ROOT", f0, f0 + 9, OFF_GLOW, "EASE_IN")
        f0, f1 = self.event("E-05.2f")  # CA 1 installs it in its crown
        self.go("CERT-CA1", f0, f1, crown, "SETTLE")
        self.glow_to("CERT-CA1", f0, f1, glow_value(R.ISSUING_CA1, 1.0))
        self.hide("CARTRIDGE", f0, 9, sink=(0.0, 0.0, 0.0))
        for i in range(lo.FOOTPRINT_COUNT):
            self.hide(f"FOOT-{i + 1:02d}", f0 + (i % 4), 9, sink=(0.0, 0.0, 0.0))
        # B-05.3: back in the present, a gold-to-cyan trust link grows from the root down to CA 1's certificate.
        f0, f1 = self.event("E-05.3a")
        self.grow("TL-CA1", f0, f1, hex_glow(palette.TEXT_HEX, 1.0))

    # ------------------------------------------------------------------ S6
    def s6(self) -> None:
        R = ColourRole
        amber = glow_value(R.PENDING, palette.GLOW_ACTIVE)
        green = glow_value(R.VALIDATED, palette.GLOW_ACTIVE)
        # B-06.1: a fresh pulse; the server presents its certificate with CA 1's copy and proves possession.
        f0, f1 = self.event("E-06.1a")
        pulse_path = tuple(lo.at_z(p, lo.FLOOR_Z + PULSE_LIFT) for p in lo.CHANNEL_RDP)
        self.show("PULSE-RDP-2", f0, 9, rise=(0.0, 0.0, 0.0), glow=glow_value(R.PENDING, palette.GLOW_PEAK), at=pulse_path[0])
        frame_at = self.travel("PULSE-RDP-2", f0 + 9, f1, pulse_path)
        self.light_path("CH-RDP", len(lo.CHANNEL_RDP) - 1, pulse_path, frame_at, amber)
        self.glow_to("PORT-RDP-LISTEN", f1 - 6, f1, amber, "EASE_OUT")
        staging_cert = lo.add(lo.STACK_CERT, (0.9, 0.5, 0.0))
        staging_copy = lo.add(lo.STACK_INTERMEDIATE, (0.9, 0.5, 0.0))
        to_client = tuple(lo.at_z(p, TRAVEL_LIFT) for p in reversed(lo.CHANNEL_RDP))
        slot = lo.add(lo.RDP, lo.CERT_SLOT)
        copy_slot = lo.add(lo.RDP, lo.INTERMEDIATE_SLOT)
        front = lo.add(lo.RDP, (0.3, lo.FRONT_Y - 0.5, 1.2))
        f0, f1 = self.event("E-06.1b")
        self.travel("CERT-RDP", f0, f1, (slot, front, *to_client, staging_cert))
        f0, f1 = self.event("E-06.1c")
        self.travel("CERT-CA1-COPY-RDP", f0, f1, (copy_slot, lo.add(front, (0.0, 0.0, -0.3)), *tuple(lo.at_z(p, TRAVEL_LIFT + 0.4) for p in reversed(lo.CHANNEL_RDP)), staging_copy))
        f0, f1 = self.event("E-06.1d")  # a key pulse inside the closed container; the key does not move
        container = lo.add(lo.RDP, lo.CONTAINER)
        self.glow_pulse("KC-RDP", f0, f1, glow_value(R.REQUEST, palette.GLOW_PEAK), rest=OFF_GLOW)
        proof_start = lo.add(container, (0.0, 0.0, 0.5))
        self.show("HS-RDP", f0, 9, rise=(0.0, 0.0, 0.0), glow=glow_value(R.REQUEST, palette.GLOW_ACTIVE), at=proof_start)
        f0, f1 = self.event("E-06.1e")  # the signature impression follows the cards
        self.travel("HS-RDP", f0, f1, (proof_start, lo.add(front, (0.0, 0.0, 0.1)), *tuple(lo.at_z(p, TRAVEL_LIFT + 0.2) for p in reversed(lo.CHANNEL_RDP)), lo.add(staging_cert, (0.0, -0.1, 0.0))))
        f0, f1 = self.event("E-06.1f")  # pressed against the card's public-key emblem: matches, dissolves
        self.glow_pulse("HS-RDP", f0, f1 - 9, glow_value(R.VALIDATED, palette.GLOW_PEAK))
        self.hide("HS-RDP", f1 - 9, 9, sink=(0.0, 0.0, 0.0))
        self.glow_pulse("CERT-RDP", f0, f1, glow_value(R.ISSUING_CA1, 1.5), rest=glow_value(R.ISSUING_CA1, 1.1))
        # B-06.2: the cards dock upward under the root card that is already in the Trusted Root cradle.
        f0, f1 = self.event("E-06.2a")
        self.go("CERT-RDP", f0, f1, lo.STACK_CERT, "SETTLE")
        f0b, f1b = self.event("E-06.2b")
        self.go("CERT-CA1-COPY-RDP", f0b, f1b, lo.STACK_INTERMEDIATE, "SETTLE")
        f0c, f1c = self.event("E-06.2c")  # "installed earlier by policy": a shimmer in place; nothing travels
        self.glow_pulse("CERT-ROOT", f0c, f1c, glow_value(R.ROOT, palette.GLOW_PEAK), rest=glow_value(R.ROOT, 0.45))
        self.glow_to("TS-CLIENT-ROOT", f0c, f1c, glow_value(R.ROOT, 0.25))
        # B-06.3: the AIA indicator on the server card glows softly; the kiosk is passively highlighted; nothing travels.
        f0, f1 = self.event("E-06.3a")
        self.show("AIA-RDP", f0, 12, rise=(0.0, 0.0, 0.0), glow=hex_glow(palette.TEXT_HEX, 0.6), at=lo.add(lo.STACK_CERT, (0.42, 0.0, 0.0)))
        self.glow_pulse(m.PKI_HTTP, f0, f1, hex_glow(palette.TEXT_HEX, 0.5), rest=hex_glow(palette.TEXT_HEX, 0.12))
        self.hide("AIA-RDP", f1)
        # B-06.4: six checks beside the stack; the sixth waits, pending.
        for letter, ev_id in zip("abcde", ("E-06.4a", "E-06.4b", "E-06.4c", "E-06.4d", "E-06.4e"), strict=True):
            self.tick(f"TICK-RDP-{letter}", self.event(ev_id), green)
        f0, f1 = self.event("E-06.4f")
        self.show("TICK-RDP-f", f0, 12, rise=(0.0, 0.0, -0.1), glow=glow_value(R.PENDING, 0.9))
        # B-06.5: two restrained-amber CRL scrolls are fetched from the kiosk and dock, one per non-root link.
        rev = glow_value(R.REVOCATION, palette.GLOW_ACTIVE)
        kiosk_top = lo.add(lo.KIOSK, (0.0, 0.0, 1.55))
        to_stack = tuple(lo.at_z(p, TRAVEL_LIFT) for p in ((-7.0, 3.0, 0.0), (-9.5, -2.5, 0.0), (-10.2, -6.4, 0.0)))
        f0, f1 = self.event("E-06.5a")
        dock_cert = lo.add(lo.STACK_CERT, (0.62, 0.0, 0.0))
        self.show("CRL-CA1", f0, 9, rise=(0.0, 0.0, 0.0), glow=rev, at=kiosk_top)
        self.travel("CRL-CA1", f0 + 9, f1, (kiosk_top, *to_stack, dock_cert))
        f0, f1 = self.event("E-06.5b")
        dock_copy = lo.add(lo.STACK_INTERMEDIATE, (0.62, 0.0, 0.0))
        self.show("CRL-ROOT", f0, 9, rise=(0.0, 0.0, 0.0), glow=rev, at=lo.add(kiosk_top, (0.3, 0.0, 0.0)))
        self.travel("CRL-ROOT", f0 + 9, f1, (lo.add(kiosk_top, (0.3, 0.0, 0.0)), *to_stack, dock_copy))
        self.event("E-06.5c")  # OCSP note: a tag on the revocation check slot (labels)
        f0, f1 = self.event("E-06.5d")
        self.glow_to("TICK-RDP-f", f0, f1, green, "EASE_OUT")
        self.key_to("TICK-RDP-f", SCALE, f0, f0 + 6, (1.25, 1.25, 1.25), "EASE_OUT")
        self.key_to("TICK-RDP-f", SCALE, f0 + 6, f0 + 12, SHOWN, "SETTLE")
        # B-06.6: the channel turns green, from the laptop to the server; the session window opens.
        f0, f1 = self.event("E-06.6a")
        self.hide("CRL-CA1", f0 - 6, 9, sink=(0.0, 0.0, 0.0))
        self.hide("CRL-ROOT", f0 - 6, 9, sink=(0.0, 0.0, 0.0))
        self.recolour_path("CH-RDP", len(lo.CHANNEL_RDP) - 1, f0, f1, green)
        self.glow_to("PORT-RDP-LISTEN", f0, f1, green, "EASE_OUT")
        self.show("SCREEN-RDP", f1 - 18, 18, rise=(0.15, 0.0, 0.0), glow=hex_glow(palette.SCREEN_HEX, 0.9))
        for tick in ("a", "b", "c", "d", "e", "f"):
            self.hide(f"TICK-RDP-{tick}", f1 + 9, 9)

    # ------------------------------------------------------------------ S7
    def s7(self) -> None:
        R = ColourRole
        # B-07.1: the camera leaves the desk; the RDP cards peel off and go home; WEB01's template badge lights.
        b0 = self.beat("B-07.1")
        slot = lo.add(lo.RDP, lo.CERT_SLOT)
        copy_slot = lo.add(lo.RDP, lo.INTERMEDIATE_SLOT)
        front = lo.add(lo.RDP, (0.3, lo.FRONT_Y - 0.5, 1.2))
        home = tuple(lo.at_z(p, TRAVEL_LIFT) for p in lo.CHANNEL_RDP)
        self.travel("CERT-RDP", b0, b0 + 45, (self.current("CERT-RDP", LOCATION), *home, front, slot), "EASE_IN_OUT")
        self.travel("CERT-CA1-COPY-RDP", b0 + 6, b0 + 51, (self.current("CERT-CA1-COPY-RDP", LOCATION), *tuple(lo.at_z(p, TRAVEL_LIFT + 0.4) for p in lo.CHANNEL_RDP), lo.add(front, (0.0, 0.0, -0.3)), copy_slot), "EASE_IN_OUT")
        self.hide("SCREEN-RDP", b0 + 45)
        f0, f1 = self.event("E-07.1a")
        top = lo.add(lo.WEB, lo.TOP_PLATE)
        self.show("TPL-WEBTLS", f0, 18, rise=(0.0, 0.0, 0.5), glow=hex_glow(palette.TEXT_HEX, 0.8), at=top)
        # B-07.2: a compressed echo of S3 at the web server (the site name goes into the request information).
        self.key_ceremony("WEB", lo.WEB, "E-07.2a", "E-07.2b", "E-07.2c", "E-07.2d", compress=True)
        # B-07.3: the capsule waits at the port while a query goes to AD; only CA 2 is eligible.
        wait = lo.port_wait(lo.WEB, lo.WEB_PORT_SIDE)
        b0 = self.beat("B-07.3")
        capsule_at = lo.add(lo.WEB, lo.CAPSULE_SPOT)
        self.travel("REQ-WEB", b0, b0 + 15, (capsule_at, lo.add(lo.WEB, (-0.45, 0.05, 1.45)), wait))
        f0, f1 = self.event("E-07.3a")
        ad_front = lo.add(lo.AD, (0.9, -0.4, 1.8))
        q_start = lo.add(wait, (0.0, 0.25, 0.1))
        self.show("QUERY-WEB", f0, 9, rise=(0.0, 0.0, 0.0), glow=glow_value(R.DIRECTORY, palette.GLOW_ACTIVE), at=q_start)
        self.travel("QUERY-WEB", f0 + 9, f1, (q_start, lo.lerp(q_start, ad_front, 0.5), ad_front))
        f0b, f1b = self.event("E-07.3b")
        self.travel("QUERY-WEB", f0b, f0b + 24, (ad_front, lo.lerp(q_start, ad_front, 0.5), q_start))
        self.hide("QUERY-WEB", f0b + 24, 9, sink=(0.0, 0.0, 0.0))
        self.show("RING-AD-1", f0b, rise=(0.0, 0.0, 0.3), glow=glow_value(R.INELIGIBLE, 0.3))
        self.show("RING-AD-2", f0b + 3, rise=(0.0, 0.0, 0.3), glow=glow_value(R.ISSUING_CA2, palette.GLOW_ACTIVE))
        self.glow_to("TRIM-CA1", f0b + 6, f0b + 24, glow_value(R.INELIGIBLE, 0.5))
        self.glow_to("TRIM-CA2", f0b + 6, f0b + 24, glow_value(R.ISSUING_CA2, palette.GLOW_ACTIVE))
        self.glow_to("EVAL-CA2", f0b + 6, f0b + 24, glow_value(R.ISSUING_CA2, 0.25))
        span = max(3, (f1b - f0b - 24) // (len(lo.ROUTE_CA2) - 1))
        for i in range(1, len(lo.ROUTE_CA2)):
            start = f0b + 24 + (i - 1) * span
            self.glow_to(f"ROUTE-CA2-S{i}", start, start + 6, glow_value(R.ISSUING_CA2, palette.GLOW_ACTIVE), "EASE_OUT")
        # B-07.4: the capsule travels only along the violet route, into Issuing CA 2's vault.
        f0, f1 = self.event("E-07.4a")
        cradle = lo.add(lo.CA2, lo.CA_CRADLE)
        route = tuple(lo.at_z(p, 0.55) for p in lo.ROUTE_CA2)
        self.travel("REQ-WEB", f0, f1, (wait, lo.add(wait, (-0.4, 0.4, -0.6)), *route, lo.add(cradle, (0.0, -0.6, 0.5)), lo.add(cradle, (0.0, 0.0, 0.42))))

    # ------------------------------------------------------------------ S8
    def s8(self) -> None:
        R = ColourRole
        violet = glow_value(R.ISSUING_CA2, palette.GLOW_ACTIVE)
        # B-08.1: the same four checks, faster, in violet.
        for letter, ev_id in zip("abcd", ("E-08.1a", "E-08.1b", "E-08.1c", "E-08.1d"), strict=True):
            self.tick(f"TICK-CA2-{letter}", self.event(ev_id), violet)
        # B-08.2: consumed at the press; CA 2's sealed key drives it; the TLS certificate is stamped and returns.
        f0, f1 = self.event("E-08.2a")
        press = lo.add(lo.CA2, lo.CA_PRESS)
        self.travel("REQ-WEB", f0, f1, (self.current("REQ-WEB", LOCATION), lo.add(press, (-0.3, -0.5, 0.9)), lo.add(press, (0.0, 0.0, 0.7))))
        self.hide("REQ-WEB", f1, 9, sink=(0.0, 0.0, -0.1))
        f0, f1 = self.event("E-08.2b")
        self.glow_to("MODULE-CA2", f0, f0 + 9, violet, "EASE_OUT")
        self.glow_to("KEY-CA2-PRIV", f0, f0 + 9, violet, "EASE_OUT")
        self.glow_to("LINK-CA2", f0 + 6, f0 + 15, violet, "EASE_OUT")
        head = lo.add(press, (0.0, 0.0, 0.85))
        self.go("PRESSHEAD-CA2", f0 + 15, f0 + 24, lo.add(head, (0.0, 0.0, -0.35)), "EASE_IN")
        out = lo.add(lo.CA2, lo.CA_PRESS_OUT)
        self.show("CERT-WEB", f0 + 24, 15, rise=(0.0, 0.0, -0.2), glow=glow_value(R.ISSUING_CA2, 0.9), at=out)
        self.go("PRESSHEAD-CA2", f0 + 24, f0 + 36, head, "EASE_OUT")
        self.glow_to("LINK-CA2", f0 + 30, f1, OFF_GLOW, "EASE_IN")
        f0, f1 = self.event("E-08.2c")
        wait = lo.port_wait(lo.WEB, lo.WEB_PORT_SIDE)
        slot = lo.add(lo.WEB, lo.CERT_SLOT)
        cradle = lo.add(lo.CA2, lo.CA_CRADLE)
        back = (out, lo.add(cradle, (0.0, -0.7, 0.5)), *tuple(lo.at_z(p, 0.8) for p in reversed(lo.ROUTE_CA2))[:-1], wait, lo.add(slot, (-0.5, 0.0, 0.0)))
        self.travel("CERT-WEB", f0, f1, back)
        crown = lo.add(lo.CA2, (0.0, 0.0, lo.CA_CROWN[2] + 0.42))
        self.show("CERT-CA2-COPY-WEB", f0, 12, rise=(0.0, 0.0, 0.0), glow=glow_value(R.ISSUING_CA2, 0.8, GHOST_ALPHA), at=crown)
        copy_back = (crown, lo.add(lo.CA2, (0.0, -1.6, 1.5)), *tuple(lo.at_z(p, 1.2) for p in reversed(lo.ROUTE_CA2))[:-1], wait, lo.add(lo.WEB, (-0.9, 0.0, 0.55)))
        self.travel("CERT-CA2-COPY-WEB", f0 + 12, f1, copy_back)
        f0, f1 = self.event("E-08.2d")
        self.go("CERT-WEB", f0, f1, slot, "SETTLE")
        self.glow_to("CERT-WEB", f0, f1, glow_value(R.ISSUING_CA2, 1.1))
        f0, f1 = self.event("E-08.2e")
        self.go("CERT-CA2-COPY-WEB", f0, f1, lo.add(lo.WEB, lo.INTERMEDIATE_SLOT), "SETTLE")
        self.dim_path("ROUTE-CA2", len(lo.ROUTE_CA2) - 1, f1, f1 + 12, reverse=True)
        self.hide("RING-AD-1", f1)
        self.hide("RING-AD-2", f1)
        # B-08.3: CA 2's existing certificate brightens and a gold-to-violet link joins it to the same root.
        f0, f1 = self.event("E-08.3a")
        self.glow_to("CERT-CA2", f0, f1, glow_value(R.ISSUING_CA2, 1.0))
        self.grow("TL-CA2", f0, f1, hex_glow(palette.TEXT_HEX, 1.0))

    # ------------------------------------------------------------------ S9
    def s9(self) -> None:
        R = ColourRole
        amber = glow_value(R.PENDING, palette.GLOW_ACTIVE)
        green = glow_value(R.VALIDATED, palette.GLOW_ACTIVE)
        # B-09.1: browser validation of the web server.
        f0, f1 = self.event("E-09.1a")
        self.show("SCREEN-WEB", f0, 18, rise=(0.15, 0.0, 0.0), glow=hex_glow(palette.SCREEN_HEX, 0.9))
        path = tuple(lo.at_z(p, lo.FLOOR_Z + PULSE_LIFT) for p in lo.CHANNEL_WEB)
        self.show("PULSE-WEB", f0, 9, rise=(0.0, 0.0, 0.0), glow=glow_value(R.PENDING, palette.GLOW_PEAK), at=path[0])
        frame_at = self.travel("PULSE-WEB", f0 + 9, f1, path)
        self.light_path("CH-WEB", len(lo.CHANNEL_WEB) - 1, path, frame_at, amber)
        slot = lo.add(lo.WEB, lo.CERT_SLOT)
        copy_slot = lo.add(lo.WEB, lo.INTERMEDIATE_SLOT)
        front = lo.add(lo.WEB, (0.3, lo.FRONT_Y - 0.5, 1.2))
        to_client = tuple(lo.at_z(p, TRAVEL_LIFT) for p in reversed(lo.CHANNEL_WEB))
        staging_cert = lo.add(lo.STACK_CERT, (0.9, 0.5, 0.0))
        staging_copy = lo.add(lo.STACK_INTERMEDIATE, (0.9, 0.5, 0.0))
        f0, f1 = self.event("E-09.1b")
        self.travel("CERT-WEB", f0, f1, (slot, front, *to_client, staging_cert))
        f0, f1 = self.event("E-09.1c")
        self.travel("CERT-CA2-COPY-WEB", f0, f1, (copy_slot, lo.add(front, (0.0, 0.0, -0.3)), *tuple(lo.at_z(p, TRAVEL_LIFT + 0.4) for p in reversed(lo.CHANNEL_WEB)), staging_copy))
        f0, f1 = self.event("E-09.1d")
        container = lo.add(lo.WEB, lo.CONTAINER)
        self.glow_pulse("KC-WEB", f0, f1, glow_value(R.REQUEST, palette.GLOW_PEAK), rest=OFF_GLOW)
        proof_start = lo.add(container, (0.0, 0.0, 0.5))
        self.show("HS-WEB", f0, 6, rise=(0.0, 0.0, 0.0), glow=glow_value(R.REQUEST, palette.GLOW_ACTIVE), at=proof_start)
        f0, f1 = self.event("E-09.1e")
        self.travel("HS-WEB", f0, f1, (proof_start, lo.add(front, (0.0, 0.0, 0.1)), *tuple(lo.at_z(p, TRAVEL_LIFT + 0.2) for p in reversed(lo.CHANNEL_WEB)), lo.add(staging_cert, (0.0, -0.1, 0.0))))
        f0, f1 = self.event("E-09.1q")
        self.glow_pulse("HS-WEB", f0, f1 - 6, glow_value(R.VALIDATED, palette.GLOW_PEAK))
        self.hide("HS-WEB", f1 - 6, 6, sink=(0.0, 0.0, 0.0))
        f0, f1 = self.event("E-09.1f")
        self.go("CERT-WEB", f0, f1, lo.STACK_CERT, "SETTLE")
        f0, f1 = self.event("E-09.1g")
        self.go("CERT-CA2-COPY-WEB", f0, f1, lo.STACK_INTERMEDIATE, "SETTLE")
        self.event("E-09.1h")
        self.event("E-09.1i")  # chain-to-root and signature checks are conveyed by the docking (not shown as ticks)
        rows = (("a", "E-09.1j"), ("b", "E-09.1k"), ("c", "E-09.1l"), ("d", "E-09.1o"))
        for letter, ev_id in rows:
            self.tick(f"TICK-WEB-{letter}", self.event(ev_id), green)
        rev = glow_value(R.REVOCATION, palette.GLOW_ACTIVE)
        # compressed revocation: each CRL appears as a brief restrained-amber flicker docked against its card
        for scroll, ev_id, dock in (("CRL-CA2", "E-09.1m", lo.STACK_CERT), ("CRL-ROOT-2", "E-09.1n", lo.STACK_INTERMEDIATE)):
            f0, f1 = self.event(ev_id)
            self.show(scroll, f0, 6, rise=(0.0, 0.0, 0.0), glow=rev, at=lo.add(dock, (0.62, 0.0, 0.0)))
            self.hide(scroll, max(f0 + 6, f1 - 6), 6, sink=(0.0, 0.0, 0.0))
        self.glow_pulse(m.PKI_HTTP, self.beat("B-09.1", 3.2), self.beat("B-09.1", 3.8), hex_glow(palette.TEXT_HEX, 0.5), rest=hex_glow(palette.TEXT_HEX, 0.1))
        f0, f1 = self.event("E-09.1p")
        self.recolour_path("CH-WEB", len(lo.CHANNEL_WEB) - 1, f0, f1, green, reverse=False)
        for letter, _ in rows:
            self.hide(f"TICK-WEB-{letter}", f1 + 6, 9)
        # B-09.2: the cards go home; cyan and violet trust paths rise from the servers' certificates and converge at the root.
        b0 = self.beat("B-09.2")
        home = tuple(lo.at_z(p, TRAVEL_LIFT) for p in lo.CHANNEL_WEB)
        self.travel("CERT-WEB", b0, b0 + 60, (self.current("CERT-WEB", LOCATION), *home, front, slot), "EASE_IN_OUT")
        self.travel("CERT-CA2-COPY-WEB", b0 + 6, b0 + 66, (self.current("CERT-CA2-COPY-WEB", LOCATION), *tuple(lo.at_z(p, TRAVEL_LIFT + 0.4) for p in lo.CHANNEL_WEB), lo.add(front, (0.0, 0.0, -0.3)), copy_slot), "EASE_IN_OUT")
        self.hide("SCREEN-WEB", b0 + 60)
        f0, f1 = self.event("E-09.2a")
        self.grow("TP-RDP", f0, f1, glow_value(R.ISSUING_CA1, palette.GLOW_ACTIVE))
        f0, f1 = self.event("E-09.2b")
        self.grow("TP-WEB", f0, f1, glow_value(R.ISSUING_CA2, palette.GLOW_ACTIVE))
        # B-09.3: the world settles; the compositor fade-to-black is keyed from the same event (see compositor).
        self.event("E-09.3a")

    # ------------------------------------------------------------------ idle micro-motion
    def idle(self) -> None:
        """The stylized user breathes: a tiny, slow rise and fall (<= 2% of the figure's height)."""
        user = BY_ID[m.USER]
        amplitude = user.size[2] * motion.IDLE_AMPLITUDE_FRACTION
        half = round(motion.IDLE_PERIOD_S * timing.FPS / 2)
        frame, up = timing.FRAME_START, True
        base = user.home
        self._set(m.USER, LOCATION, frame, base, motion.SMOOTH)
        while frame + half <= FRAME_LAST:
            frame += half
            self._set(m.USER, LOCATION, frame, lo.add(base, (0.0, 0.0, amplitude if up else 0.0)), motion.SMOOTH)
            up = not up


def build_timeline() -> Timeline:
    return Choreographer().build()


def choreographer() -> Choreographer:
    chor = Choreographer()
    chor.build()
    return chor


def object_ids_without_tracks() -> list[str]:
    animated = set(build_timeline().objects())
    return [o.id for o in CATALOGUE if o.id not in animated]
