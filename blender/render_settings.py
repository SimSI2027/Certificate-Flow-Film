"""Scene-level render settings shared by the build script and the render script."""

from __future__ import annotations

import contextlib

import bpy

from blender.common import engine_id
from cff.story import timing
from cff.theme import look
from cff.theme.render import FPS, Tier

BEAUTY_VIEW = "AgX"  # the 3D beauty pass; text colours stay exact in the caption scene (Standard)
CAPTION_VIEW = "Standard"


def set_view_transform(scene: bpy.types.Scene, wanted: str) -> str:
    """Set the view transform (this build lists it per scene; an unknown name raises) and clear the look."""
    scene.view_settings.view_transform = wanted
    with contextlib.suppress(TypeError):  # the look enum is per view transform; "None" is its default and is already set
        scene.view_settings.look = "None"
    return scene.view_settings.view_transform


def apply_timing(scene: bpy.types.Scene) -> None:
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.frame_start = timing.FRAME_START
    scene.frame_end = timing.frame_end()


def apply_tier(scene: bpy.types.Scene, tier: Tier, transparent: bool = False) -> None:
    render = scene.render
    render.engine = engine_id()
    render.resolution_x = tier.width
    render.resolution_y = tier.height
    render.resolution_percentage = 100
    render.film_transparent = transparent
    render.image_settings.file_format = "PNG"
    render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    render.image_settings.color_depth = "8"
    render.use_overwrite = False  # long renders resume by skipping finished frames (Charter 3.7)
    render.use_placeholder = True
    render.use_motion_blur = tier.motion_blur and not transparent
    if hasattr(render, "motion_blur_position"):
        render.motion_blur_position = "START"  # shutter opens at the frame: no blend across the two cuts (V1-CIN-04)
    eevee = scene.eevee
    eevee.taa_render_samples = tier.taa_samples
    eevee.use_shadows = tier.shadows
    eevee.use_raytracing = tier.raytracing
    eevee.use_fast_gi = False
    if tier.volumetrics and not transparent:
        for name, value in (
            ("volumetric_start", look.VOLUME_START_M),
            ("volumetric_end", look.VOLUME_END_M),
            ("volumetric_tile_size", look.VOLUME_TILE_SIZE),
            ("volumetric_samples", look.VOLUME_SAMPLES),
            ("volumetric_sample_distribution", look.VOLUME_SAMPLE_DISTRIBUTION),
            ("volumetric_ray_depth", look.VOLUME_RAY_DEPTH),
            ("use_volumetric_shadows", True),
        ):
            if hasattr(eevee, name):
                setattr(eevee, name, value)
    set_view_transform(scene, CAPTION_VIEW if transparent else BEAUTY_VIEW)
    apply_timing(scene)
