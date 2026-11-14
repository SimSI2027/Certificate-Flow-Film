"""V5a realistic hardware and datacenter (amendment V5-A1, owner request): pure data, no ``bpy``.

The grey-box shells became real hardware: rack cabinets filled with 1U/2U devices (``RackSpec``), a secure CA enclosure lined with
CA server racks, and a locked cage on the root's plinth holding one offline machine. The datacenter around the stage is rows of
racks with overhead cable trays above them, cold-aisle light fixtures and perforated raised-floor tiles.

Two contracts here keep the PKI hard checks exact instead of relaxing them:

- **Declared shell bounds.** Every shell (``SHELL_KINDS``) declares a local box (``local_bounds``). The containment, isolation and
  route checks measure against these boxes, and the in-Blender check ``shell_bounds`` fails if any shell mesh (with all its new
  detail) leaves its box. A detailed mesh can therefore never grow a shell and silently widen what counts as "inside".
- **No network cable at the root.** Every cable in the film is a ``CableRun`` listed here. None belongs to the Root CA, and every
  point of every run keeps ``ROOT_CABLE_CLEARANCE_M`` from the root complex (``tests/test_v5.py``; in Blender ``root_no_cables``).

Seeds: ``RACK_SEED`` (hero rack fills), ``ROW_SEED`` (background rack variants and their order). All layouts are deterministic.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from cff.stage import layout as lo
from cff.stage.layout import Vec3
from cff.stage.objects import BASE_ANCHORED, BY_ID, CATALOGUE, Kind, StageObject
from cff.story import model as m
from cff.story.model import ColourRole

RACK_UNIT_M = 0.04445  # 1U (EIA-310)
DEVICE_WIDTH_M = 0.483  # 19-inch faceplate with ears
RACK_SEED = 20261115
ROW_SEED = 20261116

# --- declared shell bounds ------------------------------------------------------------------------------------------
SHELL_KINDS: frozenset[Kind] = frozenset({Kind.CHASSIS, Kind.CA_VAULT, Kind.ROOT_VAULT, Kind.PLINTH, Kind.DAIS, Kind.AD_COLUMN, Kind.KIOSK})
PLINTH_FOOT_SCALE = 1.35  # the plinth's base flange is this much wider than its column
DAIS_RIM_M = 0.12  # the dais's raised inner deck stands this far above its size height
BOUNDS_TOLERANCE_M = 0.001

Box = tuple[Vec3, Vec3]


def local_bounds(o: StageObject) -> Box:
    """The box a shell's mesh must stay inside, in the shell's own frame (origin per ``objects.BASE_ANCHORED``)."""
    sx, sy, sz = o.size
    if o.kind is Kind.DAIS:
        return ((-sx, -sx, 0.0), (sx, sx, sz + DAIS_RIM_M))
    if o.kind is Kind.PLINTH:
        return ((-sx * PLINTH_FOOT_SCALE / 2, -sy * PLINTH_FOOT_SCALE / 2, 0.0), (sx * PLINTH_FOOT_SCALE / 2, sy * PLINTH_FOOT_SCALE / 2, sz))
    if o.kind in BASE_ANCHORED:
        return ((-sx / 2, -sy / 2, 0.0), (sx / 2, sy / 2, sz))
    return ((-sx / 2, -sy / 2, -sz / 2), (sx / 2, sy / 2, sz / 2))


SHELL_BOUNDS: dict[str, Box] = {o.id: local_bounds(o) for o in CATALOGUE if o.kind in SHELL_KINDS}


def world_box(object_id: str) -> Box:
    """A shell's declared box at its home (shells are never rotated: ``tests/test_v5.py``)."""
    (x0, y0, z0), (x1, y1, z1) = SHELL_BOUNDS[object_id]
    hx, hy, hz = BY_ID[object_id].home
    return ((hx + x0, hy + y0, hz + z0), (hx + x1, hy + y1, hz + z1))


def union(boxes: list[Box]) -> Box:
    return ((min(b[0][0] for b in boxes), min(b[0][1] for b in boxes), min(b[0][2] for b in boxes)),
            (max(b[1][0] for b in boxes), max(b[1][1] for b in boxes), max(b[1][2] for b in boxes)))


