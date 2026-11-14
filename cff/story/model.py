"""The story model: the single source of truth for the film (Charter Section 6).

Encodes as typed data the actors and their bounds roles, keys and their owners, certificates
(issuer, subject/SAN, EKU, Basic Constraints), templates and the CAs that publish them, CRLs,
beats, and events ``{id, beat, type, object, from, to, start_s, end_s}``.

Scenes, captions, audio cues, manifests and TRACEABILITY are generated from this module.
Timing (when) comes from ``cff.story.timing``; this module says what happens.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property

from cff.config import names as n
from cff.story import timing

# --------------------------------------------------------------------------- enums


class ActorKind(StrEnum):
    USER = "user"
    CLIENT = "client"
    SERVER = "server"
    DIRECTORY = "directory"
    ROOT_CA = "root_ca"
    ISSUING_CA = "issuing_ca"
    PUBLICATION_HOST = "publication_host"


class BoundsRole(StrEnum):
    """How an actor's world-space bounds are used by the in-Blender checks."""

    FIGURE = "figure"  # the stylized user
    DEVICE = "device"  # the client laptop
    CHASSIS = "chassis"  # server chassis: contains its keys
    DIRECTORY_NODE = "directory_node"  # AD node: requests may pass beside it, never into it
    CA_VAULT = "ca_vault"  # issuing CA vault: contains its CA key module
    ROOT_VAULT = "root_vault"  # root vault on a cable-free plinth: only trust links touch it
    PUBLICATION_POINT = "publication_point"  # AIA/CDP host


class ColourRole(StrEnum):
    """Colour-language roles (Charter Section 8). Values are palette token names."""

    ROOT = "root_gold"
    ISSUING_CA1 = "ca1_cyan"
    ISSUING_CA2 = "ca2_violet"
    REQUEST = "request_white"
    VALIDATED = "validated_green"
    PENDING = "pending_amber"
    REVOCATION = "revocation_amber"
    INELIGIBLE = "ineligible_grey"
    DIRECTORY = "ad_steel_blue"
    NEUTRAL = "neutral"


class KeyKind(StrEnum):
    PRIVATE = "private"
    PUBLIC = "public"


class KeyStorage(StrEnum):
    MACHINE_KEY_CONTAINER = "machine_key_container"  # LocalMachine key storage provider
    CA_PROTECTED_MODULE = "ca_protected_module"  # CA key storage: HSM or the CA's KSP


class CertKind(StrEnum):
    ROOT_SELF_SIGNED = "root_self_signed"
    ISSUING_CA = "issuing_ca"
    END_ENTITY = "end_entity"
    SELF_SIGNED_END_ENTITY = "self_signed_end_entity"  # RDP's out-of-the-box certificate


class SubjectSource(StrEnum):
    BUILD_FROM_AD = "build_from_ad"
    SUPPLY_IN_REQUEST = "supply_in_request"


class EnrollmentTrigger(StrEnum):
    GROUP_POLICY_RDP_SETTING = "group_policy_rdp_setting"
    AUTHORIZED_REQUEST = "authorized_request"


class CaType(StrEnum):
    STANDALONE_ROOT = "standalone_root"
    ENTERPRISE_SUBORDINATE = "enterprise_subordinate"


class RequestKind(StrEnum):
    END_ENTITY = "end_entity"
    SUBORDINATE_CA = "subordinate_ca"


class Transport(StrEnum):
    LOCAL = "local"  # happens inside one actor
    NETWORK = "network"
    OFFLINE_MEDIA = "offline_media"  # removable media carried by an administrator
    LOGICAL = "logical"  # a relationship shown (trust link), nothing travels
    NONE = "none"


class Era(StrEnum):
    PRESENT = "present"
    FLASHBACK = "flashback"  # S5 desaturated flashback of the setup ceremony
    RECALL = "recall"  # brief memory shimmer of something done earlier


class CaCheck(StrEnum):
    REQUESTER_AUTHENTICATED = "requester_authenticated"
    TEMPLATE_PUBLISHED_ON_CA = "template_published_on_ca"
    ENROLL_PERMISSION = "enroll_permission"
    TEMPLATE_POLICY = "template_policy"


class ValidationCheck(StrEnum):
    CHAIN_TO_TRUSTED_ROOT = "chain_to_trusted_root"
    SIGNATURES = "signatures"
    VALIDITY = "validity"
    NAME_MATCH = "name_match"
    EKU = "eku"
    REVOCATION = "revocation"


class EligibilityCriterion(StrEnum):
    TEMPLATE_PUBLISHED = "template_published"
    ENROLLMENT_POLICY = "enrollment_policy"
    PERMISSIONS = "permissions"
    CA_AVAILABLE = "ca_available"


class ServiceKind(StrEnum):
    AIA = "aia"
    CDP = "cdp"
    OCSP = "ocsp"


class LabelKind(StrEnum):
    HOST_PLATE = "host_plate"
    CA_NAMEPLATE = "ca_nameplate"
    TEMPLATE_BADGE = "template_badge"
    CARD_FIELD = "card_field"
    CHECK = "check"
    TAG = "tag"


class EventType(StrEnum):
    USER_INITIATES = "user_initiates"
    CONNECTION_PULSE = "connection_pulse"
    CONNECTION_CLOSED = "connection_closed"
    LISTENER_ACTIVATES = "listener_activates"
    PRESENT_CERT = "present_cert"
    CLIENT_CANNOT_VERIFY = "client_cannot_verify"
    POLICY_ASSIGNS_TEMPLATE = "policy_assigns_template"
    TEMPLATE_SELECTED = "template_selected"
    KEYPAIR_GENERATED = "keypair_generated"
    PRIVATE_KEY_STORED = "private_key_stored"
    REQUEST_ASSEMBLED = "request_assembled"
    PROOF_OF_POSSESSION = "proof_of_possession"
    CA_DISCOVERY_QUERY = "ca_discovery_query"
    CA_DISCOVERY_RESULT = "ca_discovery_result"
    REQUEST_SUBMITTED = "request_submitted"
    OFFLINE_CARRY = "offline_carry"
    CA_CHECK = "ca_check"
    REQUEST_CONSUMED = "request_consumed"  # the request ends its life at its destination CA
    CA_SIGNS = "ca_signs"
    CERT_RETURNED = "cert_returned"
    CERT_INSTALLED = "cert_installed"
    INTERMEDIATE_STORED = "intermediate_stored"  # copy of the issuing CA cert into the server's Intermediate store
    SELF_SIGNATURE_SHOWN = "self_signature_shown"
    ISSUER_LINK = "issuer_link"
    HANDSHAKE_SIGNATURE = "handshake_signature"
    HANDSHAKE_PROOF_SENT = "handshake_proof_sent"
    HANDSHAKE_PROOF_VERIFIED = "handshake_proof_verified"
    CHAIN_LINK = "chain_link"
    TRUST_STORE_RECALL = "trust_store_recall"
    AIA_INDICATOR = "aia_indicator"
    VALIDATION_PENDING = "validation_pending"
    VALIDATION_CHECK = "validation_check"
    CRL_FETCH = "crl_fetch"
    OCSP_NOTE = "ocsp_note"
    SESSION_ESTABLISHED = "session_established"
    TRUST_PATH_REVEAL = "trust_path_reveal"
    FINAL_FADE = "final_fade"


# Request event types that move a request toward a CA.
REQUEST_DELIVERY_TYPES = (EventType.REQUEST_SUBMITTED, EventType.OFFLINE_CARRY)
SIGNING_EVENT_TYPES = (
    EventType.PROOF_OF_POSSESSION,
    EventType.CA_SIGNS,
    EventType.HANDSHAKE_SIGNATURE,
)

# --------------------------------------------------------------------------- constants

