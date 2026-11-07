"""Static scans of the Blender code (no bpy needed): literals, builder coverage, API rules, calibration isolation."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from cff.stage.objects import CATALOGUE, Kind

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")
FRAME_NAMES = {"frame_start", "frame_end", "frame_current"}
# Documented allowlist: nothing in blender/ may hold a literal colour or a numeric frame.
HEX_ALLOWLIST: set[tuple[str, str]] = set()
FRAME_ALLOWLIST: set[tuple[str, int]] = set()


def _py_files(folder: str) -> list[Path]:
    return sorted((ROOT / folder).rglob("*.py"))


@pytest.mark.covers("C-10")
def test_no_literal_colours_outside_the_theme() -> None:
    for folder in ("blender", "cff/stage", "cff/story", "tools"):
        for path in _py_files(folder):
            rel = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and HEX.search(node.value):
                    assert (rel, node.value) in HEX_ALLOWLIST, f"{rel}: literal colour {node.value!r} (use cff.theme.palette)"


@pytest.mark.covers("C-06")
def test_no_numeric_frame_literals_in_blender_code() -> None:
    for path in _py_files("blender"):
        rel = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, ast.AugAssign | ast.AnnAssign):
                targets = [node.target]
            for target in targets:
                if isinstance(target, ast.Attribute) and target.attr in FRAME_NAMES and isinstance(getattr(node, "value", None), ast.Constant):
                    assert (rel, target.lineno) in FRAME_ALLOWLIST, f"{rel}:{target.lineno} sets {target.attr} to a literal"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "frame_set":
                assert not any(isinstance(a, ast.Constant) for a in node.args), f"{rel}:{node.lineno} frame_set with a literal"


@pytest.mark.covers("C-06")
def test_blender_code_never_uses_linear_interpolation_or_legacy_action_api() -> None:
    for path in _py_files("blender"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "LINEAR" and path.name != "scene_checks.py":
                raise AssertionError(f"{path}: LINEAR interpolation")  # the checks may name it; nothing else may use it
            if isinstance(node, ast.Attribute):
                if node.attr == "fcurves":
                    assert isinstance(node.value, ast.Name) and node.value.id in {"bag", "channelbag"}, f"{path}:{node.lineno}: legacy action.fcurves"
                assert node.attr not in {"node_tree"} or not (isinstance(node.value, ast.Name) and node.value.id == "scene"), f"{path}: scene.node_tree is gone"
                assert node.attr != "sequences", f"{path}: use strips, not sequences"
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Attribute) and t.attr == "use_nodes" and isinstance(t.value, ast.Name) and t.value.id != "world":
                        raise AssertionError(f"{path}:{node.lineno}: deprecated Material.use_nodes")


@pytest.mark.covers("C-11")
def test_every_stage_object_kind_has_a_grey_box_builder() -> None:
    built: set[str] = set()
    for path in _py_files("blender/actors"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "BUILDERS" for t in node.targets) and isinstance(node.value, ast.Dict):
                for key in node.value.keys:
                    if isinstance(key, ast.Attribute):
                        built.add(key.attr)
    missing = [k.name for k in Kind if k.name not in built]
    assert missing == [], f"kinds without a builder: {missing}"
    assert {o.kind.name for o in CATALOGUE} <= built


@pytest.mark.covers("C-02")
def test_blender_scripts_run_with_the_project_bootstrap() -> None:
    for name in ("build_scene", "render_frames", "run_checks"):
        text = (ROOT / "blender" / f"{name}.py").read_text(encoding="utf-8")
        assert "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))" in text, name


def test_calibration_code_is_unreachable_from_normal_builds() -> None:
    assert not (ROOT / "blender" / "calibration.py").exists() or "calibrate" not in (ROOT / "blender" / "build_scene.py").read_text(encoding="utf-8")
    for path in _py_files("blender"):
        if path.name != "calibration.py":
            assert "calibration" not in path.read_text(encoding="utf-8"), path
