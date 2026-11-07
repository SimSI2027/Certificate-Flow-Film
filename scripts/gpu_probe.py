"""Headless render probe (run inside Blender).

Usage:
  blender -b --factory-startup --python-exit-code 1 -P scripts/gpu_probe.py -- <engine> <out_png> <out_json>

<engine> is "eevee" or "cycles". The EEVEE identifier is detected from the
render-engine enum rather than hard-coded. Renders one frame of a lit cube on
a floor, then measures whether the frame is blank.
"""
import json
import sys

import bpy
import numpy as np


def eevee_identifier():
    enum = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    ids = [item.identifier for item in enum]
    for ident in ids:
        if ident.startswith("BLENDER_EEVEE"):
            return ident, ids
    raise RuntimeError(f"no EEVEE engine in {ids}")


def build_scene(scene):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 0.75))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(1.6, -0.5, 0.6))
    for obj in bpy.data.objects:
        mat = bpy.data.materials.new(obj.name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (
            (0.1, 0.5, 0.9, 1) if obj.name.startswith("Cube") else (0.7, 0.7, 0.7, 1)
        )
        obj.data.materials.append(mat)
    bpy.ops.object.light_add(type="AREA", location=(3, -3, 4))
    light = bpy.context.object
    light.data.energy = 800
    light.data.size = 3
    bpy.ops.object.camera_add(location=(5, -5, 3.5), rotation=(1.1, 0, 0.785))
    scene.camera = bpy.context.object
    return scene


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    engine_kind, out_png, out_json = argv
    scene = build_scene(None)
    result = {"requested": engine_kind, "blender": bpy.app.version_string}
    eevee_id, all_ids = eevee_identifier()
    result["engine_enum"] = all_ids
    if engine_kind == "eevee":
        scene.render.engine = eevee_id
    else:
        scene.render.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        backend = None
        for kind in ("OPTIX", "CUDA", "HIP"):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                if any(d.type == kind for d in prefs.devices):
                    backend = kind
                    break
            except Exception:
                continue
        for d in prefs.devices:
            d.use = d.type == backend
        scene.cycles.device = "GPU" if backend else "CPU"
        scene.cycles.seed = 1
        scene.cycles.use_denoising = True
        scene.cycles.samples = 32
        result["cycles_backend"] = backend
        result["cycles_devices"] = [(d.name, d.type, d.use) for d in prefs.devices]
    result["engine_used"] = scene.render.engine
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(out_png)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
    result["mean"] = float(px.mean())
    result["std"] = float(px.std())
    result["unique_levels"] = len(np.unique((px * 255).astype(np.uint8), axis=0))
    result["blank"] = bool(result["std"] < 0.01 or result["unique_levels"] < 16)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    print("PROBE_RESULT", json.dumps(result))
    if result["blank"]:
        raise SystemExit(2)


main()
