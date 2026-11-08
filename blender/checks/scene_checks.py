"""In-Blender hard discriminators (Charter Section 12), evaluated frame by frame on the built scene.

Each check returns a list of failure strings (empty = pass) plus metrics. ``blender/run_checks.py`` runs them all and
writes ``results.json``; ``python -m tools verify`` fails if any check fails.

Measurement notes (the spec leaves these open; the choices are recorded in docs/PROJECT-STATE.md):
- World-space bounds come from the evaluated mesh bounding box (8 corners through ``matrix_world``).
- "Pop" (C-06/C-07): a visible object (scale above ``VISIBLE_SCALE`` on both frames) that moves farther than
  ``POP_MAX_M`` (or a quarter of its own size) between consecutive frames. Whitelisted fast effects (pulses, fetches,
  travelling artefacts) use the larger ``FAST_POP_MAX_M``. The screen-space displacement (fraction of frame width, camera frozen) is reported as a
  metric.
- Camera jerk is the second difference of the camera position, as a fraction of the focus distance.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

from blender.common import PROP_CAP, PROP_ID, PROP_KIND, PROP_LABEL, bundled_font, glyph_cap_ratio
from cff.stage import camera as stage_camera
from cff.stage import labels as stage_labels
from cff.stage import signs as stage_signs
from cff.stage.objects import CATALOGUE, Kind
from cff.story import captions as story_captions
from cff.story import model as m
from cff.story import timing
from cff.theme import motion, render, shots, typography

VISIBLE_SCALE = 0.05
CONTAINMENT_TOLERANCE_M = 0.08
ROOT_CLEARANCE_M = 0.05
SCREEN_MIN_DEPTH_M = 0.5  # screen displacement is reported only for points at least this far in front of the lens
ROOT_NEIGHBOURHOOD_M = 12.0  # objects farther than this from the sealed vault cannot touch it (cheap pre-filter)
POP_MAX_M = 0.35
FAST_POP_MAX_M = 3.6  # whitelisted travel along channels and routes: light-speed data (a 27 m route in 0.8 s peaks near 3.5 m/frame), never a teleport
RISE_POP_MAX_M = 0.8  # the Root CA complex rises 7 m into place during B-05.1
RISE_KINDS = frozenset({Kind.DAIS, Kind.PLINTH, Kind.ROOT_VAULT, Kind.READER, Kind.PRESS, Kind.PRESS_HEAD, Kind.MODULE})
POP_SIZE_FRACTION = 0.25  # a big object may also move a quarter of its own size per frame (the rising Root CA complex)
FAST_KINDS = frozenset({Kind.PULSE, Kind.QUERY, Kind.SCROLL, Kind.PROOF, Kind.CAPSULE, Kind.CARD, Kind.CARTRIDGE, Kind.KEY_PRIVATE, Kind.KEY_PUBLIC,
                        Kind.BADGE, Kind.TILE, Kind.BAND, Kind.SEAL_RING})  # a closed seal ring rides with its capsule (PKI-S1R1-01)
MAX_CAMERA_JERK_FRACTION = 0.004
FILM_OPEN_SETTLE_FRAMES = 6  # the first keys carry flat end handles, so jerk is judged once the opening move has started
TITLE_SAFE = (96.0, 54.0, 1824.0, 1026.0)  # x0, y0, x1, y1 at 1920x1080 (L-03)
CAPTION_MIN_CAP_PX = 30.0
LABEL_MIN_CAP_PX = 18.0
CAPTION_CLEAR_S = timing.CAPTION_MIN_GAP_S
ALPHA_VISIBLE = 0.01
SAMPLE_STEP = 1
FAULT_TAG = "cff_fault"  # set on every scene of a deliberately broken variant (Charter 2.8)

Failures = list[str]


@dataclass
class Result:
    name: str
    failures: Failures = field(default_factory=list)
    metrics: dict[str, object] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.failures


# --- geometry helpers --------------------------------------------------------------------------


def world_bounds(ob: bpy.types.Object) -> tuple[Vector, Vector]:
    corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return lo, hi


def union(bounds: list[tuple[Vector, Vector]]) -> tuple[Vector, Vector]:
    lo = Vector((min(b[0].x for b in bounds), min(b[0].y for b in bounds), min(b[0].z for b in bounds)))
    hi = Vector((max(b[1].x for b in bounds), max(b[1].y for b in bounds), max(b[1].z for b in bounds)))
    return lo, hi


def inside(inner: tuple[Vector, Vector], outer: tuple[Vector, Vector], tol: float) -> bool:
    return all(inner[0][i] >= outer[0][i] - tol and inner[1][i] <= outer[1][i] + tol for i in range(3))


def overlaps(a: tuple[Vector, Vector], b: tuple[Vector, Vector], margin: float = 0.0) -> bool:
    return all(a[0][i] < b[1][i] + margin and a[1][i] > b[0][i] - margin for i in range(3))


def is_visible(ob: bpy.types.Object) -> bool:
    return min(abs(s) for s in ob.scale) > VISIBLE_SCALE


def objects_by_id(scene: bpy.types.Scene) -> dict[str, bpy.types.Object]:
    return {ob[PROP_ID]: ob for ob in scene.objects if PROP_ID in ob}


def frames(scene: bpy.types.Scene, step: int = SAMPLE_STEP) -> range:
    return range(scene.frame_start, scene.frame_end + 1, step)


# --- scene structure -------------------------------------------------------------------------------


def check_frame_range(scene: bpy.types.Scene) -> Result:
    r = Result("frame_range")
    if scene.frame_start != timing.FRAME_START or scene.frame_end != timing.frame_end():
        r.failures.append(f"frame range {scene.frame_start}-{scene.frame_end}, timing says {timing.FRAME_START}-{timing.frame_end()}")
    if scene.render.fps != timing.FPS or scene.render.fps_base != 1.0:
        r.failures.append(f"fps {scene.render.fps}/{scene.render.fps_base}, timing says {timing.FPS}")
    r.metrics = {"frame_end": scene.frame_end, "fps": scene.render.fps}
    return r


def check_camera_count(scene: bpy.types.Scene) -> Result:
    r = Result("one_camera")
    cams = [ob for ob in scene.objects if ob.type == "CAMERA"]
    if len(cams) != 1:
        r.failures.append(f"{len(cams)} cameras in the beauty scene (C-02 wants exactly 1)")
    else:
        data = cams[0].data
        if data.type != "PERSP":
            r.failures.append("beauty camera is not perspective (C-09)")
    r.metrics = {"cameras": len(cams)}
    return r


def check_shape_vocabulary(scene: bpy.types.Scene) -> Result:
    """C-01: no arrow glyphs anywhere in names or label text; every line-like object is a channel, route, link or beam."""
    r = Result("no_diagram_grammar")
    arrows = "→⇒▶➔➜➤"
    line_kinds = {Kind.CHANNEL.value, Kind.ROUTE.value, Kind.TRUST_LINK.value, Kind.BEAM.value}
    for ob in scene.objects:
        text = ob.get(PROP_LABEL, "") + ob.name
        if any(a in text for a in arrows) or "arrow" in ob.name.lower():
            r.failures.append(f"{ob.name}: arrow grammar")
    known = {k.value for k in Kind}
    for ob in scene.objects:
        kind = ob.get(PROP_KIND)
        if kind in known and kind in {"channel", "route_segment", "trust_link", "beam"} and kind not in line_kinds:
            r.failures.append(f"{ob.name}: unexpected line-like kind {kind}")
    return r


# --- keyframe hygiene ---------------------------------------------------------------------------------


def all_fcurves() -> list[tuple[str, bpy.types.FCurve]]:
    out: list[tuple[str, bpy.types.FCurve]] = []
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    out.extend((action.name, fc) for fc in bag.fcurves)
    return out


def check_keyframes() -> Result:
    r = Result("keyframes")
    count = 0
    for action, fc in all_fcurves():
        previous = -math.inf
        for kp in fc.keyframe_points:
            count += 1
            frame, value = kp.co
            if not (math.isfinite(frame) and math.isfinite(value)):
                r.failures.append(f"{action} {fc.data_path}[{fc.array_index}]: non-finite key at {frame}")
            if frame <= previous:
                r.failures.append(f"{action} {fc.data_path}[{fc.array_index}]: keys not strictly ordered at {frame}")
            previous = frame
            if kp.interpolation == "LINEAR" and fc.data_path not in motion.LINEAR_WHITELIST:
                r.failures.append(f"{action} {fc.data_path}[{fc.array_index}]: LINEAR interpolation at {frame}")
    r.metrics = {"fcurves": len(all_fcurves()), "keys": count}
    return r


# --- containment, isolation, routes -------------------------------------------------------------------


def _owner_bounds(objs: dict[str, bpy.types.Object]) -> dict[str, tuple[Vector, Vector]]:
    """Bounds of what contains an actor's keys: its chassis or vault; for the root, the sealed complex and its dais."""
    shells = {Kind.CHASSIS, Kind.CA_VAULT, Kind.ROOT_VAULT, Kind.PLINTH, Kind.DAIS}
    grouped: dict[str, list[tuple[Vector, Vector]]] = {}
    for o in CATALOGUE:
        if o.kind in shells and o.owner:
            grouped.setdefault(o.owner, []).append(world_bounds(objs[o.id]))
    out = {owner: union(bounds) for owner, bounds in grouped.items()}
    return out


