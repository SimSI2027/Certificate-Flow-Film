"""The stage catalogue: every object that exists in the 3D world, as pure data.

Blender builders (``blender/actors``) turn each ``StageObject`` into geometry by ``kind``. Object ids reuse
story-model ids wherever the model has a record (actors, certificates, keys, requests, templates, CRLs ...),
so scene checks and traceability can join Blender objects back to the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cff.stage import layout as lo
from cff.stage.layout import Vec3
from cff.story import model as m
from cff.story.model import ColourRole


class Kind(StrEnum):
    # shape vocabulary (C-11)
    CAPSULE = "request_capsule"
    CARD = "certificate_card"
    KEY_PUBLIC = "public_key"
    KEY_PRIVATE = "private_key"
    CONTAINER = "key_container"
    BADGE = "template_badge"
    CA_VAULT = "ca_vault"
    ROOT_VAULT = "root_vault"
    TRUST_LINK = "trust_link"
    CHANNEL = "network_channel"
    TICK = "validation_tick"
    SCROLL = "crl_scroll"
    AIA = "aia_indicator"
    PROOF = "handshake_proof"
    # actors and props
    DESK = "desk"
    LAPTOP = "laptop"
    FIGURE = "figure"
    CHASSIS = "chassis"
    PANEL = "panel"
    PORT = "port"
    CONTAINER_LID = "container_lid"
    LOCK = "lock"
    CLAMP = "clamp"
    AD_COLUMN = "ad_column"
    RING = "ring"
    KIOSK = "kiosk"
    EVAL_CRADLE = "eval_cradle"
    MODULE = "key_module"
    PRESS = "press"
    PRESS_HEAD = "press_head"
    LINK_ROD = "link_rod"
    CROWN = "crown"
    TRIM = "trim"
    PLINTH = "plinth"
    DAIS = "dais"
    SEAL = "seal"
    READER = "reader"
    TILE = "info_tile"
    BEAM = "beam"
    SEAL_RING = "seal_ring"
    ROUTE = "route_segment"
    PULSE = "pulse"
    QUERY = "query_pulse"
    CARTRIDGE = "cartridge"
    FOOTPRINT = "footprint"
    BAND = "ca_band"
    SCREEN = "screen_window"
    CRADLE = "root_cradle"


@dataclass(frozen=True)
class StageObject:
    id: str
    kind: Kind
    role: ColourRole
    home: Vec3
    yaw: float = 0.0  # degrees about Z
    size: Vec3 = (1.0, 1.0, 1.0)
    variant: str = ""
    owner: str | None = None  # model actor id (for bounds checks)
    on_stage: bool = True  # False: hidden (scale HIDDEN_SCALE) until an entrance
    points: tuple[Vec3, ...] = ()  # for channels, routes, links and beams: the polyline or end points
    spec_ids: tuple[str, ...] = ()  # criteria and facts this object helps show
    euler: Vec3 | None = None  # XYZ Euler degrees when the object is aimed; otherwise (0, 0, yaw)
    full: Vec3 = (1.0, 1.0, 1.0)  # scale when fully shown (links and beams stretch to their length)

    @property
    def rotation(self) -> Vec3:
        return self.euler if self.euler is not None else (0.0, 0.0, self.yaw)


def _link(object_id: str, role: ColourRole, start: Vec3, end: Vec3, width: float, variant: str, ids: tuple[str, ...]) -> StageObject:
    """A trust link: unit-length bar along +X, stretched to the start-end distance when fully grown."""
    return StageObject(object_id, Kind.TRUST_LINK, role, start, size=(1.0, width, width), points=(start, end), variant=variant,
                       on_stage=False, spec_ids=ids, euler=lo.aim_x(start, end), full=(lo.dist(start, end), 1.0, 1.0))


def _beam(object_id: str, role: ColourRole, start: Vec3, end: Vec3, width: float, ids: tuple[str, ...] = ()) -> StageObject:
    """A beam of light: unit-length bar along +Z, stretched to the start-end distance when fully shown."""
    return StageObject(object_id, Kind.BEAM, role, start, size=(width, width, 1.0), points=(start, end), on_stage=False, spec_ids=ids,
                       euler=lo.aim_z(start, end), full=(1.0, 1.0, lo.dist(start, end)))


def _chassis(suffix: str, actor: str, base: Vec3, port_side: float, template_id: str) -> list[StageObject]:
    out = [
        StageObject(actor, Kind.CHASSIS, ColourRole.NEUTRAL, base, size=lo.CHASSIS_SIZE, owner=actor, spec_ids=("F-01",)),
        StageObject(f"PANEL-{suffix}", Kind.PANEL, ColourRole.NEUTRAL,
                    lo.add(base, (-lo.CHASSIS_SIZE[0] / 2, lo.FRONT_Y, 0.05)), size=(lo.CHASSIS_SIZE[0], 0.05, lo.CHASSIS_SIZE[2] - 0.1), owner=actor),
        StageObject(f"PORT-{suffix}-LISTEN", Kind.PORT, ColourRole.NEUTRAL, lo.add(base, lo.LISTENER_PORT), size=(0.22, 0.05, 0.22), owner=actor),
        StageObject(f"PORT-{suffix}-OUT", Kind.PORT, ColourRole.NEUTRAL, lo.port_surface(base, port_side),
                    yaw=90.0 * port_side, size=(0.22, 0.05, 0.22), owner=actor),
        StageObject(f"KC-{suffix}", Kind.CONTAINER, ColourRole.NEUTRAL, lo.add(base, lo.CONTAINER), size=(0.5, 0.42, 0.4), owner=actor, on_stage=False, spec_ids=("F-03",)),
        StageObject(f"KCLID-{suffix}", Kind.CONTAINER_LID, ColourRole.NEUTRAL, lo.add(base, (lo.CONTAINER[0] - 0.25, lo.CONTAINER[1], lo.CONTAINER[2] + 0.2)),
                    size=(0.5, 0.42, 0.04), owner=actor, on_stage=False),
        StageObject(f"LOCK-{suffix}", Kind.LOCK, ColourRole.NEUTRAL, lo.add(base, (lo.CONTAINER[0], lo.CONTAINER[1] - 0.22, lo.CONTAINER[2])), size=(0.12, 0.05, 0.12), owner=actor, on_stage=False),
        StageObject(f"CLAMP-{suffix}-L", Kind.CLAMP, ColourRole.NEUTRAL, lo.add(base, (lo.CONTAINER[0] - 0.42, lo.CONTAINER[1], lo.CONTAINER[2] - 0.1)), size=(0.14, 0.1, 0.1), owner=actor, on_stage=False),
        StageObject(f"CLAMP-{suffix}-R", Kind.CLAMP, ColourRole.NEUTRAL, lo.add(base, (lo.CONTAINER[0] + 0.42, lo.CONTAINER[1], lo.CONTAINER[2] - 0.1)), size=(0.14, 0.1, 0.1), owner=actor, on_stage=False),
        StageObject(template_id, Kind.BADGE, ColourRole.NEUTRAL, lo.add(base, lo.TOP_PLATE), size=(0.62, 0.34, 0.06), on_stage=False, spec_ids=("F-05",)),
    ]
    return out


def _ca_vault(actor: str, tag: str, base: Vec3, role: ColourRole, cert: str, key_priv: str) -> list[StageObject]:
    cradle = lo.add(base, lo.CA_CRADLE)
    module = lo.add(base, lo.CA_MODULE)
    press = lo.add(base, lo.CA_PRESS)
    out = [
        StageObject(actor, Kind.CA_VAULT, role, base, size=lo.CA_VAULT_SIZE, owner=actor, variant="open_front", spec_ids=("AR-03",)),
        StageObject(f"TRIM-{tag}", Kind.TRIM, role, lo.add(base, (0.0, lo.CA_FRONT_Y - 0.03, 1.4)), size=(lo.CA_VAULT_SIZE[0], 0.06, lo.CA_VAULT_SIZE[2]), owner=actor),
        StageObject(f"EVAL-{tag}", Kind.EVAL_CRADLE, ColourRole.NEUTRAL, cradle, size=(0.9, 0.7, 0.5), owner=actor),
        StageObject(f"MODULE-{tag}", Kind.MODULE, role, module, size=(0.8, 0.7, 0.8), owner=actor, variant="sealed", spec_ids=("F-03",)),
        StageObject(key_priv, Kind.KEY_PRIVATE, role, module, size=(lo.KEY_SIZE,) * 3, owner=actor, variant="ca_key", spec_ids=("F-03",)),
        StageObject(f"PRESS-{tag}", Kind.PRESS, ColourRole.NEUTRAL, press, size=(0.9, 0.9, 0.8), owner=actor),
        StageObject(f"PRESSHEAD-{tag}", Kind.PRESS_HEAD, role, lo.add(press, (0.0, 0.0, 0.85)), size=(0.5, 0.5, 0.2), owner=actor),
        StageObject(f"LINK-{tag}", Kind.LINK_ROD, role, lo.add(base, (-0.05, 0.6, 1.9)), size=(1.7, 0.08, 0.08), owner=actor),
        StageObject(f"CROWN-{tag}", Kind.CROWN, ColourRole.NEUTRAL, lo.add(base, lo.CA_CROWN), size=(1.0, 0.5, 0.18), owner=actor),
        StageObject(cert, Kind.CARD, role, lo.add(base, (0.0, 0.0, lo.CA_CROWN[2] + 0.42)), size=lo.CARD_SIZE, owner=actor, variant="ca_cert", spec_ids=("AR-03",)),
    ]
    return out


def _check_slots(prefix: str, count: int, base: Vec3, step: float, role: ColourRole, pending_last: bool = False) -> list[StageObject]:
    out = []
    for i in range(count):
        letter = "abcdefgh"[i]
        variant = "pending" if pending_last and i == count - 1 else "check"
        out.append(StageObject(f"TICK-{prefix}-{letter}", Kind.TICK, role, lo.add(base, (0.0, 0.0, step * (count - 1 - i))),
                               size=(0.2, 0.05, 0.2), variant=variant, on_stage=False, spec_ids=("F-06" if prefix.startswith("CA") else "F-12",)))
    return out


def build_catalogue() -> tuple[StageObject, ...]:
    R = ColourRole
    objs: list[StageObject] = []

    # --- client cluster ---------------------------------------------------------------------
    objs += [
        StageObject("DESK", Kind.DESK, R.NEUTRAL, (-12.0, -8.0, 0.0), size=(1.8, 1.2, 0.76)),
        StageObject(m.CLIENT, Kind.LAPTOP, R.NEUTRAL, lo.LAPTOP, size=(0.5, 0.36, 0.3), owner=m.CLIENT),
        StageObject(m.USER, Kind.FIGURE, R.NEUTRAL, lo.USER, yaw=180.0, size=(0.5, 0.4, 1.25), owner=m.USER),
        StageObject("SCREEN-IDLE", Kind.SCREEN, R.NEUTRAL, (-12.2, -8.0, 0.92), yaw=90.0, size=(0.46, 0.01, 0.27), variant="idle"),
        StageObject("SCREEN-RDP", Kind.SCREEN, R.NEUTRAL, lo.SCREEN_CENTRE, yaw=90.0, size=(0.9, 0.02, 0.56), variant="session", on_stage=False),
        StageObject("SCREEN-WEB", Kind.SCREEN, R.NEUTRAL, lo.SCREEN_CENTRE, yaw=90.0, size=(0.9, 0.02, 0.56), variant="browser", on_stage=False),
        StageObject("TS-CLIENT-ROOT", Kind.CRADLE, R.NEUTRAL, lo.CRADLE_ROOT, size=(0.9, 0.12, 0.62), spec_ids=("AR-05",)),
        StageObject("CERT-ROOT", Kind.CARD, R.ROOT, lo.add(lo.CRADLE_ROOT, (0.0, 0.0, 0.0)), size=lo.CARD_SIZE, variant="root_cert", spec_ids=("AR-01", "F-11")),
    ]

    # --- channels (floor conduits) and the CA routes, as segments ------------------------------
    for tag, points in (("RDP", lo.CHANNEL_RDP), ("WEB", lo.CHANNEL_WEB)):
        for i, (a, b) in enumerate(zip(points, points[1:], strict=False), start=1):
            objs.append(StageObject(f"CH-{tag}-S{i}", Kind.CHANNEL, R.PENDING, a, size=(lo.dist(a, b), 0.22, 0.04), points=(a, b),
                                    euler=lo.aim_x(a, b), spec_ids=("C-01",)))
    for tag, points, role in (("CA1", lo.ROUTE_CA1, R.ISSUING_CA1), ("CA2", lo.ROUTE_CA2, R.ISSUING_CA2)):
        for i, (a, b) in enumerate(zip(points, points[1:], strict=False), start=1):
            objs.append(StageObject(f"ROUTE-{tag}-S{i}", Kind.ROUTE, role, a, size=(lo.dist(a, b), 0.16, 0.03), points=(a, b),
                                    euler=lo.aim_x(a, b), spec_ids=("F-05",)))

    # --- servers --------------------------------------------------------------------------------
    objs += _chassis("RDP", m.RDP_SERVER, lo.RDP, lo.RDP_PORT_SIDE, "TPL-RDPAUTH")
    objs += _chassis("WEB", m.WEB_SERVER, lo.WEB, lo.WEB_PORT_SIDE, "TPL-WEBTLS")
    for tag, base in (("RDP", lo.RDP), ("WEB", lo.WEB)):
        objs += [
            StageObject(f"KEY-{tag}-PRIV", Kind.KEY_PRIVATE, R.NEUTRAL, lo.add(base, lo.KEY_FORM_PRIV), size=(lo.KEY_SIZE,) * 3, owner=f"{tag}_SERVER", on_stage=False, spec_ids=("F-03",)),
            StageObject(f"KEY-{tag}-PUB", Kind.KEY_PUBLIC, R.REQUEST, lo.add(base, lo.KEY_FORM_PUB), size=(lo.KEY_SIZE,) * 3, owner=f"{tag}_SERVER", on_stage=False),
            StageObject(f"REQ-{tag}", Kind.CAPSULE, R.REQUEST, lo.add(base, lo.CAPSULE_SPOT), size=(lo.CAPSULE_LENGTH, lo.CAPSULE_RADIUS, lo.CAPSULE_RADIUS), owner=f"{tag}_SERVER", on_stage=False, spec_ids=("F-04",)),
            StageObject(f"TILE-{tag}", Kind.TILE, R.REQUEST, lo.add(base, (0.0, 0.4, 1.95)), size=(0.2, 0.02, 0.14), on_stage=False),
            _beam(f"BEAM-{tag}", R.REQUEST, lo.add(base, (lo.CONTAINER[0], lo.CONTAINER[1], lo.CONTAINER[2] + 0.22)),
                  lo.add(base, (lo.CAPSULE_SPOT[0], lo.CAPSULE_SPOT[1], lo.CAPSULE_SPOT[2] - 0.08)), 0.04, ("F-03", "F-04")),
            StageObject(f"SEAL-{tag}", Kind.SEAL_RING, R.REQUEST, lo.add(base, lo.CAPSULE_SPOT), size=(0.3, 0.3, 0.05), on_stage=False),
            StageObject(f"QUERY-{tag}", Kind.QUERY, R.DIRECTORY, lo.port_wait(base, lo.RDP_PORT_SIDE if tag == "RDP" else lo.WEB_PORT_SIDE), size=(0.16, 0.16, 0.16), on_stage=False, spec_ids=("AR-05",)),
            StageObject(f"HS-{tag}", Kind.PROOF, R.REQUEST, lo.add(base, (lo.CONTAINER[0], lo.CONTAINER[1], lo.CONTAINER[2] + 0.5)), size=(0.34, 0.03, 0.2), on_stage=False, spec_ids=("F-10",)),
        ]

    # --- certificates and request artefacts -----------------------------------------------------
    pale = R.NEUTRAL
    objs += [
        StageObject("CERT-RDP-SELF", Kind.CARD, pale, lo.add(lo.RDP, lo.LISTENER_PORT), size=lo.CARD_SIZE, variant="self_signed", on_stage=False, spec_ids=("F-02",)),
        StageObject("CERT-RDP", Kind.CARD, R.ISSUING_CA1, lo.add(lo.RDP, lo.CERT_SLOT), size=lo.CARD_SIZE, variant="end_entity", on_stage=False, spec_ids=("F-07", "F-08")),
        StageObject("CERT-WEB", Kind.CARD, R.ISSUING_CA2, lo.add(lo.WEB, lo.CERT_SLOT), size=lo.CARD_SIZE, variant="end_entity", on_stage=False, spec_ids=("F-07", "F-08")),
        StageObject("CERT-CA1-COPY-RDP", Kind.CARD, R.ISSUING_CA1, lo.add(lo.RDP, lo.INTERMEDIATE_SLOT), size=lo.CARD_SIZE, variant="copy", on_stage=False, spec_ids=("F-10",)),
        StageObject("CERT-CA2-COPY-WEB", Kind.CARD, R.ISSUING_CA2, lo.add(lo.WEB, lo.INTERMEDIATE_SLOT), size=lo.CARD_SIZE, variant="copy", on_stage=False, spec_ids=("F-10",)),
        StageObject("AIA-RDP", Kind.AIA, R.NEUTRAL, lo.add(lo.STACK_CERT, (0.42, 0.0, 0.0)), size=(0.16, 0.05, 0.16), on_stage=False, spec_ids=("F-11",)),
        StageObject("REQ-CA1", Kind.CAPSULE, R.REQUEST, lo.add(lo.CA1, lo.CA_MODULE), size=(lo.CAPSULE_LENGTH, lo.CAPSULE_RADIUS, lo.CAPSULE_RADIUS), owner=m.ISSUING_CA1, on_stage=False, variant="ca_request", spec_ids=("AR-02",)),
        StageObject("BAND-CA1", Kind.BAND, R.ISSUING_CA1, lo.add(lo.CA1, lo.CA_MODULE), size=(0.1, 0.12, 0.12), on_stage=False, spec_ids=("AR-02",)),
        _beam("BEAM-CA1", R.ISSUING_CA1, lo.add(lo.CA1, (lo.CA_MODULE[0], lo.CA_MODULE[1], lo.CA_MODULE[2] + 0.42)),
              lo.add(lo.CA1, (lo.CA_MODULE[0], lo.CA_MODULE[1] - 0.5, lo.CA_MODULE[2] + 0.55)), 0.04),
    ]

    # --- CA vaults ------------------------------------------------------------------------------
    objs += _ca_vault(m.ISSUING_CA1, "CA1", lo.CA1, R.ISSUING_CA1, "CERT-CA1", "KEY-CA1-PRIV")
    objs += _ca_vault(m.ISSUING_CA2, "CA2", lo.CA2, R.ISSUING_CA2, "CERT-CA2", "KEY-CA2-PRIV")
    objs += _check_slots("CA1", 4, lo.add(lo.CA1, (-1.4, 1.2, 1.15)), 0.34, R.ISSUING_CA1)
    objs += _check_slots("CA2", 4, lo.add(lo.CA2, (-1.4, 1.2, 1.15)), 0.34, R.ISSUING_CA2)

    # --- directory, publication point -----------------------------------------------------------
    objs += [
        StageObject(m.AD, Kind.AD_COLUMN, R.DIRECTORY, lo.AD, size=(lo.AD_RADIUS, lo.AD_RADIUS, lo.AD_HEIGHT), owner=m.AD, spec_ids=("AR-05",)),
        StageObject("RING-AD-1", Kind.RING, R.ISSUING_CA1, lo.add(lo.AD, (0.0, 0.0, 2.2)), size=(1.15, 1.15, 0.07), on_stage=False, owner=m.AD),
        StageObject("RING-AD-2", Kind.RING, R.ISSUING_CA2, lo.add(lo.AD, (0.0, 0.0, 2.8)), size=(1.15, 1.15, 0.07), on_stage=False, owner=m.AD),
        StageObject(m.PKI_HTTP, Kind.KIOSK, R.NEUTRAL, lo.KIOSK, size=(0.9, 0.7, 1.5), owner=m.PKI_HTTP, spec_ids=("AR-06",)),
    ]

    # --- root complex (rises in B-05.1) --------------------------------------------------------
    rz = lo.ROOT_DAIS_Z
    objs += [
        StageObject("ROOT-DAIS", Kind.DAIS, R.ROOT, (lo.ROOT[0], lo.ROOT[1] - 1.2, 0.0), size=(lo.ROOT_DAIS_RADIUS, lo.ROOT_DAIS_RADIUS, rz), on_stage=False, owner=m.ROOT_CA),
        StageObject("ROOT-PLINTH", Kind.PLINTH, R.ROOT, (lo.ROOT[0], lo.ROOT[1], rz), size=lo.ROOT_PLINTH_SIZE, on_stage=False, owner=m.ROOT_CA),
        StageObject(m.ROOT_CA, Kind.ROOT_VAULT, R.ROOT, lo.ROOT_VAULT_CENTRE, size=lo.ROOT_VAULT_SIZE, on_stage=False, owner=m.ROOT_CA, spec_ids=("AR-01",)),
        StageObject("SEAL-ROOT", Kind.SEAL, R.ROOT, lo.ROOT_SEAL, size=(0.5, 0.5, 0.06), on_stage=False, owner=m.ROOT_CA, spec_ids=("AR-01",)),
        StageObject("READER-ROOT", Kind.READER, R.ROOT, lo.ROOT_READER, size=(0.5, 0.5, 0.9), on_stage=False, owner=m.ROOT_CA),
        StageObject("PRESS-ROOT", Kind.PRESS, R.NEUTRAL, lo.ROOT_PRESS, size=(0.9, 0.9, 0.8), on_stage=False, owner=m.ROOT_CA),
        StageObject("PRESSHEAD-ROOT", Kind.PRESS_HEAD, R.ROOT, lo.add(lo.ROOT_PRESS, (0.0, 0.0, 0.85)), size=(0.5, 0.5, 0.2), on_stage=False, owner=m.ROOT_CA),
        StageObject("MODULE-ROOT", Kind.MODULE, R.ROOT, lo.ROOT_MODULE, size=(0.8, 0.7, 0.8), on_stage=False, owner=m.ROOT_CA, variant="sealed"),
        StageObject("KEY-ROOT-PRIV", Kind.KEY_PRIVATE, R.ROOT, lo.ROOT_MODULE, size=(lo.KEY_SIZE,) * 3, on_stage=False, owner=m.ROOT_CA, variant="ca_key"),
        StageObject("CARTRIDGE", Kind.CARTRIDGE, R.NEUTRAL, lo.WALKWAY[0], size=(0.3, 0.2, 0.12), on_stage=False, spec_ids=("AR-02",)),
    ]
    for i in range(lo.FOOTPRINT_COUNT):
        fraction = (i + 0.5) / lo.FOOTPRINT_COUNT
        pos = lo.point_along(lo.WALKWAY, fraction)
        objs.append(StageObject(f"FOOT-{i + 1:02d}", Kind.FOOTPRINT, R.NEUTRAL, (pos[0] + (0.14 if i % 2 else -0.14), pos[1], pos[2] + 0.02),
                                yaw=-25.0, size=(0.16, 0.34, 0.01), on_stage=False))

    # --- trust links (light, not cable) --------------------------------------------------------
    crown1 = lo.add(lo.CA1, (0.0, 0.0, lo.CA_CROWN[2] + 0.42))
    crown2 = lo.add(lo.CA2, (0.0, 0.0, lo.CA_CROWN[2] + 0.42))
    root_link_start = (lo.ROOT[0], lo.ROOT[1] - lo.ROOT_VAULT_SIZE[1] / 2 - 0.05, lo.ROOT_VAULT_Z + 0.3)
    objs += [
        _link("TL-CA1", R.ROOT, root_link_start, lo.add(crown1, (0.0, 0.0, -0.3)), 0.07, "gold_to_cyan", ("F-15",)),
        _link("TL-CA2", R.ROOT, root_link_start, lo.add(crown2, (0.0, 0.0, -0.3)), 0.07, "gold_to_violet", ("F-15",)),
        _link("TP-RDP", R.ISSUING_CA1, lo.add(lo.RDP, (0.0, 0.0, 2.3)), lo.add(crown1, (0.0, -0.3, -0.3)), 0.05, "cyan", ("F-14",)),
        _link("TP-WEB", R.ISSUING_CA2, lo.add(lo.WEB, (0.0, 0.0, 2.3)), lo.add(crown2, (0.0, -0.3, -0.3)), 0.05, "violet", ("F-14",)),
    ]

    # --- travelling pulses, scrolls -------------------------------------------------------------
    start_rdp, start_web = lo.CHANNEL_RDP[0], lo.CHANNEL_WEB[0]
    objs += [
        StageObject("PULSE-RDP-1", Kind.PULSE, R.PENDING, lo.add(start_rdp, (0.0, 0.0, 0.25)), size=(0.2, 0.2, 0.2), on_stage=False),
        StageObject("PULSE-RDP-2", Kind.PULSE, R.PENDING, lo.add(start_rdp, (0.0, 0.0, 0.25)), size=(0.2, 0.2, 0.2), on_stage=False),
        StageObject("PULSE-WEB", Kind.PULSE, R.PENDING, lo.add(start_web, (0.0, 0.0, 0.25)), size=(0.2, 0.2, 0.2), on_stage=False),
        StageObject("CRL-CA1", Kind.SCROLL, R.REVOCATION, lo.add(lo.KIOSK, (0.0, 0.0, 1.4)), size=(0.34, 0.12, 0.12), on_stage=False, spec_ids=("F-13",)),
        StageObject("CRL-ROOT", Kind.SCROLL, R.REVOCATION, lo.add(lo.KIOSK, (0.3, 0.0, 1.4)), size=(0.34, 0.12, 0.12), on_stage=False, spec_ids=("F-13",)),
        StageObject("CRL-CA2", Kind.SCROLL, R.REVOCATION, lo.add(lo.KIOSK, (0.0, 0.0, 1.4)), size=(0.34, 0.12, 0.12), on_stage=False, spec_ids=("F-13",)),
        StageObject("CRL-ROOT-2", Kind.SCROLL, R.REVOCATION, lo.add(lo.KIOSK, (0.3, 0.0, 1.4)), size=(0.34, 0.12, 0.12), on_stage=False, spec_ids=("F-13",)),
    ]

    # --- client-side validation lists -----------------------------------------------------------
    objs += _check_slots("RDP", 6, lo.CHECK_LIST, lo.CHECK_ROW_STEP, R.VALIDATED, pending_last=True)
    objs += _check_slots("WEB", 4, lo.CHECK_LIST, lo.CHECK_ROW_STEP, R.VALIDATED)
    return tuple(objs)


CATALOGUE = build_catalogue()
BY_ID: dict[str, StageObject] = {o.id: o for o in CATALOGUE}
if len(BY_ID) != len(CATALOGUE):
    raise ValueError("duplicate stage object id")


def obj(object_id: str) -> StageObject:
    return BY_ID[object_id]