OID_REMOTE_DESKTOP_AUTH = "1.3.6.1.4.1.311.54.1.2"
OID_SERVER_AUTH = "1.3.6.1.5.5.7.3.1"
EKU_NAMES: dict[str, str] = {
    OID_REMOTE_DESKTOP_AUTH: n.EKU_REMOTE_DESKTOP_AUTH_NAME,
    OID_SERVER_AUTH: n.EKU_SERVER_AUTH_NAME,
}

STORE_PERSONAL = "LocalMachine\\My"
STORE_TRUSTED_ROOT = "Trusted Root Certification Authorities"
STORE_CA = "CA database and CA certificate store"
STORE_INTERMEDIATE = "Intermediate Certification Authorities"
REQUEST_FORMAT_EE = "PKCS #10 inside CMC"
REQUEST_FORMAT_SUBCA = "PKCS #10 (request file)"
AIA_CDP_SCHEME = "http"
AIA_CDP_PATH = "pki"

# --------------------------------------------------------------------------- records


@dataclass(frozen=True)
class Scene:
    id: str
    title: str


@dataclass(frozen=True)
class Beat:
    id: str
    title: str
    summary: str
    facts: tuple[str, ...]
    focal: str
    flashback: bool = False

    @property
    def scene(self) -> str:
        return timing.scene_of(self.id)

    @property
    def start_s(self) -> float:
        return timing.beat_window(self.id)[0]

    @property
    def end_s(self) -> float:
        return timing.beat_window(self.id)[1]


@dataclass(frozen=True)
class Actor:
    id: str
    kind: ActorKind
    label: str
    bounds_role: BoundsRole
    colour_role: ColourRole
    fqdn: str | None
    domain_joined: bool
    network_connected: bool
    online: bool = True


@dataclass(frozen=True)
class KeyPair:
    id: str
    owner: str
    private_key: str
    public_key: str
    storage: KeyStorage
    generated_in_beat: str | None  # None: generated before the film's present (setup)


@dataclass(frozen=True)
class Key:
    id: str
    kind: KeyKind
    owner: str
    pair: str


@dataclass(frozen=True)
class Certificate:
    id: str
    kind: CertKind
    subject_cn: str
    subject_actor: str
    san_dns: tuple[str, ...]
    issuer_cert: str  # id of the issuer's certificate (itself when self-signed)
    signed_with: str  # private key id
    public_key: str  # subject public key id
    eku: tuple[str, ...]  # OIDs; empty for CA certificates (not restricted in this lab)
    basic_constraints_ca: bool
    template: str | None
    aia_issuer_cert: str | None  # AIA points to this certificate's location
    cdp_crl: str | None  # CDP points to this CRL
    store: str
    issued_in_beat: str | None  # None: issued before the film's present or never shown
    copy_of: str | None = None  # set on a holder's copy of another certificate (same certificate, own object)
    holder: str | None = None  # actor holding this copy in its store (copies only)


@dataclass(frozen=True)
class Crl:
    id: str
    issuer_actor: str
    signed_with: str
    covers: tuple[str, ...]  # certificates this CRL reports on
    published_on: str  # publication host actor
    publication_transport: Transport  # how the CRL reaches the host


@dataclass(frozen=True)
class Template:
    id: str
    name: str
    based_on: str | None
    eku: tuple[str, ...]
    subject_source: SubjectSource
    enroll_principals: tuple[str, ...]
    trigger: EnrollmentTrigger


@dataclass(frozen=True)
class CertificationAuthority:
    actor: str
    ca_type: CaType
    key_pair: str
    certificate: str
    crl: str
    published_templates: tuple[str, ...]
    online: bool


@dataclass(frozen=True)
class Request:
    id: str
    kind: RequestKind
    requester: str
    template: str | None
    public_key: str
    signed_with: str
    format: str
    subject_in_request: str | None
    destination: str
    transport: Transport
    result_cert: str
    contains_private_key: bool = False


@dataclass(frozen=True)
class Discovery:
    id: str
    requester: str
    template: str
    directory: str
    considered: tuple[str, ...]
    eligible: tuple[str, ...]
    criteria: tuple[EligibilityCriterion, ...]


@dataclass(frozen=True)
class Chain:
    id: str
    relying_party: str
    server: str
    certs: tuple[str, ...]  # leaf first, root last
    expected_name: str
    accepted_ekus: tuple[str, ...]
    purpose_label: str


@dataclass(frozen=True)
class Channel:
    id: str
    client: str
    server: str
    protocol: str


@dataclass(frozen=True)
class HandshakeProof:
    id: str
    server: str
    signed_with: str
    verified_with: str


@dataclass(frozen=True)
class Service:
    id: str
    kind: ServiceKind
    host: str | None  # None for a service that is not deployed in this lab
    deployed: bool
    trust_source: bool = False


@dataclass(frozen=True)
class TrustStoreEntry:
    id: str
    holder: str
    cert: str
    store: str
    source: str  # actor that distributed it (AD publication / Group Policy)
    installed_before_film: bool


@dataclass(frozen=True)
class WorldObject:
    id: str
    description: str


@dataclass(frozen=True)
class Label:
    id: str
    kind: LabelKind
    text: str
    attached_to: str
    must_read_beats: tuple[str, ...]


@dataclass(frozen=True)
class Event:
    id: str
    beat: str
    type: EventType
    object: str
    from_: str | None
    to: str | None
    transport: Transport
    uses_key: str | None = None
    check: CaCheck | ValidationCheck | None = None
    target: str | None = None
    conditional: bool = False
    era: Era = Era.PRESENT
    on_screen: bool = True
    note: str | None = None

    @property
    def start_s(self) -> float:
        return timing.event_window(self.id, self.beat)[0]

    @property
    def end_s(self) -> float:
        return timing.event_window(self.id, self.beat)[1]


Record = (
    Actor
    | KeyPair
    | Key
    | Certificate
    | Crl
    | Template
    | Request
    | Discovery
    | Chain
    | Channel
    | HandshakeProof
    | Service
    | TrustStoreEntry
    | WorldObject
)


