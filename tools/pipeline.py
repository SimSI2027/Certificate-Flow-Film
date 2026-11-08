"""Pipeline commands: env, build, render (chunked and resumable), captions, contact, palette, motion."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from cff.stage import audit, camera, choreography
from cff.story import captions as story_captions
from cff.story import model, timing
from cff.theme import palette_check, render
from tools import frames, toolchain

ROOT = toolchain.ROOT
BLEND = ROOT / "renders" / "film.blend"
SCRIPTS = ROOT / "blender"
OUTPUT = ROOT / "output"


# --- env --------------------------------------------------------------------------------------------------------------------------------------


def env_report() -> dict[str, object]:
    tools = toolchain.load()
    info: dict[str, object] = {"paths": {"blender": str(tools.blender), "ffmpeg": str(tools.ffmpeg), "ffprobe": str(tools.ffprobe), "python": str(tools.python)}}
    info["exists"] = {k: Path(v).exists() for k, v in info["paths"].items()}  # type: ignore[attr-defined]
    blender = subprocess.run([str(tools.blender), "--version"], capture_output=True, text=True, check=False)
    info["blender"] = blender.stdout.splitlines()[0] if blender.stdout else blender.stderr[:200]
    ffmpeg = subprocess.run([str(tools.ffmpeg), "-version"], capture_output=True, text=True, check=False)
    info["ffmpeg"] = ffmpeg.stdout.splitlines()[0]
    info["pinned"] = {"blender": tools.blender_version, "ffmpeg": tools.ffmpeg_version}
    info["ok"] = all(info["exists"].values()) and tools.blender_version.split()[0] in str(info["blender"])  # type: ignore[attr-defined]
    return info


# --- build --------------------------------------------------------------------------------------------------------------------------------


def build(tier: str = "animatic") -> int:
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    return toolchain.run_blender(SCRIPTS / "build_scene.py", args=["--out", str(BLEND), "--tier", tier])


# --- render -------------------------------------------------------------------------------------------------------------------------------


def progress_path(tier: str) -> Path:
    return frames.tier_dir(tier) / "progress.json"


def write_progress(tier: str, payload: dict[str, object]) -> None:
    path = progress_path(tier)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")


def render_layer(tier: str, layer: str, wanted: list[int], rebuild: bool = False, *, blend: Path = BLEND, frames_dir: str | None = None) -> int:
    """Render the frames in ``wanted`` that are not yet on disk, in resumable chunks. Returns a process-style exit code.

    ``frames_dir`` (default: the tier name) is the folder under ``renders/`` that holds the frames; ``blend`` is the file rendered.
    """
    scene = frames.LAYER_SCENES[layer]
    where = frames_dir or tier
    out_dir = frames.tier_dir(where) / layer
    have = frames.present_frames(where, layer)
    todo = [f for f in wanted if f not in have]
    chunks = frames.chunk_ranges(todo)
    log = frames.tier_dir(where) / f"render-{layer}.log"
    started = time.perf_counter()
    done = 0
    if blend == BLEND and (rebuild or not BLEND.exists()):
        code = build(tier)
        if code != 0:
            return code
    for first, last in chunks:
        code = toolchain.run_blender(SCRIPTS / "render_frames.py", blend, ["--scene", scene, "--first", str(first), "--last", str(last), "--out", str(out_dir), "--tier", tier], log)
        if code != 0:
            write_progress(where, {"layer": layer, "status": "failed", "chunk": [first, last], "exit_code": code})
            return code
        done += last - first + 1
        write_progress(where, {"layer": layer, "status": "running", "frames_done_this_run": done, "frames_todo": len(todo),
                               "present": len(frames.present_frames(where, layer)), "of": len(wanted), "elapsed_s": round(time.perf_counter() - started, 1), "last_chunk": [first, last]})
    write_progress(where, {"layer": layer, "status": "complete", "present": len(frames.present_frames(where, layer)), "of": len(wanted), "elapsed_s": round(time.perf_counter() - started, 1)})
    return 0


def render_frame_list(tier: str, layer: str, wanted: list[int], blend: Path, frames_dir: str) -> int:
    """Render scattered frames (a packet's samples) in batches of one Blender call per chunk; resumable."""
    scene = frames.LAYER_SCENES[layer]
    out_dir = frames.tier_dir(frames_dir) / layer
    have = frames.present_frames(frames_dir, layer)
    todo = sorted(f for f in set(wanted) if f not in have)
    log = frames.tier_dir(frames_dir) / f"render-{layer}.log"
    for start in range(0, len(todo), render.CHUNK_FRAMES):
        batch = ",".join(str(f) for f in todo[start : start + render.CHUNK_FRAMES])
        code = toolchain.run_blender(SCRIPTS / "render_frames.py", blend, ["--scene", scene, "--frames", batch, "--out", str(out_dir), "--tier", tier], log)
        if code != 0:
            return code
    return 0


def render_all(tier: str, scene: str = "all", first: int | None = None, last: int | None = None, rebuild: bool = False) -> int:
    first = timing.FRAME_START if first is None else first
    last = timing.frame_end() if last is None else last
    wanted = list(range(first, last + 1))
    if scene in ("all", "BEAUTY"):
        code = render_layer(tier, "beauty", wanted, rebuild)
        if code != 0:
            return code
    if scene in ("all", "SIGNS"):
        code = render_layer(tier, "signs", [f for f in frames.sign_frames() if first <= f <= last])
        if code != 0:
            return code
    if scene in ("all", "CAPTIONS"):
        needed = [f for f in frames.caption_frames() if first <= f <= last]
        return render_layer(tier, "captions", needed)
    return 0


# --- captions -----------------------------------------------------------------------------------------------------------------------------


def vtt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def captions_vtt() -> str:
    lines = ["WEBVTT", ""]
    for cap in story_captions.captions_in_order():
        lines += [cap.id, f"{vtt_time(cap.hold_start_s)} --> {vtt_time(cap.hold_end_s)}", cap.text, ""]
    return "\n".join(lines)


def transcript_md() -> str:
    lines = ["# Transcript", "", "Generated from `cff/story/captions.py`. Times are the full-opacity hold of each caption.", ""]
    by_scene: dict[str, list[story_captions.Caption]] = {}
    for cap in story_captions.captions_in_order():
        by_scene.setdefault(cap.scene, []).append(cap)
    titles = {s.id: s.title for s in model.MODEL.scenes}
    for scene_id, caps in by_scene.items():
        lines += [f"## {scene_id} — {titles.get(scene_id, '')}", ""]
        lines += [f"- {vtt_time(c.hold_start_s)}–{vtt_time(c.hold_end_s)} — {c.text}" for c in caps]
        lines.append("")
    return "\n".join(lines)


def write_captions(out_dir: Path = OUTPUT) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / "captions.vtt", out_dir / "transcript.md"]
    paths[0].write_text(captions_vtt(), encoding="utf-8", newline="\n")
    paths[1].write_text(transcript_md(), encoding="utf-8", newline="\n")
    return paths


