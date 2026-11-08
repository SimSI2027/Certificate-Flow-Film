"""Hard tests learned from the accepted Stage 1 findings (Charter 2.4 step 7). Never delete these.

Each test is named after the finding it encodes; see docs/GAN-LEDGER.md, stage1-R1. In-Blender counterparts live in
``blender/checks/scene_checks.py`` (``fonts``, ``text_materials``, ``signs``).
"""

from __future__ import annotations

import ast
from functools import cache
from pathlib import Path

import pytest

from cff.stage import camera, caption_layout, choreography, labels, signs
from cff.stage.audit import beat_of_frame, is_visible
from cff.stage.objects import BY_ID, Kind
from cff.stage.tracks import LOCATION, Timeline
from cff.story import timing
from cff.theme import palette
from cff.theme import typography as ty
from tools import legibility_audit

ROOT = Path(__file__).resolve().parents[1]


@cache
def _timeline() -> Timeline:
    return choreography.build_timeline()


def _beat_frames(beat_id: str) -> range:
    first, last = timing.frame_range(*timing.beat_window(beat_id))
    return range(first, last + 1)


@pytest.mark.covers("L-02", "L-06")
def test_LEG_S1R1_01_text_passes_never_use_dithered_transparency() -> None:  # noqa: N802
    source = (ROOT / "blender" / "materials.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "caption_material")
    assert "TEXT_RENDER_METHOD" in ast.unparse(fn)
    assert 'TEXT_RENDER_METHOD = "BLENDED"' in source
    for module in ("captions_scene.py", "signs_scene.py"):
        assert "DITHERED" not in (ROOT / "blender" / module).read_text(encoding="utf-8"), module


@pytest.mark.covers("L-01")
def test_LEG_S1R1_03_sizes_use_measured_glyph_ratios_and_clear_the_minimums() -> None:  # noqa: N802
    # measured in Blender 5.2.3 from the evaluated 'H' glyph; check_fonts re-measures them on every verify
    assert ty.CAP_RATIO[ty.CAPTION_FONT] == pytest.approx(0.5087, abs=0.002)
    assert ty.CAP_RATIO[ty.LABEL_FONT] == pytest.approx(0.5198, abs=0.002)
    assert ty.CAPTION_CAP_PX >= 30.0 and ty.SIGN_CAP_PX >= 18.0
    for module in ("captions_scene.py", "signs_scene.py"):
        text = (ROOT / "blender" / module).read_text(encoding="utf-8")
        assert "0.72" not in text and "em_per_cap" in text, module


@pytest.mark.covers("L-01", "L-03", "L-06", "F-06")
def test_LEG_S1R1_04_to_11_and_PKI_S1R1_03_every_must_read_sign_is_fully_shown_for_its_hold() -> None:  # noqa: N802
    short = [(r.label_id, r.shown, r.needed) for r in legibility_audit.label_results() if not r.ok]
    assert not short, short


@pytest.mark.covers("L-03", "L-05", "L-06")
def test_LEG_S1R1_09_shown_signs_stay_inside_title_safe_and_never_overlap() -> None:  # noqa: N802
    x0, y0, x1, y1 = ty.TITLE_SAFE_PX
    by_frame: dict[int, list[tuple[str, signs.Rect]]] = {}
    for label_id, plan in signs.plan_signs().items():
        for frame, f in plan.frames.items():
            if f.alpha <= 0.0:
                continue
            r = f.rect
            assert x0 <= r[0] and y0 <= r[1] and r[2] <= x1 and r[3] <= y1, (label_id, frame, r)
            by_frame.setdefault(frame, []).append((label_id, r))
    for frame, rects in by_frame.items():
        for i, (a_id, a) in enumerate(rects):
            for b_id, b in rects[i + 1 :]:
                assert not signs._intersects(a, b), (frame, a_id, b_id)
            for c in signs.caption_rects(frame):
                assert not signs._intersects(a, c), (frame, a_id, "caption")


@pytest.mark.covers("L-05")
def test_LEG_S1R1_12_no_caption_plate_crosses_the_focal_subject() -> None:  # noqa: N802
    assert caption_layout.focal_overlaps() == {}


@pytest.mark.covers("C-03", "C-09")
def test_CIN_S1R1_01_no_sign_is_near_the_lens_or_larger_than_its_fixed_size() -> None:  # noqa: N802
    for label_id, plan in signs.plan_signs().items():
        w, h = ty.sign_plate_size_px(labels.BY_ID[label_id].text)
        for frame, f in plan.frames.items():
            r = f.rect
            assert abs((r[2] - r[0]) - w) < 1e-6 and abs((r[3] - r[1]) - h) < 1e-6, (label_id, frame)
            assert h < 0.08 * ty.FRAME_H_PX, label_id


@pytest.mark.covers("F-04", "C-07", "B-03.4", "B-04.1")
def test_PKI_S1R1_01_the_seal_rides_with_its_capsule_and_is_consumed_with_it() -> None:  # noqa: N802
    tl = _timeline()
    for tag, closed_beat in (("RDP", "B-04.1"), ("WEB", "B-07.4")):
        ring, req = f"SEAL-{tag}", f"REQ-{tag}"
        for frame in range(timing.seconds_to_frame(timing.beat_window(closed_beat)[0]), timing.frame_end() + 1):
            ring_on, req_on = is_visible(tl, ring, frame), is_visible(tl, req, frame)
            assert ring_on == req_on or not ring_on, (ring, frame)
            if ring_on:
                ring_at, req_at = tl.value_at(ring, LOCATION, frame), tl.value_at(req, LOCATION, frame)
                assert ring_at is not None and req_at is not None
                assert max(abs(a - b) for a, b in zip(ring_at, req_at, strict=True)) < 1e-6, (ring, frame)


@pytest.mark.covers("AR-05", "B-04.1")
def test_PKI_S1R1_02_the_capsule_waits_at_its_own_port_during_the_lookup() -> None:  # noqa: N802
    tl = _timeline()
    port = BY_ID["PORT-RDP-OUT"].home
    ad = BY_ID["AD"]
    hold = list(_beat_frames("B-04.1"))[30:-15]  # after the move to the port, before it launches
    for frame in hold:
        at = tl.value_at("REQ-RDP", LOCATION, frame)
        assert at is not None
        assert sum((a - b) ** 2 for a, b in zip(at, port, strict=True)) ** 0.5 < 1.0, frame
        assert abs(at[0] - ad.home[0]) > ad.size[0] / 2 + 0.5 or abs(at[1] - ad.home[1]) > ad.size[1] / 2 + 0.5, frame


@pytest.mark.covers("C-07", "AR-02", "B-05.2")
def test_PKI_S1R1_04_no_present_tense_check_slot_or_line_appears_in_the_flashback() -> None:  # noqa: N802
    tl = _timeline()
    plans = signs.plan_signs()
    for frame in _beat_frames("B-05.2"):
        for obj in BY_ID.values():
            if obj.kind is Kind.TICK:
                assert not is_visible(tl, obj.id, frame), (obj.id, frame)
        for label_id, plan in plans.items():
            if label_id.startswith(("LBL-ISSUING_CA", "LBL-CHAIN-")):
                assert frame not in plan.frames, (label_id, frame)


@pytest.mark.covers("C-01", "C-10", "AR-01", "F-15")
def test_PKI_S1R1_05_issuer_links_are_gold_to_ca_gradients_and_bowed_light() -> None:  # noqa: N802
    assert BY_ID["TL-CA1"].variant == "gold_to_cyan" and BY_ID["TL-CA2"].variant == "gold_to_violet"
    for link in (o for o in BY_ID.values() if o.kind is Kind.TRUST_LINK):
        assert link.variant in palette.TRUST_LINK_STOPS, link.id
    assert palette.TRUST_LINK_ARC_FRACTION > 0.0
    network = (ROOT / "blender" / "actors" / "network.py").read_text(encoding="utf-8")
    assert "TRUST_LINK_ARC_FRACTION" in network
    world = (ROOT / "blender" / "world.py").read_text(encoding="utf-8")
    assert "trust_link_material" in world


@pytest.mark.covers("C-11", "F-03")
def test_LEG_S1R1_02_the_public_key_has_no_key_silhouette() -> None:  # noqa: N802
    source = (ROOT / "blender" / "actors" / "artifacts.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "public_key")
    body = ast.unparse(fn)
    assert "torus" not in body, "a ring bow makes the public key read as a key"
    assert "cylinder(bm, s * 0.42, s * 0.08, 6" in body, "the public key is a notched hexagonal token"


@pytest.mark.covers("C-09", "L-06")
def test_CIN_S1R1_04_tag_and_check_lists_stand_beside_the_focal_subject() -> None:  # noqa: N802
    tl = _timeline()
    plan = camera.CameraPlan(tl)
    beats = beat_of_frame()
    crossing = 0
    shown = 0
    for label_id, sign in signs.plan_signs().items():
        if labels.BY_ID[label_id].window is None:
            continue
        for frame, f in sign.frames.items():
            if f.alpha < 1.0 or frame not in beats:
                continue
            focal = caption_layout.focal_rect(tl, plan, beats[frame], frame)
            shown += 1
            crossing += focal is not None and signs._intersects(f.rect, focal)
    assert shown and crossing / shown <= 0.1, f"{crossing} of {shown} tag frames cross the focal subject"