@dataclass(frozen=True)
class StoryModel:
    scenes: tuple[Scene, ...]
    beats: tuple[Beat, ...]
    actors: tuple[Actor, ...]
    key_pairs: tuple[KeyPair, ...]
    keys: tuple[Key, ...]
    certificates: tuple[Certificate, ...]
    crls: tuple[Crl, ...]
    templates: tuple[Template, ...]
    cas: tuple[CertificationAuthority, ...]
    requests: tuple[Request, ...]
    discoveries: tuple[Discovery, ...]
    chains: tuple[Chain, ...]
    channels: tuple[Channel, ...]
    handshake_proofs: tuple[HandshakeProof, ...]
    services: tuple[Service, ...]
    trust_store: tuple[TrustStoreEntry, ...]
    world_objects: tuple[WorldObject, ...]
    labels: tuple[Label, ...]
    events: tuple[Event, ...]

    @cached_property
    def records(self) -> dict[str, Record]:
        index: dict[str, Record] = {}
        groups: tuple[tuple[Record, ...], ...] = (
            self.actors,
            self.key_pairs,
            self.keys,
            self.certificates,
            self.crls,
            self.templates,
            self.requests,
            self.discoveries,
            self.chains,
            self.channels,
            self.handshake_proofs,
            self.services,
            self.trust_store,
            self.world_objects,
        )
        for group in groups:
            for record in group:
                if record.id in index:
                    raise ValueError(f"duplicate model id {record.id}")
                index[record.id] = record
        return index

    def actor(self, actor_id: str) -> Actor:
        return next(a for a in self.actors if a.id == actor_id)

    def key(self, key_id: str) -> Key:
        return next(k for k in self.keys if k.id == key_id)

    def cert(self, cert_id: str) -> Certificate:
        return next(c for c in self.certificates if c.id == cert_id)

    def canonical(self, cert_id: str) -> str:
        """The original certificate a copy stands for (itself when not a copy)."""
        return self.cert(cert_id).copy_of or cert_id

    def crl(self, crl_id: str) -> Crl:
        return next(c for c in self.crls if c.id == crl_id)

    def template(self, template_id: str) -> Template:
        return next(t for t in self.templates if t.id == template_id)

    def ca(self, actor_id: str) -> CertificationAuthority:
        return next(c for c in self.cas if c.actor == actor_id)

    def request(self, request_id: str) -> Request:
        return next(r for r in self.requests if r.id == request_id)

    def beat(self, beat_id: str) -> Beat:
        return next(b for b in self.beats if b.id == beat_id)

    def discovery(self, discovery_id: str) -> Discovery:
        return next(d for d in self.discoveries if d.id == discovery_id)

    def channel(self, channel_id: str) -> Channel:
        return next(c for c in self.channels if c.id == channel_id)

    def handshake(self, proof_id: str) -> HandshakeProof:
        return next(h for h in self.handshake_proofs if h.id == proof_id)

    def private_key_for(self, public_key_id: str) -> Key:
        pair = self.key(public_key_id).pair
        return next(k for k in self.keys if k.pair == pair and k.kind == KeyKind.PRIVATE)

    def events_of(self, event_type: EventType) -> list[Event]:
        return [e for e in self.events if e.type == event_type]

    def events_in(self, beat_id: str) -> list[Event]:
        return [e for e in self.events if e.beat == beat_id]

    def issuer_actor(self, cert_id: str) -> str:
        """Actor that issued (signed) a certificate."""
        return self.key(self.cert(cert_id).signed_with).owner

    def publishing_cas(self, template_id: str) -> tuple[str, ...]:
        return tuple(c.actor for c in self.cas if template_id in c.published_templates)

    def root_ca(self) -> CertificationAuthority:
        return next(c for c in self.cas if c.ca_type == CaType.STANDALONE_ROOT)


# --------------------------------------------------------------------------- helpers


def extension_url(file_name: str) -> str:
    """AIA/CDP URL on the PKI HTTP host. Illustrative lab data; never fetched by the code."""
    return f"{AIA_CDP_SCHEME}://{n.PKI_HTTP_HOST}/{AIA_CDP_PATH}/{file_name}"


def aia_url(model: StoryModel, cert: Certificate) -> str | None:
    if cert.aia_issuer_cert is None:
        return None
    issuer = model.cert(cert.aia_issuer_cert)
    return extension_url(f"{n.file_slug(issuer.subject_cn)}.crt")


def cdp_url(model: StoryModel, cert: Certificate) -> str | None:
    if cert.cdp_crl is None:
        return None
    crl = model.crl(cert.cdp_crl)
    issuer_cert = model.ca(crl.issuer_actor).certificate
    return extension_url(f"{n.file_slug(model.cert(issuer_cert).subject_cn)}.crl")


CA_CHECK_TEXT: dict[CaCheck, str] = {
    CaCheck.REQUESTER_AUTHENTICATED: "Requester authenticated",
    CaCheck.TEMPLATE_PUBLISHED_ON_CA: "Template published on this CA",
    CaCheck.ENROLL_PERMISSION: "Enroll permission granted",
    CaCheck.TEMPLATE_POLICY: "Request meets template policy",
}

ELIGIBILITY_TEXT: dict[EligibilityCriterion, str] = {
    EligibilityCriterion.TEMPLATE_PUBLISHED: "Template published",
    EligibilityCriterion.ENROLLMENT_POLICY: "Enrollment policy",
    EligibilityCriterion.PERMISSIONS: "Permissions",
    EligibilityCriterion.CA_AVAILABLE: "CA available",
}

CA_CHECK_ORDER: tuple[CaCheck, ...] = tuple(CaCheck)
VALIDATION_ORDER: tuple[ValidationCheck, ...] = tuple(ValidationCheck)


def validation_text(check: ValidationCheck, chain: Chain) -> str:
    texts = {
        ValidationCheck.CHAIN_TO_TRUSTED_ROOT: "Chain ends at a trusted root",
        ValidationCheck.SIGNATURES: "Signatures verify",
        ValidationCheck.VALIDITY: "Currently valid",
        ValidationCheck.NAME_MATCH: f"Name matches {chain.expected_name}",
        ValidationCheck.EKU: f"EKU permits {chain.purpose_label}",
        ValidationCheck.REVOCATION: "Revocation OK",
    }
    return texts[check]


# --------------------------------------------------------------------------- build

USER = "USER"
CLIENT = "CLIENT"
RDP_SERVER = "RDP_SERVER"
WEB_SERVER = "WEB_SERVER"
AD = "AD"
ROOT_CA = "ROOT_CA"
ISSUING_CA1 = "ISSUING_CA1"
ISSUING_CA2 = "ISSUING_CA2"
PKI_HTTP = "PKI_HTTP"

SCENES: tuple[Scene, ...] = (
    Scene("S1", "The connection begins"),
    Scene("S2", "An identity the client can't verify"),
    Scene("S3", "Keys born locally, request sealed"),
    Scene("S4", "Finding the right CA, then evaluation"),
    Scene("S5", "The hierarchy and the trust anchor"),
    Scene("S6", "Presentation and validation"),
    Scene("S7", "A second workload"),
    Scene("S8", f"{n.ISSUING_CA2_ROLE} signs"),
    Scene("S9", "Full picture and close"),
)


