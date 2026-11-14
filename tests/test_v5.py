"""Session V5a (owner request, amendment V5-A1): realistic hardware and world.

V5-LIC-01: every file in assets\\ is licensed and hashed; the CC0 textures are recorded in their manifest, LICENSES\\ and README.
V5-NET-01: the Root CA is air-gapped: no cable belongs to it and every cable keeps its clearance from the root complex.
V5-BND-01: the PKI hard checks measure declared shell boxes; shells are axis-aligned and every private key starts inside its owner.
V5-HW-01: the hero racks are deterministic, fill their rails exactly and stand behind every story artefact in the chassis.
V5-DC-01: the datacenter rows stand outside the camera envelope, so no camera is ever inside or behind a rack.
V5-LOGO-01: no brand marks, text or logos in the hardware code.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
from pathlib import Path

import pytest

from cff.stage import camera, choreography, hardware, labels
from cff.stage import layout as lo
from cff.stage.layout import Vec3
from cff.stage.objects import BY_ID, CATALOGUE, Kind
from cff.story import model as m

ROOT = Path(__file__).resolve().parents[1]
ASSET_BUDGET_BYTES = 150 * 1024 * 1024
TEXTURE_MANIFEST = ROOT / "assets" / "textures" / "textures.manifest.json"
HARDWARE_CODE = ("blender/actors/hardware.py", "blender/finishes.py", "blender/datacenter.py", "cff/stage/hardware.py")
BRANDS = ("microsoft", "windows", "dell", "hpe", "hewlett", "cisco", "lenovo", "apple", "intel", "nvidia", "supermicro", "thales", "entrust",
          "apc", "schneider", "juniper", "arista", "ibm", "oracle", "fujitsu")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.covers("C-11")
def test_V5_LIC_01_every_asset_file_is_licensed_and_hashed() -> None:  # noqa: N802
    textures = json.loads(TEXTURE_MANIFEST.read_text(encoding="utf-8"))
    assert textures["licence"] == "CC0-1.0" and (ROOT / textures["licence_text"]).is_file()
    listed: dict[str, dict[str, object]] = {}
    for asset in textures["assets"]:
        assert asset["licence"] == "CC0-1.0", asset["id"]
        assert asset["page"].startswith("https://ambientcg.com/view?id=") and asset["zip_sha256"]
        for f in asset["files"]:
            listed[f["path"]] = f
    character = json.loads((ROOT / "assets" / "character.manifest.json").read_text(encoding="utf-8"))
    covered = {
        "assets/character.blend", "assets/character.manifest.json", "assets/character.report.json", "assets/textures/textures.manifest.json",
        "assets/fonts/OFL.txt", *listed,
    }
    total = 0
    for path in sorted(p for p in (ROOT / "assets").rglob("*") if p.is_file()):
        rel = path.relative_to(ROOT).as_posix()
        total += path.stat().st_size
        if rel.startswith("assets/fonts/") and rel.endswith(".ttf"):
            continue  # Inter, SIL OFL 1.1 (assets/fonts/OFL.txt)
        assert rel in covered, f"{rel} has no licence record"
        if rel in listed:
            assert _sha(path) == listed[rel]["sha256"] and path.stat().st_size == listed[rel]["bytes"], rel
    assert _sha(ROOT / "assets" / "character.blend") == character["sha256"]
    assert total < ASSET_BUDGET_BYTES, f"assets/ is {total / 2**20:.1f} MB"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "textures.manifest.json" in readme and all(a["id"] in readme for a in textures["assets"])


def test_V5_LIC_01_the_film_uses_only_recorded_textures_and_never_downloads() -> None:  # noqa: N802
    listed = {f["path"] for a in json.loads(TEXTURE_MANIFEST.read_text(encoding="utf-8"))["assets"] for f in a["files"]}
    maps = (("brushed", "Color"), ("brushed", "Roughness"), ("perforated", "Color"), ("perforated", "Roughness"), ("perforated", "Opacity"),
            ("concrete", "Color"), ("concrete", "Roughness"))
    used = {hardware.texture_file(use, ch) for use, ch in maps}
    assert used <= listed
    source = (ROOT / "blender" / "finishes.py").read_text(encoding="utf-8")
    assert "texture_file(" in source and "://" not in source and "urllib" not in source


@pytest.mark.covers("AR-01")
def test_V5_NET_01_no_network_cable_reaches_the_root() -> None:  # noqa: N802
    root_parts = {o.id for o in CATALOGUE if o.owner == m.ROOT_CA}
    box = hardware.root_complex_box()
    assert {m.ROOT_CA} == hardware.NO_CABLE_OWNERS
    assert hardware.CABLE_RUNS, "the datacenter has cables (rear bundles and tray drops)"
    for run in hardware.CABLE_RUNS:
        assert run.owner not in hardware.NO_CABLE_OWNERS and run.owner not in root_parts, run.name
        nearest = min(hardware.box_distance(p, box) for p in run.points)
        assert nearest >= hardware.ROOT_CABLE_CLEARANCE_M, f"{run.name} comes within {nearest:.2f} m of the Root CA"
    for row in hardware.ROWS:  # the trays carry cables too
        for p in hardware.row_tray(row):
            assert hardware.box_distance(p, box) >= hardware.ROOT_CABLE_CLEARANCE_M, row.name
    for o in CATALOGUE:  # nor a network channel or CA route
        if o.kind in (Kind.CHANNEL, Kind.ROUTE):
            assert all(hardware.box_distance(p, box) > 0.0 for p in o.points), o.id


def test_V5_NET_01_the_root_no_cables_check_runs_in_blender() -> None:  # noqa: N802
    source = (ROOT / "blender" / "checks" / "scene_checks.py").read_text(encoding="utf-8")
    assert "check_root_no_cables(scene)" in source and "check_shell_bounds()" in source
    builder = (ROOT / "blender" / "actors" / "hardware.py").read_text(encoding="utf-8")
    root_cage = builder[builder.index("def root_cage"):builder.index("def hsm")]
    assert "CABLE" not in root_cage and "_ports(" not in root_cage, "the root machine has no cable and no port in use"


@pytest.mark.covers("F-03")
def test_V5_BND_01_shells_are_axis_aligned_and_keys_start_inside_their_owner() -> None:  # noqa: N802
    for oid in hardware.SHELL_BOUNDS:
        assert BY_ID[oid].rotation == (0.0, 0.0, 0.0), oid
    owners: dict[str, list[hardware.Box]] = {}
    for o in CATALOGUE:
        if o.kind in (Kind.CHASSIS, Kind.CA_VAULT, Kind.ROOT_VAULT, Kind.PLINTH, Kind.DAIS) and o.owner:
            owners.setdefault(o.owner, []).append(hardware.world_box(o.id))
    for o in CATALOGUE:
        if o.kind is Kind.KEY_PRIVATE and o.owner:
            (x0, y0, z0), (x1, y1, z1) = hardware.union(owners[o.owner])
            h = lo.KEY_SIZE / 2
            assert x0 <= o.home[0] - h and o.home[0] + h <= x1 and y0 <= o.home[1] - h and o.home[1] + h <= y1, o.id
            assert z0 <= o.home[2] - h and o.home[2] + h <= z1, o.id


def test_V5_BND_01_declared_boxes_match_the_catalogue_sizes() -> None:  # noqa: N802
    for oid, ((x0, y0, z0), (x1, y1, z1)) in hardware.SHELL_BOUNDS.items():
        o = BY_ID[oid]
        if o.kind in (Kind.CHASSIS, Kind.AD_COLUMN, Kind.KIOSK, Kind.CA_VAULT):
            assert (x1 - x0, y1 - y0, z1 - z0) == pytest.approx(o.size), oid
    assert BY_ID[m.AD].size == (lo.AD_WIDTH, lo.AD_DEPTH, lo.AD_HEIGHT)
    ring = BY_ID["RING-AD-1"].size[0] / 2
    assert ring > math.hypot(lo.AD_WIDTH, lo.AD_DEPTH) / 2 + 0.1, "the Enrollment Services rings clear the AD rack"


def test_V5_HW_01_hero_racks_fill_their_rails_and_stand_behind_the_story_bay() -> None:  # noqa: N802
    for actor, spec in hardware.HERO_RACKS.items():
        for column in spec.fill:
            used = [u for d in column for u in range(d.u, d.u + d.height_u)]
            assert sorted(used) == list(range(spec.units)), f"{actor}: rack units overlap or leave gaps"
            assert sum(d.accent for d in column) <= 1
        assert sum(d.accent for c in spec.fill for d in c) == 1, f"{actor}: one named server"
        assert spec.base_z + spec.units * hardware.RACK_UNIT_M < spec.height - 0.1
    again = hardware._rack(*lo.CHASSIS_SIZE, hardware.CHASSIS_COLUMNS, hardware.CHASSIS_FACE_Y, hardware.CHASSIS_UNITS, hardware.RACK_SEED + 1, {})
    assert again == hardware._rack(*lo.CHASSIS_SIZE, hardware.CHASSIS_COLUMNS, hardware.CHASSIS_FACE_Y, hardware.CHASSIS_UNITS, hardware.RACK_SEED + 1, {})
    for tag, base in (("RDP", lo.RDP), ("WEB", lo.WEB)):  # every story artefact inside a chassis stays in front of the device faces
        for o in CATALOGUE:
            inside = o.owner in (m.RDP_SERVER, m.WEB_SERVER) or o.id.endswith(f"-{tag}") or o.id.startswith(f"CERT-{tag}")
            artefact = o.kind in (Kind.CONTAINER, Kind.KEY_PRIVATE, Kind.KEY_PUBLIC, Kind.CAPSULE, Kind.CARD, Kind.LOCK, Kind.CLAMP)
            within = abs(o.home[0] - base[0]) < lo.CHASSIS_SIZE[0] / 2 and abs(o.home[1] - base[1]) < lo.CHASSIS_SIZE[1] / 2
            if inside and artefact and within:
                assert o.home[1] - base[1] + o.size[1] / 2 < hardware.CHASSIS_FACE_Y, o.id
    for _, spec in hardware.vault_racks(m.ColourRole.ISSUING_CA1):
        assert hardware.VAULT_RACK_FACE_Y + spec.depth <= lo.CA_VAULT_SIZE[1] / 2 - 0.14 + 1e-9
    module = BY_ID["MODULE-CA1"]
    assert module.home[1] - lo.CA1[1] + module.size[1] / 2 <= hardware.VAULT_RACK_FACE_Y


def _camera_positions() -> list[Vec3]:
    plan = camera.CameraPlan(choreography.build_timeline())
    return [camera.offset_position(st.look, st.az, st.el, st.dist) for st in plan.states.values()]


def test_V5_DC_01_rack_rows_stand_outside_the_camera_envelope() -> None:  # noqa: N802
    cams = _camera_positions()
    x0, x1 = min(c[0] for c in cams), max(c[0] for c in cams)
    y0, y1 = min(c[1] for c in cams), max(c[1] for c in cams)
    w, d, _ = hardware.ROW_RACK_SIZE
    reach = math.hypot(w, d) / 2
    for r in hardware.row_racks():
        gap = max(x0 - r.position[0], r.position[0] - x1, y0 - r.position[1], r.position[1] - y1)
        assert gap > reach + 0.5, f"a row rack at {r.position} is inside the camera envelope"
    root = hardware.root_complex_box()
    for r in hardware.row_racks():
        assert hardware.box_distance(r.position, root) > hardware.ROOT_CABLE_CLEARANCE_M


def test_V5_DC_01_perforated_tiles_lie_on_the_floor_grid() -> None:  # noqa: N802
    for x, y, _ in hardware.perforated_tiles():
        assert (x / 0.6 - 0.5) == pytest.approx(round(x / 0.6 - 0.5), abs=1e-6)
        assert (y / 0.6 - 0.5) == pytest.approx(round(y / 0.6 - 0.5), abs=1e-6)


def test_V5_LEG_01_screen_lies_on_the_laptop_lid_and_the_connect_sign_stays_put() -> None:  # noqa: N802
    screen = BY_ID["SCREEN-IDLE"]
    assert screen.rotation == (-lo.LAPTOP_LID_TILT_DEG, 0.0, 90.0)
    tilt = math.radians(lo.LAPTOP_LID_TILT_DEG)
    hx, hz = lo.LAPTOP_HINGE_XZ
    along = (screen.home[0] - lo.LAPTOP[0] - hx) * -math.sin(tilt) + (screen.home[2] - lo.LAPTOP[2] - hz) * math.cos(tilt)
    assert along == pytest.approx(lo.LAPTOP_SCREEN_ALONG)
    connect = next(p for p in labels.PLACEMENTS if p.label_id == "LBL-CONNECT")
    assert lo.add(screen.home, connect.offset) == pytest.approx(lo.CONNECT_SIGN_POINT)


def test_V5_LOGO_01_no_brand_marks_text_or_logos_in_the_hardware() -> None:  # noqa: N802
    for rel in HARDWARE_CODE:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                words = {w.strip(".,:;()'\"").lower() for w in node.value.split()}
                assert not words & set(BRANDS), f"{rel}: brand name in {node.value!r}"
                assert node.value != "FONT", f"{rel}: text object"
