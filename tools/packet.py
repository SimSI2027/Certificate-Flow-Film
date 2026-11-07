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

from cff.story.export import model_dump
from cff.story.model import MODEL

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


def _git_head() -> tuple[str, bool]:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True)
    return head.stdout.strip(), bool(status.stdout.strip())


def next_round(stage: str) -> int:
    existing = [p for p in ROUNDS.glob(f"{stage}-R*") if p.is_dir()]
    numbers = [int(p.name.rsplit("-R", 1)[1]) for p in existing if p.name.rsplit("-R", 1)[1].isdigit()]
    return max(numbers, default=0) + 1


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


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