def _beats() -> tuple[Beat, ...]:
    ca1, ca2 = n.ISSUING_CA1_ROLE, n.ISSUING_CA2_ROLE
    return (
        Beat("B-01.1", "User opens RDP", f"At {n.CLIENT_HOSTNAME} the user opens an RDP connection to {n.RDP_SERVER_FQDN}.", ("F-01",), USER),
        Beat("B-01.2", "Connection pulse", "An amber connection pulse travels the floor light-channel to the RDP server.", ("F-01",), "CH-RDP"),
        Beat("B-02.1", "Listener lights", f"Arrival at {n.RDP_SERVER_FQDN}; the RDP listener lights up.", ("F-01",), RDP_SERVER),
        Beat("B-02.2", "Self-signed, unverified", "The server's out-of-the-box self-signed certificate reaches the client, which cannot verify it; nothing is accepted and the attempt closes.", ("F-01", "F-02"), "CERT-RDP-SELF"),
        Beat("B-02.3", "Template from policy", f"Group Policy names the {n.RDP_TEMPLATE} template for the RDP server.", ("F-05", "F-07"), "TPL-RDPAUTH"),
        Beat("B-03.1", "Key pair forms", "A new key pair is generated inside the RDP server chassis.", ("F-03",), "KP-RDP"),
        Beat("B-03.2", "Private key anchored", "The private key settles into the server's locked key container and stays there.", ("F-03",), "KEY-RDP-PRIV"),
        Beat("B-03.3", "Request assembled", "The public key and request information enter the request capsule.", ("F-04",), "REQ-RDP"),
        Beat("B-03.4", "Proof of possession", "The private key signs the request in place; the key does not move.", ("F-03", "F-04"), "REQ-RDP"),
        Beat("B-04.1", "Who publishes the template?", f"The enrollment client asks AD ({n.AD_DOMAIN_FQDN}) which CA publishes {n.RDP_TEMPLATE}; only {ca1} is eligible.", ("F-05", "F-14", "AR-04", "AR-05"), AD),
        Beat("B-04.2", f"Into {ca1}", f"The request travels to {ca1} only.", ("F-05", "F-04"), "REQ-RDP"),
        Beat("B-04.3", "Four checks", f"{ca1} authenticates the requester and checks publication, Enroll permission and template policy.", ("F-06", "F-07", "AR-05"), ISSUING_CA1),
        Beat("B-04.4", "CA signs", f"The request is consumed; {ca1}'s key, sealed in its module, drives the press that signs the end-entity certificate.", ("F-03", "F-07", "F-08", "AR-06"), "CERT-RDP"),
        Beat("B-04.5", "Certificate installed", "The certificate returns and locks in beside the existing private key.", ("F-09", "F-03"), "CERT-RDP"),
        Beat("B-05.1", "The trust anchor", f"A sealed, cable-free gold vault: {n.ROOT_CA_NAME}, self-signed, offline.", ("AR-01", "F-17", "F-11"), ROOT_CA),
        Beat("B-05.2", "Offline ceremony (flashback)", f"Earlier, at setup: {ca1}'s own CA request is carried to the root on removable media; the root issues and signs {ca1}'s CA certificate offline, and the certificate is carried back.", ("AR-02", "F-03", "F-04"), "REQ-CA1", flashback=True),
        Beat("B-05.3", "Issuer link", f"Present: a gold-to-cyan link joins {ca1}'s certificate to the root. No end-entity request reaches the root.", ("AR-03", "F-15", "F-17"), "CERT-CA1"),
        Beat("B-06.1", "Presentation", f"A new connection attempt: the server presents its certificate with {ca1}'s certificate and proves possession of its private key.", ("F-10", "F-03", "F-01"), "CERT-RDP"),
        Beat("B-06.2", "Chain builds", "On the client the cards dock upward to a root already in the Trusted Root store, installed earlier by policy.", ("F-11", "AR-05"), "CHAIN-RDP"),
        Beat("B-06.3", "AIA is not trust", "A small AIA indicator: a missing intermediate could be fetched; fetching never creates trust.", ("F-11", "AR-06"), "SVC-AIA"),
        Beat("B-06.4", "Validation checks", "Chain, signatures, validity, name, EKU resolve; revocation is pending.", ("F-12", "F-08"), "CHAIN-RDP"),
        Beat("B-06.5", "Revocation per link", "Two CRL fetches from the CDP, one per non-root link; OCSP only if deployed.", ("F-13", "AR-06", "AR-07"), "SVC-CDP"),
        Beat("B-06.6", "Trusted session", "The channel turns green and the RDP session opens.", ("F-12", "F-01"), "CH-RDP"),
        Beat("B-07.1", "Web server", f"{n.WEB_SERVER_HOSTNAME} serves {n.WEB_SITE_DNS_NAME} and needs a {n.WEB_TEMPLATE} certificate.", ("F-07", "F-14"), WEB_SERVER),
        Beat("B-07.2", "Local key, sealed request", "A local key pair; the private key is anchored; the request is sealed by proof of possession.", ("F-03", "F-04"), "REQ-WEB"),
        Beat("B-07.3", "Eligibility", f"AD shows both CAs: {ca1} does not publish {n.WEB_TEMPLATE}; {ca2} is eligible.", ("F-05", "F-14", "AR-04", "AR-05"), AD),
        Beat("B-07.4", f"Only to {ca2}", f"The request travels only to {ca2}.", ("F-05", "F-14"), "REQ-WEB"),
        Beat("B-08.1", "Compressed checks", f"{ca2} runs the four checks; the subject is supplied in the request, so enrollment is restricted.", ("F-06", "F-07"), ISSUING_CA2),
        Beat("B-08.2", "TLS certificate", f"{ca2}'s key-driven press signs the TLS certificate; it locks in beside the web server's private key.", ("F-03", "F-08", "F-09"), "CERT-WEB"),
        Beat("B-08.3", "Same root", f"{ca2}'s own certificate is linked in gold to the same root.", ("F-15", "AR-03"), "CERT-CA2"),
        Beat("B-09.1", "Browser validation", f"A browser validates {n.WEB_SITE_DNS_NAME} up to the root; the channel turns green.", ("F-10", "F-11", "F-12", "F-13"), "CHAIN-WEB"),
        Beat("B-09.2", "Hero topology", "Root on top, both issuing CAs, both servers and the user; cyan and violet paths converge in gold at one root.", ("F-14", "F-15", "F-17"), ROOT_CA),
        Beat("B-09.3", "Close", "Closing captions and title card; gentle settle and fade.", ("F-15",), ROOT_CA),
    )


def _actors() -> tuple[Actor, ...]:
    return (
        Actor(USER, ActorKind.USER, "User", BoundsRole.FIGURE, ColourRole.NEUTRAL, None, False, False),
        Actor(CLIENT, ActorKind.CLIENT, n.CLIENT_HOSTNAME, BoundsRole.DEVICE, ColourRole.NEUTRAL, n.CLIENT_FQDN, True, True),
        Actor(RDP_SERVER, ActorKind.SERVER, n.RDP_SERVER_FQDN, BoundsRole.CHASSIS, ColourRole.NEUTRAL, n.RDP_SERVER_FQDN, True, True),
        Actor(WEB_SERVER, ActorKind.SERVER, n.WEB_SERVER_HOSTNAME, BoundsRole.CHASSIS, ColourRole.NEUTRAL, n.WEB_SERVER_FQDN, True, True),
        Actor(AD, ActorKind.DIRECTORY, n.AD_DOMAIN_FQDN, BoundsRole.DIRECTORY_NODE, ColourRole.DIRECTORY, n.DC_FQDN, True, True),
        Actor(ROOT_CA, ActorKind.ROOT_CA, n.ROOT_CA_NAME, BoundsRole.ROOT_VAULT, ColourRole.ROOT, None, False, False, online=False),
        Actor(ISSUING_CA1, ActorKind.ISSUING_CA, n.ISSUING_CA1_NAME, BoundsRole.CA_VAULT, ColourRole.ISSUING_CA1, None, True, True),
        Actor(ISSUING_CA2, ActorKind.ISSUING_CA, n.ISSUING_CA2_NAME, BoundsRole.CA_VAULT, ColourRole.ISSUING_CA2, None, True, True),
        Actor(PKI_HTTP, ActorKind.PUBLICATION_HOST, n.PKI_HTTP_HOST, BoundsRole.PUBLICATION_POINT, ColourRole.NEUTRAL, n.PKI_HTTP_HOST, True, True),
    )


def _key_material() -> tuple[tuple[KeyPair, ...], tuple[Key, ...]]:
    spec = (
        ("KP-RDP-SELF", RDP_SERVER, "KEY-RDP-SELF", KeyStorage.MACHINE_KEY_CONTAINER, None),
        ("KP-RDP", RDP_SERVER, "KEY-RDP", KeyStorage.MACHINE_KEY_CONTAINER, "B-03.1"),
        ("KP-WEB", WEB_SERVER, "KEY-WEB", KeyStorage.MACHINE_KEY_CONTAINER, "B-07.2"),
        ("KP-ROOT", ROOT_CA, "KEY-ROOT", KeyStorage.CA_PROTECTED_MODULE, None),
        ("KP-CA1", ISSUING_CA1, "KEY-CA1", KeyStorage.CA_PROTECTED_MODULE, None),
        ("KP-CA2", ISSUING_CA2, "KEY-CA2", KeyStorage.CA_PROTECTED_MODULE, None),
    )
    pairs: list[KeyPair] = []
    keys: list[Key] = []
    for pair_id, owner, stem, storage, beat in spec:
        private, public = f"{stem}-PRIV", f"{stem}-PUB"
        pairs.append(KeyPair(pair_id, owner, private, public, storage, beat))
        keys.append(Key(private, KeyKind.PRIVATE, owner, pair_id))
        keys.append(Key(public, KeyKind.PUBLIC, owner, pair_id))
    return tuple(pairs), tuple(keys)


