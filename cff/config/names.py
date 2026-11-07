"""Project names (Charter Section 1). This is the ONLY module that defines names.

Every scene, caption, label and document reads names from here. Values shaped like
``<<REPLACE: description | fallback: value>>`` are owner placeholders: while unfilled,
the fallback is used and the placeholder text itself is never rendered.

Related links (Charter Section 1, ``RELATED_LINKS``) are deliberately NOT stored here:
``cff`` must contain no network URLs (Charter 12). They live in README/site config and
are verified with ``gh``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PLACEHOLDER_PATTERN = re.compile(
    r"^<<REPLACE:\s*(?P<description>[^|]*?)\s*\|\s*fallback:\s*(?P<fallback>[^>]*?)\s*>>$"
)
PLACEHOLDER_MARKERS: tuple[str, ...] = ("<<", ">>", "REPLACE:")


@dataclass(frozen=True)
class NameValue:
    """One resolved project variable."""

    variable: str
    raw: str
    value: str
    is_fallback: bool
    description: str


def resolve(variable: str, raw: str) -> NameValue:
    """Resolve a raw value: a filled value is used as-is, a placeholder yields its fallback."""
    match = PLACEHOLDER_PATTERN.match(raw)
    if match is None:
        if any(marker in raw for marker in PLACEHOLDER_MARKERS):
            raise ValueError(f"{variable}: malformed placeholder {raw!r}")
        return NameValue(variable, raw, raw, is_fallback=False, description="")
    fallback = match.group("fallback")
    if not fallback:
        raise ValueError(f"{variable}: placeholder has an empty fallback")
    return NameValue(variable, raw, fallback, is_fallback=True, description=match.group("description"))


# Raw values exactly as in Charter Section 1. The owner edits only this table.
RAW: dict[str, str] = {
    "AD_DOMAIN_FQDN": "1SN0S.LAB",
    "AD_NETBIOS": "1SN0S",
    "DNS_SUFFIX": "1sn0s.lab",
    "DC_HOSTNAME": "<<REPLACE: domain controller hostname | fallback: DC01>>",
    "CLIENT_HOSTNAME": "<<REPLACE: user laptop hostname | fallback: CLIENT01>>",
    "RDP_SERVER_HOSTNAME": "<<REPLACE: RDP server hostname | fallback: RDP01>>",
    "WEB_SERVER_HOSTNAME": "<<REPLACE: web server hostname | fallback: WEB01>>",
    "WEB_SITE_DNS_NAME": (
        "<<REPLACE: website DNS name in the TLS certificate SAN | fallback: portal.1sn0s.lab>>"
    ),
    "ROOT_CA_NAME": "<<REPLACE: Root CA common name | fallback: 1SN0S Root CA>>",
    "ISSUING_CA1_NAME": "<<REPLACE: Issuing CA 1 common name | fallback: 1SN0S Issuing CA 1>>",
    "ISSUING_CA2_NAME": "<<REPLACE: Issuing CA 2 common name | fallback: 1SN0S Issuing CA 2>>",
    "PKI_HTTP_HOST": "<<REPLACE: host serving AIA/CDP over HTTP | fallback: pki.1sn0s.lab>>",
    "RDP_TEMPLATE": "RDPAuth",
    "WEB_TEMPLATE": "WebServer-TLS",
    "GITHUB_OWNER": "SimSI2027",
    "REPO_NAME": "Certificate-Flow-Film",
}

RESOLVED: dict[str, NameValue] = {name: resolve(name, raw) for name, raw in RAW.items()}


def _value(variable: str) -> str:
    return RESOLVED[variable].value


AD_DOMAIN_FQDN = _value("AD_DOMAIN_FQDN")
AD_NETBIOS = _value("AD_NETBIOS")
DNS_SUFFIX = _value("DNS_SUFFIX")
DC_HOSTNAME = _value("DC_HOSTNAME")
CLIENT_HOSTNAME = _value("CLIENT_HOSTNAME")
RDP_SERVER_HOSTNAME = _value("RDP_SERVER_HOSTNAME")
WEB_SERVER_HOSTNAME = _value("WEB_SERVER_HOSTNAME")
WEB_SITE_DNS_NAME = _value("WEB_SITE_DNS_NAME").lower()
ROOT_CA_NAME = _value("ROOT_CA_NAME")
ISSUING_CA1_NAME = _value("ISSUING_CA1_NAME")
ISSUING_CA2_NAME = _value("ISSUING_CA2_NAME")
PKI_HTTP_HOST = _value("PKI_HTTP_HOST").lower()
RDP_TEMPLATE = _value("RDP_TEMPLATE")
WEB_TEMPLATE = _value("WEB_TEMPLATE")
GITHUB_OWNER = _value("GITHUB_OWNER")
REPO_NAME = _value("REPO_NAME")


def host_fqdn(hostname: str) -> str:
    """Derived FQDN: lower-case(hostname) + '.' + DNS_SUFFIX (Charter Section 1)."""
    return f"{hostname.lower()}.{DNS_SUFFIX.lower()}"


DC_FQDN = host_fqdn(DC_HOSTNAME)
CLIENT_FQDN = host_fqdn(CLIENT_HOSTNAME)
RDP_SERVER_FQDN = host_fqdn(RDP_SERVER_HOSTNAME)
WEB_SERVER_FQDN = host_fqdn(WEB_SERVER_HOSTNAME)

# Role labels used in captions and docs. They name roles, not certificate subjects.
ROOT_CA_ROLE = "Root CA"
ISSUING_CA1_ROLE = "Issuing CA 1"
ISSUING_CA2_ROLE = "Issuing CA 2"

# Display names for the two Extended Key Usages in the story (OIDs live in the model).
EKU_REMOTE_DESKTOP_AUTH_NAME = "Remote Desktop Authentication"
EKU_SERVER_AUTH_NAME = "Server Authentication"

FILM_TITLE = "Certificate Flow"
FILM_SUBTITLE = "From request to trust"


def file_slug(common_name: str) -> str:
    """File-name form of a CA common name, used for illustrative AIA/CDP file names."""
    return re.sub(r"[^A-Za-z0-9]+", "-", common_name).strip("-")


def names_in_use() -> list[NameValue]:
    """Every project variable with its resolved value (for README and PROJECT-STATE)."""
    return list(RESOLVED.values())


def fallbacks_in_use() -> list[NameValue]:
    return [name for name in RESOLVED.values() if name.is_fallback]


def derived_names() -> dict[str, str]:
    return {
        "DC_FQDN": DC_FQDN,
        "CLIENT_FQDN": CLIENT_FQDN,
        "RDP_SERVER_FQDN": RDP_SERVER_FQDN,
        "WEB_SERVER_FQDN": WEB_SERVER_FQDN,
    }
