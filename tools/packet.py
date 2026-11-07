"""Round packets (Charter 2.4). Stage 0 packets judge the written spec: no frames exist yet.

A packet holds only judgeable material: frozen docs, a model dump, the findings schema,
the regressions list and a manifest. It never holds source code, commit messages,
generator notes or claims of success.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from cff.stage import camera, choreography, labels
from cff.story import timing
from cff.story.export import model_dump
from cff.story.model import MODEL
from tools import frames

ROOT = Path(__file__).resolve().parents[1]
ROUNDS = ROOT / "qa" / "rounds"
SCHEMA = ROOT / "qa" / "schema.json"
REGRESSIONS = ROOT / "qa" / "regressions.json"
SPEC = ROOT / "docs" / "REFERENCE-SPEC.md"

FROZEN_FILES = ("docs/REFERENCE-SPEC.md", "docs/GLOSSARY.md", "docs/PKI-TECHNICAL-NOTES.md")
STAGE0_DOCS = (*FROZEN_FILES, "docs/STORYBOARD.md")

STAGE0_README = """# Stage 0 round packet: written specification

This packet is for judging the written specification. No frames exist at Stage 0, so
there are no images or motion strips. Judge the text and the model dump instead.

Contents:
- `docs/REFERENCE-SPEC.md`, `docs/GLOSSARY.md`, `docs/PKI-TECHNICAL-NOTES.md` (the frozen-file candidates)
- `docs/STORYBOARD.md` (what each beat will show on screen)
- `model-dump.json` (the story data the film is generated from: actors, keys, certificates,
  templates, CAs, CRLs, requests, discoveries, chains, labels, events and captions with timings)
- `schema.json` (the required report format)
- `regressions.json` (previously accepted findings to re-check; may be empty)
- `manifest.json` (file list with SHA-256, beat list, spec hash)

For every beat B-xx, give a verdict ACCURATE, MISLEADING or WRONG against facts F-01..F-17
and architecture AR-01..AR-07, citing the document sections and model-dump entries
(event, certificate or label IDs) in the `frames` field in place of frame files.
Report findings with severities as defined in `schema.json` and in REFERENCE-SPEC.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head(ignore_prefix: str | None = None) -> tuple[str, bool]:
    """HEAD and whether the tree is dirty (paths under ``ignore_prefix``, e.g. packets built from the same commit, are ignored)."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True)
    lines = [line for line in status.stdout.splitlines() if line.strip() and not (ignore_prefix and line[3:].startswith(ignore_prefix))]
    return head.stdout.strip(), bool(lines)


def next_round(stage: str) -> int:
    existing = [p for p in ROUNDS.glob(f"{stage}-R*") if p.is_dir()]
    numbers = [int(p.name.rsplit("-R", 1)[1]) for p in existing if p.name.rsplit("-R", 1)[1].isdigit()]
    return max(numbers, default=0) + 1


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


STAGE1_README = """# Stage 1 round packet: animatic (grey-box, 960x540)

Judge the animatic as film, not as a diagram, against the frozen spec (REFERENCE-SPEC criteria C-01..C-11,
L-01..L-08, facts F-01..F-17, architecture AR-01..AR-07).

Contents:
- `frames/`: composited animatic frames (3D beauty pass + caption layer). Three per beat (`B-xx.y_a/b/c`: just after
  entry, middle, just before exit) and the frames on both sides of each cut (`T-cut-*`).
- `strips/`: one motion strip per beat (6 frames from first to last, left to right, top to bottom).
- `shots.json`: per beat, the model's focal subject and the camera lens, f-stop and focus distance at the middle frame.
- `model-dump.json`: the story data (events, certificates, labels, captions with timings).
- `docs/`: the frozen spec, glossary, PKI notes and the storyboard.
- `schema.json`: the required report format. `regressions.json`: previously accepted findings to re-check.
- `manifest.json`: every file with its SHA-256, the frame list and the spec hash.

