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


def _calls(path: Path, name: str) -> list[ast.Call]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    def named(call: ast.Call) -> bool:
        return (isinstance(call.func, ast.Name) and call.func.id == name) or (isinstance(call.func, ast.Attribute) and call.func.attr == name)

    return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and named(n)]


def test_normal_builds_never_enable_a_fault() -> None:
    """Charter 2.8: fault code paths run only under ``python -m tools calibrate``."""
    # the normal build entry point calls build() with no hooks, and only runs as a script
    build_scene = ROOT / "blender" / "build_scene.py"
    calls = _calls(build_scene, "build")
    assert calls
    for call in calls:
        assert not call.keywords and len(call.args) == 2, f"build_scene.py:{call.lineno} passes hooks to build()"
    assert 'if __name__ == "__main__":' in build_scene.read_text(encoding="utf-8")
    # no tools module except the calibrate command references the faults or the calibration script
    for path in _py_files("tools") + _py_files("cff"):
        text = path.read_text(encoding="utf-8")
        if path.name in {"calibrate.py", "__main__.py"}:
            continue
        assert "calibration.py" not in text and "calibrate" not in text and "cff_fault" not in text, path
        for fault in ("private_key_leak", "root_issues_leaf", "flowchart", "caption_clip"):
            assert fault not in text, f"{path} mentions fault {fault}"
    # the CLI imports the calibrate module lazily, inside its own command only
    main = ast.parse((ROOT / "tools" / "__main__.py").read_text(encoding="utf-8"))
    top_imports = [n for n in main.body if isinstance(n, ast.ImportFrom)]
    assert all("calibrate" not in [a.name for a in n.names] for n in top_imports)
    # the pipeline builds and verifies with build_scene.py, never the fault script
    pipeline = (ROOT / "tools" / "pipeline.py").read_text(encoding="utf-8")
    assert '"build_scene.py"' in pipeline


def test_fault_lists_agree_and_every_fault_has_a_hard_expectation_or_a_discriminator() -> None:
    from tools import calibrate  # noqa: PLC0415  (kept local: no other test module touches the fault definitions)

    script = ast.parse((ROOT / "blender" / "calibration.py").read_text(encoding="utf-8"))
    faults = next(n.value for n in script.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "FAULTS" for t in n.targets))
    assert isinstance(faults, ast.Tuple)
    assert tuple(e.value for e in faults.elts if isinstance(e, ast.Constant)) == calibrate.FAULTS
    for fault in ("private_key_leak", "root_issues_leaf", "caption_clip"):
        assert calibrate.EXPECTED[fault], f"{fault}: the hard discriminators must be expected to fail (Charter 2.8)"
    assert set(calibrate.RELEVANT_DISCRIMINATORS) == set(calibrate.FAULTS)
    assert "FAULT_TAG = \"cff_fault\"" in (ROOT / "blender" / "checks" / "scene_checks.py").read_text(encoding="utf-8")
    assert "FAULT_PROP = \"cff_fault\"" in (ROOT / "blender" / "calibration.py").read_text(encoding="utf-8")