def _templates() -> tuple[Template, ...]:
    return (
        Template(
            "TPL-RDPAUTH",
            n.RDP_TEMPLATE,
            None,
            (OID_REMOTE_DESKTOP_AUTH,),
            SubjectSource.BUILD_FROM_AD,
            ("RDP server computer accounts",),
            EnrollmentTrigger.GROUP_POLICY_RDP_SETTING,
        ),
        Template(
            "TPL-WEBTLS",
            n.WEB_TEMPLATE,
            "Web Server",
            (OID_SERVER_AUTH,),
            SubjectSource.SUPPLY_IN_REQUEST,
            ("Authorized web-server accounts",),
            EnrollmentTrigger.AUTHORIZED_REQUEST,
        ),
    )


def _intermediate_copy(original: Certificate, copy_id: str, holder: str) -> Certificate:
    """A server's own copy of an issuing CA certificate, received with the enrollment response chain."""
    return Certificate(
        copy_id, original.kind, original.subject_cn, original.subject_actor, original.san_dns, original.issuer_cert,
        original.signed_with, original.public_key, original.eku, original.basic_constraints_ca, original.template,
        original.aia_issuer_cert, original.cdp_crl, STORE_INTERMEDIATE, None, copy_of=original.id, holder=holder,
    )


def _certificates() -> tuple[Certificate, ...]:
    originals = _original_certificates()
    by_id = {c.id: c for c in originals}
    return (
        *originals,
        _intermediate_copy(by_id["CERT-CA1"], "CERT-CA1-COPY-RDP", RDP_SERVER),
        _intermediate_copy(by_id["CERT-CA2"], "CERT-CA2-COPY-WEB", WEB_SERVER),
    )


def _original_certificates() -> tuple[Certificate, ...]:
    return (
        Certificate("CERT-ROOT", CertKind.ROOT_SELF_SIGNED, n.ROOT_CA_NAME, ROOT_CA, (), "CERT-ROOT", "KEY-ROOT-PRIV", "KEY-ROOT-PUB", (), True, None, None, None, STORE_TRUSTED_ROOT, None),
        Certificate("CERT-CA1", CertKind.ISSUING_CA, n.ISSUING_CA1_NAME, ISSUING_CA1, (), "CERT-ROOT", "KEY-ROOT-PRIV", "KEY-CA1-PUB", (), True, None, "CERT-ROOT", "CRL-ROOT", STORE_CA, "B-05.2"),
        Certificate("CERT-CA2", CertKind.ISSUING_CA, n.ISSUING_CA2_NAME, ISSUING_CA2, (), "CERT-ROOT", "KEY-ROOT-PRIV", "KEY-CA2-PUB", (), True, None, "CERT-ROOT", "CRL-ROOT", STORE_CA, None),
        Certificate("CERT-RDP-SELF", CertKind.SELF_SIGNED_END_ENTITY, n.RDP_SERVER_FQDN, RDP_SERVER, (), "CERT-RDP-SELF", "KEY-RDP-SELF-PRIV", "KEY-RDP-SELF-PUB", (OID_SERVER_AUTH,), False, None, None, None, "Remote Desktop", None),
        Certificate("CERT-RDP", CertKind.END_ENTITY, n.RDP_SERVER_FQDN, RDP_SERVER, (n.RDP_SERVER_FQDN,), "CERT-CA1", "KEY-CA1-PRIV", "KEY-RDP-PUB", (OID_REMOTE_DESKTOP_AUTH,), False, "TPL-RDPAUTH", "CERT-CA1", "CRL-CA1", STORE_PERSONAL, "B-04.4"),
        Certificate("CERT-WEB", CertKind.END_ENTITY, n.WEB_SITE_DNS_NAME, WEB_SERVER, (n.WEB_SITE_DNS_NAME,), "CERT-CA2", "KEY-CA2-PRIV", "KEY-WEB-PUB", (OID_SERVER_AUTH,), False, "TPL-WEBTLS", "CERT-CA2", "CRL-CA2", STORE_PERSONAL, "B-08.2"),
    )


def _crls() -> tuple[Crl, ...]:
    return (
        Crl("CRL-ROOT", ROOT_CA, "KEY-ROOT-PRIV", ("CERT-CA1", "CERT-CA2"), PKI_HTTP, Transport.OFFLINE_MEDIA),
        Crl("CRL-CA1", ISSUING_CA1, "KEY-CA1-PRIV", ("CERT-RDP",), PKI_HTTP, Transport.NETWORK),
        Crl("CRL-CA2", ISSUING_CA2, "KEY-CA2-PRIV", ("CERT-WEB",), PKI_HTTP, Transport.NETWORK),
    )


def _cas() -> tuple[CertificationAuthority, ...]:
    return (
        CertificationAuthority(ROOT_CA, CaType.STANDALONE_ROOT, "KP-ROOT", "CERT-ROOT", "CRL-ROOT", (), online=False),
        CertificationAuthority(ISSUING_CA1, CaType.ENTERPRISE_SUBORDINATE, "KP-CA1", "CERT-CA1", "CRL-CA1", ("TPL-RDPAUTH",), online=True),
        CertificationAuthority(ISSUING_CA2, CaType.ENTERPRISE_SUBORDINATE, "KP-CA2", "CERT-CA2", "CRL-CA2", ("TPL-WEBTLS",), online=True),
    )


def _requests() -> tuple[Request, ...]:
    return (
        Request("REQ-RDP", RequestKind.END_ENTITY, RDP_SERVER, "TPL-RDPAUTH", "KEY-RDP-PUB", "KEY-RDP-PRIV", REQUEST_FORMAT_EE, None, ISSUING_CA1, Transport.NETWORK, "CERT-RDP"),
        Request("REQ-WEB", RequestKind.END_ENTITY, WEB_SERVER, "TPL-WEBTLS", "KEY-WEB-PUB", "KEY-WEB-PRIV", REQUEST_FORMAT_EE, f"CN={n.WEB_SITE_DNS_NAME}; SAN dNSName={n.WEB_SITE_DNS_NAME}", ISSUING_CA2, Transport.NETWORK, "CERT-WEB"),
        Request("REQ-CA1", RequestKind.SUBORDINATE_CA, ISSUING_CA1, None, "KEY-CA1-PUB", "KEY-CA1-PRIV", REQUEST_FORMAT_SUBCA, f"CN={n.ISSUING_CA1_NAME}", ROOT_CA, Transport.OFFLINE_MEDIA, "CERT-CA1"),
    )


def _discoveries() -> tuple[Discovery, ...]:
    criteria = tuple(EligibilityCriterion)
    return (
        Discovery("DISC-RDP", RDP_SERVER, "TPL-RDPAUTH", AD, (ISSUING_CA1, ISSUING_CA2), (ISSUING_CA1,), criteria),
        Discovery("DISC-WEB", WEB_SERVER, "TPL-WEBTLS", AD, (ISSUING_CA1, ISSUING_CA2), (ISSUING_CA2,), criteria),
    )


def _chains() -> tuple[Chain, ...]:
    return (
        Chain("CHAIN-RDP", CLIENT, RDP_SERVER, ("CERT-RDP", "CERT-CA1-COPY-RDP", "CERT-ROOT"), n.RDP_SERVER_FQDN, (OID_REMOTE_DESKTOP_AUTH, OID_SERVER_AUTH), "RDP"),
        Chain("CHAIN-WEB", CLIENT, WEB_SERVER, ("CERT-WEB", "CERT-CA2-COPY-WEB", "CERT-ROOT"), n.WEB_SITE_DNS_NAME, (OID_SERVER_AUTH,), "TLS server auth"),
    )