def _root_sealed(objs: dict[str, bpy.types.Object]) -> tuple[Vector, Vector]:
    return union([world_bounds(objs[m.ROOT_CA]), world_bounds(objs["ROOT-PLINTH"])])


def check_dynamic(scene: bpy.types.Scene) -> list[Result]:
    """Key containment, root isolation, route integrity, and pop detection, in one pass over the frames."""
    objs = objects_by_id(scene)
    scene.frame_set(scene.frame_end)  # static shells (and the risen Root CA complex) are measured at their rest pose
    sealed = _root_sealed(objs)
    keys =[o for o in CATALOGUE if o.kind is Kind.KEY_PRIVATE and o.owner]
    capsules = [o for o in CATALOGUE if o.kind is Kind.CAPSULE]
    channel_kinds = {Kind.CHANNEL, Kind.ROUTE}
    channels = [o for o in CATALOGUE if o.kind in channel_kinds]
    # actor shells that capsules may not enter: everything except the capsule's own route
    actor_shells = {o.owner or o.id: o.id for o in CATALOGUE if o.kind in {Kind.CHASSIS, Kind.CA_VAULT, Kind.AD_COLUMN, Kind.KIOSK, Kind.LAPTOP, Kind.FIGURE}}
    allowed = {
        "REQ-RDP": {m.RDP_SERVER, m.ISSUING_CA1},
        "REQ-WEB": {m.WEB_SERVER, m.ISSUING_CA2},
        "REQ-CA1": {m.ISSUING_CA1},
    }
    sealed_centre = (sealed[0] + sealed[1]) / 2
    # The whole root complex (dais, reader bay, press, key module, plinth, vault) at its rest pose. End-entity requests
    # and end-entity certificates may never reach any of it (AR-02; found by the Charter 2.8 mutation run, root_issues_leaf: a request
    # parked at the root's press and a server certificate stamped there both passed the vault-and-plinth test).
    complex_bounds = union([world_bounds(objs[o.id]) for o in CATALOGUE if o.owner == m.ROOT_CA])
    end_entity = sorted({r.id for r in m.MODEL.requests if r.kind is m.RequestKind.END_ENTITY}
                        | {c.id for c in m.MODEL.certificates if m.MODEL.issuer_actor(c.id) != m.ROOT_CA and c.id in objs})
    touchers = [o for o in CATALOGUE if o.owner != m.ROOT_CA and o.kind is not Kind.TRUST_LINK]
    contain, isolate, routes, pops = Result("key_containment"), Result("root_isolation"), Result("route_integrity"), Result("no_pops")
    moving = [o for o in CATALOGUE if o.kind not in {Kind.CHANNEL, Kind.ROUTE}]
    last_pos: dict[str, Vector] = {}
    last_visible: dict[str, bool] = {}
    screen_max = 0.0
    camera = scene.camera
    shell_bounds = {actor: world_bounds(objs[oid]) for actor, oid in actor_shells.items()}
    reported: set[str] = set()
    for frame in frames(scene):
        scene.frame_set(frame)
        owners = _owner_bounds(objs)  # per frame: the Root CA complex rises into place during B-05.1
        for k in keys:
            ob = objs[k.id]
            if is_visible(ob) and not inside(world_bounds(ob), owners[k.owner or ""], CONTAINMENT_TOLERANCE_M):
                contain.failures.append(f"frame {frame}: {k.id} leaves {k.owner}'s bounds")
                break
        for c in capsules:
            ob = objs[c.id]
            if not is_visible(ob):
                continue
            box = world_bounds(ob)
            if overlaps(box, sealed, ROOT_CLEARANCE_M):
                isolate.failures.append(f"frame {frame}: {c.id} intersects the Root CA vault or plinth")
            for actor, bounds in shell_bounds.items():
                if actor in allowed[c.id]:
                    continue
                if overlaps(box, bounds) and f"{c.id}:{actor}" not in reported:
                    reported.add(f"{c.id}:{actor}")
                    routes.failures.append(f"frame {frame}: {c.id} enters {actor}'s bounds")
        for oid in end_entity:
            ob = objs[oid]
            if is_visible(ob) and overlaps(world_bounds(ob), complex_bounds, ROOT_CLEARANCE_M) and f"ee:{oid}" not in reported:
                reported.add(f"ee:{oid}")
                isolate.failures.append(f"frame {frame}: {oid} (end-entity) reaches the Root CA complex")
        for ch in channels:
            if frame == scene.frame_start and overlaps(world_bounds(objs[ch.id]), sealed, ROOT_CLEARANCE_M):
                isolate.failures.append(f"{ch.id}: network geometry touches the Root CA plinth or vault")
        for o in touchers:  # only trust-link geometry (and the root's own parts) may touch the sealed vault or its plinth
            ob = objs[o.id]
            near = (ob.matrix_world.translation - sealed_centre).length < ROOT_NEIGHBOURHOOD_M
            if is_visible(ob) and near and overlaps(world_bounds(ob), sealed, ROOT_CLEARANCE_M) and f"touch:{o.id}" not in reported:
                reported.add(f"touch:{o.id}")
                isolate.failures.append(f"frame {frame}: {o.id} touches the Root CA vault or plinth but is not a trust link")
        for o in moving:
            ob = objs[o.id]
            pos = ob.matrix_world.translation.copy()
            vis = is_visible(ob)
            if o.id in last_pos and vis and last_visible[o.id]:
                step = (pos - last_pos[o.id]).length
                base = FAST_POP_MAX_M if o.kind in FAST_KINDS else RISE_POP_MAX_M if o.kind in RISE_KINDS else POP_MAX_M
                limit = max(base, POP_SIZE_FRACTION * max(o.size))
                if step > limit and o.id not in reported:
                    reported.add(o.id)
                    pops.failures.append(f"frame {frame}: {o.id} moves {step:.2f} m in one frame (limit {limit})")
                if camera is not None and step > 0.0:
                    a = world_to_camera_view(scene, camera, last_pos[o.id])
                    b = world_to_camera_view(scene, camera, pos)
                    if a.z > SCREEN_MIN_DEPTH_M and b.z > SCREEN_MIN_DEPTH_M and -0.5 <= a.x <= 1.5 and -0.5 <= b.x <= 1.5:
                        screen_max = max(screen_max, abs(b.x - a.x))  # on or near the frame only: a point at the lens would blow up
            last_pos[o.id], last_visible[o.id] = pos, vis
    pops.metrics = {"max_screen_displacement_fraction_of_width": round(screen_max, 3)}
    contain.metrics = {"private_keys": len(keys)}
    routes.metrics = {"capsules": len(capsules)}
    return [contain, isolate, routes, pops]


