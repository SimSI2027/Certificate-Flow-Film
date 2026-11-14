"""Generate assets/character.blend with the MPFB add-on (Session V4, amendment V4-A2). Run through ``python -m tools character``.

Usage: blender -b --factory-startup --python-exit-code 1 -P blender/make_character.py -- --assets <mhassets dir> --out <file.blend>

MPFB (GPL-3.0-or-later, extensions.blender.org) is only the generator; the saved file holds the CC0 MakeHuman base mesh,
the CC0 default rig and weights, and the CC0 clothes, hair, eyebrows and eyes listed in ``cff.stage.character.PARTS``.
Shape keys and helper geometry are baked away; each part keeps one material slot named after it, holding only its
(downscaled, packed) diffuse texture, so ``blender.character`` can build the shading from theme tokens at film build time.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy

from blender.common import option, script_args
from cff.stage import character as ch

MPFB_MODULE = "bl_ext.user_default.mpfb"


def _service(module: str, name: str) -> object:
    return getattr(importlib.import_module(f"{MPFB_MODULE}.services.{module}"), name)


def _empty_file() -> None:
    for collection in (bpy.data.objects, bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
        for item in list(collection):
            collection.remove(item)


def _diffuse_image(obj: bpy.types.Object) -> bpy.types.Image | None:
    """The diffuse image of the MPFB material on ``obj`` (the one whose name says diffuse, else the only colour image)."""
    images = []
    for slot in obj.material_slots:
        if slot.material is None or slot.material.node_tree is None:
            continue
        images += [n.image for n in slot.material.node_tree.nodes if n.type == "TEX_IMAGE" and n.image is not None]
    named = [i for i in images if "diffuse" in i.name.lower() or "diffuse" in Path(i.filepath).name.lower()]
    plain = [i for i in images if not any(k in Path(i.filepath).name.lower() for k in ("normal", "_ao", "bump", "spec"))]
    return (named or plain or [None])[0]


def _material_slot(obj: bpy.types.Object, part: ch.Part) -> dict[str, object]:
    """Replace the MPFB material with one named slot that keeps only the packed, downscaled diffuse texture."""
    image = _diffuse_image(obj) if part.texture_px else None
    info: dict[str, object] = {"texture": None}
    if image is not None:
        image.name = f"IMG-{part.name}"
        source = (image.size[0], image.size[1])
        if max(source) > part.texture_px:
            image.scale(part.texture_px, part.texture_px)
        image.pack()
        info["texture"] = {"from_px": source, "to_px": tuple(image.size), "alpha": image.alpha_mode}
    obj.data.materials.clear()
    mat = bpy.data.materials.new(part.name)
    if image is not None:
        node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = image
        node.name = "DIFFUSE"
    obj.data.materials.append(mat)
    return info


def build(assets: Path, out: Path) -> dict[str, object]:
    bpy.ops.preferences.addon_enable(module=MPFB_MODULE)
    human = _service("humanservice", "HumanService")
    targets = _service("targetservice", "TargetService")
    export = _service("exportservice", "ExportService")
    _empty_file()

    macro = targets.get_default_macro_info_dict()  # type: ignore[attr-defined]
    macro.update(ch.MACROS)
    basemesh = human.create_human(macro_detail_dict=macro)  # type: ignore[attr-defined]
    rig = human.add_builtin_rig(basemesh, ch.RIG_NAME)  # type: ignore[attr-defined]
    parts: dict[str, bpy.types.Object] = {"CHAR-body": basemesh}
    for part in ch.PARTS:
        if part.source is None:
            continue
        obj = human.add_mhclo_asset(str(assets / part.source), basemesh, asset_type=part.asset_type, subdiv_levels=0, material_type="MAKESKIN")  # type: ignore[attr-defined]
        parts[part.name] = obj

    bpy.context.view_layer.objects.active = basemesh
    targets.bake_targets(basemesh)  # type: ignore[attr-defined]
    export.bake_modifiers_remove_helpers(basemesh, bake_masks=True, bake_subdiv=False, remove_helpers=True)  # type: ignore[attr-defined]

    collection = bpy.data.collections.new(ch.COLLECTION)
    bpy.context.scene.collection.children.link(collection)
    rig.name = rig.data.name = ch.RIG
    report: dict[str, object] = {"parts": {}}
    for name, obj in parts.items():
        obj.name = obj.data.name = name
        for modifier in list(obj.modifiers):
            if modifier.type == "SUBSURF":
                obj.modifiers.remove(modifier)
        info = _material_slot(obj, ch.PART_BY_NAME[name])
        info |= {"verts": len(obj.data.vertices), "faces": len(obj.data.polygons), "modifiers": [m.type for m in obj.modifiers],
                 "shape_keys": obj.data.shape_keys is not None, "dims": tuple(round(d, 3) for d in obj.dimensions)}
        report["parts"][name] = info  # type: ignore[index]
    for obj in [rig, *parts.values()]:
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        collection.objects.link(obj)
    for obj in list(bpy.data.objects):
        if obj.name not in collection.objects:
            bpy.data.objects.remove(obj)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.node_groups):
        for item in list(block):
            if item.users == 0:
                block.remove(item)

    report["bones"] = {b.name: [tuple(round(c, 3) for c in b.head_local), tuple(round(c, 3) for c in b.tail_local), b.parent.name if b.parent else None]
                       for b in rig.data.bones}
    report["rig_location"] = tuple(round(c, 3) for c in rig.location)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    return report


def main() -> None:
    args = script_args()
    assets, out = option(args, "assets"), option(args, "out")
    assert assets is not None and out is not None
    report = build(Path(assets), Path(out))
    report_path = Path(out).with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("CHARACTER-REPORT", report_path)


if __name__ == "__main__":
    main()
