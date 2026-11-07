"""The written spec docs agree with the story model (REFERENCE-SPEC, STORYBOARD, PKI-TECHNICAL-NOTES)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from cff.config import names as n
from cff.story import captions as cap
from cff.story import spec_ids, timing
from cff.story.model import MODEL

DOCS = Path(__file__).resolve().parents[1] / "docs"
LENS_MIN_MM, LENS_MAX_MM = 24, 50


def _read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def _sections(text: str, pattern: str) -> dict[str, str]:
    """Split text at headings matching pattern (group 1 = ID); value = heading line + body."""
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1)] = text[m.start() : end]
    return out


# ----------------------------------------------------------------- STORYBOARD


STORY_HEADING = re.compile(r"^### (B-\d{2}\.\d) — (.+) \(([\d.]+)–([\d.]+) s, frames (\d+)–(\d+)\)$", re.MULTILINE)


@pytest.mark.covers("B-*")
def test_storyboard_headings_match_model_timing() -> None:
    found = {m.group(1): m for m in STORY_HEADING.finditer(_read("STORYBOARD.md"))}
    assert list(found) == [b.id for b in MODEL.beats]
    for beat in MODEL.beats:
        m = found[beat.id]
        first, last = timing.frame_range(beat.start_s, beat.end_s)
        assert m.group(2) == beat.title, beat.id
        assert float(m.group(3)) == beat.start_s and float(m.group(4)) == beat.end_s, beat.id
        assert (int(m.group(5)), int(m.group(6))) == (first, last), beat.id


@pytest.mark.covers("B-*", "C-03", "C-09")
def test_storyboard_beats_have_lens_move_focal_and_caption() -> None:
    sections = _sections(_read("STORYBOARD.md"), r"^### (B-\d{2}\.\d) ")
    for beat in MODEL.beats:
        body = sections[beat.id]
        for field in ("**Shot:**", "**Lens:**", "**Camera move:**", "**Focal subject:**", "**Caption:**"):
            assert field in body, (beat.id, field)
        lens_line = next(line for line in body.splitlines() if line.startswith("- **Lens:**"))
        lenses = [int(v) for v in re.findall(r"(\d+) mm", lens_line)]
        assert lenses and all(LENS_MIN_MM <= v <= LENS_MAX_MM for v in lenses), (beat.id, lenses)
        focal_line = next(line for line in body.splitlines() if line.startswith("- **Focal subject:**"))
        assert f"`{beat.focal}`" in focal_line, beat.id


@pytest.mark.covers("L-04", "L-08")
def test_storyboard_captions_match_caption_model() -> None:
    sections = _sections(_read("STORYBOARD.md"), r"^### (B-\d{2}\.\d) ")
    for c in cap.CAPTIONS:
        body = sections[c.anchor_beat]
        caption_line = next(line for line in body.splitlines() if line.startswith("- **Caption:**"))
        assert f"*{c.text}*" in caption_line and f"`{c.id}`" in caption_line, c.id


# ----------------------------------------------------------------- REFERENCE-SPEC


def test_spec_names_table_matches_names_module() -> None:
    spec = _read("REFERENCE-SPEC.md")
    for nv in n.names_in_use():
        if nv.variable in ("GITHUB_OWNER", "REPO_NAME"):
            continue
        row = f"| `{nv.variable}` | `{nv.value}` | {'yes' if nv.is_fallback else 'no'} |"
        assert row in spec, row
    for variable, value in n.derived_names().items():
        assert f"`{variable}` = `{value}`" in spec, variable


@pytest.mark.covers("L-04", "L-08")
def test_spec_beat_captions_match_caption_model() -> None:
    sections = _sections(_read("REFERENCE-SPEC.md"), r"^#### (B-\d{2}\.\d) ")
    assert list(sections) == [b.id for b in MODEL.beats]
    for c in cap.CAPTIONS:
        assert f"*{c.text}*" in sections[c.anchor_beat], c.id
    all_spec_captions = re.findall(r"(?:Caption|Title card): \*(.+?)\*", "".join(sections.values()))
    assert sorted(all_spec_captions) == sorted(c.text for c in cap.CAPTIONS)


@pytest.mark.covers("L-04", "L-05", "L-07", "C-02")
def test_spec_thresholds_match_code_constants() -> None:
    spec = _read("REFERENCE-SPEC.md")
    assert "max(2.5 s, 0.35 s × words)" in spec
    assert timing.CAPTION_MIN_HOLD_S == 2.5 and timing.CAPTION_SECONDS_PER_WORD == 0.35
    assert f"≥ {timing.CAPTION_MIN_GAP_S:g} s fully clear" in spec
    assert "ΔE00 ≥ 15" in spec and "x ∈ [96, 1824] and y ∈ [54, 1026]" in spec
    assert "start of B-05.2" in spec and "start of B-05.3" in spec
    assert timing.DECLARED_CUT_BEATS == ("B-05.2", "B-05.3")


# ----------------------------------------------------------------- PKI-TECHNICAL-NOTES


@pytest.mark.covers("B-*")
def test_notes_explain_every_beat() -> None:
    sections = _sections(_read("PKI-TECHNICAL-NOTES.md"), r"^### (B-\d{2}\.\d)$")
    assert list(sections) == [b.id for b in MODEL.beats]
    for beat_id, body in sections.items():
        assert "**On screen:**" in body and "**Meaning:**" in body, beat_id


def test_notes_fact_index_matches_model() -> None:
    text = _read("PKI-TECHNICAL-NOTES.md")
    index = text.split("## Fact index", 1)[1]
    depicted: dict[str, list[str]] = {}
    for beat in MODEL.beats:
        for fact in beat.facts:
            depicted.setdefault(fact, []).append(beat.id)
    for fact in spec_ids.FACTS:
        line = next((ln for ln in index.splitlines() if ln.startswith(f"- {fact}:")), None)
        assert line is not None, fact
        listed = re.findall(r"B-\d{2}\.\d", line)
        assert listed == depicted.get(fact, []), fact
    for ar in spec_ids.ARCHITECTURE:
        m = re.search(rf"{ar}: ((?:B-\d{{2}}\.\d(?:, )?)+)", index)
        assert m is not None, ar
        assert re.findall(r"B-\d{2}\.\d", m.group(1)) == depicted.get(ar, []), ar


@pytest.mark.covers("F-16")
def test_kerberos_scope_is_documented_not_depicted() -> None:
    text = _read("PKI-TECHNICAL-NOTES.md")
    section = text.split("## Kerberos scope (F-16)", 1)[1].split("\n## ", 1)[0]
    assert "Kerberos" in section and "NLA" in section and "certificate-based server authentication" in section
    assert all("F-16" not in b.facts for b in MODEL.beats)
    for c in cap.CAPTIONS:
        assert "Kerberos" not in c.text
    assert all("Kerberos" not in label.text for label in MODEL.labels)


@pytest.mark.covers("F-17", "L-08")
def test_notes_explain_every_shortened_on_screen_text() -> None:
    text = _read("PKI-TECHNICAL-NOTES.md")
    table = text.split("## Shortened on-screen wording", 1)[1].split("\n## ", 1)[0]
    for c in cap.CAPTIONS:
        if c.kind == cap.CaptionKind.CAPTION:
            assert f"*{c.text}*" in table, c.id


def test_lab_suffix_note_recorded() -> None:
    text = _read("PKI-TECHNICAL-NOTES.md")
    section = text.split("## Lab names and the .lab suffix", 1)[1].split("\n## ", 1)[0]
    assert "IANA" in section and "not delegated" in section
    assert ".internal" in section and "2024.07.29.06" in section
    assert "collision" in section.lower()
