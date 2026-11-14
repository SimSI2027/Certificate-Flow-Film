"""Session V4 (owner request): the MALAWI rename and the realistic user character.

V4-REN-01: the lab's earlier name must not appear in any caption, sign, label, model text or site text.
V4-CHR-01: the user character is a local CC0 asset, recorded in LICENSES\\ and README, built from cff timing and theme motion.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

from cff.config import names as n
from cff.stage import labels
from cff.story import captions as cap
from cff.story.export import model_dump
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
