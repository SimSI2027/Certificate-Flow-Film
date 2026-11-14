"""V5a physical finishes (amendment V5-A1): powder-coated steel, bezels, brushed aluminium, perforated doors, LEDs, glass,
cable, concrete, raised-floor tile, and the laptop screen's UI layers.

Slot 0 of every detailed mesh stays the stage material (the glow channel and role colour, ``blender.materials``); these are
slots 1.. (``blender.actors.slots``). Finishes never take ``Object Info > Color`` as emission, so they never glow with a PKI
signal; only the UI layers do, scaled by the screen's glow level. Every finish fades with ``Object Info > Alpha``.

The meshes have no UVs, so the CC0 maps (``assets/textures``) are box-projected in object space, and their relief comes from a
bump of the roughness or albedo map (tangent-space normal maps need UVs). Colours are palette tokens; the maps only modulate them.
"""

from __future__ import annotations

import bpy

from blender.actors import slots as s
from blender.common import ROOT, linear4
from cff.stage import hardware as hw
from cff.story.model import ColourRole
from cff.theme import look, palette

PREFIX = "MAT-fin-"
BOX_BLEND = 0.2


def _new(name: str) -> tuple[bpy.types.Material, bpy.types.ShaderNodeTree, bpy.types.Node, bpy.types.Node]:
    mat = bpy.data.materials.new(name)
    mat.surface_render_method = "DITHERED"
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    info = nt.nodes.new("ShaderNodeObjectInfo")
    nt.links.new(info.outputs["Alpha"], bsdf.inputs["Alpha"])
    return mat, nt, bsdf, info


def _image(nt: bpy.types.ShaderNodeTree, use: str, channel: str, repeat: float, colour: bool) -> bpy.types.NodeSocket:
    path = ROOT / hw.texture_file(use, channel)
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (repeat, repeat, repeat)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.projection = "BOX"
    tex.projection_blend = BOX_BLEND
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    return tex.outputs["Color"]


