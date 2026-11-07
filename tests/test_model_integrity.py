"""Model-integrity hard discriminators (Charter Section 12, pure-Python part)."""

from __future__ import annotations

from itertools import pairwise

import pytest

from cff.story.model import (
    AD,
    CA_CHECK_ORDER,
    CLIENT,
    MODEL,
    PKI_HTTP,
    RDP_SERVER,
    REQUEST_DELIVERY_TYPES,
    ROOT_CA,
    VALIDATION_ORDER,
    WEB_SERVER,
    CaCheck,
    CaType,
    CertKind,
    Era,
    Event,
    EventType,
    KeyKind,
    RequestKind,
    ServiceKind,
    SubjectSource,
    Transport,
    ValidationCheck,
    cdp_url,
)
from cff.story.model import OID_REMOTE_DESKTOP_AUTH as RDA
from cff.story.model import OID_SERVER_AUTH as SERVER_AUTH

M = MODEL
EPS = 1e-9


def _before(a: Event, b: Event) -> bool:
    return a.end_s <= b.start_s + EPS


# ----------------------------------------------------------------- referential integrity


@pytest.mark.covers("B-*")
def test_ids_unique_and_references_resolve() -> None:
    ids = set(M.records)
    event_ids = [e.id for e in M.events]
    assert len(event_ids) == len(set(event_ids))
    beat_ids = {b.id for b in M.beats}
    for e in M.events:
        assert e.beat in beat_ids, e.id
        assert e.object in ids, (e.id, e.object)
        for ref in (e.from_, e.to, e.target, e.uses_key):
            assert ref is None or ref in ids, (e.id, ref)
    for b in M.beats:
        assert b.focal in ids, (b.id, b.focal)
    for label in M.labels:
        assert label.attached_to in ids, label.id
        assert set(label.must_read_beats) <= beat_ids, label.id


@pytest.mark.covers("B-*")
def test_every_beat_has_at_least_one_event() -> None:
    for b in M.beats:
        assert M.events_in(b.id), b.id


@pytest.mark.covers("B-*")
def test_events_lie_inside_their_beat() -> None:
    for e in M.events:
        beat = M.beat(e.beat)
        assert beat.start_s - EPS <= e.start_s < e.end_s <= beat.end_s + EPS, e.id


@pytest.mark.covers("F-03")
def test_key_pairs_and_keys_consistent() -> None:
    for kp in M.key_pairs:
        private, public = M.key(kp.private_key), M.key(kp.public_key)
        assert private.kind == KeyKind.PRIVATE and public.kind == KeyKind.PUBLIC
        assert private.owner == public.owner == kp.owner
        assert private.pair == public.pair == kp.id


# ----------------------------------------------------------------- private keys (F-03)


def _private_key_events() -> list[tuple[Event, str]]:
    private_owner = {k.id: k.owner for k in M.keys if k.kind == KeyKind.PRIVATE}
    pair_owner = {kp.id: kp.owner for kp in M.key_pairs}
    out: list[tuple[Event, str]] = []
    for e in M.events:
        if e.uses_key is not None and e.uses_key in private_owner:
            out.append((e, private_owner[e.uses_key]))
        if e.object in private_owner:
            out.append((e, private_owner[e.object]))
        if e.object in pair_owner:
            out.append((e, pair_owner[e.object]))
    return out


@pytest.mark.covers("F-03", "B-03.2", "B-03.4", "B-04.4", "B-06.1", "B-07.2", "B-08.2", "B-05.2")
def test_no_private_key_event_leaves_its_owner() -> None:
    events = _private_key_events()
    assert events, "expected private-key events"
    for e, owner in events:
        assert e.from_ == owner and e.to == owner, f"{e.id} moves a private key away from {owner}"
        assert e.transport == Transport.LOCAL, e.id


@pytest.mark.covers("F-03", "F-04")
def test_no_request_contains_a_private_key() -> None:
    for r in M.requests:
        assert r.contains_private_key is False
        assert M.key(r.public_key).kind == KeyKind.PUBLIC
        assert M.key(r.signed_with).kind == KeyKind.PRIVATE
        assert M.key(r.public_key).pair == M.key(r.signed_with).pair
        assert M.key(r.signed_with).owner == r.requester


