"""``python -m tools verify``: every persistent hard discriminator in one run (Charter Section 12).

Pure Python (ruff, mypy, pytest, traceability, palette, planned-film audits), in-Blender scene checks on a fresh
build, image checks on whatever frames are rendered, and, with ``--repo``, the repository checks.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from cff.story import timing
from tools import frames, pipeline, sync, toolchain, traceability

ROOT = toolchain.ROOT
CHECKS_JSON = ROOT / "renders" / "checks.json"


@dataclass
class Step:
    name: str
    passed: bool
    detail: str = ""
    seconds: float = 0.0
    lines: list[str] = field(default_factory=list)


def _run(name: str, command: list[str]) -> Step:
    started = time.perf_counter()
    done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    tail = (done.stdout + done.stderr).strip().splitlines()
    return Step(name, done.returncode == 0, tail[-1] if tail else "", time.perf_counter() - started, tail[-25:] if done.returncode != 0 else [])


def step_ruff() -> Step:
    return _run("ruff", [sys.executable, "-m", "ruff", "check", "."])


def step_mypy() -> Step:
    return _run("mypy --strict", [sys.executable, "-m", "mypy"])


def step_pytest() -> Step:
    return _run("pytest", [sys.executable, "-m", "pytest"])


def step_traceability() -> Step:
    text = traceability.render()
    current = traceability.OUTPUT.read_text(encoding="utf-8") if traceability.OUTPUT.exists() else ""
    missing = traceability.missing_ids(traceability.build_rows())
    ok = current == text and not missing
    return Step("traceability", ok, "current; every ID covered" if ok else ("stale" if current != text else f"uncovered: {missing[:5]}"))


def step_palette() -> Step:
    lines, bad = pipeline.palette_report()
    return Step("palette (L-07, CVD)", bad == 0, f"{len(lines)} pairs, {bad} failing", lines=[line for line in lines if line.startswith("FAIL")])


def step_motion() -> Step:
    lines, bad = pipeline.motion_report()
    return Step("planned-film audits (C-02/03/06/09)", bad == 0, lines[-1], lines=lines if bad else [])


def step_scene_checks() -> Step:
    started = time.perf_counter()
    code = pipeline.build("animatic")
    if code != 0:
        return Step("scene build", False, f"build_scene.py exited {code}", time.perf_counter() - started)
    log = ROOT / "renders" / "checks.log"
    log.unlink(missing_ok=True)
    code = toolchain.run_blender(ROOT / "blender" / "run_checks.py", pipeline.BLEND, ["--out", str(CHECKS_JSON)], log)
    results = json.loads(CHECKS_JSON.read_text(encoding="utf-8")) if CHECKS_JSON.exists() else []
    failed = [r for r in results if not r["passed"]]
    lines = [f"{r['name']}: {r['failure_count']} failure(s)" for r in failed]
    for r in failed:
        lines += [f"  {text}" for text in r["failures"][:6]]
    ok = code == 0 and bool(results) and not failed
    return Step("in-Blender scene checks", ok, f"{len(results)} checks, {len(failed)} failing (exit {code})", time.perf_counter() - started, lines)


def step_frames(tier: str = "animatic") -> Step:
    have = frames.present_frames(tier)
    if not have:
        return Step(f"rendered frames ({tier})", True, "none rendered yet (skipped)")
    last = timing.frame_end()
    missing = frames.missing_frames(tier)
    blank: list[int] = []
    if not missing:
        blank = frames.blank_frames(tier, timing.FRAME_START, last)
    ok = not blank
    detail = f"{len(have)}/{last} frames present, {len(missing)} missing, {len(blank)} blank"
    return Step(f"rendered frames ({tier})", ok, detail, lines=[f"blank frames: {blank[:20]}"] if blank else [])


def step_repo() -> Step:
    result = sync.check()
    return Step("repository (clean tree, HEAD == origin/main)", result.ok, f"HEAD {result.local_head[:8]} origin {(result.remote_head or '?')[:8]} clean {result.clean}")


def run(repo: bool = False, skip_blender: bool = False) -> int:
    steps: list[Callable[[], Step]] = [step_ruff, step_mypy, step_pytest, step_traceability, step_palette, step_motion]
    if not skip_blender:
        steps.append(step_scene_checks)
    steps.append(step_frames)
    if repo:
        steps.append(step_repo)
    failed = 0
    for factory in steps:
        step = factory()
        mark = "PASS" if step.passed else "FAIL"
        print(f"[{mark}] {step.name}: {step.detail} ({step.seconds:.1f}s)" if step.seconds else f"[{mark}] {step.name}: {step.detail}")
        for line in step.lines[:25]:
            print(f"        {line}")
        failed += 0 if step.passed else 1
    print("VERIFY GREEN" if failed == 0 else f"VERIFY FAILED ({failed} step(s))")
    return 0 if failed == 0 else 1
