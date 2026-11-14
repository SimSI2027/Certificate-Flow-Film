"""Static checks for the v1.2 materials and lighting pass (docs/LOOK-PLAN-v1.2.md). No Blender needed. Test names carry the finding ID."""
# ruff: noqa: N802

from __future__ import annotations

import ast
from pathlib import Path

from cff.story.model import ColourRole
from cff.theme import colour, look, palette, render

ROOT = Path(__file__).resolve().parents[1]
# Ruling L1-R1 (docs/GAN-LEDGER.md "Session L1"): the plan said 25 dE2000, but its own gold root pool (15.9 from REVOCATION, as close as
# the root's identity colour itself) cannot reach that. The project's existing role-separation floor applies instead.
STATE_DE_MIN = palette.L07_MIN_DELTA_E


def _function_source(path: str, name: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(f"{path}: no function {name}")


def test_LOOK_A_haze_only_on_volumetric_tiers() -> None:
    assert "tier.volumetrics" in _function_source("blender/world.py", "build_world")
    assert render.tier("animatic").volumetrics is False
    assert render.tier("final").volumetrics is True


def test_LOOK_A_pools_never_use_state_colours() -> None:
    states = (ColourRole.VALIDATED, ColourRole.PENDING, ColourRole.REVOCATION)
    for _name, _anchor, token, _power in look.POOLS:
        lab = colour.rgb_to_lab(colour.hex_to_rgb(getattr(palette, token)))
        for state in states:
            state_lab = colour.rgb_to_lab(colour.hex_to_rgb(palette.role_hex(state)))
            assert colour.delta_e_2000(lab, state_lab) > STATE_DE_MIN, f"pool {token} is within {STATE_DE_MIN} dE of {state.name}"


def test_LOOK_A_pools_are_static() -> None:
    assert ".key(" not in _function_source("blender/lighting.py", "build_pools")


def test_LOOK_A_ambient_unchanged() -> None:
    assert palette.WORLD_STRENGTH == 0.02
    assert palette.KEY_LIGHT_POWER_W == 900.0
    assert palette.RIM_LIGHT_POWER_W == 1050.0


def test_LOOK_A_one_pool_per_actor_and_unique_names() -> None:
    names = [row[0] for row in look.POOLS]
    assert len(names) == len(set(names)) == 7
    assert all(hasattr(palette, row[2]) for row in look.POOLS)


def test_LOOK_A_haze_density_stays_in_its_tuning_range() -> None:
    assert look.HAZE_DENSITY_MIN <= look.HAZE_DENSITY <= look.HAZE_DENSITY_MAX


def test_F3_LEG_01_flashback_marker_ends_at_the_cut() -> None:
    from cff.stage import signs  # noqa: PLC0415

    sign = signs.plan_signs()["LBL-FLASHBACK"]
    assert max(f for f, s in sign.frames.items() if s.alpha > 0) <= 1395


def test_F3_AUD_01_true_peak_aim_and_mp4_measurement() -> None:
    from tools import film, verify  # noqa: PLC0415

    assert film.TARGET_TP == -2.0
    assert verify.MP4_TRUE_PEAK_MAX_DBFS == -1.0
    summary = "  Integrated loudness:\n    I:         -16.0 LUFS\n  True peak:\n    Peak:       -1.4 dBFS\n"
    assert verify.mp4_true_peak(summary) == -1.4
    assert verify.mp4_true_peak("nothing here") is None


def test_F3_PIPE_02_metadata_records_a_dirty_flag() -> None:
    from tools import film  # noqa: PLC0415

    assert isinstance(film.source_dirty(), bool)
    assert '"dirty": source_dirty()' in (ROOT / "tools" / "film.py").read_text(encoding="utf-8")
    assert '.get("dirty") is True' in (ROOT / "tools" / "verify.py").read_text(encoding="utf-8")


def test_LOOK_C_web_badge_rests_before_the_flyovers() -> None:
    from cff.stage import choreography  # noqa: PLC0415
    from cff.stage.tracks import GLOW  # noqa: PLC0415
    from cff.story import timing  # noqa: PLC0415

    tl = choreography.build_timeline()
    rest = choreography.hex_glow(palette.TEXT_HEX, palette.BADGE_REST_GLOW)
    start = timing.seconds_to_frame(timing.beat_window("B-07.4")[0]) + 30
    assert start <= 2416
    for frame in (start, start + 30, timing.frame_end()):
        assert tl.value_at("TPL-WEBTLS", GLOW, frame) == rest, frame