def _labels(chains: tuple[Chain, ...]) -> tuple[Label, ...]:
    labels: list[Label] = [
        Label("LBL-HOST-CLIENT", LabelKind.HOST_PLATE, n.CLIENT_HOSTNAME, CLIENT, ("B-01.1",)),
        Label("LBL-HOST-RDP", LabelKind.HOST_PLATE, n.RDP_SERVER_FQDN, RDP_SERVER, ("B-02.1",)),
        Label("LBL-HOST-WEB", LabelKind.HOST_PLATE, n.WEB_SERVER_HOSTNAME, WEB_SERVER, ("B-07.1",)),
        Label("LBL-SITE-WEB", LabelKind.HOST_PLATE, n.WEB_SITE_DNS_NAME, WEB_SERVER, ("B-07.1",)),
        Label("LBL-AD", LabelKind.HOST_PLATE, n.AD_DOMAIN_FQDN, AD, ("B-04.1", "B-07.3")),
        Label("LBL-DC", LabelKind.HOST_PLATE, n.DC_HOSTNAME, AD, ()),
        Label("LBL-PKI", LabelKind.HOST_PLATE, n.PKI_HTTP_HOST, PKI_HTTP, ()),
        Label("LBL-ROOT", LabelKind.CA_NAMEPLATE, n.ROOT_CA_NAME, ROOT_CA, ("B-05.1",)),
        Label("LBL-CA1", LabelKind.CA_NAMEPLATE, n.ISSUING_CA1_NAME, ISSUING_CA1, ("B-04.2", "B-04.3")),
        Label("LBL-CA2", LabelKind.CA_NAMEPLATE, n.ISSUING_CA2_NAME, ISSUING_CA2, ("B-07.3", "B-08.1")),
        Label("LBL-TPL-RDP", LabelKind.TEMPLATE_BADGE, n.RDP_TEMPLATE, "TPL-RDPAUTH", ("B-02.3", "B-04.1")),
        Label("LBL-TPL-WEB", LabelKind.TEMPLATE_BADGE, n.WEB_TEMPLATE, "TPL-WEBTLS", ("B-07.1", "B-07.3")),
        Label("LBL-SELF", LabelKind.CARD_FIELD, "Self-signed", "CERT-RDP-SELF", ("B-02.2",)),
        Label("LBL-UNVERIFIED", LabelKind.TAG, "Unverified", CLIENT, ("B-02.2",)),
        Label("LBL-CONNECT", LabelKind.TAG, f"Connect to {n.RDP_SERVER_FQDN}", CLIENT, ("B-01.1",)),  # the name later matched to the SAN
        Label("LBL-CERT-RDP-SAN", LabelKind.CARD_FIELD, n.RDP_SERVER_FQDN, "CERT-RDP", ("B-04.4",)),
        Label("LBL-CERT-RDP-EKU", LabelKind.CARD_FIELD, n.EKU_REMOTE_DESKTOP_AUTH_NAME, "CERT-RDP", ("B-04.4",)),
        Label("LBL-CERT-WEB-SAN", LabelKind.CARD_FIELD, n.WEB_SITE_DNS_NAME, "CERT-WEB", ("B-08.2",)),
        Label("LBL-CERT-WEB-EKU", LabelKind.CARD_FIELD, n.EKU_SERVER_AUTH_NAME, "CERT-WEB", ("B-08.2",)),
        Label("LBL-FLASHBACK", LabelKind.TAG, "Earlier: offline signing ceremony", ROOT_CA, ("B-05.2",)),
        Label("LBL-KEY-RDP-PRIV", LabelKind.TAG, "Private key", "KEY-RDP-PRIV", ("B-03.1", "B-03.2")),  # V1-PKI-03: name both keys
        Label("LBL-KEY-RDP-PUB", LabelKind.TAG, "Public key", "KEY-RDP-PUB", ("B-03.1",)),
        Label("LBL-KEY-WEB-PRIV", LabelKind.TAG, "Private key", "KEY-WEB-PRIV", ("B-07.2",)),
        Label("LBL-KEY-WEB-PUB", LabelKind.TAG, "Public key", "KEY-WEB-PUB", ("B-07.2",)),
        Label("LBL-REQ-CA1", LabelKind.TAG, f"{n.ISSUING_CA1_ROLE}'s own CA request", "REQ-CA1", ("B-05.2",)),
        Label("LBL-ROOT-STORE", LabelKind.TAG, "Installed earlier by policy", "TS-CLIENT-ROOT", ("B-06.2",)),
        Label("LBL-AIA-1", LabelKind.TAG, "Missing intermediate? AIA can fetch it", "SVC-AIA", ("B-06.3",)),
        Label("LBL-AIA-2", LabelKind.TAG, "Fetching never creates trust", "SVC-AIA", ("B-06.3",)),
        Label("LBL-OCSP", LabelKind.TAG, "OCSP if deployed", "CHAIN-RDP", ("B-06.5",)),
        Label("LBL-CA1-INELIGIBLE", LabelKind.TAG, f"{n.WEB_TEMPLATE} not published here", ISSUING_CA1, ("B-07.3",)),
        Label("LBL-CA2-NOTE", LabelKind.TAG, "Name supplied in request — enrollment restricted", ISSUING_CA2, ("B-08.1",)),
    ]
    for criterion, text in ELIGIBILITY_TEXT.items():
        labels.append(Label(f"LBL-ELIG-{criterion.name}", LabelKind.TAG, text, ISSUING_CA2, ("B-07.3",)))
    for ca_actor, beat in ((ISSUING_CA1, "B-04.3"), (ISSUING_CA2, "B-08.1")):
        for ca_check, text in CA_CHECK_TEXT.items():
            labels.append(Label(f"LBL-{ca_actor}-{ca_check.name}", LabelKind.CHECK, text, ca_actor, (beat,)))
    # every RDP check line is held through B-06.5 while revocation resolves, and is read there too (V1-LEG-03: a line
    # now appears with its own check, so a late check's line would otherwise be readable for under 1.5 s)
    rdp_beats: dict[ValidationCheck, tuple[str, ...]] = {v: ("B-06.4", "B-06.5") for v in ValidationCheck}
    web_on_screen = (ValidationCheck.NAME_MATCH, ValidationCheck.EKU, ValidationCheck.VALIDITY, ValidationCheck.REVOCATION)
    for chain in chains:
        for v_check in ValidationCheck:
            beats: tuple[str, ...]
            if chain.id == "CHAIN-RDP":
                beats = rdp_beats[v_check]
            elif v_check in web_on_screen:
                beats = ("B-09.1",)
            else:
                continue
            labels.append(Label(f"LBL-{chain.id}-{v_check.name}", LabelKind.CHECK, validation_text(v_check, chain), chain.relying_party, beats))
    return tuple(labels)


