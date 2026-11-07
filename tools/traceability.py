"""Generate docs/TRACEABILITY.md from the story model and the test suite (Charter 2.7).

Coverage of a spec ID comes from three sources:
- the story model (beats, their scene/frames, and the facts each beat depicts)
- pytest tests marked ``@pytest.mark.covers("ID", ...)`` (found by static AST scan; ``B-*`` = every beat)
- planned hard checks (Charter Section 12) that later stages implement, listed below with their stage
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from cff.story import spec_ids, timing
from cff.story.model import MODEL

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
OUTPUT = ROOT / "docs" / "TRACEABILITY.md"
WILDCARD_BEATS = "B-*"

DISCRIMINATOR_BY_PREFIX = {
    "AR": "pki-discriminator",
    "F": "pki-discriminator",
    "C": "cinema-discriminator",
    "L": "legibility-discriminator",
    "B": "pki-, cinema- and legibility-discriminator",
}

# Facts that are documentation-only by charter (not depicted on screen).
DOCS_ONLY_FACTS = {"F-16": "Kerberos scope: docs only (PKI-TECHNICAL-NOTES, 'F-16')"}

# Planned hard checks (Charter Section 12 and the REFERENCE-SPEC measurement column).
# Each entry: (check, where it runs, stage that implements it). None exist yet unless a pytest is listed.
IN_BLENDER, IMAGE, STAGE1, STAGE2 = "in-Blender", "image", "Stage 1", "Stage 2"
PLANNED: dict[str, list[tuple[str, str, str]]] = {
    "AR-01": [("Root isolation: no capsule touches the root vault; no channel reaches the plinth", IN_BLENDER, STAGE1)],
    "AR-02": [("Root isolation: only trust-link geometry touches the root plinth", IN_BLENDER, STAGE1)],
    "F-03": [("Key containment: private-key bounds stay inside the owner on every frame", IN_BLENDER, STAGE1)],
    "F-05": [("Route integrity: capsules touch only their source and destination CA", IN_BLENDER, STAGE1)],
    "C-01": [("Scene audit: no arrow/connector objects; line-like objects are links or channels", IN_BLENDER, STAGE1)],
    "C-02": [("Camera continuity: one camera; per-frame motion under thresholds except cuts", IN_BLENDER, STAGE1)],
    "C-03": [("Focal framing and focus distance per beat", IN_BLENDER, STAGE1)],
    "C-04": [("Depth layers in front of and behind the focal subject per beat", IN_BLENDER, STAGE1)],
    "C-05": [("Light audit: key and rim light per scene; ambient ratio", f"{IN_BLENDER} + {IMAGE}", STAGE2)],
    "C-06": [("F-curve audit: Bezier presets, LINEAR whitelist, no NaN, ordered keys, no pops", IN_BLENDER, STAGE1)],
    "C-07": [("Object identity and boundary continuity across scenes", IN_BLENDER, STAGE1)],
    "C-08": [("Clipped-highlight fraction, haze lift, particle audit", f"{IMAGE} + {IN_BLENDER}", STAGE2)],
    "C-09": [("Camera audit: perspective only, 24-50 mm, no frontal grid-of-cards framing", IN_BLENDER, STAGE1)],
    "C-10": [("Material audit: every object's colour is its role token", IN_BLENDER, STAGE1)],
    "C-11": [("Silhouette IoU test of the shape vocabulary", IMAGE, STAGE1)],
    "L-01": [("Caption and must-read label cap height", IN_BLENDER, STAGE1)],
    "L-02": [("Sampled caption and label contrast", IMAGE, STAGE1)],
    "L-03": [("Projected text bounds inside 90% title-safe", IN_BLENDER, STAGE1)],
    "L-05": [("Caption bounds never overlap the focal subject's projected bounds", IN_BLENDER, STAGE1)],
    "L-06": [("Must-read labels: size, facing, occlusion and focus at their beats", IN_BLENDER, STAGE1)],
    "L-07": [("Palette CIEDE2000 incl. Machado 2009 deuteranopia/protanopia", IMAGE, STAGE1)],
}


def _is_covers(deco: ast.expr) -> bool:
    return isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute) and deco.func.attr == "covers"


@dataclass
class Row:
    id: str
    title: str
    beats: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    planned: list[str] = field(default_factory=list)
    docs_only: str = ""


def collect_covers(tests_dir: Path = TESTS_DIR) -> dict[str, list[str]]:
    """Map spec ID -> sorted list of 'tests/file.py::test_name' from covers markers."""
    beat_ids = [b.id for b in MODEL.beats]
    coverage: dict[str, set[str]] = {}
    for path in sorted(tests_dir.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for deco in node.decorator_list:
                if not isinstance(deco, ast.Call) or not _is_covers(deco):
                    continue
                for arg in deco.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        ids = beat_ids if arg.value == WILDCARD_BEATS else [arg.value]
                        for spec_id in ids:
                            coverage.setdefault(spec_id, set()).add(f"tests/{path.name}::{node.name}")
    return {k: sorted(v) for k, v in coverage.items()}


def build_rows(coverage: dict[str, list[str]] | None = None) -> dict[str, Row]:
    coverage = collect_covers() if coverage is None else coverage
    titles = {
        **spec_ids.ARCHITECTURE,
        **spec_ids.FACTS,
        **spec_ids.CINEMATIC,
        **spec_ids.LEGIBILITY,
        **{b.id: b.title for b in MODEL.beats},
    }
    rows = {spec_id: Row(spec_id, title) for spec_id, title in titles.items()}
    for beat in MODEL.beats:
        for fact in beat.facts:
            rows[fact].beats.append(beat.id)
    for spec_id, tests in coverage.items():
        if spec_id in rows:
            rows[spec_id].tests = list(tests)
    for spec_id, checks in PLANNED.items():
        rows[spec_id].planned = [f"{c} ({where}, {stage})" for c, where, stage in checks]
    for spec_id, text in DOCS_ONLY_FACTS.items():
        rows[spec_id].docs_only = text
    return rows


def missing_ids(rows: dict[str, Row]) -> list[str]:
    """IDs without adequate coverage. Empty means every ID is traced."""
    missing: list[str] = []
    expected = [*spec_ids.all_ids(), *(b.id for b in MODEL.beats)]
    for spec_id in expected:
        row = rows.get(spec_id)
        if row is None:
            missing.append(f"{spec_id}: no row")
            continue
        prefix = spec_id.split("-")[0]
        if prefix == "B" and not row.tests:
            missing.append(f"{spec_id}: no test")
        if prefix in ("F", "AR"):
            if not row.beats and not row.docs_only:
                missing.append(f"{spec_id}: not depicted in any beat and not docs-only")
            if not row.tests:
                missing.append(f"{spec_id}: no test")
        if prefix in ("C", "L") and not row.tests and not row.planned:
            missing.append(f"{spec_id}: no test and no planned check")
    return missing


def _cell(items: list[str]) -> str:
    return "<br>".join(f"`{i}`" for i in items) if items else "—"


def render(rows: dict[str, Row] | None = None) -> str:
    rows = build_rows() if rows is None else rows
    lines = [
        "# Traceability",
        "",
        "Generated by `python -m tools traceability` from `cff/story/model.py`, `cff/story/spec_ids.py`,",
        "`cff/story/timing.py` and the `covers` markers in `tests/`. Do not edit by hand;",
        "`tests/test_traceability.py` fails if this file is stale or any ID is uncovered.",
        "",
        "Frames are 1-based at "
        f"{timing.FPS} fps; the film runs frames {timing.FRAME_START}–{timing.frame_end()} "
        f"({timing.total_duration_s():g} s).",
        "\"Planned\" checks are Charter Section 12 hard discriminators that later stages implement;",
        "they are listed so coverage gaps are visible, not claimed as existing.",
        "",
        "## Beats",
        "",
        "| Beat | Scene | Title | Time (s) | Frames | Focal subject | Facts | Events | Tests | Discriminators |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for beat in MODEL.beats:
        first, last = timing.frame_range(beat.start_s, beat.end_s)
        events = len(MODEL.events_in(beat.id))
        row = rows[beat.id]
        lines.append(
            f"| {beat.id} | {beat.scene} | {beat.title} | {beat.start_s:g}–{beat.end_s:g} | {first}–{last} | "
            f"`{beat.focal}` | {', '.join(beat.facts)} | {events} | {len(row.tests)} tests | "
            f"{DISCRIMINATOR_BY_PREFIX['B']} |"
        )
    for heading, group in (
        ("Architecture", spec_ids.ARCHITECTURE),
        ("PKI facts", spec_ids.FACTS),
        ("Cinematic criteria", spec_ids.CINEMATIC),
        ("Legibility criteria", spec_ids.LEGIBILITY),
    ):
        lines += [
            "",
            f"## {heading}",
            "",
            "| ID | Statement | Depicted in beats | Tests (pytest) | Planned hard checks | Discriminator |",
            "|---|---|---|---|---|---|",
        ]
        for spec_id in group:
            row = rows[spec_id]
            depicted = ", ".join(row.beats) if row.beats else (row.docs_only or "—")
            planned = "<br>".join(row.planned) if row.planned else "—"
            prefix = spec_id.split("-")[0]
            lines.append(
                f"| {spec_id} | {row.title} | {depicted} | {_cell(row.tests)} | {planned} | "
                f"{DISCRIMINATOR_BY_PREFIX[prefix]} |"
            )
    lines += ["", "## Beat test detail", ""]
    for beat in MODEL.beats:
        lines.append(f"- **{beat.id}**: {', '.join(f'`{t}`' for t in rows[beat.id].tests)}")
    lines.append("")
    return "\n".join(lines)


def write(path: Path = OUTPUT) -> Path:
    path.write_text(render(), encoding="utf-8", newline="\n")
    return path
