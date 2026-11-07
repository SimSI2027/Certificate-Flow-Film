"""Discriminator calibration (Charter 2.8): deliberately broken variants of the animatic.

Only ``python -m tools calibrate <fault>`` runs this script. Nothing else in ``blender/`` imports it, and the normal
build (``blender/build_scene.py`` run as a script) never sets its hooks; ``tests/test_blender_static.py`` checks both.

Usage: blender -b --factory-startup --python-exit-code 1 -P blender/calibration.py -- --fault <name> --out <file.blend> [--tier animatic]

Faults (each one is a mutation of the real animatic, applied to the timeline before the camera is planned, or to the
built scene before it is saved, so that the camera, lights and captions treat it like any other content):
- ``private_key_leak``: the RDP private key leaves its container and rides inside the request capsule.
- ``root_issues_leaf``: the RDP request flies to the Root CA, and the root's press stamps the server certificate.
- ``flowchart``: a static, top-down, orthographic shot of flat boxes joined by lines.
- ``caption_clip``: a caption drawn at 14 px cap height that extends outside the title-safe area.
The blend is tagged with ``FAULT_PROP`` so its provenance is never ambiguous.
"""

from __future__ import annotations

import math
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bmesh
import bpy

from blender import build_scene, materials
from blender.captions_scene import CAPTION_SCENE, TEXT_TO_EM, UNIT_PX
from blender.common import LABEL_FONT, PROP_ID, ROOT, bundled_font, option, script_args
from cff.config import names as n
from cff.stage import choreography
from cff.stage import layout as lo
from cff.stage.objects import CATALOGUE
from cff.stage.tracks import GLOW, LOCATION, SCALE, Key, Timeline, Value
from cff.story import model as m
from cff.story import timing
from cff.theme import palette, render
from cff.theme.palette import ColourRole

FAULT_PROP = "cff_fault"
FAULTS = ("private_key_leak", "root_issues_leaf", "flowchart", "caption_clip")