def _events() -> tuple[Event, ...]:
    T, E = Transport, EventType
    F = Era.FLASHBACK
    ev: list[Event] = [
        # S1
        Event("E-01.1a", "B-01.1", E.USER_INITIATES, "CH-RDP", USER, CLIENT, T.LOCAL),
        Event("E-01.2a", "B-01.2", E.CONNECTION_PULSE, "CH-RDP", CLIENT, RDP_SERVER, T.NETWORK),
        # S2
        Event("E-02.1a", "B-02.1", E.LISTENER_ACTIVATES, "CH-RDP", RDP_SERVER, RDP_SERVER, T.LOCAL),
        Event("E-02.2a", "B-02.2", E.PRESENT_CERT, "CERT-RDP-SELF", RDP_SERVER, CLIENT, T.NETWORK),
        Event("E-02.2b", "B-02.2", E.CLIENT_CANNOT_VERIFY, "CERT-RDP-SELF", CLIENT, CLIENT, T.LOCAL),
        Event("E-02.2c", "B-02.2", E.CONNECTION_CLOSED, "CH-RDP", CLIENT, RDP_SERVER, T.NETWORK),
        Event("E-02.3a", "B-02.3", E.POLICY_ASSIGNS_TEMPLATE, "TPL-RDPAUTH", AD, RDP_SERVER, T.NETWORK),
        # S3
        Event("E-03.1a", "B-03.1", E.KEYPAIR_GENERATED, "KP-RDP", RDP_SERVER, RDP_SERVER, T.LOCAL),
        Event("E-03.2a", "B-03.2", E.PRIVATE_KEY_STORED, "KEY-RDP-PRIV", RDP_SERVER, RDP_SERVER, T.LOCAL),
        Event("E-03.3a", "B-03.3", E.REQUEST_ASSEMBLED, "REQ-RDP", RDP_SERVER, RDP_SERVER, T.LOCAL),
        Event("E-03.4a", "B-03.4", E.PROOF_OF_POSSESSION, "REQ-RDP", RDP_SERVER, RDP_SERVER, T.LOCAL, uses_key="KEY-RDP-PRIV"),
        # S4
        Event("E-04.1a", "B-04.1", E.CA_DISCOVERY_QUERY, "DISC-RDP", RDP_SERVER, AD, T.NETWORK),
        Event("E-04.1b", "B-04.1", E.CA_DISCOVERY_RESULT, "DISC-RDP", AD, RDP_SERVER, T.NETWORK),
        Event("E-04.2a", "B-04.2", E.REQUEST_SUBMITTED, "REQ-RDP", RDP_SERVER, ISSUING_CA1, T.NETWORK),
    ]
    for suffix, ca_check in zip("abcd", CA_CHECK_ORDER, strict=True):
        ev.append(Event(f"E-04.3{suffix}", "B-04.3", E.CA_CHECK, "REQ-RDP", ISSUING_CA1, ISSUING_CA1, T.LOCAL, check=ca_check))
    ev += [
        Event("E-04.4a", "B-04.4", E.REQUEST_CONSUMED, "REQ-RDP", ISSUING_CA1, ISSUING_CA1, T.LOCAL),
        Event("E-04.4b", "B-04.4", E.CA_SIGNS, "CERT-RDP", ISSUING_CA1, ISSUING_CA1, T.LOCAL, uses_key="KEY-CA1-PRIV"),
        Event("E-04.5a", "B-04.5", E.CERT_RETURNED, "CERT-RDP", ISSUING_CA1, RDP_SERVER, T.NETWORK),
        Event("E-04.5b", "B-04.5", E.CERT_INSTALLED, "CERT-RDP", RDP_SERVER, RDP_SERVER, T.LOCAL),
        Event("E-04.5c", "B-04.5", E.INTERMEDIATE_STORED, "CERT-CA1-COPY-RDP", ISSUING_CA1, RDP_SERVER, T.NETWORK, note="Copy returned with the enrollment response chain"),
        # S5
        Event("E-05.1a", "B-05.1", E.SELF_SIGNATURE_SHOWN, "CERT-ROOT", ROOT_CA, ROOT_CA, T.NONE),
        Event("E-05.2a", "B-05.2", E.PROOF_OF_POSSESSION, "REQ-CA1", ISSUING_CA1, ISSUING_CA1, T.LOCAL, uses_key="KEY-CA1-PRIV", era=F),
        Event("E-05.2b", "B-05.2", E.OFFLINE_CARRY, "REQ-CA1", ISSUING_CA1, ROOT_CA, T.OFFLINE_MEDIA, era=F),
        Event("E-05.2c", "B-05.2", E.REQUEST_CONSUMED, "REQ-CA1", ROOT_CA, ROOT_CA, T.LOCAL, era=F),
        Event("E-05.2d", "B-05.2", E.CA_SIGNS, "CERT-CA1", ROOT_CA, ROOT_CA, T.LOCAL, uses_key="KEY-ROOT-PRIV", era=F),
        Event("E-05.2e", "B-05.2", E.OFFLINE_CARRY, "CERT-CA1", ROOT_CA, ISSUING_CA1, T.OFFLINE_MEDIA, era=F),
        Event("E-05.2f", "B-05.2", E.CERT_INSTALLED, "CERT-CA1", ISSUING_CA1, ISSUING_CA1, T.LOCAL, era=F),
        Event("E-05.3a", "B-05.3", E.ISSUER_LINK, "CERT-CA1", ROOT_CA, ISSUING_CA1, T.LOGICAL),
        # S6
        Event("E-06.1a", "B-06.1", E.CONNECTION_PULSE, "CH-RDP", CLIENT, RDP_SERVER, T.NETWORK),
        Event("E-06.1b", "B-06.1", E.PRESENT_CERT, "CERT-RDP", RDP_SERVER, CLIENT, T.NETWORK),
        Event("E-06.1c", "B-06.1", E.PRESENT_CERT, "CERT-CA1-COPY-RDP", RDP_SERVER, CLIENT, T.NETWORK),
        Event("E-06.1d", "B-06.1", E.HANDSHAKE_SIGNATURE, "HS-RDP", RDP_SERVER, RDP_SERVER, T.LOCAL, uses_key="KEY-RDP-PRIV"),
        Event("E-06.1e", "B-06.1", E.HANDSHAKE_PROOF_SENT, "HS-RDP", RDP_SERVER, CLIENT, T.NETWORK),
        Event("E-06.1f", "B-06.1", E.HANDSHAKE_PROOF_VERIFIED, "HS-RDP", CLIENT, CLIENT, T.LOCAL, target="CERT-RDP"),
        Event("E-06.2a", "B-06.2", E.CHAIN_LINK, "CERT-RDP", CLIENT, CLIENT, T.LOCAL, target="CERT-CA1-COPY-RDP"),
        Event("E-06.2b", "B-06.2", E.CHAIN_LINK, "CERT-CA1-COPY-RDP", CLIENT, CLIENT, T.LOCAL, target="CERT-ROOT"),
        Event("E-06.2c", "B-06.2", E.TRUST_STORE_RECALL, "TS-CLIENT-ROOT", AD, CLIENT, T.NONE, era=Era.RECALL),
        Event("E-06.3a", "B-06.3", E.AIA_INDICATOR, "SVC-AIA", CLIENT, PKI_HTTP, T.NONE, target="CERT-CA1", conditional=True),
    ]
    for suffix, v_check in zip("abcde", VALIDATION_ORDER[:5], strict=True):
        ev.append(Event(f"E-06.4{suffix}", "B-06.4", E.VALIDATION_CHECK, "CHAIN-RDP", CLIENT, CLIENT, T.LOCAL, check=v_check))
    ev += [
        Event("E-06.4f", "B-06.4", E.VALIDATION_PENDING, "CHAIN-RDP", CLIENT, CLIENT, T.LOCAL, check=ValidationCheck.REVOCATION),
        Event("E-06.5a", "B-06.5", E.CRL_FETCH, "CRL-CA1", CLIENT, PKI_HTTP, T.NETWORK, target="CERT-RDP"),
        Event("E-06.5b", "B-06.5", E.CRL_FETCH, "CRL-ROOT", CLIENT, PKI_HTTP, T.NETWORK, target="CERT-CA1-COPY-RDP"),
        Event("E-06.5c", "B-06.5", E.OCSP_NOTE, "SVC-OCSP", CLIENT, CLIENT, T.NONE, conditional=True),
        Event("E-06.5d", "B-06.5", E.VALIDATION_CHECK, "CHAIN-RDP", CLIENT, CLIENT, T.LOCAL, check=ValidationCheck.REVOCATION),
        Event("E-06.6a", "B-06.6", E.SESSION_ESTABLISHED, "CH-RDP", CLIENT, RDP_SERVER, T.NETWORK),
        # S7
        Event("E-07.1a", "B-07.1", E.TEMPLATE_SELECTED, "TPL-WEBTLS", WEB_SERVER, WEB_SERVER, T.LOCAL),
        Event("E-07.2a", "B-07.2", E.KEYPAIR_GENERATED, "KP-WEB", WEB_SERVER, WEB_SERVER, T.LOCAL),
        Event("E-07.2b", "B-07.2", E.PRIVATE_KEY_STORED, "KEY-WEB-PRIV", WEB_SERVER, WEB_SERVER, T.LOCAL),
        Event("E-07.2c", "B-07.2", E.REQUEST_ASSEMBLED, "REQ-WEB", WEB_SERVER, WEB_SERVER, T.LOCAL),
        Event("E-07.2d", "B-07.2", E.PROOF_OF_POSSESSION, "REQ-WEB", WEB_SERVER, WEB_SERVER, T.LOCAL, uses_key="KEY-WEB-PRIV"),
        Event("E-07.3a", "B-07.3", E.CA_DISCOVERY_QUERY, "DISC-WEB", WEB_SERVER, AD, T.NETWORK),
        Event("E-07.3b", "B-07.3", E.CA_DISCOVERY_RESULT, "DISC-WEB", AD, WEB_SERVER, T.NETWORK),
        Event("E-07.4a", "B-07.4", E.REQUEST_SUBMITTED, "REQ-WEB", WEB_SERVER, ISSUING_CA2, T.NETWORK),
    ]
    for suffix, ca_check in zip("abcd", CA_CHECK_ORDER, strict=True):
        note = "Name supplied in request — enrollment restricted" if ca_check == CaCheck.ENROLL_PERMISSION else None
        ev.append(Event(f"E-08.1{suffix}", "B-08.1", E.CA_CHECK, "REQ-WEB", ISSUING_CA2, ISSUING_CA2, T.LOCAL, check=ca_check, note=note))
    V = ValidationCheck
    ev += [
        Event("E-08.2a", "B-08.2", E.REQUEST_CONSUMED, "REQ-WEB", ISSUING_CA2, ISSUING_CA2, T.LOCAL),
        Event("E-08.2b", "B-08.2", E.CA_SIGNS, "CERT-WEB", ISSUING_CA2, ISSUING_CA2, T.LOCAL, uses_key="KEY-CA2-PRIV"),
        Event("E-08.2c", "B-08.2", E.CERT_RETURNED, "CERT-WEB", ISSUING_CA2, WEB_SERVER, T.NETWORK),
        Event("E-08.2d", "B-08.2", E.CERT_INSTALLED, "CERT-WEB", WEB_SERVER, WEB_SERVER, T.LOCAL),
        Event("E-08.2e", "B-08.2", E.INTERMEDIATE_STORED, "CERT-CA2-COPY-WEB", ISSUING_CA2, WEB_SERVER, T.NETWORK, note="Copy returned with the enrollment response chain"),
        Event("E-08.3a", "B-08.3", E.ISSUER_LINK, "CERT-CA2", ROOT_CA, ISSUING_CA2, T.LOGICAL),
        # S9
        Event("E-09.1a", "B-09.1", E.CONNECTION_PULSE, "CH-WEB", CLIENT, WEB_SERVER, T.NETWORK),
        Event("E-09.1b", "B-09.1", E.PRESENT_CERT, "CERT-WEB", WEB_SERVER, CLIENT, T.NETWORK),
        Event("E-09.1c", "B-09.1", E.PRESENT_CERT, "CERT-CA2-COPY-WEB", WEB_SERVER, CLIENT, T.NETWORK),
        Event("E-09.1d", "B-09.1", E.HANDSHAKE_SIGNATURE, "HS-WEB", WEB_SERVER, WEB_SERVER, T.LOCAL, uses_key="KEY-WEB-PRIV"),
        Event("E-09.1e", "B-09.1", E.HANDSHAKE_PROOF_SENT, "HS-WEB", WEB_SERVER, CLIENT, T.NETWORK),
        Event("E-09.1q", "B-09.1", E.HANDSHAKE_PROOF_VERIFIED, "HS-WEB", CLIENT, CLIENT, T.LOCAL, target="CERT-WEB"),
        Event("E-09.1f", "B-09.1", E.CHAIN_LINK, "CERT-WEB", CLIENT, CLIENT, T.LOCAL, target="CERT-CA2-COPY-WEB"),
        Event("E-09.1g", "B-09.1", E.CHAIN_LINK, "CERT-CA2-COPY-WEB", CLIENT, CLIENT, T.LOCAL, target="CERT-ROOT"),
        Event("E-09.1h", "B-09.1", E.VALIDATION_CHECK, "CHAIN-WEB", CLIENT, CLIENT, T.LOCAL, check=V.CHAIN_TO_TRUSTED_ROOT, on_screen=False),
        Event("E-09.1i", "B-09.1", E.VALIDATION_CHECK, "CHAIN-WEB", CLIENT, CLIENT, T.LOCAL, check=V.SIGNATURES, on_screen=False),
        Event("E-09.1j", "B-09.1", E.VALIDATION_CHECK, "CHAIN-WEB", CLIENT, CLIENT, T.LOCAL, check=V.NAME_MATCH),
        Event("E-09.1k", "B-09.1", E.VALIDATION_CHECK, "CHAIN-WEB", CLIENT, CLIENT, T.LOCAL, check=V.EKU),
        Event("E-09.1l", "B-09.1", E.VALIDATION_CHECK, "CHAIN-WEB", CLIENT, CLIENT, T.LOCAL, check=V.VALIDITY),
        Event("E-09.1m", "B-09.1", E.CRL_FETCH, "CRL-CA2", CLIENT, PKI_HTTP, T.NETWORK, target="CERT-WEB"),
        Event("E-09.1n", "B-09.1", E.CRL_FETCH, "CRL-ROOT", CLIENT, PKI_HTTP, T.NETWORK, target="CERT-CA2-COPY-WEB"),
        Event("E-09.1o", "B-09.1", E.VALIDATION_CHECK, "CHAIN-WEB", CLIENT, CLIENT, T.LOCAL, check=V.REVOCATION),
        Event("E-09.1p", "B-09.1", E.SESSION_ESTABLISHED, "CH-WEB", CLIENT, WEB_SERVER, T.NETWORK),
        Event("E-09.2a", "B-09.2", E.TRUST_PATH_REVEAL, "CHAIN-RDP", None, None, T.LOGICAL),
        Event("E-09.2b", "B-09.2", E.TRUST_PATH_REVEAL, "CHAIN-WEB", None, None, T.LOGICAL),
        Event("E-09.3a", "B-09.3", E.FINAL_FADE, "WORLD", None, None, T.NONE),
    ]
    return tuple(ev)


