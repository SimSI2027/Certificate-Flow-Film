"""Materials: one shader for every stage object, driven by the object's colour (the ``glow`` channel).

Base colour is the role colour; emission is ``Object Info > Color`` times the palette emission strength and
opacity is ``Object Info > Alpha``. Animating ``object.color`` therefore animates glow and opacity together.
"""

from __future__ import annotations

import bpy

from blender.common import linear4
from cff.stage.objects import Kind
from cff.story.model import ColourRole
from cff.theme import palette

SOLID_ROUGHNESS = 0.55


def _principled(nt: bpy.types.ShaderNodeTree) -> tuple[bpy.types.Node, bpy.types.Node]:
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return out, bsdf


# Kinds whose colour is a signal, not an identity: dark until their glow channel lights them (C-10: green only after
# validation, amber only on pending connections, and so on).
GLOW_ONLY_KINDS: frozenset[Kind] = frozenset({
    Kind.CHANNEL, Kind.ROUTE, Kind.TRUST_LINK, Kind.BEAM, Kind.TICK, Kind.RING, Kind.SEAL_RING, Kind.TRIM, Kind.PULSE, Kind.QUERY,
    Kind.BAND, Kind.LINK_ROD, Kind.PRESS_HEAD, Kind.MODULE, Kind.SEAL, Kind.SCREEN, Kind.PORT, Kind.PROOF, Kind.TILE,
})


def stage_material(role: ColourRole, glow_only: bool = False) -> bpy.types.Material:
    name = f"MAT-{role.value}" + ("-glow" if glow_only else "")
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.surface_render_method = "DITHERED"
    nt = mat.node_tree
    _, bsdf = _principled(nt)
    info = nt.nodes.new("ShaderNodeObjectInfo")
    base = palette.role_hex(ColourRole.NEUTRAL if glow_only else role)
    bsdf.inputs["Base Color"].default_value = linear4(base)
    bsdf.inputs["Roughness"].default_value = SOLID_ROUGHNESS
    bsdf.inputs["Emission Strength"].default_value = palette.EMISSION_STRENGTH
    nt.links.new(info.outputs["Color"], bsdf.inputs["Emission Color"])
    nt.links.new(info.outputs["Alpha"], bsdf.inputs["Alpha"])
    return mat


def label_material(kind: str) -> bpy.types.Material:
    """``plate``: dark, mostly opaque backing (counts as the background for L-02). ``text``: white emission."""
    name = f"MAT-label-{kind}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    _, bsdf = _principled(nt)
    if kind == "plate":
        mat.surface_render_method = "DITHERED"
        bsdf.inputs["Base Color"].default_value = linear4(palette.PLATE_HEX)
        bsdf.inputs["Alpha"].default_value = 0.82
        bsdf.inputs["Roughness"].default_value = 0.9
    else:
        bsdf.inputs["Base Color"].default_value = linear4(palette.TEXT_HEX)
        bsdf.inputs["Emission Color"].default_value = linear4(palette.TEXT_HEX)
        bsdf.inputs["Emission Strength"].default_value = 2.2
        bsdf.inputs["Roughness"].default_value = 1.0
    return mat


def caption_material(kind: str) -> bpy.types.Material:
    """Caption-layer materials: exact colours under the Standard view transform, faded by ``Object Info > Alpha``."""
    name = f"MAT-caption-{kind}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.surface_render_method = "DITHERED"
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emission = nt.nodes.new("ShaderNodeEmission")
    transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    emission.inputs["Color"].default_value = linear4(palette.TEXT_HEX if kind == "text" else palette.PLATE_HEX)
    emission.inputs["Strength"].default_value = 1.0
    if kind == "plate":
        scale = nt.nodes.new("ShaderNodeMath")
        scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = 0.82
        nt.links.new(info.outputs["Alpha"], scale.inputs[0])
        nt.links.new(scale.outputs["Value"], mix.inputs["Fac"])
    else:
        nt.links.new(info.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(transparent.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emission.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def floor_material() -> bpy.types.Material:
    """Near-black navy floor with a subtle line grid every 2 m."""
    if "MAT-floor" in bpy.data.materials:
        return bpy.data.materials["MAT-floor"]
    mat = bpy.data.materials.new("MAT-floor")
    nt = mat.node_tree
    _, bsdf = _principled(nt)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs["Vector"])
    lines = []
    for axis in ("X", "Y"):
        div = nt.nodes.new("ShaderNodeMath")
        div.operation = "DIVIDE"
        div.inputs[1].default_value = GRID_SPACING_M
        wrap = nt.nodes.new("ShaderNodeMath")
        wrap.operation = "WRAP"
        wrap.inputs[1].default_value = 0.0
        wrap.inputs[2].default_value = 1.0
        less = nt.nodes.new("ShaderNodeMath")
        less.operation = "LESS_THAN"
        less.inputs[1].default_value = GRID_LINE_FRACTION
        nt.links.new(sep.outputs[axis], div.inputs[0])
        nt.links.new(div.outputs["Value"], wrap.inputs[0])
        nt.links.new(wrap.outputs["Value"], less.inputs[0])
        lines.append(less)
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MAXIMUM"
    nt.links.new(lines[0].outputs["Value"], add.inputs[0])
    nt.links.new(lines[1].outputs["Value"], add.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = linear4(palette.FLOOR_HEX)
    mix.inputs["B"].default_value = linear4(palette.GRID_HEX)
    nt.links.new(add.outputs["Value"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    return mat


GRID_SPACING_M = 2.0
GRID_LINE_FRACTION = 0.012