@pytest.mark.covers("F-03")
def test_signing_keys_are_used_only_by_their_owner() -> None:
    for e in M.events:
        if e.uses_key is not None:
            owner = M.key(e.uses_key).owner
            assert e.from_ == e.to == owner, e.id


@pytest.mark.covers("F-09", "B-04.5", "B-08.2")
def test_issued_certificates_install_beside_existing_private_key() -> None:
    for cert_id in ("CERT-RDP", "CERT-WEB"):
        cert = M.cert(cert_id)
        installs = [e for e in M.events_of(EventType.CERT_INSTALLED) if e.object == cert_id]
        assert len(installs) == 1
        install = installs[0]
        assert install.from_ == install.to == cert.subject_actor
        assert cert.store == "LocalMachine\\My"
        key_pair = M.key(cert.public_key).pair
        generated = [e for e in M.events_of(EventType.KEYPAIR_GENERATED) if e.object == key_pair]
        assert len(generated) == 1 and _before(generated[0], install)


# ----------------------------------------------------------------- root CA (AR-01, AR-02)


@pytest.mark.covers("AR-01", "B-05.1", "B-05.2", "B-05.3")
def test_root_is_offline_standalone_and_never_on_the_network() -> None:
    root = M.actor(ROOT_CA)
    assert root.online is False and root.network_connected is False and root.domain_joined is False
    assert M.root_ca().ca_type == CaType.STANDALONE_ROOT and M.root_ca().online is False
    for e in M.events:
        if ROOT_CA in (e.from_, e.to):
            assert e.transport in (Transport.LOCAL, Transport.OFFLINE_MEDIA, Transport.LOGICAL, Transport.NONE), e.id


@pytest.mark.covers("AR-01", "AR-02", "F-05", "B-04.2", "B-07.4", "B-05.2")
def test_no_request_event_targets_the_root_ca() -> None:
    for e in M.events:
        if e.type == EventType.REQUEST_SUBMITTED:
            assert e.to != ROOT_CA, e.id
        if e.type in REQUEST_DELIVERY_TYPES and e.object in {r.id for r in M.requests}:
            request = M.request(e.object)
            if e.to == ROOT_CA:
                assert request.kind == RequestKind.SUBORDINATE_CA, e.id
                assert e.transport == Transport.OFFLINE_MEDIA and e.era == Era.FLASHBACK, e.id
    for r in M.requests:
        if r.kind == RequestKind.END_ENTITY:
            assert r.destination != ROOT_CA


@pytest.mark.covers("AR-02", "B-05.2")
def test_root_issues_only_issuing_ca_certificates_and_its_own_crl() -> None:
    root_key = M.ca(ROOT_CA).key_pair
    root_priv = next(kp.private_key for kp in M.key_pairs if kp.id == root_key)
    for cert in M.certificates:
        if cert.signed_with == root_priv:
            assert cert.kind in (CertKind.ISSUING_CA, CertKind.ROOT_SELF_SIGNED), cert.id
    for crl in M.crls:
        if crl.signed_with == root_priv:
            assert crl.issuer_actor == ROOT_CA and crl.id == M.ca(ROOT_CA).crl
            assert all(M.cert(c).kind == CertKind.ISSUING_CA for c in crl.covers)
            assert crl.publication_transport == Transport.OFFLINE_MEDIA
    for e in M.events_of(EventType.CA_SIGNS):
        if e.from_ == ROOT_CA:
            assert M.cert(e.object).kind == CertKind.ISSUING_CA and e.era == Era.FLASHBACK


@pytest.mark.covers("AR-01", "F-11", "F-17")
def test_root_certificate_is_self_signed_trust_anchor() -> None:
    root = M.cert("CERT-ROOT")
    assert root.kind == CertKind.ROOT_SELF_SIGNED and root.issuer_cert == root.id
    assert M.key(root.signed_with).pair == M.key(root.public_key).pair
    assert root.basic_constraints_ca is True
    assert root.aia_issuer_cert is None and root.cdp_crl is None
    # It is trusted because it is already in the client's Trusted Root store, not because it is self-signed.
    entries = [t for t in M.trust_store if t.cert == root.id]
    assert len(entries) == 1 and entries[0].holder == CLIENT and entries[0].installed_before_film
    assert entries[0].source == AD
    assert {t.cert for t in M.trust_store} == {root.id}, "only the root is a trust anchor"