For each beat give a PKI verdict (ACCURATE, MISLEADING or WRONG) citing frame file names; report findings with
severities as defined in `schema.json`. Grey-box geometry is expected at this stage: judge composition, motion,
legibility, colour language and accuracy, not surface finish.

Judging protocol (every reviewer):
- Open every file in `frames/` and `strips/`, and list each one in `files_read`. Never judge a beat from a sample.
- Track persistent objects across beats, not frame by frame in isolation. In particular, follow every private key
  (each server's key and each CA's module key) from the moment it forms to the end of the film, and every request
  capsule from its creation to the place it is consumed. Once stored, a private key must stay inside its own locked
  container or sealed module; a key outside it, beside or attached to a capsule, travelling with anything, or an
  emptied container, is a key violation even when the shape is small or partly hidden.
- PKI reviewers: from the beat where a private key forms onward, every beat's verdict `reason` must state where each
  formed private key is in that beat's frames and strip tiles (for example "RDP key: inside its locked container, all
  tiles"), comparing its shape with the key you saw form and lock. If a key cannot be located, or a key-like shape
  appears outside a container or module, the verdict is WRONG and the finding is a BLOCKER (F-03), unless you can
  positively identify the shape as something else. When in doubt, report the BLOCKER and say why.
"""


def _frame_entry(path: Path, folder: Path, beat: str | None, frame: int | None) -> dict[str, object]:
    return {"path": path.relative_to(folder).as_posix(), "beat": beat, "frame": frame, "sha256": sha256(path)}


def stage1_frames() -> list[int]:
    """Every frame a Stage 1 packet shows: three samples per beat, both sides of each cut, and the motion-strip frames."""
    wanted: set[int] = set()
    for beat in MODEL.beats:
        wanted.update(frames.sample_frames(beat.id))
        wanted.update(frames.strip_frames(beat.id))
    for cut_beat in timing.DECLARED_CUT_BEATS:
        first = timing.seconds_to_frame(timing.beat_window(cut_beat)[0])
        wanted.update((first - 1, first))
    return sorted(wanted)


def build_stage1(round_number: int | None = None, tier: str = "animatic", folder: Path | None = None, round_name: str | None = None) -> Path:
    """A Stage 1 packet: composited frames, motion strips, shots.json, manifest, regressions and schema. No source, no claims.

    A real round needs every frame of ``tier`` rendered. A calibration packet (``folder`` and ``round_name`` given, ``tier`` naming
    its frames folder under ``renders/``) needs only the frames the packet shows. Both look the same to a discriminator.
    """
    if folder is None:
        missing = frames.missing_frames(tier)
        number = next_round("stage1") if round_number is None else round_number
        folder = ROUNDS / f"stage1-R{number}"
        round_name = f"stage1-R{number}"
    else:
        have = frames.present_frames(tier)
        missing = [f for f in stage1_frames() if f not in have]
    if missing:
        raise RuntimeError(f"{len(missing)} {tier} frames are not rendered yet (first missing: {missing[0]})")
    if folder.exists():
        raise FileExistsError(f"{folder} already exists; packets are immutable")
    candidate, dirty = _git_head(ignore_prefix=folder.parent.relative_to(ROOT).as_posix() + "/")
    if dirty:
        raise RuntimeError("working tree is dirty: commit the candidate before building its packet")
    (folder / "docs").mkdir(parents=True)
    for rel in STAGE0_DOCS:
        shutil.copyfile(ROOT / rel, folder / rel)
    frame_entries: list[dict[str, object]] = []
    for beat in MODEL.beats:
        for letter, frame in zip("abc", frames.sample_frames(beat.id), strict=True):
            out = frames.composite(tier, frame, folder / "frames" / f"{beat.id}_{letter}_f{frame:04d}.png")
            frame_entries.append(_frame_entry(out, folder, beat.id, frame))
    for cut_beat in timing.DECLARED_CUT_BEATS:
        first = timing.seconds_to_frame(timing.beat_window(cut_beat)[0])
        for frame in (first - 1, first):
            out = frames.composite(tier, frame, folder / "frames" / f"T-cut-{cut_beat}_f{frame:04d}.png")
            frame_entries.append(_frame_entry(out, folder, cut_beat, frame))
    strip_entries: list[dict[str, object]] = []
    for beat in MODEL.beats:
        picks = frames.strip_frames(beat.id)
        images = [frames.composite(tier, f, folder / "strips" / "tmp" / f"{beat.id}_{f:04d}.png") for f in picks]
        strip = frames.tile(images, folder / "strips" / f"{beat.id}_strip.png", columns=3, width=frames.STRIP_TILE_WIDTH)
        strip_entries.append({**_frame_entry(strip, folder, beat.id, None), "frames": picks})
    shutil.rmtree(folder / "strips" / "tmp")
    timeline = choreography.build_timeline()
    labels.add_label_tracks(timeline)
    plan = camera.CameraPlan(timeline)
    shots_data = []
    for beat in MODEL.beats:
        mid = frames.sample_frames(beat.id)[1]
        state = plan.state(mid)
        shots_data.append({"beat": beat.id, "focal_subject": beat.focal, "frame": mid, "lens_mm": round(state.lens, 1), "f_stop": round(state.fstop, 2),
                           "focus_distance_m": round(state.focus_distance, 2)})
    _write_json(folder / "shots.json", shots_data)
    _write_json(folder / "model-dump.json", model_dump())
    shutil.copyfile(SCHEMA, folder / "schema.json")
    regressions = json.loads(REGRESSIONS.read_text(encoding="utf-8")) if REGRESSIONS.exists() else []
    _write_json(folder / "regressions.json", regressions)
    (folder / "README.md").write_text(STAGE1_README, encoding="utf-8", newline="\n")
    files = sorted(p for p in folder.rglob("*") if p.is_file())
    manifest = {
        "stage": "stage1",
        "round": round_name,
        "tier": "animatic",
        "candidate": candidate,
        "spec_sha256": sha256(SPEC),
        "frozen_files": list(FROZEN_FILES),
        "beats": [b.id for b in MODEL.beats],
        "frames": frame_entries,
        "motion_strips": strip_entries,
        "files": [{"path": p.relative_to(folder).as_posix(), "sha256": sha256(p)} for p in files],
    }
    _write_json(folder / "manifest.json", manifest)
    return folder


def build_stage0(round_number: int | None = None) -> Path:
    number = next_round("stage0") if round_number is None else round_number
    folder = ROUNDS / f"stage0-R{number}"
    if folder.exists():
        raise FileExistsError(f"{folder} already exists; packets are immutable")
    candidate, dirty = _git_head()
    if dirty:
        raise RuntimeError("working tree is dirty: commit the candidate before building its packet")
    (folder / "docs").mkdir(parents=True)
    for rel in STAGE0_DOCS:
        shutil.copyfile(ROOT / rel, folder / rel)
    _write_json(folder / "model-dump.json", model_dump())
    shutil.copyfile(SCHEMA, folder / "schema.json")
    regressions = json.loads(REGRESSIONS.read_text(encoding="utf-8")) if REGRESSIONS.exists() else []
    _write_json(folder / "regressions.json", regressions)
    (folder / "README.md").write_text(STAGE0_README, encoding="utf-8", newline="\n")
    files = sorted(p for p in folder.rglob("*") if p.is_file())
    manifest = {
        "stage": "stage0",
        "round": f"stage0-R{number}",
        "candidate": candidate,
        "spec_sha256": sha256(SPEC),
        "frozen_files": list(FROZEN_FILES),
        "beats": [b.id for b in MODEL.beats],
        "frames": [],
        "motion_strips": [],
        "files": [{"path": p.relative_to(folder).as_posix(), "sha256": sha256(p)} for p in files],
    }
    _write_json(folder / "manifest.json", manifest)
    return folder
