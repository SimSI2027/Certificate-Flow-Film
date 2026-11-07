"""Hard tests learned from accepted GAN findings (Charter 2.4 step 7). Never delete these.

Each test is named after the finding ID it encodes; see docs/GAN-LEDGER.md.
"""

from __future__ import annotations

import pytest

from cff.story.model import (
    MODEL,
    ROOT_CA,
    CertKind,
    Era,
    Event,
    EventType,
    KeyKind,
    RequestKind,
    Transport,
)

M = MODEL
EPS = 1e-9

# Events that belong to a server's own enrollment, which is driven by policy on the server and
# must never happen while one of that server's client connections is pending.
ENROLLMENT_TYPES = {
    EventType.KEYPAIR_GENERATED,
    EventType.PRIVATE_KEY_STORED,
    EventType.REQUEST_ASSEMBLED,
    EventType.PROOF_OF_POSSESSION,
    EventType.CA_DISCOVERY_QUERY,
    EventType.CA_DISCOVERY_RESULT,
    EventType.REQUEST_SUBMITTED,
    EventType.CERT_RETURNED,
    EventType.CERT_INSTALLED,
    EventType.INTERMEDIATE_STORED,
}
LEAF_KINDS = {CertKind.END_ENTITY, CertKind.SELF_SIGNED_END_ENTITY}


def _attempts(channel_id: str) -> list[list[Event]]:
    """Split a channel's events into connection attempts, each starting with a CONNECTION_PULSE."""
    channel = M.channel(channel_id)
    related = [
        e
        for e in M.events
        if e.object == channel_id
        or (e.type == EventType.PRESENT_CERT and e.from_ == channel.server and e.to == channel.client)
    ]
    related.sort(key=lambda e: (e.start_s, e.id))
    attempts: list[list[Event]] = []
    for e in related:
        if e.type == EventType.CONNECTION_PULSE:
            attempts.append([e])
        elif e.type != EventType.USER_INITIATES:
            assert attempts, f"{e.id} happens on {channel_id} before any connection attempt"
            attempts[-1].append(e)
    return attempts


@pytest.mark.covers("F-10", "F-05", "B-02.2", "B-06.1", "B-06.6", "B-09.1")
def test_PKI_S0R1_01_one_certificate_per_connection_attempt() -> None:  # noqa: N802
    """A TLS handshake presents exactly one server certificate; a new certificate needs a new attempt.

    The unverified S2 attempt must end before enrollment, enrollment must not run while a connection
    to that server is pending, and the trusted session must be a new attempt presenting the CA-issued
    certificate.
    """
    for channel in M.channels:
        attempts = _attempts(channel.id)
        assert attempts, channel.id
        for attempt in attempts:
            leaves = [
                e for e in attempt if e.type == EventType.PRESENT_CERT and M.cert(e.object).kind in LEAF_KINDS
            ]
            assert len(leaves) == 1, (channel.id, [e.id for e in attempt])
            end = attempt[-1]
            assert end.type in (EventType.CONNECTION_CLOSED, EventType.SESSION_ESTABLISHED), end.id
            assert leaves[0].end_s <= end.start_s + EPS
            if end.type == EventType.SESSION_ESTABLISHED:
                assert M.cert(leaves[0].object).kind == CertKind.END_ENTITY, "trusted session needs a CA-issued cert"
            if M.cert(leaves[0].object).kind == CertKind.SELF_SIGNED_END_ENTITY:
                assert end.type == EventType.CONNECTION_CLOSED, "the unverified attempt must end"
            window = (attempt[0].start_s, end.end_s)
            for e in M.events:
                if e.type in ENROLLMENT_TYPES and channel.server in (e.from_, e.to):
                    overlaps = e.start_s < window[1] - EPS and e.end_s > window[0] + EPS
                    assert not overlaps, f"{e.id} (enrollment) overlaps pending connection {attempt[0].id}"
    rdp_attempts = _attempts("CH-RDP")
    assert len(rdp_attempts) == 2, "S2 attempt (closed) and S6 attempt (trusted)"