# ----------------------------------------------------------------- issuing CAs and templates


@pytest.mark.covers("AR-03", "F-15", "B-05.3", "B-08.3", "B-09.2")
def test_both_issuing_ca_certificates_chain_to_the_same_root() -> None:
    issuing = [c for c in M.certificates if c.kind == CertKind.ISSUING_CA]
    assert {c.subject_actor for c in issuing} == {"ISSUING_CA1", "ISSUING_CA2"}
    for c in issuing:
        assert c.issuer_cert == "CERT-ROOT" and c.basic_constraints_ca is True
        assert M.ca(c.subject_actor).ca_type == CaType.ENTERPRISE_SUBORDINATE
    assert {chain.certs[-1] for chain in M.chains} == {"CERT-ROOT"}
    links = M.events_of(EventType.ISSUER_LINK)
    assert {(e.object, e.from_) for e in links} == {("CERT-CA1", ROOT_CA), ("CERT-CA2", ROOT_CA)}


@pytest.mark.covers("AR-04", "F-14", "B-04.1", "B-07.3")
def test_issuing_ca1_issues_rdpauth_and_ca2_issues_webserver_tls() -> None:
    assert M.publishing_cas("TPL-RDPAUTH") == ("ISSUING_CA1",)
    assert M.publishing_cas("TPL-WEBTLS") == ("ISSUING_CA2",)
    assert M.issuer_actor("CERT-RDP") == "ISSUING_CA1" and M.cert("CERT-RDP").template == "TPL-RDPAUTH"
    assert M.issuer_actor("CERT-WEB") == "ISSUING_CA2" and M.cert("CERT-WEB").template == "TPL-WEBTLS"
    assert M.ca(ROOT_CA).published_templates == ()


@pytest.mark.covers("F-05", "F-14", "B-04.1", "B-04.2", "B-07.3", "B-07.4")
def test_requests_go_only_to_a_publishing_ca_after_discovery() -> None:
    submissions = M.events_of(EventType.REQUEST_SUBMITTED)
    assert {e.object for e in submissions} == {"REQ-RDP", "REQ-WEB"}
    for e in submissions:
        request = M.request(e.object)
        assert request.template is not None
        assert e.from_ == request.requester and e.to == request.destination
        assert e.to in M.publishing_cas(request.template), e.id
        assert M.actor(e.to).online
        queries = [
            q for q in M.events_of(EventType.CA_DISCOVERY_QUERY) if M.discovery(q.object).requester == request.requester
        ]
        results = [r for r in M.events_of(EventType.CA_DISCOVERY_RESULT) if r.object in {q.object for q in queries}]
        assert queries and results, e.id
        assert all(q.to == AD for q in queries) and all(r.from_ == AD for r in results)
        assert all(_before(q, e) for q in queries) and all(_before(r, e) for r in results), e.id


@pytest.mark.covers("F-05", "AR-05", "B-04.1", "B-07.3")
def test_discovery_results_match_template_publication() -> None:
    for d in M.discoveries:
        computed = tuple(
            ca for ca in d.considered if d.template in M.ca(ca).published_templates and M.ca(ca).online
        )
        assert d.eligible == computed, d.id
        assert len(d.eligible) == 1
        request = next(r for r in M.requests if r.requester == d.requester and r.template == d.template)
        assert request.destination in d.eligible


@pytest.mark.covers("F-04", "B-03.4", "B-07.2", "B-05.2")
def test_every_request_is_preceded_by_proof_of_possession() -> None:
    for r in M.requests:
        pops = [e for e in M.events_of(EventType.PROOF_OF_POSSESSION) if e.object == r.id]
        deliveries = [e for e in M.events if e.type in REQUEST_DELIVERY_TYPES and e.object == r.id]
        assert len(pops) == 1 and deliveries, r.id
        pop = pops[0]
        assert pop.uses_key == r.signed_with
        assert all(_before(pop, d) for d in deliveries), r.id
        assembled = [e for e in M.events_of(EventType.REQUEST_ASSEMBLED) if e.object == r.id]
        if r.kind == RequestKind.END_ENTITY:
            assert len(assembled) == 1 and _before(assembled[0], pop)


