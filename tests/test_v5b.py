"""Session V5b (owner request): PKI iconography, one symbol per concept, the same symbol everywhere.

V5B-ICON-01: every card shows exactly the marks of its certificate kind (CA badge on CA certificates only, the self-closing seal on
             self-signed certificates only, the issuer's ribbon seal on issued certificates only).
V5B-ICON-02: a card's seal is coloured by its issuer, read from the story model (gold root seal on the CA certificates).
V5B-ICON-03: the 14 C-11 shapes are all measured, with the spec's thresholds, by the in-Blender ``silhouettes`` check.
V5B-ICON-04: the IoU maths is right (identity, disjoint, unit-area normalisation).
V5B-PIPE-01: material slots are claimed per primitive; no Blender builder creates geometry with a raw bmesh op that would bypass it
             (the position-range assignment left issuer seals unlit).
V5B-ICON-05: the symbols are original code: no imported icon files and no vendor names in the icon code.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from cff.stage import icons
from cff.stage import layout as lo
from cff.stage.objects import BY_ID, CATALOGUE, Kind
from cff.story import model as m
from cff.story.model import ColourRole

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "REFERENCE-SPEC.md"
ICON_CODE = ("blender/actors/artifacts.py", "blender/actors/network.py", "blender/icon_sheet.py", "cff/stage/icons.py")


@pytest.mark.covers("C-11", "F-02", "AR-01")
def test_V5B_ICON_01_every_card_shows_the_marks_of_its_certificate_kind() -> None:  # noqa: N802
    certs = {c.id: c for c in m.MODEL.certificates}
    assert set(icons.cards()) == set(certs), "every certificate in the model has exactly one card, and no card is invented"
    for card_id in icons.cards():
        cert = certs[card_id]
        marks = icons.card_marks(card_id)
        self_signed = cert.issuer_cert == cert.id
        assert {"document", "public_key"} <= marks, card_id
        assert ("ca_badge" in marks) == cert.basic_constraints_ca, f"{card_id}: the CA badge marks exactly the CA certificates"
        assert ("self_seal" in marks) == self_signed, f"{card_id}: the self-closing seal marks exactly the self-signed certificates"
        assert ("ribbon_seal" in marks) == (not self_signed), f"{card_id}: an issued certificate carries its issuer's seal"


@pytest.mark.covers("C-10", "F-15")
def test_V5B_ICON_02_a_cards_seal_is_coloured_by_its_issuer() -> None:  # noqa: N802
    expected = {"CERT-RDP": ColourRole.ISSUING_CA1, "CERT-WEB": ColourRole.ISSUING_CA2, "CERT-CA1": ColourRole.ROOT, "CERT-CA2": ColourRole.ROOT,
                "CERT-CA1-COPY-RDP": ColourRole.ROOT, "CERT-CA2-COPY-WEB": ColourRole.ROOT, "CERT-ROOT": ColourRole.ROOT,
                "CERT-RDP-SELF": ColourRole.NEUTRAL}
    assert {cid: icons.issuer_role(cid) for cid in icons.cards()} == expected
    for cert in m.MODEL.certificates:
        assert icons.issuer_role(cert.id) is BY_ID[cert.issuer_cert].role


@pytest.mark.covers("C-11")
def test_V5B_ICON_03_the_c11_check_measures_all_14_shapes_with_the_spec_thresholds() -> None:  # noqa: N802
    text = SPEC.read_text(encoding="utf-8")
    block = text[text.index("### C-11"):text.index("## Legibility criteria")]
    listed = re.search(r"The 14 shapes are: (.+?)\. The subordinate", block)
    assert listed is not None
    spec_names = [n.strip().replace(" (on a cable-free plinth)", "").replace(" (a signature impression)", "")
                  for n in re.split(r",\s*|\s+and\s+", listed.group(1))]
    assert sorted(s.name for s in icons.C11_SHAPES) == sorted(spec_names)
    assert "IoU ≤ 0.75 for every pair" in block and icons.PAIR_IOU_MAX == 0.75
    assert "Private key vs public key IoU ≤ 0.6" in block and icons.STRICT_IOU_MAX == 0.6
    assert set(icons.STRICT_PAIRS) == {("private key", "public key"), ("handshake proof", "private key"), ("handshake proof", "public key")}
    for shape in icons.C11_SHAPES:
        assert all(oid in BY_ID for oid in shape.object_ids), shape
        assert shape.view in {"FRONT", "TOP"}
    assert next(s for s in icons.C11_SHAPES if s.name == "root vault").object_ids == (m.ROOT_CA, "ROOT-PLINTH"), "the spec's root vault stands on its plinth"
    checks = (ROOT / "blender" / "checks" / "scene_checks.py").read_text(encoding="utf-8")
    run_all = checks[checks.index("def run_all"):]
    assert "check_silhouettes()" in run_all, "the silhouettes check runs in verify"


@pytest.mark.covers("C-11")
def test_V5B_ICON_04_iou_maths() -> None:  # noqa: N802
    square = [((0.0, 0.0), (2.0, 0.0), (2.0, 2.0)), ((0.0, 0.0), (2.0, 2.0), (0.0, 2.0))]
    norm = icons.normalise(square)
    xs = [p[0] for t in norm for p in t]
    assert max(xs) - min(xs) == pytest.approx(1.0) and min(xs) == pytest.approx(-0.5)
    a = icons.rasterise(norm)
    cell = (2 * icons.GRID_HALF_EXTENT / icons.GRID_CELLS) ** 2
    assert len(a) * cell == pytest.approx(1.0, rel=0.03)
    assert icons.iou(a, a) == 1.0
    wide = icons.rasterise(icons.normalise([((0.0, 0.0), (4.0, 0.0), (4.0, 1.0)), ((0.0, 0.0), (4.0, 1.0), (0.0, 1.0))]))
    assert icons.iou(a, wide) == pytest.approx(1 / 3, abs=0.03), "unit square vs 2x0.5 strip: overlap 0.5, union 1.5"
    left = icons.rasterise([((-2.0, -1.0), (-1.0, -1.0), (-1.0, 1.0))])
    right = icons.rasterise([((1.0, -1.0), (2.0, -1.0), (2.0, 1.0))])
    assert icons.iou(left, right) == 0.0


def _calls(path: Path) -> list[tuple[str, int]]:
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr.startswith("create_"):
            target = node.func.value
            if isinstance(target, ast.Attribute) and target.attr == "ops":
                out.append((node.func.attr, node.lineno))
    return out


@pytest.mark.covers("C-10")
def test_V5B_PIPE_01_material_slots_are_claimed_per_primitive() -> None:  # noqa: N802
    prims = (ROOT / "blender" / "actors" / "primitives.py").read_text(encoding="utf-8")
    slot_fn = prims[prims.index("def slot"):prims.index("def _claim")]
    assert "range(" not in slot_fn and "bm.faces[" not in slot_fn, "slot() must not assign faces by position"
    for name in ("cube", "cylinder", "cone", "sphere", "icosphere", "torus", "tube", "prism"):
        body = prims[prims.index(f"def {name}("):]
        body = body[: body.find("\ndef ", 1)]
        assert "_claim" in body or "cube(bm" in body, f"primitives.{name} must claim the faces it creates"
    for path in sorted((ROOT / "blender" / "actors").glob("*.py")):
        if path.name != "primitives.py":
            assert _calls(path) == [], f"{path.name}: use the primitives (p.cube) so material slots are claimed"


@pytest.mark.covers("C-05", "C-06")
def test_V5B_CIN_01_rig_lights_never_enter_a_datacenter_row() -> None:  # noqa: N802
    from cff.stage import camera, choreography, hardware, rig  # noqa: PLC0415

    plan = camera.CameraPlan(choreography.build_timeline())
    from cff.theme import look  # noqa: PLC0415

    over_band = hardware.ROW_RACK_SIZE[2] + look.RIG_KEEP_OUT_ABOVE_M  # the full clearance applies over the rack band itself
    for frame in plan.frames():
        placed = rig.rig_frame(plan.state(frame))
        for light in (placed.key, placed.rim):
            for row in hardware.ROWS:
                needed = rig.row_clearance(light[0], light[1], row)
                assert light[2] >= needed - 1e-9, f"frame {frame}: a rig light at {light} is below the {row.name} row's clearance"
                if needed >= over_band - 1e-9:
                    assert light[2] > hardware.ROW_RACK_SIZE[2], f"frame {frame}: a rig light at {light} is inside the {row.name} row"
    f1922 = rig.rig_frame(plan.state(1922)).rim
    assert f1922[2] > hardware.ROW_RACK_SIZE[2], "the rim that was cut off inside the west row at f1922 now passes over it"


@pytest.mark.covers("C-02", "C-05")
def test_V5B_CIN_02_rig_lights_cut_with_the_camera() -> None:  # noqa: N802
    text = (ROOT / "blender" / "lighting.py").read_text(encoding="utf-8")
    fn = text[text.index("def build_lights"):]
    assert "hold = (frame + 1) in cut_frames" in fn
    assert fn.count("constant=hold") == 3, "location, energy and spot size all step at the cuts"
    assert "{c - 1 for c in cut_frames} | cut_frames" in fn, "both sides of each cut are keyed"


@pytest.mark.covers("C-11")
def test_V5B_ICON_05_symbols_are_original_and_sized_to_stay_apart() -> None:  # noqa: N802
    for rel in ICON_CODE:
        text = (ROOT / rel).read_text(encoding="utf-8").lower()
        assert ".svg" not in text and "import_curve" not in text, f"{rel}: the symbols are drawn in code"
        for vendor in ("microsoft", "windows logo", "material symbols", "lucide", "tabler"):
            assert vendor not in text, f"{rel}: {vendor}"
    assert lo.CRL_SIZE[2] > lo.CRL_SIZE[0], "the CRL hangs tall where the card is wide"
    assert lo.PROOF_SIZE[0] / lo.PROOF_SIZE[2] >= 4.0, "the proof is a long signature banner"
    assert lo.CARD_SIZE[0] > lo.CARD_SIZE[2]
    for o in CATALOGUE:
        if o.kind is Kind.SCROLL:
            assert o.size == lo.CRL_SIZE
        if o.kind is Kind.PROOF:
            assert o.size == lo.PROOF_SIZE
    assert Kind.CARD in icons.ICON_KINDS and Kind.KEY_PRIVATE in icons.ICON_KINDS and Kind.KEY_PUBLIC in icons.ICON_KINDS
