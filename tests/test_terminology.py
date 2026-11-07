"""Terminology (F-17, L-08): on-screen text and docs follow the glossary."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from cff.story import captions as cap
from cff.story.model import MODEL

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BANNED = re.compile(r"\b(sub[- ]?certificates?|child certificates?|leaf CA|root of trust)\b", re.IGNORECASE)
# A banned term may appear in docs only where the line says not to use it.
BANNED_CONTEXT = re.compile(r"\b(never|not use|do not|banned|instead of|avoid)\b", re.IGNORECASE)
SPEC_DOCS = ("REFERENCE-SPEC.md", "GLOSSARY.md", "PKI-TECHNICAL-NOTES.md", "STORYBOARD.md", "GAN-FRAMEWORK.md")

REQUIRED_GLOSSARY_TERMS = (
    "Active Directory Certificate Services (ADCS)",
    "Root CA",
    "Trust anchor",
    "Subordinate (intermediate) issuing CA",
    "Standalone CA",
    "Enterprise CA",
    "End-entity certificate",
    "Self-signed certificate",
    "Certificate template",
    "Template publication",
    "Enrollment Services object",
    "Enroll permission",
    "Request Certificates permission",
    "Certificate request (PKCS #10, CMC)",
    "Proof of possession",
    "Key pair",
    "Private key",
    "Public key",
    "Key container",
    "Subject",
    "Subject Alternative Name (SAN)",
    "Extended Key Usage (EKU)",
    "Basic Constraints",
    "Critical extension",
    "Validity period",
    "Authority Information Access (AIA)",
    "CRL Distribution Point (CDP)",
    "Certificate Revocation List (CRL)",
    "Online Certificate Status Protocol (OCSP)",
    "Chain building",
    "Path validation",
    "Trusted Root Certification Authorities store",
    "Personal store (LocalMachine\\My)",
    "TLS handshake",
    "Remote Desktop Protocol (RDP)",
    "Network Level Authentication (NLA)",
    "Kerberos",
    "Group Policy",
    "Offline root ceremony",
    "Revocation",
    "Issuance",
)


def _on_screen_texts() -> list[tuple[str, str]]:
    return [(c.id, c.text) for c in cap.CAPTIONS] + [(lbl.id, lbl.text) for lbl in MODEL.labels]


@pytest.mark.covers("F-17", "L-08")
def test_on_screen_text_uses_no_banned_terms() -> None:
    for item_id, text in _on_screen_texts():
        assert not BANNED.search(text), item_id


@pytest.mark.covers("F-17", "L-08")
def test_trust_anchor_refers_only_to_the_root() -> None:
    for item_id, text in _on_screen_texts():
        if "trust anchor" in text.lower():
            assert "root" in text.lower(), item_id


@pytest.mark.covers("F-17", "L-08")
def test_docs_use_no_banned_terms_except_to_forbid_them() -> None:
    for name in SPEC_DOCS:
        for number, line in enumerate((DOCS / name).read_text(encoding="utf-8").splitlines(), start=1):
            if BANNED.search(line):
                assert BANNED_CONTEXT.search(line), f"{name}:{number}: {line.strip()}"


@pytest.mark.covers("L-08")
def test_glossary_defines_required_terms() -> None:
    lines = (DOCS / "GLOSSARY.md").read_text(encoding="utf-8").splitlines()
    headings = {line[4:].strip() for line in lines if line.startswith("### ")}
    missing = [t for t in REQUIRED_GLOSSARY_TERMS if t not in headings]
    assert not missing, missing