def root_complex_box() -> Box:
    return union([world_box(o.id) for o in CATALOGUE if o.kind in SHELL_KINDS and o.owner == m.ROOT_CA])


def box_distance(point: Vec3, box: Box) -> float:
    """Distance from a point to an axis-aligned box (0 inside)."""
    d = [max(box[0][i] - point[i], 0.0, point[i] - box[1][i]) for i in range(3)]
    return math.hypot(*d)


# --- rack devices ---------------------------------------------------------------------------------------------------
# Device kinds and their height in rack units. Faces are built in blender/actors/hardware.py.
DEVICE_U: dict[str, int] = {
    "server_1u": 1, "server_2u": 2, "storage_2u": 2, "switch_1u": 1, "patch_1u": 1, "blank_1u": 1, "ups_2u": 2, "manager_1u": 1,
}
FILL_MENU: tuple[str, ...] = ("server_1u", "server_1u", "server_2u", "server_2u", "storage_2u", "blank_1u")


@dataclass(frozen=True)
class Device:
    kind: str
    u: int  # lowest rack unit, 0-based from the bottom of the rail
    accent: bool = False  # carries the rack's identity accent (the named server of the rack)

    @property
    def height_u(self) -> int:
        return DEVICE_U[self.kind]


@dataclass(frozen=True)
class RackSpec:
    """One or more 19-inch columns of devices inside a cabinet. Positions are in the cabinet's local frame (base centre, front -Y)."""
    width: float
    depth: float
    height: float
    columns: tuple[float, ...]  # local x of each 19-inch column centre
    face_y: float  # local y of the device faces (devices reach back from here)
    base_z: float  # local z of rack unit 0
    units: int
    fill: tuple[tuple[Device, ...], ...]  # per column
    accent_role: ColourRole | None = None  # identity tint of the accent LEDs and bezel stripe


def fill_column(rng: random.Random, units: int, fixed: tuple[Device, ...] = ()) -> tuple[Device, ...]:
    """Seeded rack fill: the fixed devices, then menu devices bottom-up in the gaps (a UPS at the bottom when it fits)."""
    used = {u for d in fixed for u in range(d.u, d.u + d.height_u)}
    out = list(fixed)
    u = 0
    if not used & {0, 1}:
        out.append(Device("ups_2u", 0))
        used |= {0, 1}
        u = 2
    while u < units:
        if u in used:
            u += 1
            continue
        kind = rng.choice(FILL_MENU)
        h = DEVICE_U[kind]
        if any(v in used or v >= units for v in range(u, u + h)):
            kind, h = "blank_1u", 1
        out.append(Device(kind, u))
        used |= set(range(u, u + h))
        u += h
    return tuple(sorted(out, key=lambda d: d.u))


def _network_top(units: int) -> tuple[Device, ...]:
    """Patch panel, switch and cable manager at the top of a column (the front patch cords run between them)."""
    return (Device("patch_1u", units - 1), Device("manager_1u", units - 2), Device("switch_1u", units - 3))


# Server chassis (RDP, WEB): two 19-inch columns behind the story bay. The devices stand against the back wall
# (faces at CHASSIS_FACE_Y), clear of every story artefact inside (the key container's back face is at y 0.31).
CHASSIS_FACE_Y = 0.33
CHASSIS_BASE_Z = 0.12
CHASSIS_UNITS = 42
CHASSIS_COLUMNS = (-0.32, 0.32)
AD_UNITS = 42
KIOSK_UNITS = 26
VAULT_RACK_COUNT = 4
VAULT_RACK_SIZE: Vec3 = (0.8, 0.4, 2.2)  # the CA server racks along the vault's back wall (visible depth)
VAULT_RACK_FACE_Y = 1.06  # vault-local: just behind the key module (back face y 1.05)
VAULT_RACK_UNITS = 42
ROW_RACK_SIZE: Vec3 = (0.6, 1.2, 2.2)
ROW_RACK_UNITS = 42
ROW_VARIANTS = 6