# --- camera motion ----------------------------------------------------------------------------------------


def check_camera_motion(scene: bpy.types.Scene) -> Result:
    """C-02 on the built camera: per-frame translation / rotation / lens change, exactly the declared cuts, jerk."""
    r = Result("camera_motion")
    cam = scene.camera
    focus = bpy.data.objects.get("CAM_FOCUS")
    assert cam is not None and focus is not None
    declared = {timing.seconds_to_frame(timing.beat_window(b)[0]) for b in timing.DECLARED_CUT_BEATS}
    previous_pos = previous_fwd = previous_lens = None
    previous_move = None
    cuts: list[int] = []
    worst = {"translation": 0.0, "rotation": 0.0, "lens": 0.0, "jerk": 0.0}
    for frame in frames(scene):
        scene.frame_set(frame)
        pos = cam.matrix_world.translation.copy()
        fwd = (cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))).normalized()
        lens = cam.data.lens
        distance = max((focus.matrix_world.translation - pos).length, 1e-6)
        if previous_pos is not None:
            move = pos - previous_pos
            frac = move.length / distance
            rot = math.degrees(previous_fwd.angle(fwd))
            is_cut = frac > stage_camera.CUT_TRANSLATION_FRACTION or rot > stage_camera.CUT_ROTATION_DEG
            if is_cut:
                cuts.append(frame)
            elif frame not in declared:
                worst["translation"] = max(worst["translation"], frac)
                worst["rotation"] = max(worst["rotation"], rot)
                worst["lens"] = max(worst["lens"], abs(lens - previous_lens))
                if frac > stage_camera.MAX_TRANSLATION_FRACTION:
                    r.failures.append(f"frame {frame}: camera moves {frac:.3f} of the focus distance")
                if rot > stage_camera.MAX_ROTATION_DEG:
                    r.failures.append(f"frame {frame}: camera turns {rot:.2f} degrees")
                if abs(lens - previous_lens) > stage_camera.MAX_LENS_STEP_MM:
                    r.failures.append(f"frame {frame}: lens changes {abs(lens - previous_lens):.2f} mm")
                if previous_move is not None and frame > timing.FRAME_START + FILM_OPEN_SETTLE_FRAMES:
                    jerk = (move - previous_move).length / distance
                    worst["jerk"] = max(worst["jerk"], jerk)
                    if jerk > MAX_CAMERA_JERK_FRACTION:
                        r.failures.append(f"frame {frame}: camera jerk {jerk:.4f} of the focus distance")
            previous_move = None if is_cut else move
        if not shots.LENS_MIN_MM - 1e-3 <= lens <= shots.LENS_MAX_MM + 1e-3:
            r.failures.append(f"frame {frame}: lens {lens:.1f} mm outside {shots.LENS_MIN_MM}-{shots.LENS_MAX_MM}")
        previous_pos, previous_fwd, previous_lens = pos, fwd, lens
    if cuts != sorted(declared):
        r.failures.append(f"cuts at {cuts}, declared {sorted(declared)}")
    r.metrics = {"cuts": cuts, **{k: round(v, 4) for k, v in worst.items()}}
    r.failures = r.failures[:40]
    return r


