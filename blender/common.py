"""Shared helpers for every Blender entry script: repo path bootstrap, argument parsing, colour and tag helpers.

Blender scripts run with ``blender -b --factory-startup --python-exit-code 1 -P <script> -- <args>``; the repository
root is added to ``sys.path`` so ``cff`` and ``blender`` import as normal packages.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bpy  # noqa: E402  (after the path bootstrap)

from cff.theme import colour, typography  # noqa: E402

PROP_ID = "cff_id"
PROP_KIND = "cff_kind"
PROP_OWNER = "cff_owner"
PROP_ROLE = "cff_role"
PROP_LABEL = "cff_label"
PROP_CAP = "cff_cap_m"


def script_args() -> list[str]:
    argv = sys.argv
    return argv[argv.index("--") + 1 :] if "--" in argv else []


def option(args: list[str], name: str, default: str | None = None) -> str | None:
    """Value after ``--name`` in ``args``, or ``default``."""
    flag = f"--{name}"
    if flag in args:
        index = args.index(flag)
        if index + 1 < len(args):
            return args[index + 1]
    return default


def linear(hex_colour: str) -> tuple[float, float, float]:
    return colour.rgb_to_linear(colour.hex_to_rgb(hex_colour))


def linear4(hex_colour: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    r, g, b = linear(hex_colour)
    return (r, g, b, alpha)


def tag(obj: bpy.types.Object, **props: object) -> None:
    for key, value in props.items():
        obj[key] = value


def engine_id() -> str:
    """The EEVEE render-engine identifier, detected from the enum (it has changed between versions)."""
    items = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    for candidate in items:
        if "EEVEE" in candidate:
            return candidate
    raise RuntimeError(f"no EEVEE engine in {items}")


LABEL_FONT = typography.LABEL_FONT
CAPTION_FONT = typography.CAPTION_FONT


def glyph_cap_ratio(font: bpy.types.VectorFont) -> float:
    """Measured cap height per unit font size: the height of an evaluated 'H' glyph mesh (never an assumed constant)."""
    curve = bpy.data.curves.new("CAP-PROBE", "FONT")
    curve.body = "H"
    curve.size = 1.0
    curve.font = font
    probe = bpy.data.objects.new("CAP-PROBE", curve)
    scene = bpy.context.scene
    scene.collection.objects.link(probe)
    try:
        evaluated = probe.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        heights = [v.co.y for v in mesh.vertices]
        ratio = max(heights) - min(heights)
        evaluated.to_mesh_clear()
    finally:
        bpy.data.objects.remove(probe)
        bpy.data.curves.remove(curve)
    return ratio


def bundled_font(file_name: str) -> bpy.types.VectorFont:
    """A font shipped with this Blender build (no external fonts; Charter Section 8)."""
    path = Path(bpy.utils.system_resource("DATAFILES")) / "fonts" / file_name
    existing = next((f for f in bpy.data.fonts if Path(f.filepath).name == file_name), None)
    return existing or bpy.data.fonts.load(str(path))


def reset_scene() -> bpy.types.Scene:
    """An empty file: factory startup still has a default cube, camera and light."""
    for collection in (bpy.data.objects, bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
        for item in list(collection):
            collection.remove(item)
    return bpy.context.scene
