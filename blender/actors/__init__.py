"""Grey-box actors: one mesh builder per ``cff.stage.objects.Kind``.

``mesh_for(stage_object)`` returns a new mesh whose origin follows the catalogue contract: base-anchored kinds
(``BASE_ANCHORED``) have their origin at the bottom centre, hinged and stretched kinds (panel, lid, channel, route,
trust link, beam) at their start, everything else at its centre. Scaling and animation happen on the object.
"""

from __future__ import annotations

from collections.abc import Callable

import bmesh
import bpy

from blender.actors import artifacts, authorities, client, network, servers
from cff.stage.objects import Kind, StageObject

Builder = Callable[[bmesh.types.BMesh, StageObject], None]

BUILDERS: dict[Kind, Builder] = {
    **client.BUILDERS,
    **servers.BUILDERS,
    **authorities.BUILDERS,
    **artifacts.BUILDERS,
    **network.BUILDERS,
}


def missing_kinds() -> list[str]:
    return [k.value for k in Kind if k not in BUILDERS]


def mesh_for(o: StageObject) -> bpy.types.Mesh:
    bm = bmesh.new()
    BUILDERS[o.kind](bm, o)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"MESH-{o.id}")
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False
    return mesh
