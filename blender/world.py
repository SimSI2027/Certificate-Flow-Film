"""World: dark navy environment, the gridded floor, and the stage objects built from the catalogue."""

from __future__ import annotations

import math

import bpy

from blender import actors, materials
from blender.common import PROP_ID, PROP_KIND, PROP_OWNER, PROP_ROLE, linear4, tag
from cff.stage.objects import CATALOGUE, Kind, StageObject
from cff.theme import motion, palette

FLOOR_HALF_EXTENT_M = 120.0
FLOOR_CENTRE_Y_M = 20.0


def build_world(scene: bpy.types.Scene) -> None:
    world = bpy.data.worlds.new("WORLD")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = linear4(palette.WORLD_HEX)
    background.inputs["Strength"].default_value = palette.WORLD_STRENGTH * 10  # navy ambient, far below the key light
    scene.world = world


def build_floor(collection: bpy.types.Collection) -> bpy.types.Object:
    mesh = bpy.data.meshes.new("MESH-floor")
    half = FLOOR_HALF_EXTENT_M
    verts = [(-half, FLOOR_CENTRE_Y_M - half, 0.0), (half, FLOOR_CENTRE_Y_M - half, 0.0), (half, FLOOR_CENTRE_Y_M + half, 0.0), (-half, FLOOR_CENTRE_Y_M + half, 0.0)]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.materials.append(materials.floor_material())
    floor = bpy.data.objects.new("FLOOR", mesh)
    collection.objects.link(floor)
    tag(floor, **{PROP_ID: "FLOOR", PROP_KIND: "floor"})
    return floor


def build_actor(o: StageObject, collection: bpy.types.Collection) -> bpy.types.Object:
    ob = bpy.data.objects.new(o.id, actors.mesh_for(o))
    if o.kind is Kind.TRUST_LINK:
        ob.data.materials.append(materials.trust_link_material(o.variant))
    else:
        ob.data.materials.append(materials.stage_material(o.role, o.kind in materials.GLOW_ONLY_KINDS))
    collection.objects.link(ob)
    ob.location = o.home
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = tuple(math.radians(a) for a in o.rotation)
    ob.scale = o.full if o.on_stage else (motion.HIDDEN_SCALE,) * 3
    ob.color = (0.0, 0.0, 0.0, 1.0)  # unlit until the glow channel says otherwise
    tag(ob, **{PROP_ID: o.id, PROP_KIND: o.kind.value, PROP_ROLE: o.role.value, PROP_OWNER: o.owner or ""})
    return ob


def build_actors(collection: bpy.types.Collection) -> dict[str, bpy.types.Object]:
    return {o.id: build_actor(o, collection) for o in CATALOGUE}