def _rack(width: float, depth: float, height: float, columns: tuple[float, ...], face_y: float, units: int, seed: int,
          fixed: dict[int, tuple[Device, ...]], accent: ColourRole | None = None) -> RackSpec:
    rng = random.Random(seed)
    fill = tuple(fill_column(rng, units, fixed.get(i, ())) for i in range(len(columns)))
    return RackSpec(width, depth, height, columns, face_y, CHASSIS_BASE_Z, units, fill, accent)


def _named_server(u: int) -> tuple[Device, ...]:
    return (Device("server_2u", u, accent=True),)


HERO_RACKS: dict[str, RackSpec] = {
    m.RDP_SERVER: _rack(*lo.CHASSIS_SIZE, CHASSIS_COLUMNS, CHASSIS_FACE_Y, CHASSIS_UNITS, RACK_SEED + 1,
                        {0: _network_top(CHASSIS_UNITS) + _named_server(20), 1: _network_top(CHASSIS_UNITS)}),
    m.WEB_SERVER: _rack(*lo.CHASSIS_SIZE, CHASSIS_COLUMNS, CHASSIS_FACE_Y, CHASSIS_UNITS, RACK_SEED + 2,
                        {0: _network_top(CHASSIS_UNITS), 1: _network_top(CHASSIS_UNITS) + _named_server(20)}),
    m.AD: _rack(lo.AD_WIDTH, lo.AD_DEPTH, lo.AD_HEIGHT, (0.0,), -lo.AD_DEPTH / 2 + 0.12, AD_UNITS, RACK_SEED + 3,
                {0: _network_top(AD_UNITS) + _named_server(22)}, ColourRole.DIRECTORY),
    m.PKI_HTTP: _rack(*BY_ID[m.PKI_HTTP].size, (0.0,), -BY_ID[m.PKI_HTTP].size[1] / 2 + 0.1, KIOSK_UNITS, RACK_SEED + 4,
                      {0: _network_top(KIOSK_UNITS) + _named_server(12)}),
}


def vault_racks(role: ColourRole) -> tuple[tuple[float, RackSpec], ...]:
    """The CA server racks inside an issuing CA's enclosure: (vault-local x, rack). The CA server itself is the accent 2U."""
    w, d, h = VAULT_RACK_SIZE
    span = VAULT_RACK_COUNT * w
    out = []
    for i in range(VAULT_RACK_COUNT):
        x = -span / 2 + w / 2 + i * w
        fixed = _network_top(VAULT_RACK_UNITS) + (_named_server(21) if i in (1, 2) else ())
        out.append((x, _rack(w, d, h, (0.0,), -d / 2 + 0.02, VAULT_RACK_UNITS, RACK_SEED + 10 + i + (0 if role is ColourRole.ISSUING_CA1 else 20),
                              {0: fixed}, role)))
    return tuple(out)


def row_variants() -> tuple[RackSpec, ...]:
    w, d, h = ROW_RACK_SIZE
    return tuple(_rack(w, d, h, (0.0,), -d / 2 + 0.1, ROW_RACK_UNITS, ROW_SEED + i, {0: _network_top(ROW_RACK_UNITS)}) for i in range(ROW_VARIANTS))


# --- root: one offline machine in a locked cage -----------------------------------------------------------------------
# Root-vault-local (centred) dimensions. The machine is a tower on a stand; it has no port in use and no cable (AR-01).
CAGE_POST_M = 0.08
CAGE_BAR_M = 0.012
CAGE_BAR_PITCH_M = 0.075
CAGE_DOOR_WIDTH_M = 1.0
ROOT_MACHINE_SIZE: Vec3 = (0.42, 0.62, 0.9)
ROOT_STAND_SIZE: Vec3 = (0.6, 0.8, 0.7)
ROOT_MACHINE_X = 0.9  # right of the door (the seal ring covers the door's centre)
CAGE_MID_RAIL_Z = -0.5  # below the machine's front panel
ROOT_CABLE_CLEARANCE_M = 3.0

