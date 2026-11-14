"""``python -m tools verify``: every persistent hard discriminator in one run (Charter Section 12).

Pure Python (ruff, mypy, pytest, traceability, palette, planned-film audits), in-Blender scene checks on a fresh
build, image checks on whatever frames are rendered, and, with ``--repo``, the repository checks.
"""

from __future__ import annotations

import json
import re
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


FINAL_TIER = "final"
CUT_FRAMES = (1246, 1396)  # 1-based frames of the two cuts (V1-CIN-04)
CUT_LUMA_STEP_MAX = 3.0
EXPECTED_VIDEO = {"codec_name": "h264", "width": 1920, "height": 1080, "r_frame_rate": "30/1", "color_transfer": "bt709", "level": 41}  # V1-ENC-01
DURATION_TOLERANCE_S = 0.05
# The v1.0.0 MP4 predated the F1 fixes (blended cut frames, sRGB transfer tag, level 5.0). While this was True the two MP4 steps
# reported those known problems without failing. Session F2 set it to False after the final re-render: the MP4 checks are binding.
MP4_PENDING_RERENDER = False


def step_frame_tiers() -> list[Step]:
    """V1-PIPE-01: the frame check runs for every tier that has rendered beauty frames, one line per tier."""
    tiers = [t for t in ("animatic", FINAL_TIER) if frames.present_frames(t)]
    return [step_frames(t) for t in tiers] or [step_frames("animatic")]


def mp4_problems(info: dict[str, object]) -> list[str]:
    """Compare ffprobe output with the delivery spec; an empty list means the MP4 is as specified."""
    streams = [s for s in info.get("streams", []) if isinstance(s, dict)]  # type: ignore[attr-defined]
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    problems = [f"video {k}={video.get(k)!r}, want {v!r}" for k, v in EXPECTED_VIDEO.items() if video.get(k) != v]
    if str(video.get("nb_frames")) != str(timing.frame_end()):
        problems.append(f"video nb_frames={video.get('nb_frames')!r}, want {timing.frame_end()}")
    if audio.get("codec_name") != "aac" or str(audio.get("sample_rate")) != "48000" or audio.get("channels") != 2:
        problems.append(f"audio {audio.get('codec_name')}/{audio.get('sample_rate')}/{audio.get('channels')}, want aac/48000/2")
    fmt = info.get("format", {})
    duration = float(fmt.get("duration", 0.0)) if isinstance(fmt, dict) else 0.0
    if abs(duration - timing.total_duration_s()) > DURATION_TOLERANCE_S:
        problems.append(f"duration {duration:.3f} s, want {timing.total_duration_s():.3f} s")
    return problems


def step_final_mp4() -> Step:
    from tools import film  # noqa: PLC0415

    if not film.FINAL_MP4.exists():
        return Step("final MP4", True, "skipped (not built)")
    problems = mp4_problems(film.probe(film.FINAL_MP4))
    if problems and MP4_PENDING_RERENDER:
        return Step("final MP4", True, f"PENDING F2 re-render: {len(problems)} known v1.0.0 problem(s)", lines=problems)
    return Step("final MP4", not problems, "matches the delivery spec" if not problems else f"{len(problems)} problem(s)", lines=problems)


def cut_luma_steps(text: str) -> dict[int, float]:
    """Parse signalstats output into frame index -> YAVG, in order of appearance."""
    return {i: float(v) for i, v in enumerate(re.findall(r"lavfi\.signalstats\.YAVG=([0-9.]+)", text))}


def step_cut_frames() -> Step:
    """V1-CIN-04: each cut frame must be one shot, not a blend of both (luma equal to its neighbour within a small step)."""
    from tools import film  # noqa: PLC0415

    if not film.FINAL_MP4.exists():
        return Step("cut frames", True, "skipped (no final MP4)")
    log = ROOT / "renders" / "cuts-stats.txt"
    select = "+".join(f"between(n,{f - 1},{f})" for f in CUT_FRAMES)  # 0-based n: the cut frame and the next one
    done = toolchain.run_ffmpeg(["-i", str(film.FINAL_MP4), "-an", "-vf", f"select='{select}',signalstats,metadata=print:file={log.relative_to(ROOT).as_posix()}", "-f", "null", "-"])
    if done.returncode != 0 or not log.exists():
        return Step("cut frames", False, f"ffmpeg failed: {done.stderr[-200:]}")
    values = cut_luma_steps(log.read_text(encoding="utf-8"))
    log.unlink()
    steps = [abs(values[2 * i] - values[2 * i + 1]) for i in range(len(CUT_FRAMES)) if 2 * i + 1 in values]
    ok = len(steps) == len(CUT_FRAMES) and all(s <= CUT_LUMA_STEP_MAX for s in steps)
    if not ok and MP4_PENDING_RERENDER:
        return Step("cut frames", True, "PENDING F2 re-render: v1.0.0 cut frames are blends (" + ", ".join(f"{s:.1f}" for s in steps) + ")")
    return Step("cut frames", ok, "luma steps " + ", ".join(f"{s:.1f}" for s in steps), lines=[] if ok else [f"limit {CUT_LUMA_STEP_MAX}"])


def step_repo() -> Step:
    result = sync.check()
    return Step("repository (clean tree, HEAD == origin/main)", result.ok, f"HEAD {result.local_head[:8]} origin {(result.remote_head or '?')[:8]} clean {result.clean}")


def run(repo: bool = False, skip_blender: bool = False) -> int:
    steps: list[Callable[[], list[Step]]] = [lambda f=f: [f()] for f in (step_ruff, step_mypy, step_pytest, step_traceability, step_palette, step_motion)]  # type: ignore[misc]
    if not skip_blender:
        steps.append(lambda: [step_scene_checks()])
    steps.append(step_frame_tiers)
    steps.append(lambda: [step_final_mp4(), step_cut_frames()])
    if repo:
        steps.append(lambda: [step_repo()])
    failed = 0
    for step in (s for factory in steps for s in factory()):
        mark = "PASS" if step.passed else "FAIL"
        print(f"[{mark}] {step.name}: {step.detail} ({step.seconds:.1f}s)" if step.seconds else f"[{mark}] {step.name}: {step.detail}")
        for line in step.lines[:25]:
            print(f"        {line}")
        failed += 0 if step.passed else 1
    print("VERIFY GREEN" if failed == 0 else f"VERIFY FAILED ({failed} step(s))")
    return 0 if failed == 0 else 1
