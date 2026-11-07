"""Names (Charter Section 1 and 12): every placeholder resolves; no placeholder text anywhere."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from cff.config import names as n
from cff.story import captions as cap
from cff.story.model import MODEL

ROOT = Path(__file__).resolve().parents[1]
DNS_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
NETBIOS_MAX = 15
# Docs that legitimately quote the raw placeholder syntax (the charter and the session prompts).
PLACEHOLDER_DOC_ALLOWLIST = {"BUILD-CHARTER.md", "SESSION-PROMPTS.md"}


def _has_placeholder(text: str) -> bool:
    return any(marker in text for marker in n.PLACEHOLDER_MARKERS)


def _is_dns_name(name: str) -> bool:
    return len(name) <= 253 and all(DNS_LABEL.match(label) for label in name.split("."))


def test_resolve_placeholder_and_filled_values() -> None:
    filled = n.resolve("X", "RDP99")
    assert filled.value == "RDP99" and not filled.is_fallback
    placeholder = n.resolve("X", "<<REPLACE: something | fallback: ABC>>")
    assert placeholder.value == "ABC" and placeholder.is_fallback and placeholder.description == "something"
    with pytest.raises(ValueError):
        n.resolve("X", "<<REPLACE: missing fallback>>")
    with pytest.raises(ValueError):
        n.resolve("X", "<<REPLACE: empty | fallback: >>")


def test_every_variable_resolves_without_placeholder_text() -> None:
    assert set(n.RAW) == set(n.RESOLVED)
    for nv in n.names_in_use():
        assert nv.value and not _has_placeholder(nv.value), nv.variable
    for value in n.derived_names().values():
        assert not _has_placeholder(value)


def test_expected_fallbacks_in_use() -> None:
    fallbacks = {nv.variable: nv.value for nv in n.fallbacks_in_use()}
    assert fallbacks == {
        "DC_HOSTNAME": "DC01",
        "CLIENT_HOSTNAME": "CLIENT01",
        "RDP_SERVER_HOSTNAME": "RDP01",
        "WEB_SERVER_HOSTNAME": "WEB01",
        "WEB_SITE_DNS_NAME": "portal.1sn0s.lab",
        "ROOT_CA_NAME": "1SN0S Root CA",
        "ISSUING_CA1_NAME": "1SN0S Issuing CA 1",
        "ISSUING_CA2_NAME": "1SN0S Issuing CA 2",
        "PKI_HTTP_HOST": "pki.1sn0s.lab",
    }


def test_fixed_names() -> None:
    assert n.AD_DOMAIN_FQDN == "1SN0S.LAB"
    assert n.AD_NETBIOS == "1SN0S"
    assert n.DNS_SUFFIX == "1sn0s.lab"
    assert n.RDP_TEMPLATE == "RDPAuth"
    assert n.WEB_TEMPLATE == "WebServer-TLS"
    assert n.AD_DOMAIN_FQDN.lower() == n.DNS_SUFFIX


def test_derived_fqdns_are_lower_case_and_computed() -> None:
    assert n.RDP_SERVER_FQDN == f"{n.RDP_SERVER_HOSTNAME.lower()}.{n.DNS_SUFFIX}" == "rdp01.1sn0s.lab"
    assert n.WEB_SERVER_FQDN == "web01.1sn0s.lab"
    assert n.DC_FQDN == "dc01.1sn0s.lab" and n.CLIENT_FQDN == "client01.1sn0s.lab"
    for name in (*n.derived_names().values(), n.WEB_SITE_DNS_NAME, n.PKI_HTTP_HOST):
        assert name == name.lower() and _is_dns_name(name), name
        assert name.endswith("." + n.DNS_SUFFIX)


def test_hostnames_fit_netbios_limits() -> None:
    for host in (n.DC_HOSTNAME, n.CLIENT_HOSTNAME, n.RDP_SERVER_HOSTNAME, n.WEB_SERVER_HOSTNAME, n.AD_NETBIOS):
        assert 1 <= len(host) <= NETBIOS_MAX and re.fullmatch(r"[A-Za-z0-9-]+", host), host


def test_file_slug() -> None:
    assert n.file_slug("1SN0S Issuing CA 1") == "1SN0S-Issuing-CA-1"


@pytest.mark.covers("L-06", "L-08")
def test_no_placeholder_in_captions_labels_or_model() -> None:
    for c in cap.CAPTIONS:
        assert not _has_placeholder(c.text), c.id
    for label in MODEL.labels:
        assert label.text and not _has_placeholder(label.text), label.id
    for actor in MODEL.actors:
        assert not _has_placeholder(actor.label), actor.id
    for cert in MODEL.certificates:
        assert not _has_placeholder(cert.subject_cn) and not any(_has_placeholder(s) for s in cert.san_dns)


def test_no_placeholder_text_in_document_outputs() -> None:
    docs = [p for p in (ROOT / "docs").glob("*.md") if p.name not in PLACEHOLDER_DOC_ALLOWLIST]
    docs += [ROOT / "README.md"]
    assert docs
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "<<REPLACE" not in text, path.name


def test_cff_names_module_holds_no_urls() -> None:
    source = (ROOT / "cff" / "config" / "names.py").read_text(encoding="utf-8")
    assert not re.search(r"[a-z][a-z0-9+.-]*://", source)