# --- captions and labels ---------------------------------------------------------------------------------------


def _animated(ob: bpy.types.Object, data_path: str, index: int, frame: int, default: float) -> float:
    """An animated property evaluated straight from the object's slotted action (or its static value).

    The caption layer is a second scene. In background mode only the context scene (BEAUTY) has a depsgraph, so
    ``frame_set`` on the caption scene does not reliably update its matrices or colours (found by the Charter 2.8 mutation run,
    caption_clip: the title-safe check measured every plate at the frame centre). Reading the F-curves directly is exact.
    """
    ad = ob.animation_data
    if ad is not None and ad.action is not None and ad.action_slot is not None:
        for layer in ad.action.layers:
            for strip in layer.strips:
                bag = strip.channelbag(ad.action_slot)
                if bag is not None:
                    curve = bag.fcurves.find(data_path, index=index)
                    if curve is not None:
                        return float(curve.evaluate(frame))
    return default


def _caption_alpha(ob: bpy.types.Object, frame: int) -> float:
    return _animated(ob, "color", 3, frame, float(ob.color[3]))


def _caption_matrix(ob: bpy.types.Object, frame: int) -> Matrix:
    """World matrix of a caption part (plate or glyphs) at ``frame``: the animated root times the part's own transform."""
    root = ob.parent
    loc = Vector([_animated(root, "location", i, frame, root.location[i]) for i in range(3)])
    root_matrix = Matrix.LocRotScale(loc, root.rotation_euler, root.scale)
    return root_matrix @ ob.matrix_parent_inverse @ ob.matrix_basis


