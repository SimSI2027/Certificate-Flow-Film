"""Build the film's .blend from the story model, timing, theme and stage plan (entry point).

Usage: blender -b --factory-startup --python-exit-code 1 -P blender/build_scene.py -- --out <file.blend> [--tier animatic]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the repository root, so `blender` and `cff` import

import bpy

from blender import camera_rig, captions_scene, compositor, lighting, signage, world
from blender.animation import write_timeline
from blender.common import ROOT, option, reset_scene, script_args
from blender.render_settings import apply_tier
from cff.stage import choreography, labels
from cff.stage.camera import CameraPlan
from cff.theme import render

BEAUTY_SCENE = "BEAUTY"


def build(out_path: str, tier_name: str) -> dict[str, object]:
    started = time.perf_counter()
    tier = render.tier(tier_name)
    scene = reset_scene()
    scene.name = BEAUTY_SCENE
    apply_tier(scene, tier)
    stage = bpy.data.collections.new("STAGE")
    rig = bpy.data.collections.new("RIG")
    signs = bpy.data.collections.new("LABELS")
    for collection in (stage, rig, signs):
        scene.collection.children.link(collection)

    world.build_world(scene)
    world.build_floor(stage)
    objects = world.build_actors(stage)

    timeline = choreography.build_timeline()
    labels.add_label_tracks(timeline)
    plan = CameraPlan(timeline)

    camera = camera_rig.build_rig(scene, rig, plan, use_dof=True)
    lighting.build_lights(rig, bpy.data.objects[camera_rig.LOOK_NAME], plan)
    label_objects = signage.build_labels(signs, objects, camera)
    keys = write_timeline(timeline, {**objects, **label_objects})
    compositor.build_compositor(scene, tier)
    captions_scene.build_caption_scene(tier)

    bpy.context.window_manager  # noqa: B018  (touch: keeps the background context alive for saving)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    return {
        "objects": len(objects),
        "labels": len(label_objects),
        "animated_objects": len(timeline.objects()),
        "keyframes": keys,
        "seconds": round(time.perf_counter() - started, 1),
        "out": out_path,
    }


def main() -> None:
    args = script_args()
    out = option(args, "out", str(ROOT / "renders" / "film.blend"))
    tier_name = option(args, "tier", "animatic")
    assert out is not None and tier_name is not None
    summary = build(out, tier_name)
    print("BUILD-SUMMARY", summary)


main()
