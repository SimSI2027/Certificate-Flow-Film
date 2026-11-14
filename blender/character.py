"""The user character at build time (Session V4): load assets/character.blend, seat it at the laptop, key its motion, shade it.

Nothing is downloaded: the file was generated once by ``python -m tools character``. The rig is parented to the user
object (the chair). Every pose is computed here from the geometry in ``cff.stage.character`` (aims, a two-bone arm solve that
puts the wrists over the keyboard, a palm-down forearm twist), and every animated channel is a quaternion keyed between
poses computed the same way, with handles from ``cff.theme.motion`` presets (``blender.animation.FCurveWriter``).
"""

from __future__ import annotations

import math
from collections.abc import Callable

import bpy
from mathutils import Matrix, Quaternion, Vector

from blender.animation import FCurveWriter
from blender.common import ROOT, linear4
from cff.stage import character as ch
from cff.stage import layout as lo
from cff.story import model as m
from cff.theme import look, motion, palette
from cff.theme.render import Tier

Pose = dict[str, Quaternion]
FINGER_SEGMENTS = ("1", "2", "3")
NECK_CHAIN = ("neck01", "neck02", "neck03", "head")


def _update() -> None:
    bpy.context.view_layer.update()


def _load() -> tuple[bpy.types.Collection, bpy.types.Object]:
    path = ROOT / ch.ASSET_PATH
    with bpy.data.libraries.load(str(path), link=False) as (_, data_to):
        data_to.collections = [ch.COLLECTION]
    collection = bpy.data.collections[ch.COLLECTION]
    return collection, bpy.data.objects[ch.RIG]


# --- posing helpers (armature space) -------------------------------------------------------------------------------------------


def _set(rig: bpy.types.Object, name: str, matrix: Matrix) -> None:
    rig.pose.bones[name].matrix = matrix
    _update()


def _matrix(rig: bpy.types.Object, name: str) -> Matrix:
    return rig.pose.bones[name].matrix.copy()


def _rotate(rig: bpy.types.Object, name: str, rotation: Quaternion) -> None:
    """Rotate a bone about its own head by an armature-space rotation."""
    mat = _matrix(rig, name)
    head = mat.translation.copy()
    _set(rig, name, Matrix.Translation(head) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-head) @ mat)


def _aim(rig: bpy.types.Object, name: str, direction: Vector) -> None:
    """Swing a bone (shortest arc) so its Y axis points along ``direction``."""
    current = _matrix(rig, name).to_3x3().col[1].normalized()
    _rotate(rig, name, current.rotation_difference(direction.normalized()))


def _twist(rig: bpy.types.Object, name: str, angle: float) -> None:
    _set(rig, name, _matrix(rig, name) @ Matrix.Rotation(angle, 4, "Y"))


def _head(rig: bpy.types.Object, name: str) -> Vector:
    return _matrix(rig, name).translation.copy()


def _tail(rig: bpy.types.Object, name: str) -> Vector:
    pb = rig.pose.bones[name]
    return (pb.matrix @ Vector((0.0, pb.bone.length, 0.0))).copy()


def _signed_angle(a: Vector, b: Vector, axis: Vector) -> float:
    """Angle that turns ``a`` onto ``b`` about ``axis`` (both projected onto the plane normal to the axis)."""
    axis = axis.normalized()
    pa, pb = (a - axis * a.dot(axis)).normalized(), (b - axis * b.dot(axis)).normalized()
    return math.atan2(axis.dot(pa.cross(pb)), pa.dot(pb))


# --- the seated pose --------------------------------------------------------------------------------------------------------------


def _place(rig: bpy.types.Object, user: bpy.types.Object) -> None:
    rig.parent = user
    rig.matrix_parent_inverse = Matrix.Identity(4)
    rig.rotation_mode = "XYZ"
    rig.rotation_euler = (0.0, 0.0, math.radians(ch.RIG_YAW_DEG))
    bones = rig.data.bones
    hip_rig = (bones["upperleg01.L"].head_local + bones["upperleg01.R"].head_local) / 2
    hip_user = rig.rotation_euler.to_matrix() @ hip_rig
    rig.location = Vector(ch.HIP_JOINT) - hip_user
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = Quaternion()
    _update()


def _to_rig(rig: bpy.types.Object, world: Vector) -> Vector:
    return rig.matrix_world.inverted() @ world


