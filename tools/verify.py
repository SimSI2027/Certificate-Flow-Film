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
MP4_PENDING_RERENDER = False  # Session L1: was True from the F3-AUD-01/F3-PIPE-02 commit until the v1.2 re-render was encoded (2026-11-14)


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


MP4_TRUE_PEAK_MAX_DBFS = -1.0  # F3-AUD-01: measured on the AAC stream of the Final MP4, not on the WAV mix


def mp4_true_peak(stderr: str) -> float | None:
    """True peak in dBFS from the ``ebur128=peak=true`` summary (the last ``Peak:`` line), or None when absent."""
    found = re.findall(r"Peak:\s+(-?[0-9.]+|-inf)\s+dBFS", stderr)
    return float(found[-1]) if found else None


def step_final_mp4() -> Step:
    from tools import film  # noqa: PLC0415

    if not film.FINAL_MP4.exists():
        return Step("final MP4", True, "skipped (not built)")
    problems = mp4_problems(film.probe(film.FINAL_MP4))
    peak_run = toolchain.run_ffmpeg(["-loglevel", "info", "-i", str(film.FINAL_MP4), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
    peak = mp4_true_peak(peak_run.stderr)
    if peak is None:
        problems.append("true peak could not be measured")
    elif peak > MP4_TRUE_PEAK_MAX_DBFS:
        problems.append(f"AAC true peak {peak:.1f} dBFS is above {MP4_TRUE_PEAK_MAX_DBFS:.1f} dBFS")
    if film.METADATA.exists() and json.loads(film.METADATA.read_text(encoding="utf-8")).get("dirty") is True:
        problems.append("render-metadata.json says dirty: true (the render was made from uncommitted source)")
    if problems and MP4_PENDING_RERENDER:
        return Step("final MP4", True, f"PENDING re-render: {len(problems)} known problem(s) of the previous MP4", lines=problems)
    detail = "matches the delivery spec" if not problems else f"{len(problems)} problem(s)"
    return Step("final MP4", not problems, f"{detail}; true peak {peak} dBFS" if peak is not None and not problems else detail, lines=problems)


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


L2_CIN_01_FRAMES = (746, 1376, 1534, 1535)  # 1-based frames of the rig-light pops (L2-CIN-01): each step to the previous frame <= STEP_LIMIT
HERO_LUMA_MIN = 50.0  # V1-CIN-02 / v1.3: mean YAVG of B-09.2, and of the hold from HERO_WHOLE_FROM_S to the beat end
HERO_WHOLE_FROM_S = 98.5


def step_mp4_luma() -> Step:
    """L2-CIN-01 and the v1.3 hero: luma steps at the old pop frames and the hero brightness, measured on the Final MP4."""
    from tools import film, luma  # noqa: PLC0415

    if not film.FINAL_MP4.exists():
        return Step("MP4 luma (L2-CIN-01, hero)", True, "skipped (no final MP4)")
    yavg = luma.mp4_yavg(film.FINAL_MP4)
    problems = [f"f{f} step {abs(yavg[f] - yavg[f - 1]):.1f} > {luma.STEP_LIMIT}" for f in L2_CIN_01_FRAMES if abs(yavg[f] - yavg[f - 1]) > luma.STEP_LIMIT]
    beat_mean = luma.beat_means(yavg)["B-09.2"]
    first = timing.seconds_to_frame(HERO_WHOLE_FROM_S)
    last = timing.frame_range(*timing.beat_window("B-09.2"))[1]
    hold = [yavg[f] for f in range(first, last + 1)]
    hold_mean = sum(hold) / len(hold)
    problems += [f"{name} mean YAVG {value:.1f} < {HERO_LUMA_MIN}" for name, value in (("B-09.2", beat_mean), (f"f{first}-f{last}", hold_mean)) if value < HERO_LUMA_MIN]
    steps = ", ".join(f"f{f} {abs(yavg[f] - yavg[f - 1]):.1f}" for f in L2_CIN_01_FRAMES)
    return Step("MP4 luma (L2-CIN-01, hero)", not problems, f"steps {steps}; B-09.2 mean {beat_mean:.1f}, from {HERO_WHOLE_FROM_S} s {hold_mean:.1f}", lines=problems)


def step_repo() -> Step:
    result = sync.check()
    return Step("repository (clean tree, HEAD == origin/main)", result.ok, f"HEAD {result.local_head[:8]} origin {(result.remote_head or '?')[:8]} clean {result.clean}")


def run(repo: bool = False, skip_blender: bool = False) -> int:
    steps: list[Callable[[], list[Step]]] = [lambda f=f: [f()] for f in (step_ruff, step_mypy, step_pytest, step_traceability, step_palette, step_motion)]  # type: ignore[misc]
    if not skip_blender:
        steps.append(lambda: [step_scene_checks()])
    steps.append(step_frame_tiers)
    steps.append(lambda: [step_final_mp4(), step_cut_frames(), step_mp4_luma()])
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