@pytest.mark.covers("F-06", "B-04.3", "B-08.1")
def test_ca_runs_all_four_checks_in_order_before_signing() -> None:
    for r in M.requests:
        if r.kind != RequestKind.END_ENTITY:
            continue
        checks = [e for e in M.events_of(EventType.CA_CHECK) if e.object == r.id]
        assert tuple(e.check for e in checks) == CA_CHECK_ORDER, r.id
        assert all(e.from_ == e.to == r.destination for e in checks)
        submit = next(e for e in M.events_of(EventType.REQUEST_SUBMITTED) if e.object == r.id)
        sign = next(e for e in M.events_of(EventType.CA_SIGNS) if e.object == r.result_cert)
        assert all(_before(submit, c) and _before(c, sign) for c in checks)
        for a, b in pairwise(checks):
            assert a.start_s < b.start_s
        assert sign.from_ == r.destination


@pytest.mark.covers("F-07", "B-02.3", "B-04.3", "B-08.1")
def test_subject_sources_and_restricted_enrollment() -> None:
    rdp, web = M.template("TPL-RDPAUTH"), M.template("TPL-WEBTLS")
    assert rdp.subject_source == SubjectSource.BUILD_FROM_AD
    assert M.request("REQ-RDP").subject_in_request is None
    assert web.subject_source == SubjectSource.SUPPLY_IN_REQUEST and web.based_on == "Web Server"
    assert M.request("REQ-WEB").subject_in_request is not None
    assert web.enroll_principals == ("Authorized web-server accounts",)
    notes = [e.note for e in M.events_of(EventType.CA_CHECK) if e.object == "REQ-WEB" and e.note]
    assert notes == ["Name supplied in request — enrollment restricted"]


@pytest.mark.covers("F-08", "B-04.4", "B-08.2")
def test_ekus() -> None:
    assert RDA == "1.3.6.1.4.1.311.54.1.2" and SERVER_AUTH == "1.3.6.1.5.5.7.3.1"
    assert M.template("TPL-RDPAUTH").eku == (RDA,) and M.cert("CERT-RDP").eku == (RDA,)
    assert M.template("TPL-WEBTLS").eku == (SERVER_AUTH,) and M.cert("CERT-WEB").eku == (SERVER_AUTH,)
    rdp_chain = next(c for c in M.chains if c.id == "CHAIN-RDP")
    assert set(rdp_chain.accepted_ekus) == {RDA, SERVER_AUTH}
    for c in M.certificates:
        if c.kind == CertKind.END_ENTITY:
            assert c.basic_constraints_ca is False
            assert c.template is not None and c.eku == M.template(c.template).eku


@pytest.mark.covers("F-07", "F-12", "B-04.4", "B-08.2")
def test_san_matches_the_names_clients_use() -> None:
    for chain in M.chains:
        leaf = M.cert(chain.certs[0])
        assert chain.expected_name in leaf.san_dns
        assert leaf.subject_actor == chain.server
        assert chain.expected_name == chain.expected_name.lower()


# ----------------------------------------------------------------- presentation and validation


