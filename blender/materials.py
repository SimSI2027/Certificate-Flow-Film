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


def vault_material(role: ColourRole) -> bpy.types.Material:
    """An issuing CA's vault: the stage material with its role colour's value scaled down (V1-CIN-03 step 1)."""
    name = f"MAT-vault-{role.value}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = stage_material(role).copy()
    mat.name = name
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            node.inputs["Base Color"].default_value = linear4(palette.value_scaled_hex(palette.role_hex(role), palette.VAULT_VALUE_SCALE))
    return mat


def backdrop_material() -> bpy.types.Material:
    """Far set dressing: a dark, rough neutral that the key and rim lights pick out as silhouettes, never a role colour."""
    if "MAT-backdrop" in bpy.data.materials:
        return bpy.data.materials["MAT-backdrop"]
    mat = bpy.data.materials.new("MAT-backdrop")
    _, bsdf = _principled(mat.node_tree)
    bsdf.inputs["Base Color"].default_value = linear4(palette.BACKDROP_HEX)
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def trust_link_material(variant: str) -> bpy.types.Material:
    """Gradient light along the link's local X (0 = issuer end, 1 = subject end); intensity from the glow channel's value."""
    name = f"MAT-trust-{variant}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    start, end = palette.TRUST_LINK_STOPS[variant]
    mat = bpy.data.materials.new(name)
    mat.surface_render_method = "DITHERED"
    nt = mat.node_tree
    _, bsdf = _principled(nt)
    bsdf.inputs["Base Color"].default_value = linear4(palette.role_hex(ColourRole.NEUTRAL))
    bsdf.inputs["Roughness"].default_value = SOLID_ROUGHNESS
    bsdf.inputs["Emission Strength"].default_value = palette.TRUST_LINK_EMISSION
    coord = nt.nodes.new("ShaderNodeTexCoord")
    axis = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], axis.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = linear4(palette.role_hex(start))
    ramp.color_ramp.elements[1].color = linear4(palette.role_hex(end))
    nt.links.new(axis.outputs["X"], ramp.inputs["Fac"])
    info = nt.nodes.new("ShaderNodeObjectInfo")
    hsv = nt.nodes.new("ShaderNodeSeparateColor")
    hsv.mode = "HSV"
    nt.links.new(info.outputs["Color"], hsv.inputs["Color"])
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], tint.inputs["A"])
    nt.links.new(hsv.outputs["Blue"], tint.inputs["B"])  # HSV value: the glow level
    nt.links.new(tint.outputs["Result"], bsdf.inputs["Emission Color"])
    nt.links.new(info.outputs["Alpha"], bsdf.inputs["Alpha"])
    return mat


TEXT_RENDER_METHOD = "BLENDED"  # never DITHERED: dithered alpha stipples glyphs at any sample count (LEG-S1R1-01)
SIGN_PLATE = "MAT-sign-plate"


def sign_plate_material() -> bpy.types.Material:
    """Sign plates: blended like the glyphs, so fades are smooth (a dithered plate stippled while fading: LEG-S1R2-02).
    Plates render in their own view layer under the text (``blender.signs_scene``), so sorting never matters."""
    if SIGN_PLATE in bpy.data.materials:
        return bpy.data.materials[SIGN_PLATE]
    mat = caption_material("plate").copy()
    mat.name = SIGN_PLATE
    mat.surface_render_method = TEXT_RENDER_METHOD
    for node in mat.node_tree.nodes:
        if node.type == "MATH":  # the plate opacity factor
            node.inputs[1].default_value = palette.SIGN_PLATE_OPACITY
    return mat


def sign_tick_material(hex_colour: str) -> bpy.types.Material:
    """A check line's tick (V1-LEG-03): the sign text material in a role colour, faded by ``Object Info > Alpha``."""
    name = f"MAT-sign-tick-{hex_colour.lstrip('#')}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = caption_material("text").copy()
    mat.name = name
    for node in mat.node_tree.nodes:
        if node.type == "EMISSION":
            node.inputs["Color"].default_value = linear4(hex_colour)
    return mat


def caption_material(kind: str) -> bpy.types.Material:
    """Text-pass materials (captions and signs): exact colours under the Standard view transform, faded by ``Object Info > Alpha``."""
    name = f"MAT-caption-{kind}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.surface_render_method = TEXT_RENDER_METHOD
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
        scale.inputs[1].default_value = palette.PLATE_OPACITY
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
