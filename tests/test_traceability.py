"""TRACEABILITY (Charter 2.7, 12): every F/AR/B/C/L ID is covered; the file is current."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from cff.story import spec_ids
from cff.story.model import MODEL
from tools import traceability

ROOT = Path(__file__).resolve().parents[1]
SPEC_ID = re.compile(r"^#{2,4} ((?:AR|F|B|C|L)-\d{2}(?:\.\d)?)\b", re.MULTILINE)


@pytest.mark.covers("B-*")
def test_no_id_is_missing_coverage() -> None:
    assert traceability.missing_ids(traceability.build_rows()) == []


def test_missing_coverage_is_detected() -> None:
    """Mutation check: dropping a beat's tests or a fact's beats must be reported."""
    coverage = traceability.collect_covers()
    coverage.pop("B-04.3")
    rows = traceability.build_rows(coverage)
    rows["F-06"].beats.clear()
    rows.pop("L-07")
    missing = traceability.missing_ids(rows)
    assert any(m.startswith("B-04.3") for m in missing)
    assert any(m.startswith("F-06") for m in missing)
    assert any(m.startswith("L-07") for m in missing)


def test_traceability_file_is_current() -> None:
    current = traceability.OUTPUT.read_text(encoding="utf-8")
    assert current == traceability.render(), "run: python -m tools traceability"


def test_traceability_lists_every_id() -> None:
    text = traceability.OUTPUT.read_text(encoding="utf-8")
    for spec_id in [*spec_ids.all_ids(), *(b.id for b in MODEL.beats)]:
        assert f"| {spec_id} |" in text, spec_id


@pytest.mark.covers("B-*")
def test_reference_spec_defines_exactly_the_model_ids() -> None:
    spec = (ROOT / "docs" / "REFERENCE-SPEC.md").read_text(encoding="utf-8")
    defined = SPEC_ID.findall(spec)
    assert len(defined) == len(set(defined)), "an ID is defined twice"
    expected = [*spec_ids.all_ids(), *(b.id for b in MODEL.beats)]
    assert sorted(defined) == sorted(expected)


def test_every_fact_and_architecture_item_is_depicted_or_docs_only() -> None:
    rows = traceability.build_rows()
    for spec_id in [*spec_ids.FACTS, *spec_ids.ARCHITECTURE]:
        assert rows[spec_id].beats or rows[spec_id].docs_only, spec_id
    assert set(traceability.DOCS_ONLY_FACTS) == {"F-16"}