@pytest.mark.covers("F-01", "F-10", "B-06.1", "B-09.1")
def test_servers_present_their_own_certificate_and_prove_possession() -> None:
    for chain in M.chains:
        leaf = M.cert(chain.certs[0])
        presents = [e for e in M.events_of(EventType.PRESENT_CERT) if e.object == leaf.id]
        assert len(presents) == 1 and presents[0].from_ == chain.server == leaf.subject_actor
        assert presents[0].to == chain.relying_party
        intermediate = [e for e in M.events_of(EventType.PRESENT_CERT) if e.object == chain.certs[1]]
        assert len(intermediate) == 1 and intermediate[0].from_ == chain.server
        assert not [e for e in M.events_of(EventType.PRESENT_CERT) if e.object == chain.certs[-1]]
        sigs = [e for e in M.events_of(EventType.HANDSHAKE_SIGNATURE) if M.handshake(e.object).server == chain.server]
        assert len(sigs) == 1 and sigs[0].uses_key == M.private_key_for(leaf.public_key).id
        assert M.handshake(sigs[0].object).verified_with == leaf.public_key
        sent = [e for e in M.events_of(EventType.HANDSHAKE_PROOF_SENT) if e.object == sigs[0].object]
        assert len(sent) == 1 and _before(sigs[0], sent[0])
    assert M.key(M.cert("CERT-RDP").public_key).owner == RDP_SERVER
    assert M.key(M.cert("CERT-WEB").public_key).owner == WEB_SERVER
    assert M.key("KEY-WEB-PRIV").owner == WEB_SERVER


@pytest.mark.covers("F-02", "B-02.2")
def test_out_of_the_box_certificate_is_self_signed_and_unverified() -> None:
    self_signed = M.cert("CERT-RDP-SELF")
    assert self_signed.kind == CertKind.SELF_SIGNED_END_ENTITY and self_signed.issuer_cert == self_signed.id
    assert self_signed.subject_actor == RDP_SERVER
    assert self_signed.id not in {t.cert for t in M.trust_store}
    shown = [e for e in M.events_of(EventType.PRESENT_CERT) if e.object == self_signed.id]
    rejected = [e for e in M.events_of(EventType.CLIENT_CANNOT_VERIFY) if e.object == self_signed.id]
    assert len(shown) == 1 and len(rejected) == 1 and _before(shown[0], rejected[0])
    first_session = min(e.start_s for e in M.events_of(EventType.SESSION_ESTABLISHED))
    assert rejected[0].end_s <= first_session


@pytest.mark.covers("F-11", "B-06.2", "B-09.1")
def test_chain_links_follow_issuers_up_to_a_preinstalled_root() -> None:
    for chain in M.chains:
        for child, parent in pairwise(chain.certs):
            assert M.cert(child).issuer_cert == parent
            links = [e for e in M.events_of(EventType.CHAIN_LINK) if e.object == child and e.target == parent]
            assert len(links) == 1 and links[0].from_ == links[0].to == chain.relying_party
        assert chain.certs[-1] in {t.cert for t in M.trust_store if t.holder == chain.relying_party}


@pytest.mark.covers("F-11", "AR-06", "B-06.3")
def test_aia_is_never_a_trust_source() -> None:
    for s in M.services:
        assert s.trust_source is False
    aia = next(s for s in M.services if s.kind == ServiceKind.AIA)
    for e in M.events:
        if e.object == aia.id:
            assert e.type == EventType.AIA_INDICATOR and e.conditional and e.transport == Transport.NONE
        if e.type == EventType.TRUST_STORE_RECALL:
            assert e.from_ == AD and e.from_ != PKI_HTTP and e.era == Era.RECALL
    # Nothing coming from the PKI HTTP host ever becomes trusted.
    assert all(t.source != PKI_HTTP for t in M.trust_store)


@pytest.mark.covers("F-12", "B-06.4", "B-06.5", "B-09.1")
def test_validation_is_a_complete_set_of_distinct_checks() -> None:
    for chain in M.chains:
        checks = [e for e in M.events_of(EventType.VALIDATION_CHECK) if e.object == chain.id]
        assert {c.check for c in checks} == set(VALIDATION_ORDER), chain.id
        assert len(checks) == len(VALIDATION_ORDER)
        last_link = max(
            (e for e in M.events_of(EventType.CHAIN_LINK) if e.object in chain.certs), key=lambda e: e.end_s
        )
        for c in checks:
            assert c.from_ == c.to == chain.relying_party
            assert _before(last_link, c), c.id
        session = _session_for(chain.server)
        assert all(_before(c, session) for c in checks), chain.id


def _session_for(server: str) -> Event:
    return next(e for e in M.events_of(EventType.SESSION_ESTABLISHED) if M.channel(e.object).server == server)


