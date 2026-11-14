"""Regression tests for the v1 audit (docs/AUDIT-v1.md), session F1. Each test is named after its finding ID."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from cff.stage import camera, caption_layout, choreography, labels, signs
from cff.stage.audit import beat_of_frame
from cff.stage.tracks import GLOW
from cff.story import timing
from cff.theme import typography as ty
from tools import film, verify

ROOT = Path(__file__).resolve().parents[1]
FPS = timing.FPS


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _event_start_s(event_id: str) -> float:
    from cff.story import model  # noqa: PLC0415

    return next(e for e in model.MODEL.events if e.id == event_id).start_s


@pytest.mark.covers("L-06")
def test_V1_LEG_01_overlay_scenes_never_use_motion_blur() -> None:  # noqa: N802
    source = _text("blender/render_settings.py")
    line = next(ln for ln in source.splitlines() if "render.use_motion_blur" in ln)
    assert "and not transparent" in line


@pytest.mark.covers("C-02")
def test_V1_CIN_04_shutter_opens_at_the_frame() -> None:  # noqa: N802
    assert 'motion_blur_position = "START"' in _text("blender/render_settings.py")


@pytest.mark.covers("C-02")
def test_V1_PIPE_01_verify_inspects_the_final_tier_and_the_mp4() -> None:  # noqa: N802
    run_source = _text("tools/verify.py").split("def run(", 1)[1]
    for step in ("step_frame_tiers", "step_final_mp4", "step_cut_frames"):
        assert step in run_source, step
    good: dict[str, Any] = {
        "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080, "r_frame_rate": "30/1", "nb_frames": str(timing.frame_end()),
             "color_transfer": "bt709", "level": 41},
            {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 2},
        ],
        "format": {"duration": f"{timing.total_duration_s():.3f}"},
    }
    assert verify.mp4_problems(good) == []
    bad: dict[str, Any] = {**good, "streams": [{**good["streams"][0], "width": 1280, "color_transfer": "iec61966-2-1"}, good["streams"][1]]}
    assert len(verify.mp4_problems(bad)) == 2
    assert verify.cut_luma_steps("lavfi.signalstats.YAVG=43.6\nlavfi.signalstats.YAVG=97.3") == {0: 43.6, 1: 97.3}


@pytest.mark.covers("C-02")
def test_V1_ENC_01_stream_tags_and_level() -> None:  # noqa: N802
    source = _text("tools/film.py")
    assert "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" in source
    assert film.H264_LEVEL == ["-refs", "4", "-level:v", "4.1"]
    assert source.count("*H264_LEVEL") == 2  # both the Final and the Preview encode


@pytest.mark.covers("AR-05", "F-11")
def test_V1_PKI_01_trust_store_is_gold_before_docking() -> None:  # noqa: N802
    tl = choreography.build_timeline()
    first_event_frame = timing.seconds_to_frame(_event_start_s("E-06.2a"))
    last_beat_frame = timing.seconds_to_frame(timing.beat_window("B-06.6")[1])
    start = tl.value_at("TS-CLIENT-ROOT", GLOW, 1)
    assert start is not None
    assert tl.value_at("TS-CLIENT-ROOT", GLOW, first_event_frame) == start
    assert tl.value_at("TS-CLIENT-ROOT", GLOW, last_beat_frame) == start


@pytest.mark.covers("AR-01", "B-05.2")
def test_V1_PKI_02_flashback_marker_whole_flashback() -> None:  # noqa: N802
    sign = signs.plan_signs()["LBL-FLASHBACK"]
    first, last = timing.frame_range(*timing.beat_window("B-05.2"))
    full = sum(1 for f in range(first, last + 1) if f in sign.frames and sign.frames[f].alpha >= 1.0)
    assert full >= 125, f"marker fully shown on {full} frames"
    assert any(sign.frames.get(f) is not None and sign.frames[f].alpha > 0 for f in range(first, first + 5))
    assert any(s.rect[1] >= ty.TITLE_SAFE_PX[1] for s in sign.frames.values())


@pytest.mark.covers("F-03", "F-04")
def test_V1_PKI_03_private_key_tag_never_leaves_the_server() -> None:  # noqa: N802
    keys = ("RDP-PRIV", "RDP-PUB", "WEB-PRIV", "WEB-PUB")
    for label_id, parent in ((f"LBL-KEY-{k}", f"KEY-{k}") for k in keys):
        assert labels.BY_ID[label_id].parent == parent
        assert labels.LABELS[label_id].text in ("Private key", "Public key")
        assert len(labels.must_read_frames(label_id)) >= 45
    tl = choreography.build_timeline()
    plan = camera.CameraPlan(tl)
    from cff.story import model  # noqa: PLC0415

    for f in signs.plan_signs()["LBL-KEY-RDP-PRIV"].frames:
        server = caption_layout.objects_rect(tl, plan, (model.RDP_SERVER,), f)
        anchor_px = camera.project(plan.state(f), signs.anchor(tl, labels.BY_ID["LBL-KEY-RDP-PRIV"], f))
        if server is None or anchor_px[2] <= 0:
            continue
        x, y = anchor_px[0] * ty.FRAME_W_PX, anchor_px[1] * ty.FRAME_H_PX
        assert server[0] - 100 <= x <= server[2] + 100 and server[1] - 100 <= y <= server[3] + 100, f
    assert "Private key" in _text("docs/STORYBOARD.md")


@pytest.mark.covers("L-06")
def test_V1_LEG_04_plate_beats_cover_must_read() -> None:  # noqa: N802
    for label_id, beats in labels.PLATE_BEATS.items():
        must = labels.LABELS[label_id].must_read_beats
        assert set(must) <= set(beats), (label_id, must, beats)


@pytest.mark.covers("L-06")
def test_V1_LEG_04_plates_only_in_their_beats() -> None:  # noqa: N802
    beats = beat_of_frame()
    for label_id, allowed in labels.PLATE_BEATS.items():
        for f in signs.plan_signs()[label_id].frames:
            assert beats.get(f) in allowed, (label_id, f)


@pytest.mark.covers("L-06")
def test_V1_LEG_04_at_most_10_signs() -> None:  # noqa: N802
    count: dict[int, int] = {}
    for sign in signs.plan_signs().values():
        for f in sign.frames:
            count[f] = count.get(f, 0) + 1
    worst = max(count.values())
    assert worst <= SIGN_COUNT_LIMIT, f"{worst} signs on one frame (v1.0.0 peaked at 15)"


SIGN_COUNT_LIMIT = 10


# --- session F2: camera ---------------------------------------------------------------------------------------------

def _event_frames(first_event: str, last_event: str | None = None) -> tuple[int, int]:
    from cff.story import model  # noqa: PLC0415

    by_id = {e.id: e for e in model.MODEL.events}
    a, b = by_id[first_event], by_id[last_event or first_event]
    return timing.frame_range(timing.event_window(a.id, a.beat)[0], timing.event_window(b.id, b.beat)[1])


def _hold(beat_id: str) -> tuple[int, int]:
    from cff.stage.audit import HOLD_MARGIN_S  # noqa: PLC0415

    start, end = timing.beat_window(beat_id)
    return timing.frame_range(start + HOLD_MARGIN_S, end - HOLD_MARGIN_S)


def _plan() -> tuple[Any, camera.CameraPlan]:
    tl = choreography.build_timeline()
    return tl, camera.CameraPlan(tl)


def _raw_rect(tl: Any, plan: camera.CameraPlan, obj_id: str, frame: int) -> tuple[float, float, float, float] | None:
    """Unclamped projected bounds (1080p px); None when hidden, an infinite rect when a corner is behind the lens."""
    import math  # noqa: PLC0415

    from cff.stage.audit import is_visible, position_at  # noqa: PLC0415
    from cff.stage.tracks import SCALE  # noqa: PLC0415

    if not is_visible(tl, obj_id, frame):
        return None
    state = plan.state(frame)
    scale = tl.value_at(obj_id, SCALE, frame) or (1.0, 1.0, 1.0)
    xs, ys = [], []
    for corner in caption_layout._corners(obj_id, position_at(tl, obj_id, frame), scale):
        px, py, depth = camera.project(state, corner)
        if depth <= 0 or not math.isfinite(px):
            return (-math.inf, -math.inf, math.inf, math.inf)
        xs.append(px * ty.FRAME_W_PX)
        ys.append(py * ty.FRAME_H_PX)
    return (min(xs), min(ys), max(xs), max(ys))


@pytest.mark.covers("C-03")
def test_V1_CIN_01_focal_subject_size() -> None:  # noqa: N802
    from tools import focal_audit  # noqa: PLC0415

    assert focal_audit.failing() == {}
    sizes = focal_audit.beat_sizes()
    for beat_id in focal_audit.RESIDUAL_PX:  # a residual that now meets its real target must be removed
        assert sizes[beat_id] < focal_audit.TARGET_PX.get(beat_id, focal_audit.DEFAULT_TARGET_PX), beat_id
    assert len(focal_audit.RESIDUAL_PX) <= 9  # v1.0.0: 11 beats under target


@pytest.mark.covers("F-10")
def test_V1_PKI_04_handshake_proof_is_visible() -> None:  # noqa: N802
    from tools import focal_audit  # noqa: PLC0415

    tl, plan = _plan()
    assert focal_audit.longer_side(tl, plan, ("HS-RDP",), *_event_frames("E-06.1d", "E-06.1f")) >= 60.0
    assert focal_audit.longer_side(tl, plan, ("HS-WEB",), *_event_frames("E-09.1d", "E-09.1q")) >= 45.0


@pytest.mark.covers("F-13")
def test_V1_PKI_05_crl_fetches_are_visible() -> None:  # noqa: N802
    import math  # noqa: PLC0415

    from cff.stage.audit import position_at  # noqa: PLC0415
    from tools import focal_audit  # noqa: PLC0415

    tl, plan = _plan()
    for scroll, event_id, card in (("CRL-CA1", "E-06.5a", "CERT-RDP"), ("CRL-ROOT", "E-06.5b", "CERT-CA1-COPY-RDP")):
        first, last = _event_frames(event_id)
        assert focal_audit.longer_side(tl, plan, (scroll,), first, last) >= FETCH_MIN_PX, scroll
        at = position_at(tl, scroll, last)
        assert math.dist(at, position_at(tl, card, last)) <= 1.0, (scroll, card)
        assert math.dist(at, position_at(tl, "CERT-ROOT", last)) >= 0.6, scroll


FETCH_MIN_PX = 60.0


@pytest.mark.covers("C-03", "B-06.6")
def test_V1_CIN_05_session_window_is_visible() -> None:  # noqa: N802
    from tools import focal_audit  # noqa: PLC0415

    tl, plan = _plan()
    first, last = _hold("B-06.6")
    assert focal_audit.longer_side(tl, plan, ("SCREEN-RDP",), first, last) >= SESSION_WINDOW_MIN_PX
    plan_signs = signs.plan_signs()
    for f in range(first, last + 1):
        screen = caption_layout.objects_rect(tl, plan, ("SCREEN-RDP",), f)
        if screen is None:
            continue
        for label_id, sign in plan_signs.items():
            s = sign.frames.get(f)
            if s is not None and s.alpha > 0:
                assert not caption_layout._hits(s.rect, screen), (label_id, f)


SESSION_WINDOW_MIN_PX = 185.0  # residual (target 220): closer framings break C-02 on the move into B-07.1


@pytest.mark.covers("B-09.2")
def test_V1_CIN_02_hero_holds_the_whole_topology() -> None:  # noqa: N802
    from cff.story import model  # noqa: PLC0415

    tl, plan = _plan()
    objs = (model.USER, model.CLIENT, model.RDP_SERVER, model.WEB_SERVER, model.ISSUING_CA1, model.ISSUING_CA2, model.ROOT_CA)
    _, last = _hold("B-09.2")
    c, d = _hold("B-09.3")
    frames = [*range(last - HERO_ARRIVED_FRAMES + 1, last + 1), *range(c, d + 1)]

    def inside(f: int) -> bool:
        rects = [_raw_rect(tl, plan, o, f) for o in objs]
        return all(r is not None and r[0] >= 96 and r[2] <= 1824 and r[1] >= 200 and r[3] <= 1026 for r in rects)

    assert sum(inside(f) for f in frames) >= 0.9 * len(frames)
    root = _raw_rect(tl, plan, model.ROOT_CA, last)
    assert root is not None and root[2] - root[0] >= 110.0
    assert caption_layout.bands()["CAP-S9a"] == caption_layout.TOP
    assert "CAP-S9a" not in caption_layout.focal_overlaps()


HERO_ARRIVED_FRAMES = 60  # residual: the camera pulls back from the B-09.1 close-up, so the topology is whole from ~102 s


# --- session F2: small fixes ----------------------------------------------------------------------------------------

@pytest.mark.covers("AR-01", "B-05.1")
def test_V1_PKI_06_self_signed_seals_are_perceivable() -> None:  # noqa: N802
    from tools import focal_audit  # noqa: PLC0415

    tl, plan = _plan()
    assert focal_audit.longer_side(tl, plan, ("SEAL-ROOT",), *_hold("B-05.1")) >= 110.0
    assert "h * 0.36, 0.012" in _text("blender/actors/artifacts.py")  # the self-seal ring radius doubled (was h * 0.18)


@pytest.mark.covers("F-04", "B-03.4")
def test_V1_CIN_07_sealing_changes_the_capsule() -> None:  # noqa: N802
    from cff.theme import palette  # noqa: PLC0415

    assert "o.size[0] / 2, 0.045" in _text("blender/actors/network.py")
    tl = choreography.build_timeline()
    levels = [max(v[:3]) for f in range(1, timing.frame_end() + 1) if (v := tl.value_at("SEAL-RDP", GLOW, f)) is not None]
    assert levels and max(levels) > levels[0] * 1.2, "the closed seal peaks above the glow it appears with"
    assert palette.GLOW_PEAK > palette.GLOW_ACTIVE


@pytest.mark.covers("L-07")
def test_V1_COL_01_role_hues_hold_at_distance() -> None:  # noqa: N802
    from cff.theme import palette  # noqa: PLC0415

    assert palette.EMISSION_STRENGTH <= 1.8 and palette.TRUST_LINK_EMISSION <= 1.2


@pytest.mark.covers("C-05")
def test_V1_CIN_03_step1_issuing_ca_vaults_are_dimmed() -> None:  # noqa: N802
    from cff.story.model import ColourRole  # noqa: PLC0415
    from cff.theme import palette  # noqa: PLC0415

    cyan = palette.role_hex(ColourRole.ISSUING_CA1)
    dim = palette.value_scaled_hex(cyan, palette.VAULT_VALUE_SCALE)
    assert max(int(dim[i:i + 2], 16) for i in (1, 3, 5)) == round(max(int(cyan[i:i + 2], 16) for i in (1, 3, 5)) * 0.45)
    assert "vault_material" in _text("blender/world.py")


# --- session F2: signs ----------------------------------------------------------------------------------------------

def _check_lines() -> list[str]:
    return [i for ids in labels.CHECK_LISTS for i in ids if i in labels.CHECK_TICK_ROLES]


@pytest.mark.covers("F-06", "F-12")
def test_V1_LEG_03_no_check_line_before_its_check() -> None:  # noqa: N802
    lines = _check_lines()
    assert len(lines) == 18
    plan_signs = signs.plan_signs()
    by_event = {p.label_id: p for p in labels.PLACEMENTS}
    for label_id in lines:
        window = by_event[label_id].window
        assert window is not None
        event_frame = labels.window_frames(window)[0]
        first = min(plan_signs[label_id].frames)
        assert first >= event_frame, (label_id, first, event_frame)
    # every line's window opens at its own check event (not at a shared list start)
    from cff.story import model  # noqa: PLC0415

    events = {e.id: e for e in model.MODEL.events}
    ca1 = [i for i in labels.CHECK_LISTS[0] if i in labels.CHECK_TICK_ROLES]
    for letter, label_id in zip("abcd", ca1, strict=True):
        start = labels.window_frames(by_event[label_id].window)[0]  # type: ignore[arg-type]
        assert start >= timing.seconds_to_frame(events[f"E-04.3{letter}"].start_s), label_id


@pytest.mark.covers("L-06")
def test_V1_LEG_03_check_lines_never_move() -> None:  # noqa: N802
    plan_signs = signs.plan_signs()
    fixed = signs.fixed_list_positions()
    for ids in labels.CHECK_LISTS:
        for label_id in ids:
            rects = {f.rect for f in plan_signs[label_id].frames.values()}
            assert len(rects) == 1, (label_id, len(rects))
            assert label_id in fixed
        xs = {fixed[i][0] for i in ids}
        assert len(xs) == 1  # one left edge per list


@pytest.mark.covers("F-13", "B-06.4")
def test_V1_LEG_03_revocation_ok_after_fetches() -> None:  # noqa: N802
    resolve = labels.tick_resolve_frame("LBL-CHAIN-RDP-REVOCATION")
    assert resolve == timing.seconds_to_frame(_event_start_s("E-06.5d"))
    assert resolve > timing.seconds_to_frame(_event_start_s("E-06.5b"))
    source = _text("blender/signs_scene.py")
    assert "tick_resolve_frame" in source and '"pending"' in source and '"resolved"' in source
    assert "ob.hide_render = True" in _text("blender/world.py")


@pytest.mark.covers("C-06", "L-06")
def test_V1_LEG_02_no_sign_jumps() -> None:  # noqa: N802
    import math  # noqa: PLC0415

    out = []
    for label_id, sign in signs.plan_signs().items():
        for f in sorted(sign.frames):
            a, b = sign.frames.get(f - 1), sign.frames[f]
            if a and min(a.alpha, b.alpha) >= 0.5 and math.hypot(b.rect[0] - a.rect[0], b.rect[1] - a.rect[1]) > 96.0:
                out.append((f, label_id))
    assert out == []  # v1.0.0: 51 frames


@pytest.mark.covers("C-06", "L-06")
def test_V1_LEG_02_no_sign_flashes() -> None:  # noqa: N802
    for label_id, sign in signs.plan_signs().items():
        frames = sorted(sign.frames)
        runs: list[list[int]] = []
        for f in frames:
            if runs and f == runs[-1][1] + 1:
                runs[-1][1] = f
            else:
                runs.append([f, f])
        short = [r for r in runs if r[1] - r[0] + 1 < 24]
        assert short == [], (label_id, short)


@pytest.mark.covers("L-06")
def test_V1_LEG_05_aia_tags_hold_long_enough() -> None:  # noqa: N802
    plan_signs = signs.plan_signs()
    for label_id in ("LBL-AIA-1", "LBL-AIA-2", "LBL-CA2-NOTE"):
        full = sum(1 for f in plan_signs[label_id].frames.values() if f.alpha >= 1.0)
        assert full >= round(2.1 * FPS), (label_id, full)  # 6 words at 0.35 s per word


@pytest.mark.covers("L-05")
def test_V1_DOC_01_caption_track_is_opt_in() -> None:  # noqa: N802
    import importlib.util  # noqa: PLC0415

    spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for page in (module.PAGE, _text("site/index.html")):
        track = re.search(r"<track[^>]*>", page)
        assert track is not None
        assert " default" not in track.group(0)


@pytest.mark.covers("L-05")
def test_V1_DOC_02_wording_matches_the_film_and_its_status() -> None:  # noqa: N802
    readme, site = _text("README.md"), _text("site/index.html")
    assert "v1.0.0 pre-release" in readme and "released" not in readme.lower()
    assert "one continuous camera move, with a single flashback" in readme
    assert "continuous shot" not in readme and "continuous shot" not in site
    assert "whose CA certificate was signed offline by the" in site
    assert "the request carries only the public key" in site
    assert "pre-release" in site and "Release v1.0.0" not in site
