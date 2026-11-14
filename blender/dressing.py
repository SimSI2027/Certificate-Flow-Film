"""v1.3 interiors: static set dressing inside the server chassis and the issuing-CA vaults.

The close-ups at 14-24 s (keys in the RDP chassis), 73-76 s (the web server's keys), 29-36 s and 82-90 s (the CA vaults)
were plain grey or flat-coloured boxes. Each interior now gets relief (rack ribs and rails), practical light strips and
status lights that glow at a fixed level, and the light those practicals motivate: a soft ceiling key and, in the chassis,
a cool back rim that separates the keys from the back wall.

Set dressing only (like the backdrop): no story role, no label, not in the catalogue, never animated, and parented to its
shell so it sits exactly where the shell is. Colours are existing palette tokens: the pale pool tints and the rim blue,
never a state colour (C-10). Every number is a constant in ``cff.theme.look`` or a shell dimension from ``cff.stage.layout``.
"""

from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Matrix

from blender import materials
from blender.common import PROP_ID, PROP_KIND, linear, tag
from cff.stage import layout as lo
from cff.stage.objects import CATALOGUE, Kind
from cff.story.model import ColourRole
from cff.theme import look, palette

DRESSING_KIND = "dressing"
PREFIX = "DRESS-"
CHASSIS_WALL_M = 0.06  # blender/actors/servers.py WALL
VAULT_WALL_M = 0.14  # blender/actors/authorities.py ca_vault wall
STRIP_M = 0.02  # width of a light strip
RIB_DEPTH_M = 0.025
RIB_HEIGHT_M = 0.03
LED_M = 0.025
LED_STEP_M = 0.06
VAULT_RIB_M = (0.08, 0.06)  # width, depth
FACE_FRONT = (-math.pi / 2, 0.0, 0.0)  # an area light emits along its local -Z; this turns it to face -Y (the open front)
UNLIT = (0.0, 0.0, 0.0, 1.0)  # as blender/world.py build_actor: no glow, fully opaque
VAULT_POOL_TOKENS ={ColourRole.ISSUING_CA1: "POOL_CA1_HEX", ColourRole.ISSUING_CA2: "POOL_CA2_HEX"}

Box = tuple[tuple[float, float, float], tuple[float, float, float]]  # (centre, size) in the shell's local frame


def _mesh_object(name: str, boxes: list[Box], material: bpy.types.Material, shell: bpy.types.Object, collection: bpy.types.Collection) -> bpy.types.Object:
    bm = bmesh.new()
    for centre, size in boxes:
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(centre) @ Matrix.Diagonal((*size, 1.0)))
    mesh = bpy.data.meshes.new(f"MESH-{name}")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    ob.parent = shell
    ob.color = UNLIT  # the shell materials glow by Object Info > Color; the default white would make every rib glow
    tag(ob, **{PROP_ID: name, PROP_KIND: DRESSING_KIND})
    return ob