@pytest.mark.covers("F-12", "B-06.4")
def test_identity_check_is_separate_from_chain_building() -> None:
    for chain in M.chains:
        name_checks = [
            e
            for e in M.events_of(EventType.VALIDATION_CHECK)
            if e.object == chain.id and e.check == ValidationCheck.NAME_MATCH
        ]
        assert len(name_checks) == 1 and name_checks[0].on_screen
        assert name_checks[0].type != EventType.CHAIN_LINK
        chain_ids = {e.id for e in M.events_of(EventType.CHAIN_LINK)}
        assert name_checks[0].id not in chain_ids


@pytest.mark.covers("F-13", "AR-06", "AR-07", "B-06.5", "B-09.1")
def test_revocation_checked_for_each_non_root_link_and_never_for_the_root() -> None:
    fetches = M.events_of(EventType.CRL_FETCH)
    for chain in M.chains:
        revocation = next(
            e
            for e in M.events_of(EventType.VALIDATION_CHECK)
            if e.object == chain.id and e.check == ValidationCheck.REVOCATION
        )
        for cert_id in chain.certs[:-1]:
            cert = M.cert(cert_id)
            mine = [f for f in fetches if f.target == cert_id]
            assert len(mine) == 1, cert_id
            fetch = mine[0]
            assert fetch.object == cert.cdp_crl and cert_id in M.crl(fetch.object).covers
            assert M.crl(fetch.object).issuer_actor == M.issuer_actor(cert_id)
            assert fetch.from_ == chain.relying_party and fetch.to == PKI_HTTP == M.crl(fetch.object).published_on
            assert cdp_url(M, cert) is not None
            assert fetch.end_s <= revocation.end_s + EPS, fetch.id
        assert not [f for f in fetches if f.target == chain.certs[-1]], "the root is not revocation-checked"
    assert not [f for f in fetches if f.to == ROOT_CA]
    ocsp = next(s for s in M.services if s.kind == ServiceKind.OCSP)
    assert ocsp.deployed is False
    assert all(e.conditional for e in M.events if e.object == ocsp.id)


@pytest.mark.covers("F-02", "F-12", "B-06.6", "B-09.1")
def test_connection_turns_trusted_only_after_validation() -> None:
    for chain in M.chains:
        session = _session_for(chain.server)
        fetches = [e for e in M.events_of(EventType.CRL_FETCH) if e.target in chain.certs]
        assert all(_before(f, session) for f in fetches)


@pytest.mark.covers("F-05", "B-02.3")
def test_rdp_enrollment_is_triggered_by_policy() -> None:
    policy = M.events_of(EventType.POLICY_ASSIGNS_TEMPLATE)
    assert len(policy) == 1 and policy[0].object == "TPL-RDPAUTH"
    assert policy[0].from_ == AD and policy[0].to == RDP_SERVER
    keygen = next(e for e in M.events_of(EventType.KEYPAIR_GENERATED) if e.object == "KP-RDP")
    assert _before(policy[0], keygen)


@pytest.mark.covers("C-02", "B-05.2")
def test_flashback_is_the_only_declared_cut_and_is_self_contained() -> None:
    flashback = [b for b in M.beats if b.flashback]
    assert [b.id for b in flashback] == ["B-05.2"]
    for e in M.events:
        assert (e.era == Era.FLASHBACK) == (e.beat == "B-05.2"), e.id


@pytest.mark.covers("F-06")
def test_ca_check_enum_matches_charter_order() -> None:
    assert CA_CHECK_ORDER == (
        CaCheck.REQUESTER_AUTHENTICATED,
        CaCheck.TEMPLATE_PUBLISHED_ON_CA,
        CaCheck.ENROLL_PERMISSION,
        CaCheck.TEMPLATE_POLICY,
    )
    assert VALIDATION_ORDER == (
        ValidationCheck.CHAIN_TO_TRUSTED_ROOT,
        ValidationCheck.SIGNATURES,
        ValidationCheck.VALIDITY,
        ValidationCheck.NAME_MATCH,
        ValidationCheck.EKU,
        ValidationCheck.REVOCATION,
    )
