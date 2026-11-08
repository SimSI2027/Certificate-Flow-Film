"""Measured object positions for a round packet: where each tracked artefact is on screen in each packet frame.

Usage: blender -b <film.blend> --factory-startup --python-exit-code 1 -P blender/locate.py -- --frames a,b,c --out <locator.json>

For every listed frame this writes the projected screen bounds of every visible private key, request capsule and
certificate card, plus the key containers and key modules (the places keys are stored), measured from the evaluated
scene through the scene camera. It is a measurement, like the text bounds in a legibility manifest: it carries no
verdict and makes no occlusion claim (an object can be measured inside the frame and still be hidden behind another).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

from blender.checks.scene_checks import is_visible, objects_by_id, parent_chain_visible
from blender.common import option, script_args
from cff.stage.objects import CATALOGUE, Kind
from cff.theme import render

TRACKED_KINDS = (Kind.KEY_PRIVATE, Kind.CAPSULE, Kind.CARD, Kind.CONTAINER, Kind.MODULE)
DESCRIPTION = (
    "Measured object positions. For each packet frame: the screen bounds of each visible private key, request capsule, "
    "certificate card, key container and key module, projected from the evaluated 3D scene through the film camera. "
    "Boxes are [x0, y0, x1, y1] in pixels of a {w}x{h} frame, origin top left. 'in_frame' is true when the box overlaps the frame. "
    "'depth_m' is the distance in front of the lens. Objects at zero scale (not yet formed, consumed or hidden) are not listed. "
    "These are measurements only: occlusion is not measured, so check each box against the frame image."
)


def screen_box(scene: bpy.types.Scene, ob: bpy.types.Object, width: int, height: int) -> dict[str, object] | None:
    camera = scene.camera
    corners = [world_to_camera_view(scene, camera, ob.matrix_world @ Vector(c)) for c in ob.bound_box]
    if all(c.z <= 0 for c in corners):
        return None  # entirely behind the lens
    front = [c for c in corners if c.z > 0]
    xs = [c.x * width for c in front]
    ys = [(1.0 - c.y) * height for c in front]
    box = [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]
    in_frame = box[2] >= 0 and box[0] <= width and box[3] >= 0 and box[1] <= height
    centre = world_to_camera_view(scene, camera, ob.matrix_world.translation)
    return {"box": box, "in_frame": in_frame, "depth_m": round(centre.z, 2)}


def locate(scene: bpy.types.Scene, wanted: list[int], width: int, height: int) -> dict[str, object]:
    objs = objects_by_id(scene)
    tracked = [o for o in CATALOGUE if o.kind in TRACKED_KINDS and o.id in objs]
    per_frame: dict[str, list[dict[str, object]]] = {}
    for frame in sorted(set(wanted)):
        scene.frame_set(frame)
        rows: list[dict[str, object]] = []
        for o in tracked:
            ob = objs[o.id]
            if not (is_visible(ob) and parent_chain_visible(ob)):
                continue
            measured = screen_box(scene, ob, width, height)
            if measured is not None:
                rows.append({"id": o.id, **measured})
        per_frame[f"{frame:04d}"] = rows
    return {
        "description": DESCRIPTION.format(w=width, h=height),
        "frame_size_px": [width, height],
        "objects": {o.id: {"kind": o.kind.value, "owner": o.owner} for o in tracked},
        "frames": per_frame,
    }


def main() -> None:
    args = script_args()
    out = option(args, "out")
    listed = option(args, "frames")
    tier = render.tier(option(args, "tier", "animatic") or "animatic")
    assert out and listed
    data = locate(bpy.data.scenes["BEAUTY"], [int(f) for f in listed.split(",")], tier.width, tier.height)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("LOCATOR", json.dumps({"frames": len(data["frames"]), "objects": len(data["objects"])}))  # type: ignore[arg-type]


main()
