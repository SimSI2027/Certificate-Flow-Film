"""Frozen-spec change control (Charter 2.2): REFERENCE-SPEC.md must match the latest hash in the ledger.

Any change to the spec needs a Chief of Staff amendment in docs/GAN-LEDGER.md that records a new
"Frozen REFERENCE-SPEC SHA-256" line; until then this test fails.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
FROZEN_LINE = re.compile(r"Frozen REFERENCE-SPEC SHA-256:\*\*\s*`([0-9a-f]{64})`")


def test_reference_spec_matches_latest_frozen_hash() -> None:
    ledger = (DOCS / "GAN-LEDGER.md").read_text(encoding="utf-8")
    recorded = FROZEN_LINE.findall(ledger)
    assert recorded, "no frozen spec hash recorded in GAN-LEDGER.md"
    actual = hashlib.sha256((DOCS / "REFERENCE-SPEC.md").read_bytes()).hexdigest()
    assert actual == recorded[-1], "REFERENCE-SPEC.md changed without a recorded amendment"
