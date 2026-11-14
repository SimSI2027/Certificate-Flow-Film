"""Compositor (Blender 5.x: ``scene.compositing_node_group``, no Composite node).

Chain: render layer -> flashback grade (desaturate, soft gate vignette) -> optional bloom (preview/final tiers)
-> fade to black -> group output. The flashback and the fade are keyed from the story timing.
"""

from __future__ import annotations

import bpy

from blender.animation import FCurveWriter
from cff.story import model as m
from cff.story import timing
from cff.theme import look, palette, render
from cff.theme.render import Tier

GRADE_NODE = "Grade"
VIGNETTE_VALUE = "VignetteAmount"
VIGNETTE_MASK = "VignetteMask"
VIGNETTE_BLUR = "VignetteBlur"
VIGNETTE_MIX = "VignetteMix"
VIGNETTE_SIZE = (1.15, 1.0)
VIGNETTE_BLUR_PX = 160
BLOOM_THRESHOLD = look.BLOOM_THRESHOLD
BLOOM_SIZE = 6
BLOOM_STRENGTH = look.BLOOM_STRENGTH


def _flashback_frames() -> tuple[int, int]:
    first = timing.seconds_to_frame(timing.beat_window("B-05.2")[0])
    after = timing.seconds_to_frame(timing.beat_window("B-05.2")[1])
    return first, after


def build_compositor(scene: bpy.types.Scene, tier: Tier) -> None:
    group = bpy.data.node_groups.new("CFF-Comp", "CompositorNodeTree")
    group.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    scene.compositing_node_group = group
    nodes, links = group.nodes, group.links
    layers = nodes.new("CompositorNodeRLayers")
    layers.scene = scene
    grade = nodes.new("CompositorNodeHueSat")
    grade.name = GRADE_NODE
    links.new(layers.outputs["Image"], grade.inputs["Image"])
    last = grade.outputs["Image"]

    mask = nodes.new("CompositorNodeEllipseMask")
    mask.name = VIGNETTE_MASK
    mask.inputs["Size"].default_value = VIGNETTE_SIZE
    blur = nodes.new("CompositorNodeBlur")
    blur.name = VIGNETTE_BLUR
    blur.inputs["Size"].default_value = (VIGNETTE_BLUR_PX * tier.width / render.CAPTION_REFERENCE_WIDTH_PX,) * 2
    links.new(mask.outputs["Mask"], blur.inputs["Image"])
    invert = nodes.new("ShaderNodeMath")
    invert.operation = "SUBTRACT"
    invert.inputs[0].default_value = 1.0
    links.new(blur.outputs["Image"], invert.inputs[1])
    amount = nodes.new("ShaderNodeValue")
    amount.name = VIGNETTE_VALUE
    amount.outputs[0].default_value = 0.0
    weight = nodes.new("ShaderNodeMath")
    weight.operation = "MULTIPLY"
    links.new(invert.outputs["Value"], weight.inputs[0])
    links.new(amount.outputs[0], weight.inputs[1])
    mix = nodes.new("ShaderNodeMix")
    mix.name = VIGNETTE_MIX
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = (0.0, 0.0, 0.0, 1.0)
    links.new(weight.outputs["Value"], mix.inputs["Factor"])
    links.new(last, mix.inputs["A"])
    last = mix.outputs["Result"]

    if tier.bloom:
        glare = nodes.new("CompositorNodeGlare")
        glare.inputs["Type"].default_value = "Bloom"
        glare.inputs["Threshold"].default_value = BLOOM_THRESHOLD
        glare.inputs["Size"].default_value = BLOOM_SIZE
        glare.inputs["Strength"].default_value = BLOOM_STRENGTH
        links.new(last, glare.inputs["Image"])
        last = glare.outputs["Image"]

    out = nodes.new("NodeGroupOutput")
    links.new(last, out.inputs["Image"])
    _key_grade(group)


def _key_grade(group: bpy.types.NodeTree) -> None:
    first, after = _flashback_frames()
    sat = FCurveWriter(group, "CFF-Comp-anim")
    grade = group.nodes[GRADE_NODE]
    sat_index = list(grade.inputs).index(grade.inputs["Saturation"])
    val_index = list(grade.inputs).index(grade.inputs["Value"])
    amount_path = f'nodes["{VIGNETTE_VALUE}"].outputs[0].default_value'
    sat_path = f'nodes["{GRADE_NODE}"].inputs[{sat_index}].default_value'
    val_path = f'nodes["{GRADE_NODE}"].inputs[{val_index}].default_value'
    last_frame = timing.frame_end()
    fade_event = next(e for e in m.MODEL.events if e.id == "E-09.3a")  # the world fades to black under the title card
    fade_start, fade_end = timing.seconds_to_frame(fade_event.start_s), timing.seconds_to_frame(fade_event.end_s)
    keys = (
        (timing.FRAME_START, 1.0, 1.0, 0.0),
        (first - 1, 1.0, 1.0, 0.0),
        (first, palette.FLASHBACK_SATURATION, 1.0, palette.FLASHBACK_VIGNETTE),
        (after - 1, palette.FLASHBACK_SATURATION, 1.0, palette.FLASHBACK_VIGNETTE),
        (after, 1.0, 1.0, 0.0),
        (fade_start, 1.0, 1.0, 0.0),
        (fade_end, 1.0, 0.0, 0.0),
        (last_frame, 1.0, 0.0, 0.0),
    )
    for frame, saturation, value, vignette in keys:
        step = frame in (first - 1, after - 1)  # the flashback is entered and left by cuts
        sat.key(sat_path, frame, (saturation,), smooth=True, constant=step)
        sat.key(val_path, frame, (value,), smooth=True, constant=step)
        sat.key(amount_path, frame, (vignette,), smooth=True, constant=step)
    sat.finish()