def _area_light(name: str, hex_colour: str, watts: float, size: tuple[float, float], location: tuple[float, float, float],
                rotation: tuple[float, float, float], shell: bpy.types.Object, collection: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.lights.new(name, "AREA")
    data.shape = "RECTANGLE"
    data.size, data.size_y = size
    data.energy = watts
    data.color = linear(hex_colour)
    # V3-CIN-01: no shadow pages. With shadows, these close-range lights pushed EEVEE's shadow pool into overflow and the chassis
    # interior toggled between two levels about 4.7 apart (f477, f595, f600 in one render; f671, f705, f719 in the next).
    data.use_shadow = False
    ob = bpy.data.objects.new(name, data)
    collection.objects.link(ob)
    ob.parent = shell
    ob.location = location
    ob.rotation_euler = rotation
    tag(ob, **{PROP_ID: name, PROP_KIND: DRESSING_KIND})
    return ob


def _chassis(shell: bpy.types.Object, collection: bpy.types.Collection) -> None:
    sx, sy, sz = lo.CHASSIS_SIZE
    back = sy / 2 - CHASSIS_WALL_M  # inner face of the back wall
    side = sx / 2 - CHASSIS_WALL_M
    roof = sz - 0.08
    name = f"{PREFIX}{shell.name}"
    z0, z1 = look.CHASSIS_RIB_Z
    ribs: list[Box] = [((0.0, back - RIB_DEPTH_M / 2, z0 + (z1 - z0) * i / (look.CHASSIS_RIB_COUNT - 1)), (sx - 2 * CHASSIS_WALL_M - 0.1, RIB_DEPTH_M, RIB_HEIGHT_M))
                       for i in range(look.CHASSIS_RIB_COUNT)]
    rails: list[Box] = [((s * (side - 0.03), -sy / 2 + 0.12, roof / 2 + 0.04), (0.04, 0.04, roof - 0.08)) for s in (-1, 1)]
    _mesh_object(f"{name}-ribs", ribs + rails, materials.chassis_material(), shell, collection)
    strips: list[Box] = [((s * (side - 0.04), back - 0.02, (z0 + z1) / 2), (STRIP_M, 0.015, z1 - z0)) for s in (-1, 1)]
    _mesh_object(f"{name}-strips", strips, materials.dressing_material(palette.POOL_NEUTRAL_HEX, look.CHASSIS_STRIP_EMISSION), shell, collection)
    lamp: list[Box] = [((0.0, -sy / 2 + 0.14, roof - 0.02), (sx - 2 * CHASSIS_WALL_M - 0.2, 0.04, STRIP_M))]
    _mesh_object(f"{name}-lamp", lamp, materials.dressing_material(palette.POOL_NEUTRAL_HEX, look.CHASSIS_LAMP_EMISSION), shell, collection)
    leds: list[Box] = [((side - 0.14, back - 0.015, z1 - 0.25 + i * LED_STEP_M), (LED_M, 0.012, LED_M)) for i in range(look.CHASSIS_LED_COUNT)]
    _mesh_object(f"{name}-leds", leds, materials.dressing_material(palette.RIM_LIGHT_HEX, look.CHASSIS_LED_EMISSION), shell, collection)
    _area_light(f"{name}-top", palette.POOL_NEUTRAL_HEX, look.CHASSIS_TOP_W, (sx - 0.3, sy - 0.3), (0.0, -0.05, roof - 0.06), (0.0, 0.0, 0.0), shell, collection)
    _area_light(f"{name}-rim", palette.RIM_LIGHT_HEX, look.CHASSIS_RIM_W, (sx - 0.4, z1 - z0), (0.0, back - 0.08, (z0 + z1) / 2), FACE_FRONT, shell, collection)


def _vault(shell: bpy.types.Object, role: ColourRole, collection: bpy.types.Collection) -> None:
    sx, sy, sz = lo.CA_VAULT_SIZE
    back = sy / 2 - VAULT_WALL_M
    side = sx / 2 - VAULT_WALL_M
    roof = sz - VAULT_WALL_M
    tint = getattr(palette, VAULT_POOL_TOKENS[role])
    name = f"{PREFIX}{shell.name}"
    span = 2 * side - 0.7
    ribs: list[Box] = [((-span / 2 + span * i / (look.VAULT_RIB_COUNT - 1), back - VAULT_RIB_M[1] / 2, roof / 2 + 0.06), (VAULT_RIB_M[0], VAULT_RIB_M[1], roof - 0.3))
                       for i in range(look.VAULT_RIB_COUNT)]
    _mesh_object(f"{name}-ribs", ribs, materials.vault_material(role), shell, collection)
    strips: list[Box] = [((s * (side - 0.06), back - 0.03, roof / 2 + 0.06), (STRIP_M, 0.02, roof - 0.3)) for s in (-1, 1)]
    strips.append(((0.0, back - 0.03, roof - 0.12), (2 * side - 0.2, 0.02, STRIP_M)))
    _mesh_object(f"{name}-strips", strips, materials.dressing_material(tint, look.VAULT_STRIP_EMISSION), shell, collection)
    _area_light(f"{name}-top", tint, look.VAULT_TOP_W, (2 * side - 0.6, 2 * back - 0.6), (0.0, 0.0, roof - 0.05), (0.0, 0.0, 0.0), shell, collection)


def build_dressing(collection: bpy.types.Collection, objects: dict[str, bpy.types.Object]) -> int:
    """Dress every server chassis and issuing-CA vault. Returns the number of dressing objects."""
    for o in CATALOGUE:
        if o.kind is Kind.CHASSIS:
            _chassis(objects[o.id], collection)
        elif o.kind is Kind.CA_VAULT and o.role in VAULT_POOL_TOKENS:
            _vault(objects[o.id], o.role, collection)
    return len(collection.objects)