def _user_dir(rig: bpy.types.Object, direction: tuple[float, float, float]) -> Vector:
    """A direction given in the user object's local frame, in rig space."""
    return (rig.matrix_basis.to_3x3().inverted() @ Vector(direction)).normalized()


def _pose_body(rig: bpy.types.Object, laptop: bpy.types.Object) -> dict[str, float]:
    """Seat the figure, put its hands on the keyboard; returns the finger flex sign per bone (+1 or -1 about local X)."""
    pitch_axis = _user_dir(rig, (0.0, 1.0, 0.0))  # turning about the user's left-right axis tips the top forward
    for name, lean in zip(ch.SPINE_BONES, ch.SPINE_LEAN_DEG, strict=True):
        _rotate(rig, name, Quaternion(pitch_axis, math.radians(lean)))
    decline, shin = math.radians(ch.THIGH_DECLINE_DEG), math.radians(ch.SHIN_FORWARD_DEG)
    signs: dict[str, float] = {}
    for side, s in (("L", 1.0), ("R", -1.0)):
        foot_rest = rig.data.bones[f"foot.{side}"].vector.copy()
        thigh = _user_dir(rig, (math.cos(decline), s * ch.KNEE_SPREAD, -math.sin(decline)))
        for name in (f"upperleg01.{side}", f"upperleg02.{side}"):
            _aim(rig, name, thigh)
        shin_dir = _user_dir(rig, (math.sin(shin), 0.0, -math.cos(shin)))
        for name in (f"lowerleg01.{side}", f"lowerleg02.{side}"):
            _aim(rig, name, shin_dir)
        _aim(rig, f"foot.{side}", foot_rest)
        signs |= _pose_arm(rig, laptop, side, s)
    return signs


def _pose_arm(rig: bpy.types.Object, laptop: bpy.types.Object, side: str, s: float) -> dict[str, float]:
    kx, _, kz = ch.KEYBOARD_HOME
    lateral = -s * ch.HAND_SPREAD  # the user faces -X in the world, so their left is the laptop's -Y
    finger_tip = _to_rig(rig, laptop.matrix_world @ Vector((kx, lateral, kz)))
    wrist = _to_rig(rig, laptop.matrix_world @ Vector((kx + ch.WRIST_BACK, lateral, kz + ch.WRIST_LIFT)))
    bones = rig.data.bones
    upper = (bones[f"lowerarm01.{side}"].head_local - bones[f"upperarm01.{side}"].head_local).length
    lower = (bones[f"wrist.{side}"].head_local - bones[f"lowerarm01.{side}"].head_local).length
    shoulder = _head(rig, f"upperarm01.{side}")
    reach = wrist - shoulder
    dist = min(reach.length, (upper + lower) * 0.999)
    u = reach.normalized()
    pole = _user_dir(rig, (ch.ELBOW_POLE[0], s * ch.ELBOW_POLE[1], ch.ELBOW_POLE[2]))
    v = (pole - u * pole.dot(u)).normalized()
    angle = math.acos(max(-1.0, min(1.0, (upper * upper + dist * dist - lower * lower) / (2 * upper * dist))))
    elbow = shoulder + upper * (math.cos(angle) * u + math.sin(angle) * v)
    for name in (f"upperarm01.{side}", f"upperarm02.{side}"):
        _aim(rig, name, elbow - _head(rig, name))
    for name in (f"lowerarm01.{side}", f"lowerarm02.{side}"):
        _aim(rig, name, wrist - _head(rig, name))
    inward = _user_dir(rig, (0.0, -s, 0.0))  # palm down: the index side faces the body's mid-line
    for name, share in ((f"lowerarm01.{side}", 0.5), (f"lowerarm02.{side}", 1.0)):
        across = _head(rig, f"finger2-1.{side}") - _head(rig, f"finger5-1.{side}")
        axis = _matrix(rig, name).to_3x3().col[1]
        _twist(rig, name, share * _signed_angle(across, inward, axis))
    _aim(rig, f"wrist.{side}", finger_tip - _head(rig, f"wrist.{side}"))
    across = _head(rig, f"finger2-1.{side}") - _head(rig, f"finger5-1.{side}")
    _twist(rig, f"wrist.{side}", _signed_angle(across, inward, _matrix(rig, f"wrist.{side}").to_3x3().col[1]))
    signs = _curl_fingers(rig, side)
    _level_hand(rig, laptop, side)
    return signs


