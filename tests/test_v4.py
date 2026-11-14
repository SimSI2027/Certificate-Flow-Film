"""Session V4 (owner request): the MALAWI rename and the realistic user character.

V4-REN-01: the lab's earlier name must not appear in any caption, sign, label, model text or site text.
V4-CHR-01: the user character is a local CC0 asset, recorded in LICENSES\\ and README, built from cff timing and theme motion.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest

from cff.config import names as n
from cff.stage import character as ch
from cff.stage import labels
from cff.stage import layout as lo
from cff.stage.objects import BY_ID
from cff.story import captions as cap
from cff.story import model, timing
from cff.story.export import model_dump
from cff.theme import motion
from tools import pipeline

ROOT = Path(__file__).resolve().parents[1]
OLD_NAME = re.compile("1" + "sn0s", re.IGNORECASE)  # split so this file never matches a repo-wide search for the old name


def _site_page() -> str:
    spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    page: str = module.page_html("https://example.invalid/release")
    return page


@pytest.mark.covers("L-08")
def test_V4_REN_01_names_are_malawi() -> None:  # noqa: N802
    assert (n.AD_DOMAIN_FQDN, n.AD_NETBIOS, n.DNS_SUFFIX) == ("MALAWI.LAB", "MALAWI", "malawi.lab")
    assert (n.ROOT_CA_NAME, n.ISSUING_CA1_NAME, n.ISSUING_CA2_NAME) == ("MALAWI Root CA", "MALAWI Issuing CA 1", "MALAWI Issuing CA 2")
    assert (n.WEB_SITE_DNS_NAME, n.PKI_HTTP_HOST) == ("portal.malawi.lab", "pki.malawi.lab")


@pytest.mark.covers("L-08")
def test_V4_REN_01_old_name_absent_from_captions_labels_and_site() -> None:  # noqa: N802
    texts: dict[str, str] = {}
    texts.update({f"caption {c.id}": c.text for c in cap.CAPTIONS})
    texts.update({f"sign {p.label_id}": p.text for p in labels.PLACEMENTS})
    texts["captions.vtt"] = pipeline.captions_vtt()
    texts["transcript.md"] = pipeline.transcript_md()
    texts["model dump"] = json.dumps(model_dump(), ensure_ascii=False)
    texts["names"] = json.dumps({v.variable: v.value for v in n.names_in_use()} | n.derived_names())
    texts["site page (scripts/build_site.py)"] = _site_page()
    for where in ("README.md", "docs/REFERENCE-SPEC.md", "docs/STORYBOARD.md", "docs/GLOSSARY.md", "docs/PKI-TECHNICAL-NOTES.md", "docs/BUILD-CHARTER.md"):
        texts[where] = (ROOT / where).read_text(encoding="utf-8")
    hits = [where for where, text in texts.items() if OLD_NAME.search(text)]
    assert not hits, hits
    assert n.AD_DOMAIN_FQDN in texts["model dump"] and n.ISSUING_CA1_NAME in texts["site page (scripts/build_site.py)"]


# --- V4-CHR-01: the user character --------------------------------------------------------------------------------------------


def _manifest() -> dict[str, object]:
    data: dict[str, object] = json.loads((ROOT / "assets" / "character.manifest.json").read_text(encoding="utf-8"))
    return data


def test_V4_CHR_01_character_asset_is_local_small_and_matches_its_manifest() -> None:  # noqa: N802
    blend = ROOT / ch.ASSET_PATH
    assert blend.is_file() and blend.stat().st_size <= ch.ASSET_MAX_BYTES
    manifest = _manifest()
    assert manifest["sha256"] == hashlib.sha256(blend.read_bytes()).hexdigest()
    assert manifest["bytes"] == blend.stat().st_size


def test_V4_CHR_01_every_character_part_is_cc0_and_recorded_in_licenses_and_readme() -> None:  # noqa: N802
    manifest = _manifest()
    parts = manifest["parts"]
    assert isinstance(parts, list)
    recorded = {p["source"] for p in parts}
    for part in ch.PARTS:
        if part.source is not None:
            assert part.source in recorded, part.name
    assert any("base.obj" in s for s in recorded) and any("weights.default.json" in s for s in recorded)
    for p in parts:
        assert p["licence"] == "CC0-1.0" and "CC0" in p["evidence"], p
    assert manifest["asset_pack"]["licence"] == "CC0-1.0"  # type: ignore[index]
    legal = (ROOT / str(manifest["licence_text"])).read_text(encoding="utf-8")
    assert "CC0 1.0 Universal" in legal
    readme, summary = (ROOT / "README.md").read_text(encoding="utf-8"), (ROOT / "LICENSE").read_text(encoding="utf-8")
    sources = ("base.obj", "weights.default.json", "low-poly", "eyebrow001", "short02", "male_casualsuit01", "shoes02")
    for name in (*sources, "CC0-1.0.txt", "character.manifest.json"):
        assert name in readme, name
    assert "CC0" in summary and "assets/character.blend" in summary


def test_V4_CHR_01_the_build_never_downloads() -> None:  # noqa: N802
    for path in ("blender/character.py", "blender/build_scene.py", "cff/stage/character.py"):
        source = (ROOT / path).read_text(encoding="utf-8")
        assert "urllib" not in source and "://" not in source and "requests" not in source, path


def test_V4_CHR_01_motion_is_deterministic_eased_and_inside_the_film() -> None:  # noqa: N802
    assert ch.typing_strokes() == ch.typing_strokes()
    end = timing.frame_end()
    for bone, keys in ch.finger_keys().items():
        frames = [f for f, _ in keys]
        assert frames == sorted(set(frames)) and frames[0] == timing.FRAME_START and frames[-1] <= end, bone
        assert max(a for _, a in keys) == motion.TYPING_STROKE_ANGLE_DEG
    gaze = ch.gaze_keys()
    assert [k.frame for k in gaze] == sorted({k.frame for k in gaze}) and gaze[-1].frame <= end
    assert {k.target for k in gaze} == set(ch.GAZE_TARGETS) and all(k.ease in motion.PRESETS for k in gaze)
    assert motion.CHARACTER_EASE in motion.PRESETS
    wake = timing.seconds_to_frame(next(e for e in model.MODEL.events if e.id == "E-01.1a").start_s)
    turns = [k.frame for k in gaze[1:]]
    assert wake in turns and all(opened in turns for opened, _ in ch.session_windows())
    assert len(ch.session_windows()) == 2


@pytest.mark.covers("C-06")
def test_V4_CHR_01_breathing_stays_within_two_percent_of_the_figure() -> None:  # noqa: N802
    figure = BY_ID[model.USER].size[2]
    assert ch.head_breath_displacement_m() <= 0.02 * figure
    assert {a for _, a in ch.breath_keys()} == {0.0, motion.BREATH_ANGLE_DEG}


def test_V4_CHR_01_the_keyboard_is_within_a_seated_reach() -> None:  # noqa: N802
    """At the desk centre the keyboard was 1.6 m from the user; a seated adult reaches about 0.45 m past the desk edge."""
    hip_world_x = lo.USER[0] - ch.HIP_JOINT[0]  # the user faces -X, so local +X is world -X
    home_row_x = lo.LAPTOP[0] + ch.KEYBOARD_HOME[0]
    assert 0.4 <= hip_world_x - home_row_x <= 0.65
    assert BY_ID["SCREEN-IDLE"].home[0] == lo.LAPTOP[0] + lo.LAPTOP_LID_X_OFFSET
