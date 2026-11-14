"""v1.3 finishing pass (session V3): one regression test per item.

1. L2-CIN-01: the camera-following rig lights never sit inside an actor, never jump, and the rim is not hidden behind the
   root tower at 51 s. The luma steps themselves are measured on the Final MP4 by ``tools verify`` (``step_mp4_luma``).
2. Interiors: every server chassis and issuing-CA vault is dressed with static practicals in non-state token colours.
3. Hero: the whole topology, the user included, is in frame from 98.5 s; brightness is measured on the MP4 by verify.
4. F3-PKI-01: the handshake proof carries a short tag that is fully readable for 1.5 s, and the tag is accurate to F-10.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path
from typing import Any

import pytest

from cff.stage import camera, choreography, labels, rig
from cff.stage.tracks import SCALE
from cff.story import model, timing
from cff.theme import look, palette, shots

ROOT = Path(__file__).resolve().parents[1]
RIG_MAX_EXTRA_STEP_M = 0.5  # the keep-out may add at most this much to a light's frame-to-frame move (no jumps)
ROOT_HIDE_FRAMES = range(1529, 1535)  # L2: the rim's glow sat behind the root tower here and came out at f1535


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _plan() -> tuple[Any, camera.CameraPlan]:
    tl = choreography.build_timeline()
    return tl, camera.CameraPlan(tl)


# --- 1. L2-CIN-01 -------------------------------------------------------------------------------------------------------------------------


def _hidden_by(cam: tuple[float, float, float], light: tuple[float, float, float], solid: rig.Solid) -> bool:
    body = solid.radius - look.RIG_KEEP_OUT_MARGIN_M
    for i in range(1, 400):
        t = i / 400
        p = (cam[0] + (light[0] - cam[0]) * t, cam[1] + (light[1] - cam[1]) * t, cam[2] + (light[2] - cam[2]) * t)
        if math.hypot(p[0] - solid.centre[0], p[1] - solid.centre[1]) < body and p[2] < solid.top:
            return True
    return False


@pytest.mark.covers("C-05")
def test_L2_CIN_01_rig_lights_stay_out_of_actors() -> None:  # noqa: N802
    _, plan = _plan()
    previous: tuple[Any, ...] | None = None
    for frame in plan.frames():
        state = plan.state(frame)
        placed = rig.rig_frame(state)
        key, rim, _ = rig.raw_positions(state)
        for name, point in (("key", placed.key), ("rim", placed.rim)):
            inside = [s.name for s in rig.SOLIDS if rig.inside(point, s)]
            assert not inside, f"f{frame}: the {name} light is inside {inside}"
        if previous is not None:
            for raw_a, raw_b, a, b in ((previous[0], key, previous[2], placed.key), (previous[1], rim, previous[3], placed.rim)):
                assert math.dist(a, b) <= math.dist(raw_a, raw_b) + RIG_MAX_EXTRA_STEP_M, f"f{frame}: the keep-out makes a light jump"
        previous = (key, rim, placed.key, placed.rim)
    root = next(s for s in rig.SOLIDS if s.name == "root")
    for frame in ROOT_HIDE_FRAMES:
        state = plan.state(frame)
        assert not _hidden_by(state.position, rig.rig_frame(state).rim, root), f"f{frame}: the rim is hidden behind the root tower"
    source = _text("blender/lighting.py")
    assert "rig.rig_frame(state)" in source and "RIM_BEHIND" not in source, "blender/lighting.py must key the planned, kept-out rig"


# --- 2. interiors -------------------------------------------------------------------------------------------------------------------------


@pytest.mark.covers("C-05", "C-10")
def test_V13_interiors_are_dressed_with_static_practicals() -> None:  # noqa: N802
    source = _text("blender/dressing.py")
    tree = ast.parse(source)
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not calls & {"keyframe_insert", "key"}, "dressing never animates"
    tokens = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "palette"}
    tokens |= {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.endswith("_HEX")}
    assert tokens == {"POOL_NEUTRAL_HEX", "RIM_LIGHT_HEX", "POOL_CA1_HEX", "POOL_CA2_HEX"}, tokens
    states = {palette.role_hex(r) for r in (model.ColourRole.VALIDATED, model.ColourRole.PENDING, model.ColourRole.REVOCATION)}
    assert not {getattr(palette, t) for t in tokens} & states
    assert "dressing.build_dressing(" in _text("blender/build_scene.py")
    assert "check_dressing()" in _text("blender/checks/scene_checks.py")
    assert "materials.chassis_material()" in _text("blender/world.py")
    assert look.CHASSIS_TOP_W > 0 and look.CHASSIS_RIM_W > 0 and look.VAULT_TOP_W > 0


# --- 3. hero ------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.covers("C-03", "B-09.2")
def test_V13_hero_holds_the_whole_topology_from_98_5_s() -> None:  # noqa: N802
    from tests.test_audit_v1 import _hold, _raw_rect  # noqa: PLC0415
    from tools import verify  # noqa: PLC0415

    tl, plan = _plan()
    objs = (model.USER, model.CLIENT, model.RDP_SERVER, model.WEB_SERVER, model.ISSUING_CA1, model.ISSUING_CA2, model.ROOT_CA)
    first = timing.seconds_to_frame(verify.HERO_WHOLE_FROM_S)
    _, last = timing.frame_range(*timing.beat_window("B-09.2"))
    c, d = _hold("B-09.3")
    for f in [*range(first, last + 1), *range(c, d + 1)]:
        for o in objs:
            r = _raw_rect(tl, plan, o, f)
            assert r is not None and r[0] >= 96 and r[2] <= 1824 and r[1] >= 200 and r[3] <= 1026, f"f{f}: {o} is not whole in frame"
    assert verify.HERO_WHOLE_FROM_S == 98.5 and verify.HERO_LUMA_MIN == 50.0
    assert shots.BY_BEAT["B-09.2"].start is None, "no cut: the hero is reached by one continuous move (C-02)"


# --- 4. F3-PKI-01 -------------------------------------------------------------------------------------------------------------------------


@pytest.mark.covers("F-10", "B-06.1")
def test_F3_PKI_01_handshake_proof_is_labelled_and_readable() -> None:  # noqa: N802
    from tools import legibility_audit  # noqa: PLC0415

    label = labels.LABELS["LBL-HS-RDP"]
    assert label.text == "Proof: private-key signature"  # the proof is a signature made with the key; the key itself never travels
    assert labels.BY_ID["LBL-HS-RDP"].parent == "HS-RDP"
    result = next(r for r in legibility_audit.label_results() if r.label_id == "LBL-HS-RDP")
    assert result.ok and result.needed == round(legibility_audit.MUST_READ_HOLD_S * timing.FPS), result
    tl = choreography.build_timeline()
    _, beat_last = timing.frame_range(*timing.beat_window("B-06.1"))
    scale = tl.value_at("HS-RDP", SCALE, beat_last)
    assert scale is not None and min(scale) > 0.5, "the matched proof rests by the card until B-06.1 ends"
    event = next(e for e in model.MODEL.events if e.id == "E-06.1d")
    assert event.uses_key == "KEY-RDP-PRIV"