def _level_hand(rig: bpy.types.Object, laptop: bpy.types.Object, side: str) -> None:
    """Pitch the hand about its knuckle line so the curled middle fingertip rests at ``FINGERTIP_REST_Z`` over the keys
    (the aimed hand plus the resting curl otherwise drops the fingertips through the laptop base)."""
    name, tip = f"wrist.{side}", f"finger3-3.{side}"
    to_laptop = laptop.matrix_world.inverted() @ rig.matrix_world
    base = _matrix(rig, name)
    axis = (_head(rig, f"finger2-1.{side}") - _head(rig, f"finger5-1.{side}")).normalized()

    def height(angle: float) -> float:
        head = base.translation
        _set(rig, name, Matrix.Translation(head) @ Matrix.Rotation(angle, 4, axis) @ Matrix.Translation(-head) @ base)
        return (to_laptop @ _tail(rig, tip)).z

    low, high = -math.radians(60.0), math.radians(60.0)
    rising = height(high) > height(low)
    for _ in range(40):  # bisection on the pitch angle
        mid = (low + high) / 2
        if (height(mid) < ch.FINGERTIP_REST_Z) == rising:
            low = mid
        else:
            high = mid
    height((low + high) / 2)


def _flex_sign(rig: bpy.types.Object, name: str) -> float:
    """+1 or -1: the sense of rotation about the bone's local X that bends the finger toward the palm (down, palm-down hand)."""
    down = _user_dir(rig, (0.0, 0.0, -1.0))
    base = _matrix(rig, name)
    scores = []
    for sign in (1.0, -1.0):
        _set(rig, name, base @ Matrix.Rotation(sign * math.radians(10.0), 4, "X"))
        scores.append((_tail(rig, name).dot(down), sign))
    _set(rig, name, base)
    return max(scores)[1]


def _curl_fingers(rig: bpy.types.Object, side: str) -> dict[str, float]:
    signs: dict[str, float] = {}
    for finger in ch.FINGERS:
        for segment, curl in zip(FINGER_SEGMENTS, ch.FINGER_CURL_DEG, strict=True):
            name = f"{finger}-{segment}.{side}"
            sign = _flex_sign(rig, name)
            signs[name] = sign
            _set(rig, name, _matrix(rig, name) @ Matrix.Rotation(sign * math.radians(curl), 4, "X"))
    for segment in FINGER_SEGMENTS:
        name = f"finger1-{segment}.{side}"
        _set(rig, name, _matrix(rig, name) @ Matrix.Rotation(_flex_sign(rig, name) * math.radians(ch.THUMB_CURL_DEG), 4, "X"))
    return signs


# --- motion poses -----------------------------------------------------------------------------------------------------------------


def _snapshot(rig: bpy.types.Object, names: tuple[str, ...]) -> Pose:
    return {n: rig.pose.bones[n].rotation_quaternion.copy() for n in names}


def _restore(rig: bpy.types.Object, pose: Pose) -> None:
    for name, q in pose.items():
        rig.pose.bones[name].rotation_quaternion = q
    _update()


def _variant(rig: bpy.types.Object, names: tuple[str, ...], change: Callable[[], None]) -> Pose:
    """The local rotations of ``names`` after ``change``, with the base pose restored afterwards."""
    base = _snapshot(rig, names)
    change()
    out = _snapshot(rig, names)
    _restore(rig, base)
    for name in names:  # same hemisphere as the base, so interpolation takes the short way
        if out[name].dot(base[name]) < 0:
            out[name].negate()
    return out


def _gaze(rig: bpy.types.Object, target: Vector) -> None:
    for _ in range(2):  # the second pass removes the error of turning about separate pivots
        eyes = (_head(rig, "eye.L") + _head(rig, "eye.R")) / 2
        face = ((_tail(rig, "eye.L") + _tail(rig, "eye.R")) / 2 - eyes).normalized()
        turn = face.rotation_difference((target - eyes).normalized())
        for name, share in zip(NECK_CHAIN, ch.HEAD_SHARE, strict=True):
            _rotate(rig, name, Quaternion().slerp(turn, share))


def _gaze_targets(rig: bpy.types.Object, objects: dict[str, bpy.types.Object]) -> dict[str, Vector]:
    laptop = objects[m.CLIENT]
    kx, _, kz = ch.KEYBOARD_HOME
    return {
        "keyboard": _to_rig(rig, laptop.matrix_world @ Vector((kx, 0.0, kz))),
        "laptop": _to_rig(rig, objects["SCREEN-IDLE"].matrix_world.translation),
        "session": _to_rig(rig, Vector(lo.SCREEN_CENTRE)),
    }


