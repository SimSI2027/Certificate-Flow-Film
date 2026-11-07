"""Render a frame range of one scene to a PNG sequence (resumable).

Usage: blender -b <film.blend> --factory-startup --python-exit-code 1 -P blender/render_frames.py --
           --scene BEAUTY|CAPTIONS --first N --last M --out <dir> [--tier animatic]
Existing frames are skipped (``use_overwrite = False``) and a placeholder is written first
(``use_placeholder = True``), so an interrupted chunk resumes where it stopped.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy

from blender.common import option, script_args
from blender.render_settings import apply_tier
from cff.theme import render

FRAME_PATTERN = "f_"


def render_range(scene_name: str, first: int, last: int, out_dir: Path, tier_name: str) -> dict[str, object]:
    scene = bpy.data.scenes[scene_name]
    apply_tier(scene, render.tier(tier_name), transparent=scene_name == "CAPTIONS")
    scene.frame_start, scene.frame_end = first, last
    out_dir.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out_dir / FRAME_PATTERN)
    started = time.perf_counter()
    bpy.ops.render.render(animation=True, scene=scene_name)
    return {"scene": scene_name, "first": first, "last": last, "seconds": round(time.perf_counter() - started, 1), "dir": str(out_dir)}


def render_list(scene_name: str, wanted: list[int], out_dir: Path, tier_name: str) -> dict[str, object]:
    """Render scattered frames (packet samples) as one-frame animation renders; frames already on disk are skipped.

    A still render of a scene that is not the context scene (CAPTIONS) is not animation-evaluated in background mode,
    so every frame is rendered through the animation path, exactly like ``render_range``.
    """
    scene = bpy.data.scenes[scene_name]
    apply_tier(scene, render.tier(tier_name), transparent=scene_name == "CAPTIONS")
    out_dir.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out_dir / FRAME_PATTERN)
    started = time.perf_counter()
    done = 0
    for frame in wanted:
        target = out_dir / f"{FRAME_PATTERN}{frame:04d}.png"
        if target.exists() and target.stat().st_size > 0:
            continue
        scene.frame_start = scene.frame_end = frame
        bpy.ops.render.render(animation=True, scene=scene_name)
        done += 1
    return {"scene": scene_name, "frames": len(wanted), "rendered": done, "seconds": round(time.perf_counter() - started, 1), "dir": str(out_dir)}


def main() -> None:
    args = script_args()
    scene_name = option(args, "scene", "BEAUTY")
    out = option(args, "out")
    tier_name = option(args, "tier", "animatic")
    assert scene_name and out and tier_name
    listed = option(args, "frames")
    if listed:
        print("RENDER-SUMMARY", render_list(scene_name, [int(f) for f in listed.split(",")], Path(out), tier_name))
        return
    first, last = int(option(args, "first", "1") or 1), int(option(args, "last", "1") or 1)
    print("RENDER-SUMMARY", render_range(scene_name, first, last, Path(out), tier_name))


main()