def _caption_bounds(ob: bpy.types.Object, frame: int) -> tuple[Vector, Vector]:
    matrix = _caption_matrix(ob, frame)
    corners = [matrix @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return lo, hi


def check_captions() -> Result:
    r = Result("captions")
    scene = bpy.data.scenes.get("CAPTIONS")
    if scene is None:
        r.failures.append("no CAPTIONS scene")
        return r
    cam = scene.camera
    ortho = cam.data.ortho_scale
    px_per_unit = render.CAPTION_REFERENCE_WIDTH_PX / ortho
    texts = {ob[PROP_ID]: ob for ob in scene.objects if ob.get(PROP_KIND) == "caption"}
    plates = {k: next(c for c in ob.children if c.name.startswith("PLATE-")) for k, ob in texts.items()}
    glyphs = {k: next(c for c in ob.children if c.name.startswith("TXT-")) for k, ob in texts.items()}
    visible_frames: dict[str, list[int]] = {k: [] for k in texts}
    for frame in frames(scene):
        shown = [k for k in texts if _caption_alpha(plates[k], frame) > ALPHA_VISIBLE or _caption_alpha(glyphs[k], frame) > ALPHA_VISIBLE]
        if len(shown) > 1:
            r.failures.append(f"frame {frame}: {len(shown)} captions visible at once ({', '.join(shown)})")
        for k in shown:
            visible_frames[k].append(frame)
    order = sorted((frames_[0], frames_[-1], k) for k, frames_ in visible_frames.items() if frames_)
    clear = round(CAPTION_CLEAR_S * timing.FPS)
    for (_a0, a1, ka), (b0, _b1, kb) in itertools.pairwise(order):
        if b0 - a1 - 1 < clear:
            r.failures.append(f"{ka} and {kb}: only {b0 - a1 - 1} frames fully clear (need {clear})")
    # geometry on every visible frame (title-safe) and at the middle of each hold (cap height, measured from the glyphs)
    ref_w, ref_h = render.CAPTION_REFERENCE_WIDTH_PX, render.CAPTION_REFERENCE_HEIGHT_PX
    for caption in story_captions.CAPTIONS:
        ob = texts[caption.id]
        for frame in visible_frames[caption.id]:
            for part in (plates[caption.id], glyphs[caption.id]):
                lo, hi = _caption_bounds(part, frame)
                x0, x1 = ref_w / 2 + lo.x * px_per_unit, ref_w / 2 + hi.x * px_per_unit
                y0, y1 = ref_h / 2 - hi.y * px_per_unit, ref_h / 2 - lo.y * px_per_unit
                if x0 < TITLE_SAFE[0] or x1 > TITLE_SAFE[2] or y0 < TITLE_SAFE[1] or y1 > TITLE_SAFE[3]:
                    r.failures.append(f"{caption.id}: frame {frame}: {part.name} ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f}) leaves the title-safe area")
                    break
            else:
                continue
            break
        mid = timing.FRAME_START + round((caption.hold_start_s + caption.hold_end_s) / 2 * timing.FPS)
        glyph = glyphs[caption.id]
        cap_px = glyph.data.size * _cap_ratio(glyph.data.font) * _caption_matrix(glyph, mid).to_scale().y * px_per_unit  # LEG-S1R1-03
        if cap_px < CAPTION_MIN_CAP_PX:
            r.failures.append(f"{caption.id}: cap height {cap_px:.1f} px < {CAPTION_MIN_CAP_PX} (measured from the glyphs)")
        if abs(cap_px - float(ob[PROP_CAP]) * px_per_unit) > 0.5:
            r.failures.append(f"{caption.id}: glyphs are {cap_px:.1f} px but the caption is tagged {float(ob[PROP_CAP]) * px_per_unit:.1f} px")
        hold = caption.hold_s
        if hold + 1e-9 < caption.required_hold_s:
            r.failures.append(f"{caption.id}: hold {hold:.2f} s < {caption.required_hold_s:.2f} s")
    r.metrics = {"captions": len(texts)}
    return r


_CAP_RATIOS: dict[str, float] = {}


def _cap_ratio(font: bpy.types.VectorFont) -> float:
    key = font.filepath or font.name
    if key not in _CAP_RATIOS:
        _CAP_RATIOS[key] = glyph_cap_ratio(font)
    return _CAP_RATIOS[key]


def check_fonts() -> Result:
    """The cap ratios the layout plans with (cff.theme.typography) match the glyphs this Blender build draws (LEG-S1R1-03)."""
    r = Result("fonts")
    measured: dict[str, float] = {}
    for name, planned in typography.CAP_RATIO.items():
        ratio = _cap_ratio(bundled_font(name))
        measured[name] = round(ratio, 4)
        if abs(ratio - planned) > typography.CAP_RATIO_TOLERANCE:
            r.failures.append(f"{name}: measured cap ratio {ratio:.4f} differs from the planned {planned:.4f}")
    r.metrics = {"cap_ratio": measured}
    return r


def check_text_materials() -> Result:
    """Text-pass materials (captions, signs) never use dithered transparency, which stipples glyphs (LEG-S1R1-01)."""
    r = Result("text_materials")
    for scene_name in ("CAPTIONS", "SIGNS"):
        scene = bpy.data.scenes.get(scene_name)
        if scene is None:
            r.failures.append(f"no {scene_name} scene")
            continue
        for ob in scene.objects:
            for slot in getattr(ob.data, "materials", []) or []:
                if slot is not None and slot.surface_render_method == "DITHERED":
                    r.failures.append(f"{scene_name}/{ob.name}: material {slot.name} is DITHERED")
    beauty_text = [ob.name for ob in bpy.data.scenes["BEAUTY"].objects if ob.type == "FONT"]
    if beauty_text:
        r.failures.append(f"text objects in the BEAUTY pass (signs belong to the SIGNS pass): {beauty_text[:5]}")
    return r


SIGN_POSITION_TOLERANCE = 0.002  # metres per metre of depth
SIGN_CHECK_STEP = 3


def check_signs(scene: bpy.types.Scene) -> Result:
    """L-01 / L-03 / L-06 for every sign, measured in Blender against the beauty camera.

    The SIGNS scene is not the context scene, so sign transforms are read from their F-curves (as for captions); the
    beauty camera is evaluated with ``frame_set``. On every ``SIGN_CHECK_STEP``-th fully shown frame each sign must:
    sit where the sign plan put it; have a glyph cap height (font size x measured cap ratio x scale, projected) of at least
    18 px at 1080p; and have its plate inside title-safe. Every must-read label must be fully shown for >= 1.5 s (or its
    whole window) inside its must-read beats, measured on the keyed opacity.
    """
    r = Result("signs")
    board = bpy.data.scenes.get("SIGNS")
    if board is None:
        r.failures.append("no SIGNS scene")
        return r
    roots = {ob[PROP_ID]: ob for ob in board.objects if ob.get(PROP_KIND) == "sign"}
    missing = sorted({p.label_id for p in stage_labels.PLACEMENTS} - set(roots))
    if missing:
        r.failures.append(f"labels without a sign: {missing}")
    planned = stage_signs.plan_signs()
    camera = scene.camera
    worst_cap = math.inf
    checked = 0
    for frame in range(timing.FRAME_START, timing.frame_end() + 1, SIGN_CHECK_STEP):
        live = [(k, planned[k].frames[frame]) for k in roots if frame in planned[k].frames and planned[k].frames[frame].alpha >= 1.0 - 1e-6]
        if not live:
            continue
        scene.frame_set(frame)
        lens = camera.data.lens
        for label_id, plan_frame in live:
            root = roots[label_id]
            text = next(c for c in root.children if c.name.startswith("TXT-"))
            loc = Vector([_animated(root, "location", i, frame, root.location[i]) for i in range(3)])
            scale = _animated(root, "scale", 0, frame, root.scale[0])
            alpha = _animated(text, "color", 3, frame, float(text.color[3]))
            view = world_to_camera_view(scene, camera, loc)
            if view.z <= 0:
                r.failures.append(f"{label_id}: frame {frame}: behind the camera")
                continue
            if (loc - Vector(plan_frame.origin)).length > SIGN_POSITION_TOLERANCE * view.z + 1e-4 or alpha < 0.99:
                r.failures.append(f"{label_id}: frame {frame}: keyed sign differs from the plan (offset {(loc - Vector(plan_frame.origin)).length:.4f} m, alpha {alpha:.2f})")
                continue
            cap_m = text.data.size * _cap_ratio(text.data.font) * scale
            cap_px = cap_m / view.z * (lens / shots.SENSOR_WIDTH_MM) * render.CAPTION_REFERENCE_WIDTH_PX
            worst_cap = min(worst_cap, cap_px)
            x0, y0, x1, y1 = plan_frame.rect
            centre = (view.x * render.CAPTION_REFERENCE_WIDTH_PX, (1 - view.y) * render.CAPTION_REFERENCE_HEIGHT_PX)
            anchor_x = centre[0] - (typography.SIGN_CAP_PX * typography.SIGN_PLATE_MARGIN_CAPS if stage_labels.BY_ID[label_id].align == "LEFT" else (x1 - x0) / 2)
            if abs(anchor_x - x0) > 2.0 or abs(centre[1] - (y0 + y1) / 2) > 2.0:
                r.failures.append(f"{label_id}: frame {frame}: projected at ({centre[0]:.0f},{centre[1]:.0f}), planned plate ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})")
            if cap_px < LABEL_MIN_CAP_PX:
                r.failures.append(f"{label_id}: frame {frame}: cap height {cap_px:.1f} px < {LABEL_MIN_CAP_PX}")
            if x0 < TITLE_SAFE[0] or y0 < TITLE_SAFE[1] or x1 > TITLE_SAFE[2] or y1 > TITLE_SAFE[3]:
                r.failures.append(f"{label_id}: frame {frame}: plate leaves title-safe")
            checked += 1
    for placement in stage_labels.PLACEMENTS:
        must = stage_labels.must_read_frames(placement.label_id)
        if not must or placement.label_id not in roots:
            continue
        text = next(c for c in roots[placement.label_id].children if c.name.startswith("TXT-"))
        shown = sum(1 for f in must if _animated(text, "color", 3, f, float(text.color[3])) >= 0.99)
        needed = min(len(must), round(1.5 * timing.FPS))
        if shown < needed:
            r.failures.append(f"{placement.label_id}: fully shown on {shown} must-read frames, needs {needed} (L-06)")
    if len(r.failures) > 40:
        r.failures = [*r.failures[:40], f"... and {len(r.failures) - 40} more"]
    r.metrics = {"signs": len(roots), "checked_sign_frames": checked, "smallest_cap_px": round(worst_cap, 1) if checked else None}
    return r


def parent_chain_visible(ob: bpy.types.Object) -> bool:
    parent = ob.parent
    while parent is not None:
        if min(abs(s) for s in parent.scale) < VISIBLE_SCALE:
            return False
        parent = parent.parent
    return True


def check_provenance() -> Result:
    """A film build carries no fault tag: deliberately broken variants (Charter 2.8) can never pass as the film."""
    r = Result("build_provenance")
    for s in bpy.data.scenes:
        if FAULT_TAG in s:
            r.failures.append(f"scene {s.name} is a deliberately broken variant ({s[FAULT_TAG]})")
    return r


def run_all(scene: bpy.types.Scene) -> list[Result]:
    results = [check_provenance(), check_frame_range(scene), check_camera_count(scene), check_shape_vocabulary(scene), check_keyframes()]
    results += check_dynamic(scene)
    results.append(check_camera_motion(scene))
    results.append(check_captions())
    results += [check_fonts(), check_text_materials(), check_signs(scene)]
    return results
