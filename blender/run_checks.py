"""Run every in-Blender hard discriminator on a built .blend and write ``results.json``.

Usage: blender -b <film.blend> --factory-startup --python-exit-code 1 -P blender/run_checks.py -- --out <results.json>
Exits non-zero (a failing script) when any check fails, so ``tools verify`` cannot miss it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy

from blender.checks import scene_checks
from blender.common import option, script_args


def main() -> None:
    args = script_args()
    out = Path(option(args, "out", "renders/checks.json") or "renders/checks.json")
    scene = bpy.data.scenes["BEAUTY"]
    results = scene_checks.run_all(scene)
    payload = [{"name": r.name, "passed": r.passed, "failures": r.failures[:60], "failure_count": len(r.failures), "metrics": r.metrics} for r in results]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")
    failed = [r.name for r in results if not r.passed]
    print("CHECKS", json.dumps({"failed": failed, "total": len(results)}))
    if failed:
        raise SystemExit(f"scene checks failed: {', '.join(failed)}")


main()
