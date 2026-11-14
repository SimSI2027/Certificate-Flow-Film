"""Build the film's .blend from the story model, timing, theme and stage plan (entry point).

Usage: blender -b --factory-startup --python-exit-code 1 -P blender/build_scene.py -- --out <file.blend> [--tier animatic]
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the repository root, so `blender` and `cff` import

import bpy

from blender import camera_rig, captions_scene, compositor, lighting, signs_scene, world
from blender.animation import write_timeline
from blender.common import ROOT, option, reset_scene, script_args
from blender.render_settings import apply_tier
from cff.stage import choreography
from cff.stage.camera import CameraPlan
from cff.stage.tracks import Timeline
from cff.theme import render

BEAUTY_SCENE = "BEAUTY"


TimelineHook = Callable[[Timeline], None]
SceneHook = Callable[[bpy.types.Scene, dict[str, bpy.types.Object]], None]


def build(out_path: str, tier_name: str, timeline_hook: TimelineHook | None = None, scene_hook: SceneHook | None = None) -> dict[str, object]:
    """Build and save the film. The hooks default to None; this entry script never sets them."""
    started = time.perf_counter()
    tier = render.tier(tier_name)
    scene = reset_scene()
    scene.name = BEAUTY_SCENE
    apply_tier(scene, tier)
    stage = bpy.data.collections.new("STAGE")
    rig = bpy.data.collections.new("RIG")
    for collection in (stage, rig):
        scene.collection.children.link(collection)

    world.build_world(scene, tier)
    world.build_floor(stage)
    backdrop = bpy.data.collections.new("BACKDROP")
    scene.collection.children.link(backdrop)
    world.build_backdrop(backdrop)
    objects = world.build_actors(stage)

    timeline = choreography.build_timeline()
    if timeline_hook is not None:
        timeline_hook(timeline)
    plan = CameraPlan(timeline)

    camera_rig.build_rig(scene, rig, plan, use_dof=True)
    lighting.build_lights(rig, bpy.data.objects[camera_rig.LOOK_NAME], plan)
    keys = write_timeline(timeline, objects)
    compositor.build_compositor(scene, tier)
    captions_scene.build_caption_scene(tier)
    sign_scene = signs_scene.build_signs_scene(tier, plan)
    if scene_hook is not None:
        scene_hook(scene, objects)

    bpy.context.window_manager  # noqa: B018  (touch: keeps the background context alive for saving)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    return {
        "objects": len(objects),
        "signs": len([o for o in sign_scene.objects if o.get("cff_kind") == "sign"]),
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


if __name__ == "__main__":  # Blender runs -P scripts as __main__; importing this module builds nothing
    main()