# --- datacenter (absolute positions) ---------------------------------------------------------------------------------
# Rows stand just outside the camera envelope (x -16.2..27.6, y -26.0..10.1 over the film), so no camera ever sits inside or
# behind one. Each side has an inner row facing the stage and an outer row back to back with it (a hot aisle between them);
# the cold aisle is the strip in front of the inner row, with perforated tiles and the light fixtures above it.
ROW_PITCH_M = 0.6
HOT_AISLE_M = 1.2
COLD_AISLE_M = 1.8
TRAY_Z = 2.65
TRAY_WIDTH_M = 0.45
FIXTURE_Z = 3.2
FIXTURE_SIZE: Vec3 = (1.2, 0.18, 0.06)
FIXTURE_PITCH_M = 2.4


@dataclass(frozen=True)
class Row:
    name: str
    start: Vec3  # centre of the first rack's front face, on the floor
    along: Vec3  # unit vector along the row
    facing: Vec3  # unit vector the inner row's fronts face (toward the stage)
    count: int


def _row(name: str, start: Vec3, along: Vec3, facing: Vec3, length: float) -> Row:
    return Row(name, start, along, facing, int(length / ROW_PITCH_M))


ROWS: tuple[Row, ...] = (
    _row("north", (-19.0, 30.0, 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), 49.0),
    _row("south", (-19.0, -28.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 49.0),
    _row("west", (-19.0, -26.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), 55.0),
    _row("east", (30.0, -26.0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), 55.0),
)


@dataclass(frozen=True)
class RowRack:
    position: Vec3  # base centre
    yaw_deg: float  # the rack's front (-Y local) turned to face this way
    variant: int


def _yaw_facing(facing: Vec3) -> float:
    """Yaw that turns local -Y (a rack's front) onto ``facing``."""
    return math.degrees(math.atan2(facing[0], -facing[1]))


def row_racks() -> tuple[RowRack, ...]:
    rng = random.Random(ROW_SEED)
    out: list[RowRack] = []
    d = ROW_RACK_SIZE[1]
    for row in ROWS:
        for i in range(row.count):
            base = lo.add(row.start, lo.mul(row.along, ROW_PITCH_M * (i + 0.5)))
            inner = lo.add(base, lo.mul(row.facing, -d / 2))
            outer = lo.add(base, lo.mul(row.facing, -(1.5 * d + HOT_AISLE_M)))
            out.append(RowRack(inner, _yaw_facing(row.facing), rng.randrange(ROW_VARIANTS)))
            out.append(RowRack(outer, _yaw_facing(lo.mul(row.facing, -1.0)), rng.randrange(ROW_VARIANTS)))
    return tuple(out)


def row_tray(row: Row) -> tuple[Vec3, Vec3]:
    """The overhead ladder tray above a row pair (over the hot aisle, where the rear cables rise)."""
    off = -(ROW_RACK_SIZE[1] + HOT_AISLE_M / 2)
    a = lo.add(lo.add(row.start, lo.mul(row.facing, off)), (0.0, 0.0, TRAY_Z))
    b = lo.add(a, lo.mul(row.along, ROW_PITCH_M * row.count))
    return a, b


def cold_aisle_centre(row: Row, fraction: float) -> Vec3:
    p = lo.add(row.start, lo.mul(row.along, ROW_PITCH_M * row.count * fraction))
    return lo.add(p, lo.mul(row.facing, COLD_AISLE_M / 2))


def fixtures() -> tuple[tuple[Vec3, float], ...]:
    """Cold-aisle LED fixtures: (centre, yaw degrees), hung above each row's cold aisle."""
    out = []
    for row in ROWS:
        length = ROW_PITCH_M * row.count
        yaw = math.degrees(math.atan2(row.along[1], row.along[0]))
        for i in range(int(length / FIXTURE_PITCH_M)):
            c = cold_aisle_centre(row, (i + 0.5) * FIXTURE_PITCH_M / length)
            out.append(((c[0], c[1], FIXTURE_Z), yaw))
    return tuple(out)


def perforated_tiles() -> tuple[Vec3, ...]:
    """Perforated raised-floor tiles (tile centres, snapped to the floor grid): in front of each hero rack and along each cold aisle."""
    t = 0.6

    def snap(v: float) -> float:
        return (math.floor(v / t) + 0.5) * t

    cells: set[tuple[float, float]] = set()
    for actor in (m.RDP_SERVER, m.WEB_SERVER, m.AD, m.PKI_HTTP):
        (x0, y0, _), (x1, _, _) = world_box(actor)
        for k in range(3):
            cells.add((snap(x0 + (x1 - x0) * (k + 0.5) / 3), snap(y0 - t)))
    for row in ROWS:
        for i in range(0, row.count, 2):
            p = lo.add(lo.add(row.start, lo.mul(row.along, ROW_PITCH_M * (i + 0.5))), lo.mul(row.facing, t / 2))
            cells.add((snap(p[0]), snap(p[1])))
    return tuple((x, y, 0.0) for x, y in sorted(cells))


# --- CC0 textures (assets/textures, licences in assets/textures/textures.manifest.json) --------------------------------
TEXTURE_DIR = "assets/textures"
TEXTURES: dict[str, str] = {"brushed": "Metal009", "perforated": "SheetMetal001", "concrete": "Concrete034"}


def texture_file(use: str, channel: str) -> str:
    """Repository-relative path of one CC0 map, e.g. ``texture_file("concrete", "Color")``."""
    asset = TEXTURES[use]
    return f"{TEXTURE_DIR}/{asset}/{asset}_1K-JPG_{channel}.jpg"


# --- cables ----------------------------------------------------------------------------------------------------------
CABLE_RADIUS_M = 0.006
CABLES_PER_BUNDLE = 6


@dataclass(frozen=True)
class CableRun:
    name: str
    owner: str  # the shell (or background row) it serves
    points: tuple[Vec3, ...]  # a smooth curve through these points


def _rear_bundle(actor: str) -> list[CableRun]:
    """A hero rack's rear cabling: cables leave the rear door's brush strip and drop into a floor grommet behind the rack."""
    (x0, _, _), (x1, y1, z1) = world_box(actor)
    out = []
    for i in range(CABLES_PER_BUNDLE):
        f = (i + 0.5) / CABLES_PER_BUNDLE
        x = x0 + 0.15 + (x1 - x0 - 0.3) * f
        exit_z = z1 * (0.55 + 0.35 * f)
        gx = (x0 + x1) / 2 + (f - 0.5) * 0.12
        out.append(CableRun(f"CABLE-{actor}-{i + 1}", actor, (
            (x, y1 + 0.01, exit_z), (x, y1 + 0.12, exit_z - 0.08), (x + (gx - x) * 0.6, y1 + 0.2, exit_z * 0.35),
            (gx, y1 + 0.3, 0.06), (gx, y1 + 0.32, -0.05))))
    return out


def _row_drops(row: Row) -> list[CableRun]:
    """Cable drops from a row's overhead tray into every fourth rack top."""
    a, _ = row_tray(row)
    out = []
    for i in range(0, row.count, 4):
        top = lo.add(a, lo.mul(row.along, ROW_PITCH_M * (i + 0.5)))
        for side, sign in (("i", 1.0), ("o", -1.0)):
            rack_top = lo.add(top, lo.mul(row.facing, sign * (HOT_AISLE_M / 2 + 0.2)))
            out.append(CableRun(f"CABLE-{row.name}-{i:03d}{side}", f"ROW-{row.name}", (
                lo.add(top, (0.0, 0.0, 0.02)), lo.add(lo.lerp(top, rack_top, 0.6), (0.0, 0.0, -0.05)), (rack_top[0], rack_top[1], ROW_RACK_SIZE[2] + 0.2),
                (rack_top[0], rack_top[1], ROW_RACK_SIZE[2] - 0.02))))
    return out


def cable_runs() -> tuple[CableRun, ...]:
    out: list[CableRun] = []
    for actor in (m.RDP_SERVER, m.WEB_SERVER, m.AD, m.PKI_HTTP):
        out += _rear_bundle(actor)
    for row in ROWS:
        out += _row_drops(row)
    return tuple(out)


CABLE_RUNS: tuple[CableRun, ...] = cable_runs()
NO_CABLE_OWNERS: frozenset[str] = frozenset({m.ROOT_CA})
