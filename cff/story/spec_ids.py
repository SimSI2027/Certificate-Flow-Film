"""Registry of frozen-spec IDs with short titles (docs/REFERENCE-SPEC.md holds the full text).

Used by the story model (beats cite facts) and by TRACEABILITY generation. A test checks
that REFERENCE-SPEC.md defines exactly these IDs.
"""

from __future__ import annotations

ARCHITECTURE: dict[str, str] = {
    "AR-01": "Root CA is offline, standalone, non-domain-joined, self-signed: the trust anchor",
    "AR-02": "Root CA signs only issuing CA certificates (offline ceremony) and its own CRL",
    "AR-03": "Issuing CAs are enterprise subordinate CAs, signed by the root, CA=true, not trust anchors",
    "AR-04": "RDPAuth is published only on Issuing CA 1; WebServer-TLS only on Issuing CA 2",
    "AR-05": "AD authenticates requesters, stores templates/permissions/Enrollment Services, distributes the root",
    "AR-06": "AIA and CDP are HTTP locations on the PKI HTTP host, embedded in issued certificates",
    "AR-07": "OCSP appears only as 'if an Online Responder is deployed'",
}

FACTS: dict[str, str] = {
    "F-01": "The user initiates RDP; the RDP server owns and presents the RDP certificate",
    "F-02": "Out of the box RDP uses a self-signed certificate the client cannot verify",
    "F-03": "Key pairs are generated locally; private keys (including CA keys) never leave their owner",
    "F-04": "The request contains the public key, is signed with the private key, never contains it",
    "F-05": "RDP enrollment is policy-triggered; eligible CAs are discovered from AD before sending",
    "F-06": "The CA authenticates, checks publication, Enroll permission and template policy before signing",
    "F-07": "RDPAuth builds subject/SAN from AD; WebServer-TLS takes the subject from the request",
    "F-08": "RDPAuth uses Remote Desktop Authentication EKU; WebServer-TLS uses Server Authentication",
    "F-09": "The issued certificate goes to LocalMachine\\My beside the existing private key",
    "F-10": "In TLS the server sends its chain and proves possession of the private key by signing",
    "F-11": "The client builds the chain to a root already trusted; AIA may fetch, never creates trust",
    "F-12": "Validation is a set of distinct checks; the name match is a separate identity check",
    "F-13": "Revocation is checked for each non-root link via CDP/CRL; the root is not checked",
    "F-14": "Different templates can be issued by different eligible issuing CAs",
    "F-15": "Both issuing paths terminate at the same Root CA",
    "F-16": "Kerberos server authentication is out of scope on screen; the film shows certificate-based auth",
    "F-17": "Terminology: end-entity certificate, subordinate/intermediate issuing CA, trust anchor = root",
}

CINEMATIC: dict[str, str] = {
    "C-01": "No arrows or connector-diagram grammar",
    "C-02": "One continuous camera; no hard cuts except the S5 flashback",
    "C-03": "One clear focal subject per shot",
    "C-04": "Foreground, midground and background layers with parallax",
    "C-05": "Motivated key/rim lighting",
    "C-06": "Eased motion; no pops or jitter; exits slightly faster than entrances",
    "C-07": "Object continuity across scenes",
    "C-08": "Restraint in glow, haze and particles",
    "C-09": "Never template-like or slide-like",
    "C-10": "Consistent colour language",
    "C-11": "Shape vocabulary distinct in greyscale",
}

LEGIBILITY: dict[str, str] = {
    "L-01": "Caption cap height >= 30 px; must-read in-world labels >= 18 px at 1080p",
    "L-02": "Contrast >= 4.5:1 against the sampled local background",
    "L-03": "All text inside the 90% title-safe area",
    "L-04": "Each caption on screen >= max(2.5 s, 0.35 s per word)",
    "L-05": "One caption at a time, never covering the focal action",
    "L-06": "In-world names readable at the moment they matter",
    "L-07": "Role colours distinguishable (CIEDE2000 >= 15), including under CVD simulation",
    "L-08": "Terminology matches the glossary",
}


def all_ids() -> list[str]:
    return [*ARCHITECTURE, *FACTS, *CINEMATIC, *LEGIBILITY]