def _write_keys(rig: bpy.types.Object, objects: dict[str, bpy.types.Object], flex: dict[str, float]) -> int:
    writer = FCurveWriter(rig, ch.RIG)
    count = 0

    def key(name: str, frame: int, q: Quaternion, ease: str) -> None:
        nonlocal count
        writer.key(f'pose.bones["{name}"].rotation_quaternion', frame, tuple(q), ease=ease, smooth=ease == motion.SMOOTH)
        count += 4

    targets = _gaze_targets(rig, objects)
    gaze = {t: _variant(rig, NECK_CHAIN, lambda t=t: _gaze(rig, targets[t])) for t in ch.GAZE_TARGETS}  # type: ignore[misc]
    for k in ch.gaze_keys():
        for name in NECK_CHAIN:
            key(name, k.frame, gaze[k.target][name], k.ease)
    pitch_axis = _user_dir(rig, (0.0, 1.0, 0.0))
    chest = ("spine02",)
    breath = {a: _variant(rig, chest, lambda a=a: _rotate(rig, "spine02", Quaternion(pitch_axis, math.radians(a))))  # type: ignore[misc]
              for a in {v for _, v in ch.breath_keys()}}
    for frame, angle in ch.breath_keys():
        key("spine02", frame, breath[angle]["spine02"], motion.SMOOTH)
    for name, keys in ch.finger_keys().items():
        angles = {v for _, v in keys}
        poses = {a: _variant(rig, (name,), lambda a=a, name=name: _set(rig, name, _matrix(rig, name) @ Matrix.Rotation(flex[name] * math.radians(a), 4, "X")))  # type: ignore[misc]
                 for a in angles}
        for frame, angle in keys:
            key(name, frame, poses[angle][name], motion.CHARACTER_EASE)
    writer.finish()
    return count


# --- shading -------------------------------------------------------------------------------------------------------------------


def _shade(obj: bpy.types.Object) -> None:
    mat = obj.data.materials[0]
    nt = mat.node_tree
    image = next((n.image for n in nt.nodes if n.type == "TEX_IMAGE"), None)
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    if obj.name == "CHAR-body":
        bsdf.inputs["Base Color"].default_value = linear4(palette.SKIN_HEX)
        bsdf.inputs["Roughness"].default_value = look.CHARACTER_SKIN_ROUGHNESS
        bsdf.inputs["Subsurface Weight"].default_value = look.CHARACTER_SKIN_SUBSURFACE
        bsdf.inputs["Subsurface Radius"].default_value = (look.CHARACTER_SKIN_SUBSURFACE_RADIUS_M,) * 3
        return
    assert image is not None, obj.name
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = look.CHARACTER_TEXTURE_SATURATION
    hsv.inputs["Value"].default_value = look.CHARACTER_TEXTURE_VALUE
    nt.links.new(tex.outputs["Color"], hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    roughness = {"CHAR-hair": look.CHARACTER_HAIR_ROUGHNESS, "CHAR-brows": look.CHARACTER_HAIR_ROUGHNESS, "CHAR-eyes": look.CHARACTER_EYE_ROUGHNESS}
    bsdf.inputs["Roughness"].default_value = roughness.get(obj.name, look.CHARACTER_CLOTH_ROUGHNESS)
    if obj.name in ("CHAR-hair", "CHAR-brows"):
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        mat.surface_render_method = "DITHERED"


def build_character(scene: bpy.types.Scene, objects: dict[str, bpy.types.Object], tier: Tier) -> dict[str, object]:
    collection, rig = _load()
    scene.collection.children.link(collection)
    scene.frame_set(scene.frame_start)
    _place(rig, objects[m.USER])
    flex = _pose_body(rig, objects[m.CLIENT])
    keys = _write_keys(rig, objects, flex)
    levels = look.CHARACTER_SUBDIVISION[tier.name]
    for obj in collection.objects:
        if obj.type != "MESH":
            continue
        _shade(obj)
        if levels and obj.name in ("CHAR-body", "CHAR-clothes"):
            sub = obj.modifiers.new("SUBDIV", "SUBSURF")
            sub.levels, sub.render_levels = 0, levels
    return {"character_keys": keys, "flex_bones": len(flex)}