@pytest.mark.covers("AR-02", "F-04", "B-04.4", "B-05.2", "B-08.2")
def test_PKI_S0R1_02_requests_end_at_their_destination_and_the_ca_request_is_labelled() -> None:  # noqa: N802
    """Every request is consumed at its destination before its certificate is signed, and never
    reappears; the subordinate-CA request in the flashback carries its own must-read identity tag."""
    for r in M.requests:
        consumed = [e for e in M.events_of(EventType.REQUEST_CONSUMED) if e.object == r.id]
        assert len(consumed) == 1, r.id
        c = consumed[0]
        assert c.from_ == c.to == r.destination, r.id
        delivery_types = (EventType.REQUEST_SUBMITTED, EventType.OFFLINE_CARRY)
        delivery = [e for e in M.events if e.object == r.id and e.type in delivery_types]
        assert delivery and all(d.end_s <= c.start_s + EPS for d in delivery), r.id
        sign = next(e for e in M.events_of(EventType.CA_SIGNS) if e.object == r.result_cert)
        assert c.end_s <= sign.start_s + EPS, r.id
        later = [e for e in M.events if e.object == r.id and e.start_s >= c.end_s - EPS and e.id != c.id]
        assert not later, (r.id, [e.id for e in later])
        if r.kind == RequestKind.END_ENTITY:
            assert all(e.era == Era.PRESENT for e in M.events if e.object == r.id), r.id
            assert c.end_s <= M.beat("B-05.2").start_s + EPS or r.id == "REQ-WEB"
    sub_ca = next(r for r in M.requests if r.kind == RequestKind.SUBORDINATE_CA)
    tags = [lbl for lbl in M.labels if lbl.attached_to == sub_ca.id]
    assert tags and all("B-05.2" in t.must_read_beats for t in tags)
    assert any("CA request" in t.text for t in tags)


@pytest.mark.covers("AR-01", "AR-02", "B-05.1")
def test_PKI_S0R1_03_root_performs_no_operation_in_the_present() -> None:  # noqa: N802
    for e in M.events:
        if ROOT_CA in (e.from_, e.to) and e.era == Era.PRESENT:
            assert e.uses_key is None, e.id
            assert e.type in (EventType.SELF_SIGNATURE_SHOWN, EventType.ISSUER_LINK), e.id


@pytest.mark.covers("F-03", "F-10", "B-06.1", "B-09.1")
def test_PKI_S0R1_04_handshake_proof_is_not_key_material() -> None:  # noqa: N802
    key_ids = {k.id for k in M.keys}
    for e in M.events_of(EventType.HANDSHAKE_PROOF_SENT):
        assert e.object not in key_ids
        proof = M.handshake(e.object)
        assert M.key(proof.signed_with).kind == KeyKind.PRIVATE
        assert M.key(proof.verified_with).kind == KeyKind.PUBLIC


@pytest.mark.covers("AR-05", "F-11", "B-06.2")
def test_PKI_S0R1_05_trust_store_recall_does_not_travel() -> None:  # noqa: N802
    recalls = M.events_of(EventType.TRUST_STORE_RECALL)
    assert recalls
    for e in recalls:
        assert e.transport == Transport.NONE and e.era == Era.RECALL, e.id


@pytest.mark.covers("F-02", "B-02.2")
def test_PKI_S0R1_07_self_signed_certificate_contents_match_notes() -> None:  # noqa: N802
    assert M.cert("CERT-RDP-SELF").san_dns == ()