# --- fault parameters (calibration only; never part of the film) -------------------------------------------
LEAK_ENTER_S = 0.5  # the private key slides from its container into the capsule over this long
LEAK_KEY_SCALE = 1.0  # full size: the key is larger than the capsule, so it visibly rides in (and through) it
LEAK_CAPSULE_SCALE = 1.0
ROOT_ARC_POINT: lo.Vec3 = (2.0, 10.0, 5.0)  # the request's flight arcs over the AD node toward the root
ROOT_PRESS_DIP_M = 0.35
CLIP_CAP_PX = 14.0
CLIP_CAPTION = "CAP-S4"
CLIP_LEFT_EDGE_PX = 30.0  # the clipped caption plate starts here, inside the frame but outside title-safe (96 px)
CHART_CAMERA_HEIGHT_M = 60.0
CHART_ORTHO_SCALE_M = 60.0
CHART_CENTRE: lo.Vec3 = (0.0, 7.0, 0.0)
CHART_BOX: lo.Vec3 = (8.0, 2.6, 0.1)
CHART_TEXT_SIZE_M = 0.7
CHART_LINE_WIDTH_M = 0.12
CHART_NODES: tuple[tuple[str, lo.Vec3], ...] = (
    (n.CLIENT_HOSTNAME, lo.CLIENT),
    (n.RDP_SERVER_HOSTNAME, lo.RDP),
    (n.WEB_SERVER_HOSTNAME, lo.WEB),
    (n.AD_DOMAIN_FQDN, lo.AD),
    (n.ISSUING_CA1_NAME, lo.CA1),
    (n.ISSUING_CA2_NAME, lo.CA2),
    (n.ROOT_CA_NAME, lo.ROOT),
    (n.PKI_HTTP_HOST, lo.KIOSK),
)
CHART_EDGES: tuple[tuple[int, int], ...] = ((0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (3, 5), (4, 6), (5, 6), (0, 7))


def _frames(seconds: float) -> int:
    return round(seconds * timing.FPS)


def _event(event_id: str) -> tuple[int, int]:
    ev = next(e for e in m.MODEL.events if e.id == event_id)
    return timing.seconds_to_frame(ev.start_s), timing.seconds_to_frame(ev.end_s)


def _beat(beat_id: str) -> tuple[int, int]:
    return timing.frame_range(*timing.beat_window(beat_id))


# --- timeline editing -------------------------------------------------------------------------------------------


def _keys(tl: Timeline, obj: str, channel: str) -> dict[int, Key]:
    return tl.tracks.setdefault((obj, channel), {})


def _drop(tl: Timeline, obj: str, channel: str, first: int, last: int) -> None:
    track = _keys(tl, obj, channel)
    for frame in [f for f in track if first <= f <= last]:
        del track[frame]


def _value(tl: Timeline, obj: str, channel: str, frame: int) -> Value:
    value = tl.value_at(obj, channel, frame)
    assert value is not None, f"{obj}.{channel} has no keys"
    return value


def _scaled(value: Value, k: float) -> Value:
    return tuple(v * k for v in value)


def private_key_leak(tl: Timeline) -> None:
    capsule, key = "REQ-RDP", "KEY-RDP-PRIV"
    f0, _ = _event("E-03.3a")
    start = f0 + _frames(LEAK_ENTER_S)
    aboard = start + _frames(LEAK_ENTER_S)
    for frame, k in list(_keys(tl, capsule, SCALE).items()):
        _keys(tl, capsule, SCALE)[frame] = Key(frame, _scaled(k.value, LEAK_CAPSULE_SCALE), k.ease)
    here, size = _value(tl, key, LOCATION, start), _value(tl, key, SCALE, start)
    _drop(tl, key, LOCATION, start, timing.frame_end())
    _drop(tl, key, SCALE, start, timing.frame_end())
    tl.key(key, LOCATION, start, here)
    tl.key(key, SCALE, start, size)
    tl.key(key, SCALE, aboard, _scaled(size, LEAK_KEY_SCALE))
    tl.key(key, LOCATION, aboard, _value(tl, capsule, LOCATION, aboard))
    for k in tl.keys(capsule, LOCATION):
        if k.frame > aboard:
            tl.key(key, LOCATION, k.frame, k.value, k.ease)


def root_issues_leaf(tl: Timeline) -> None:
    gold = choreography.glow_value(ColourRole.ROOT, palette.GLOW_ACTIVE)
    # the root complex makes its own B-05.1 rise, unchanged, but early: during B-04.1, so it is there to receive the request
    rise0, _ = _beat("B-04.1")
    b51, b51_end = _beat("B-05.1")
    early = b51 - rise0
    for o in CATALOGUE:
        if o.owner != m.ROOT_CA:
            continue
        for channel in (LOCATION, SCALE):
            track = _keys(tl, o.id, channel)
            moved = {f: k for f, k in track.items() if b51 <= f <= b51_end}
            for f in moved:
                del track[f]
            for f, k in moved.items():
                track[f - early] = Key(f - early, k.value, k.ease)
            if moved:
                last = max(moved)
                track[b51_end] = Key(b51_end, moved[last].value, moved[last].ease)
    # the request leaves the RDP server's port and flies to the root's press instead of Issuing CA 1
    f42, f42_end = _event("E-04.2a")
    f44, f44_end = _event("E-04.4a")
    _drop(tl, "REQ-RDP", LOCATION, f42 + 1, timing.frame_end())
    at_root = lo.add(lo.ROOT_PRESS, (0.0, -0.6, 0.9))
    tl.key("REQ-RDP", LOCATION, (f42 + f42_end) // 2, ROOT_ARC_POINT)
    tl.key("REQ-RDP", LOCATION, f42_end, at_root)
    tl.key("REQ-RDP", LOCATION, f44, at_root)
    tl.key("REQ-RDP", LOCATION, f44_end, lo.add(lo.ROOT_PRESS, (0.0, 0.0, 0.7)))
    # the root's key module lights and its press stamps the RDP certificate; Issuing CA 1's press stays still
    s0, s1 = _event("E-04.4b")
    for oid in ("PRESSHEAD-CA1",):
        _drop(tl, oid, LOCATION, s0, s1)
    for oid in ("MODULE-CA1", "KEY-CA1-PRIV", "LINK-CA1"):
        _drop(tl, oid, GLOW, s0, s1)
    head = _value(tl, "PRESSHEAD-ROOT", LOCATION, s0)
    tl.key("PRESSHEAD-ROOT", LOCATION, s0 + _frames(0.3), head)
    tl.key("PRESSHEAD-ROOT", LOCATION, s0 + _frames(0.6), lo.add(head, (0.0, 0.0, -ROOT_PRESS_DIP_M)), "EASE_IN")
    tl.key("PRESSHEAD-ROOT", LOCATION, s0 + _frames(1.0), head, "EASE_OUT")
    for oid in ("MODULE-ROOT", "KEY-ROOT-PRIV", "PRESSHEAD-ROOT"):
        rest = _value(tl, oid, GLOW, s0)
        tl.key(oid, GLOW, s0, rest)
        tl.key(oid, GLOW, s0 + _frames(0.2), gold, "EASE_OUT")
        tl.key(oid, GLOW, s1, rest, "EASE_IN")
    # the stamped card is born at the root's press and starts its journey back from there
    e45, _ = _event("E-04.5a")
    shift = lo.sub(lo.add(lo.ROOT_PRESS, (0.0, -0.7, 0.45)), lo.add(lo.CA1, lo.CA_PRESS_OUT))
    track = _keys(tl, "CERT-RDP", LOCATION)
    for frame, k in list(track.items()):
        if s0 <= frame <= e45:
            track[frame] = Key(frame, lo.add(k.value, shift), k.ease)


# --- scene editing ----------------------------------------------------------------------------------------------


def caption_clip(scene: bpy.types.Scene, objects: dict[str, bpy.types.Object]) -> None:
    del scene, objects
    captions = bpy.data.scenes[CAPTION_SCENE]
    root = next(ob for ob in captions.objects if ob.get(PROP_ID) == CLIP_CAPTION)
    text = next(c for c in root.children if c.name.startswith("TXT-"))
    plate = next(c for c in root.children if c.name.startswith("PLATE-"))
    factor = (CLIP_CAP_PX / UNIT_PX * TEXT_TO_EM) / text.data.size
    text.data.size *= factor
    plate.scale = (factor, factor, 1.0)
    captions.view_layers[0].update()
    half_width_px = plate.dimensions.x / 2 * UNIT_PX  # dimensions already include the object scale
    centre_px = CLIP_LEFT_EDGE_PX + half_width_px
    dx = (centre_px - render.CAPTION_REFERENCE_WIDTH_PX / 2) / UNIT_PX
    for child in (text, plate):
        child.location.x = dx


def _flat_box(name: str, size: lo.Vec3, centre: lo.Vec3, yaw_deg: float, material: bpy.types.Material, collection: bpy.types.Collection) -> None:
    mesh = bpy.data.meshes.new(f"MESH-{name}")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    ob = bpy.data.objects.new(name, mesh)
    ob.location = centre
    ob.rotation_euler = (0.0, 0.0, math.radians(yaw_deg))
    collection.objects.link(ob)


def flowchart(scene: bpy.types.Scene, objects: dict[str, bpy.types.Object]) -> None:
    del objects
    for ob in scene.objects:  # the 3D world, labels, floor and lights are replaced by the chart
        if ob.type in {"MESH", "FONT", "CURVE", "LIGHT", "EMPTY"}:
            ob.hide_render = True
    cam = scene.camera
    cam.constraints.clear()
    cam.animation_data_clear()
    cam.data.animation_data_clear()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = CHART_ORTHO_SCALE_M
    cam.data.dof.use_dof = False
    cam.location = (CHART_CENTRE[0], CHART_CENTRE[1], CHART_CAMERA_HEIGHT_M)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    chart = bpy.data.collections.new("CHART")
    scene.collection.children.link(chart)
    box_mat, ink = materials.caption_material("plate"), materials.caption_material("text")
    for i, (label, at) in enumerate(CHART_NODES):
        _flat_box(f"CHART-BOX-{i}", CHART_BOX, lo.at_z(at, 0.5), 0.0, box_mat, chart)
        curve = bpy.data.curves.new(f"CHART-TXT-{i}", "FONT")
        curve.body = label
        curve.size = CHART_TEXT_SIZE_M
        curve.align_x, curve.align_y = "CENTER", "CENTER"
        curve.font = bundled_font(LABEL_FONT)
        curve.materials.append(ink)
        text = bpy.data.objects.new(f"CHART-TXT-{i}", curve)
        text.location = lo.at_z(at, 0.7)
        chart.objects.link(text)
    for a, b in CHART_EDGES:
        pa, pb = CHART_NODES[a][1], CHART_NODES[b][1]
        length = lo.dist(pa, pb)
        yaw = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
        _flat_box(f"CHART-LINE-{a}-{b}", (length, CHART_LINE_WIDTH_M, 0.05), lo.at_z(lo.lerp(pa, pb, 0.5), 0.3), yaw, ink, chart)
    for ob in list(chart.objects):  # the caption-layer materials fade by object alpha: keep the chart fully opaque
        ob.color = (1.0, 1.0, 1.0, 1.0)


TIMELINE_FAULTS: dict[str, Callable[[Timeline], None]] = {"private_key_leak": private_key_leak, "root_issues_leaf": root_issues_leaf}
SCENE_FAULTS: dict[str, Callable[[bpy.types.Scene, dict[str, bpy.types.Object]], None]] = {"flowchart": flowchart, "caption_clip": caption_clip}


def main() -> None:
    args = script_args()
    fault = option(args, "fault")
    out = option(args, "out", str(ROOT / "renders" / "calibration" / f"{fault}" / "film.blend"))
    tier_name = option(args, "tier", "animatic")
    if fault not in FAULTS:
        raise SystemExit(f"unknown fault {fault!r}; choose one of {', '.join(FAULTS)}")
    assert out is not None and tier_name is not None
    scene_fault = SCENE_FAULTS.get(fault)

    def tag_and_mutate(scene: bpy.types.Scene, objects: dict[str, bpy.types.Object]) -> None:
        if scene_fault is not None:
            scene_fault(scene, objects)
        for s in bpy.data.scenes:
            s[FAULT_PROP] = fault

    summary = build_scene.build(out, tier_name, timeline_hook=TIMELINE_FAULTS.get(fault), scene_hook=tag_and_mutate)
    print("CALIBRATION-BUILD", fault, summary)


main()