def build_model() -> StoryModel:
    key_pairs, keys = _key_material()
    chains = _chains()
    return StoryModel(
        scenes=SCENES,
        beats=_beats(),
        actors=_actors(),
        key_pairs=key_pairs,
        keys=keys,
        certificates=_certificates(),
        crls=_crls(),
        templates=_templates(),
        cas=_cas(),
        requests=_requests(),
        discoveries=_discoveries(),
        chains=chains,
        channels=(
            Channel("CH-RDP", CLIENT, RDP_SERVER, "RDP over TLS"),
            Channel("CH-WEB", CLIENT, WEB_SERVER, "HTTPS (TLS)"),
        ),
        handshake_proofs=(
            HandshakeProof("HS-RDP", RDP_SERVER, "KEY-RDP-PRIV", "KEY-RDP-PUB"),
            HandshakeProof("HS-WEB", WEB_SERVER, "KEY-WEB-PRIV", "KEY-WEB-PUB"),
        ),
        services=(
            Service("SVC-AIA", ServiceKind.AIA, PKI_HTTP, deployed=True),
            Service("SVC-CDP", ServiceKind.CDP, PKI_HTTP, deployed=True),
            Service("SVC-OCSP", ServiceKind.OCSP, None, deployed=False),
        ),
        trust_store=(
            TrustStoreEntry("TS-CLIENT-ROOT", CLIENT, "CERT-ROOT", STORE_TRUSTED_ROOT, AD, installed_before_film=True),
        ),
        world_objects=(WorldObject("WORLD", "The whole stage, for the final settle and fade"),),
        labels=_labels(chains),
        events=_events(),
    )


MODEL = build_model()