@pytest.mark.covers("F-10", "B-04.5", "B-08.2", "B-06.1", "B-09.1")
def test_PKI_S0R2_01_server_holds_the_intermediate_it_presents() -> None:  # noqa: N802
    for chain in M.chains:
        intermediate = chain.certs[1]
        present = next(
            e for e in M.events_of(EventType.PRESENT_CERT) if e.object == intermediate and e.from_ == chain.server
        )
        stored = [
            e for e in M.events_of(EventType.INTERMEDIATE_STORED) if e.object == intermediate and e.to == chain.server
        ]
        assert len(stored) == 1, chain.id
        assert stored[0].from_ == M.cert(intermediate).subject_actor
        assert stored[0].end_s <= present.start_s + EPS


@pytest.mark.covers("F-10", "F-13", "B-06.1", "B-06.5", "B-09.1")
def test_PKI_S0R2_02_presentation_and_revocation_follow_causal_order() -> None:  # noqa: N802
    for channel in M.channels:
        for attempt in _attempts(channel.id):
            pulse = attempt[0]
            for e in attempt:
                if e.type == EventType.PRESENT_CERT:
                    assert pulse.end_s <= e.start_s + EPS, f"{e.id} presents before {pulse.id} arrives"
    for chain in M.chains:
        revocation = next(
            e
            for e in M.events_of(EventType.VALIDATION_CHECK)
            if e.object == chain.id and e.check is not None and e.check.value == "revocation"
        )
        fetches = [e for e in M.events_of(EventType.CRL_FETCH) if e.target in chain.certs]
        assert fetches and all(f.end_s <= revocation.start_s + EPS for f in fetches), chain.id


@pytest.mark.covers("F-10", "B-06.1", "B-09.1")
def test_PKI_S0R2_03_handshake_proof_is_verified_with_the_certificate_key() -> None:  # noqa: N802
    for proof in M.handshake_proofs:
        sent = [e for e in M.events_of(EventType.HANDSHAKE_PROOF_SENT) if e.object == proof.id]
        verified = [e for e in M.events_of(EventType.HANDSHAKE_PROOF_VERIFIED) if e.object == proof.id]
        assert len(sent) == 1 and len(verified) == 1, proof.id
        v = verified[0]
        assert v.from_ == v.to == sent[0].to and sent[0].end_s <= v.start_s + EPS
        assert v.target is not None and M.cert(v.target).public_key == proof.verified_with
        later = [e for e in M.events if e.object == proof.id and e.start_s >= v.end_s - EPS]
        assert not later, "the proof ends its life once verified"
        session = next(
            e for e in M.events_of(EventType.SESSION_ESTABLISHED) if M.channel(e.object).server == proof.server
        )
        assert v.end_s <= session.start_s + EPS


@pytest.mark.covers("F-10", "C-07", "B-04.5", "B-05.3", "B-06.1", "B-08.2", "B-08.3", "B-09.1")
def test_PKI_S0R3_01_servers_present_their_own_copy_and_crown_originals_never_move() -> None:  # noqa: N802
    originals = {c.certificate for c in M.cas}
    static_reveals = (EventType.ISSUER_LINK, EventType.SELF_SIGNATURE_SHOWN)
    for e in M.events:
        if e.object in originals and e.era == Era.PRESENT:
            assert e.type in static_reveals, f"{e.id} moves or uses a CA's own certificate"
    for chain in M.chains:
        intermediate = M.cert(chain.certs[1])
        assert intermediate.copy_of is not None and intermediate.copy_of in originals, chain.id
        assert intermediate.holder == chain.server and intermediate.store == "Intermediate Certification Authorities"
        original = M.cert(intermediate.copy_of)
        assert (intermediate.public_key, intermediate.signed_with) == (original.public_key, original.signed_with)
        assert all(e.object != intermediate.id or e.era == Era.PRESENT for e in M.events)


@pytest.mark.covers("AR-07", "B-06.5")
def test_PKI_S0R2_08_undeployed_responder_has_no_host_and_its_tag_is_on_the_client() -> None:  # noqa: N802
    for service in M.services:
        if not service.deployed:
            assert service.host is None, service.id
    tag = next(lbl for lbl in M.labels if lbl.id == "LBL-OCSP")
    assert tag.attached_to in {c.id for c in M.chains}
