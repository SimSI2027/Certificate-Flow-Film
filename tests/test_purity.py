"""Purity of the pure-Python layer (CLAUDE.md, Charter Sections 9 and 12)."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NETWORK_MODULES = {"urllib", "http", "socket", "requests", "httpx", "ftplib", "smtplib", "ssl"}
# Allowlisted string literals containing "://": (relative path, enclosing function) -> reason.
URL_ALLOWLIST = {
    ("cff/story/model.py", "extension_url"): "builds illustrative lab-internal AIA/CDP URLs; data only, never fetched",
}


def _py_files(*dirs: str) -> list[Path]:
    return [p for d in dirs for p in (ROOT / d).rglob("*.py")]


def _imports(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def _enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef):
            return current.name
        current = parents.get(current)
    return None


def test_cff_never_imports_bpy_or_network_modules() -> None:
    files = _py_files("cff")
    assert files
    for path in files:
        imported = _imports(ast.parse(path.read_text(encoding="utf-8")))
        assert "bpy" not in imported and "mathutils" not in imported, path
        assert not imported & NETWORK_MODULES, (path, imported & NETWORK_MODULES)


def test_no_network_urls_in_cff_or_blender() -> None:
    for path in _py_files("cff", "blender"):
        rel = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and "://" in node.value:
                owner = _enclosing_function(node, parents)
                assert (rel, owner) in URL_ALLOWLIST, f"{rel}: URL literal {node.value!r}"