# --- contact sheet, palette, motion ------------------------------------------------------------------------------------------------------


def contact_sheet(tier: str, out: Path | None = None) -> Path:
    """One tile per beat (the middle frame, composited with captions), 6 columns."""
    out = out or OUTPUT / tier / "contact-sheet.png"
    work = frames.tier_dir(tier) / "contact"
    images = [frames.composite(tier, frames.sample_frames(beat.id)[1], work / f"{beat.id}.png") for beat in model.MODEL.beats]
    return frames.tile(images, out, columns=6, width=320)


def palette_report() -> tuple[list[str], int]:
    lines = []
    for p in palette_check.pairs():
        flag = "ok " if p.passed else "FAIL"
        lines.append(f"{flag} {p.condition:13s} {p.a.value:16s} {p.b.value:16s} dE00 {p.delta_e:5.1f} (min {p.minimum:g})")
    return lines, len(palette_check.failures())


def motion_report() -> tuple[list[str], int]:
    """The planned-film audits: camera (C-02, C-03, C-09), keys and glow (C-06, C-08). Pops are reported, not failed."""
    timeline = choreography.build_timeline()
    plan = camera.CameraPlan(timeline)
    beat_focal = camera.subject_ids()
    findings: list[audit.Finding] = []
    findings += audit.audit_camera_steps(plan)
    findings += audit.audit_not_frontal(plan)
    findings += audit.audit_keys(timeline)
    findings += audit.audit_glow_range(timeline)
    focal = audit.audit_focal(plan, timeline, beat_focal)
    hard_focal = [f for f in focal if f.where not in audit.C03_OPEN_BEATS]
    advisory = [f for f in focal if f.where in audit.C03_OPEN_BEATS]
    findings += hard_focal
    pops = audit.audit_pops(timeline, plan, frozenset())
    lines = [str(f) for f in findings[:80]]
    lines += [f"advisory (open for the Stage 1 rounds) {f}" for f in advisory]
    lines.append(f"{len(findings)} hard finding(s), {len(advisory)} advisory; camera frames {len(plan.frames())}, cuts {plan.cut_frames}, "
                 f"objects animated {len(timeline.objects())}, screen-pop candidates {len(pops)} (measured in Blender by scene checks)")
    return lines, len(findings)