def _bump(nt: bpy.types.ShaderNodeTree, bsdf: bpy.types.Node, height: bpy.types.NodeSocket, strength: float) -> None:
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    nt.links.new(height, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def _tinted(nt: bpy.types.ShaderNodeTree, albedo: bpy.types.NodeSocket, hex_colour: str) -> bpy.types.NodeSocket:
    """A token colour modulated by a map's luminance (the map supplies variation, the token the colour)."""
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(albedo, bw.inputs["Color"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs["A"].default_value = linear4(hex_colour)
    gain = nt.nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = 2.0  # the CC0 albedos are mid-grey: this keeps the token's own value on average
    nt.links.new(bw.outputs["Val"], gain.inputs[0])
    nt.links.new(gain.outputs["Value"], mix.inputs["B"])
    return mix.outputs["Result"]


def _cached(name: str) -> bpy.types.Material | None:
    return bpy.data.materials.get(PREFIX + name)


def plain(name: str, hex_colour: str, roughness: float, metallic: float = 0.0) -> bpy.types.Material:
    mat = _cached(name)
    if mat is not None:
        return mat
    mat, _, bsdf, _ = _new(PREFIX + name)
    bsdf.inputs["Base Color"].default_value = linear4(hex_colour)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def powder_steel() -> bpy.types.Material:
    """Powder-coated rack steel: a fine orange-peel bump on graphite."""
    mat = _cached("steel")
    if mat is not None:
        return mat
    mat, nt, bsdf, _ = _new(PREFIX + "steel")
    bsdf.inputs["Base Color"].default_value = linear4(palette.STEEL_HEX)
    bsdf.inputs["Roughness"].default_value = look.STEEL_ROUGHNESS
    bsdf.inputs["Metallic"].default_value = look.STEEL_METALLIC
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = look.POWDER_NOISE_SCALE
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    _bump(nt, bsdf, noise.outputs["Fac"], look.POWDER_BUMP)
    return mat


def brushed_aluminium() -> bpy.types.Material:
    """Brushed aluminium (CC0 Metal009 albedo and roughness; the roughness map also drives the brushed bump)."""
    mat = _cached("aluminium")
    if mat is not None:
        return mat
    mat, nt, bsdf, _ = _new(PREFIX + "aluminium")
    rep = look.BRUSHED_REPEAT_PER_M
    nt.links.new(_tinted(nt, _image(nt, "brushed", "Color", rep, True), palette.ALUMINIUM_HEX), bsdf.inputs["Base Color"])
    rough = _image(nt, "brushed", "Roughness", rep, False)
    span = nt.nodes.new("ShaderNodeMapRange")
    span.inputs["To Min"].default_value = look.ALUMINIUM_ROUGHNESS * 0.6
    span.inputs["To Max"].default_value = look.ALUMINIUM_ROUGHNESS * 1.4
    nt.links.new(rough, span.inputs["Value"])
    nt.links.new(span.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = look.ALUMINIUM_METALLIC
    _bump(nt, bsdf, rough, look.NORMAL_STRENGTH * 0.3)
    return mat


def perforated_steel() -> bpy.types.Material:
    """Perforated door steel (CC0 SheetMetal001): the opacity map cuts the holes, so lit devices show through the door."""
    mat = _cached("perforated")
    if mat is not None:
        return mat
    mat, nt, bsdf, info = _new(PREFIX + "perforated")
    rep = look.PERFORATED_REPEAT_PER_M
    nt.links.new(_tinted(nt, _image(nt, "perforated", "Color", rep, True), palette.STEEL_HEX), bsdf.inputs["Base Color"])
    nt.links.new(_image(nt, "perforated", "Roughness", rep, False), bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = look.STEEL_METALLIC
    opacity = _image(nt, "perforated", "Opacity", rep, False)
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(opacity, bw.inputs["Color"])
    alpha = nt.nodes.new("ShaderNodeMath")
    alpha.operation = "MULTIPLY"
    nt.links.new(bw.outputs["Val"], alpha.inputs[0])
    nt.links.new(info.outputs["Alpha"], alpha.inputs[1])
    nt.links.new(alpha.outputs["Value"], bsdf.inputs["Alpha"])
    _bump(nt, bsdf, bw.outputs["Val"], look.NORMAL_STRENGTH * 0.2)
    return mat


def concrete() -> bpy.types.Material:
    """Cast concrete (CC0 Concrete034) for the root's plinth and dais."""
    mat = _cached("concrete")
    if mat is not None:
        return mat
    mat, nt, bsdf, _ = _new(PREFIX + "concrete")
    rep = look.CONCRETE_REPEAT_PER_M
    albedo = _image(nt, "concrete", "Color", rep, True)
    nt.links.new(_tinted(nt, albedo, palette.CONCRETE_HEX), bsdf.inputs["Base Color"])
    rough = _image(nt, "concrete", "Roughness", rep, False)
    span = nt.nodes.new("ShaderNodeMapRange")
    span.inputs["To Min"].default_value = look.CONCRETE_ROUGHNESS - 0.1
    span.inputs["To Max"].default_value = 1.0
    nt.links.new(rough, span.inputs["Value"])
    nt.links.new(span.outputs["Result"], bsdf.inputs["Roughness"])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(albedo, bw.inputs["Color"])
    _bump(nt, bsdf, bw.outputs["Val"], look.NORMAL_STRENGTH * 0.5)
    return mat


def emitter(name: str, hex_colour: str, strength: float) -> bpy.types.Material:
    """A static emitter (LEDs, light diffusers): it never takes the glow channel."""
    mat = _cached(name)
    if mat is not None:
        return mat
    mat, _, bsdf, _ = _new(PREFIX + name)
    bsdf.inputs["Base Color"].default_value = linear4(hex_colour)
    bsdf.inputs["Roughness"].default_value = look.BEZEL_ROUGHNESS
    bsdf.inputs["Emission Color"].default_value = linear4(hex_colour)
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def ui_layer(name: str, hex_colour: str) -> bpy.types.Material:
    """A laptop-screen UI layer: emission is the token colour times the screen's glow level (HSV value of ``Object Info > Color``)."""
    mat = _cached(name)
    if mat is not None:
        return mat
    mat, nt, bsdf, info = _new(PREFIX + name)
    bsdf.inputs["Base Color"].default_value = linear4(palette.GLASS_HEX)
    bsdf.inputs["Roughness"].default_value = look.GLASS_ROUGHNESS
    hsv = nt.nodes.new("ShaderNodeSeparateColor")
    hsv.mode = "HSV"
    nt.links.new(info.outputs["Color"], hsv.inputs["Color"])
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    tint.inputs["A"].default_value = linear4(hex_colour)
    nt.links.new(hsv.outputs["Blue"], tint.inputs["B"])
    nt.links.new(tint.outputs["Result"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = palette.EMISSION_STRENGTH * look.UI_EMISSION_GAIN
    return mat


ACCENT_TOKENS: dict[ColourRole, str] = {
    ColourRole.ISSUING_CA1: palette.role_hex(ColourRole.ISSUING_CA1),
    ColourRole.ISSUING_CA2: palette.role_hex(ColourRole.ISSUING_CA2),
    ColourRole.ROOT: palette.role_hex(ColourRole.ROOT),
    ColourRole.DIRECTORY: palette.role_hex(ColourRole.DIRECTORY),
}


def slot_materials(role: ColourRole) -> list[bpy.types.Material]:
    """Materials for slots 1.. of a detailed mesh (slot 0 is the caller's stage material). ``role`` picks the accent LED tint."""
    accent = ACCENT_TOKENS.get(role, palette.LED_HEX)
    by_slot = {
        s.STEEL: powder_steel(),
        s.STEEL_LIGHT: plain("steel-light", palette.STEEL_LIGHT_HEX, look.STEEL_LIGHT_ROUGHNESS, look.STEEL_LIGHT_METALLIC),
        s.BEZEL: plain("bezel", palette.BEZEL_HEX, look.BEZEL_ROUGHNESS),
        s.CADDY: plain("caddy", palette.CADDY_HEX, look.CADDY_ROUGHNESS, 0.3),
        s.VENT: plain("vent", palette.VENT_HEX, 0.9),
        s.ALUMINIUM: brushed_aluminium(),
        s.PERFORATED: perforated_steel(),
        s.LED: emitter("led", palette.LED_HEX, look.LED_EMISSION),
        s.ACCENT_LED: emitter(f"accent-{accent.lstrip('#')}", accent, look.ACCENT_LED_EMISSION),
        s.GLASS: plain("glass", palette.GLASS_HEX, look.GLASS_ROUGHNESS),
        s.CABLE: plain("cable", palette.CABLE_HEX, look.CABLE_ROUGHNESS),
        s.CONCRETE: concrete(),
        s.TILE: plain("tile", palette.TILE_HEX, look.TILE_ROUGHNESS),
        s.DESK: plain("desk", palette.DESK_HEX, look.DESK_ROUGHNESS),
        s.FABRIC: plain("fabric", palette.FABRIC_HEX, look.FABRIC_ROUGHNESS),
        s.UI_TITLE: ui_layer("ui-title", palette.UI_TITLE_HEX),
        s.UI_DESKTOP: ui_layer("ui-desktop", palette.UI_DESKTOP_HEX),
        s.UI_TASKBAR: ui_layer("ui-taskbar", palette.UI_TASKBAR_HEX),
        s.UI_ICON: ui_layer("ui-icon", palette.UI_ICON_HEX),
    }
    return [by_slot[i] for i in range(1, len(s.NAMES))]


def raised_floor() -> bpy.types.Material:
    """The raised floor: 0.6 m tiles of laminate on a dark steel grid, each tile a little lighter or darker than the next."""
    mat = _cached("raised-floor")
    if mat is not None:
        return mat
    mat, nt, bsdf, _ = _new(PREFIX + "raised-floor")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    scale = nt.nodes.new("ShaderNodeVectorMath")
    scale.operation = "DIVIDE"
    scale.inputs[1].default_value = (look.FLOOR_TILE_M, look.FLOOR_TILE_M, 1.0)
    nt.links.new(coord.outputs["Object"], scale.inputs[0])
    cell = nt.nodes.new("ShaderNodeVectorMath")
    cell.operation = "FLOOR"
    nt.links.new(scale.outputs["Vector"], cell.inputs[0])
    frac = nt.nodes.new("ShaderNodeVectorMath")
    frac.operation = "FRACTION"
    nt.links.new(scale.outputs["Vector"], frac.inputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(frac.outputs["Vector"], sep.inputs["Vector"])
    seams = []
    for axis in ("X", "Y"):
        near = nt.nodes.new("ShaderNodeMath")  # distance to the nearest tile edge, as a fraction of the tile
        near.operation = "PINGPONG"
        near.inputs[1].default_value = 0.5
        nt.links.new(sep.outputs[axis], near.inputs[0])
        edge = nt.nodes.new("ShaderNodeMath")
        edge.operation = "LESS_THAN"
        edge.inputs[1].default_value = look.FLOOR_SEAM_FRACTION
        nt.links.new(near.outputs["Value"], edge.inputs[0])
        seams.append(edge)
    seam = nt.nodes.new("ShaderNodeMath")
    seam.operation = "MAXIMUM"
    nt.links.new(seams[0].outputs["Value"], seam.inputs[0])
    nt.links.new(seams[1].outputs["Value"], seam.inputs[1])
    noise = nt.nodes.new("ShaderNodeTexWhiteNoise")
    noise.noise_dimensions = "3D"
    nt.links.new(cell.outputs["Vector"], noise.inputs["Vector"])
    vary = nt.nodes.new("ShaderNodeMapRange")
    vary.inputs["To Min"].default_value = 1.0 - look.FLOOR_TILE_VARIATION
    vary.inputs["To Max"].default_value = 1.0 + look.FLOOR_TILE_VARIATION
    nt.links.new(noise.outputs["Value"], vary.inputs["Value"])
    tile = nt.nodes.new("ShaderNodeMix")
    tile.data_type = "RGBA"
    tile.blend_type = "MULTIPLY"
    tile.inputs["Factor"].default_value = 1.0
    tile.inputs["A"].default_value = linear4(palette.TILE_HEX)
    nt.links.new(vary.outputs["Result"], tile.inputs["B"])
    colour = nt.nodes.new("ShaderNodeMix")
    colour.data_type = "RGBA"
    colour.inputs["B"].default_value = linear4(palette.TILE_SEAM_HEX)
    nt.links.new(tile.outputs["Result"], colour.inputs["A"])
    nt.links.new(seam.outputs["Value"], colour.inputs["Factor"])
    nt.links.new(colour.outputs["Result"], bsdf.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = look.TILE_ROUGHNESS
    rough.inputs["To Max"].default_value = 0.9
    nt.links.new(seam.outputs["Value"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    _bump(nt, bsdf, seam.outputs["Value"], -0.3)
    return mat


def perforated_tile() -> bpy.types.Material:
    """A perforated airflow tile: the SheetMetal001 hole pattern over the dark under-floor void."""
    mat = _cached("perforated-tile")
    if mat is not None:
        return mat
    mat, nt, bsdf, _ = _new(PREFIX + "perforated-tile")
    opacity = _image(nt, "perforated", "Opacity", look.PERFORATED_REPEAT_PER_M * 0.8, False)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = linear4(palette.VENT_HEX)
    mix.inputs["B"].default_value = linear4(palette.STEEL_LIGHT_HEX)
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(opacity, bw.inputs["Color"])
    nt.links.new(bw.outputs["Val"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = look.STEEL_METALLIC
    bsdf.inputs["Roughness"].default_value = look.STEEL_LIGHT_ROUGHNESS
    _bump(nt, bsdf, bw.outputs["Val"], look.NORMAL_STRENGTH * 0.3)
    return mat
