"""Toolchain paths and the standard Blender invocation (Charter 5.2).

Paths come from the gitignored ``config/toolchain.local.json``; nothing machine-specific is hard-coded.
Every Blender call is ``"<blender.exe>" -b [file.blend] --factory-startup --python-exit-code 1 -P <script.py> -- <args>``.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "toolchain.local.json"


@dataclass(frozen=True)
class Toolchain:
    blender: Path
    ffmpeg: Path
    ffprobe: Path
    python: Path
    blender_version: str
    ffmpeg_version: str


def load() -> Toolchain:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    return Toolchain(
        blender=Path(data["blender"]["exe"]),
        ffmpeg=Path(data["ffmpeg"]["exe"]),
        ffprobe=Path(data["ffmpeg"]["ffprobe"]),
        python=ROOT / data["python"]["interpreter"],
        blender_version=data["blender"]["version"],
        ffmpeg_version=data["ffmpeg"]["version"],
    )


def blender_command(script: Path, blend: Path | None = None, args: list[str] | None = None) -> list[str]:
    tools = load()
    command = [str(tools.blender), "-b"]
    if blend is not None:
        command.append(str(blend))
    command += ["--factory-startup", "--python-exit-code", "1", "-P", str(script)]
    command += ["--", *(args or [])]
    return command


def run_blender(script: Path, blend: Path | None = None, args: list[str] | None = None, log: Path | None = None) -> int:
    """Run one Blender script; stdout and stderr go to ``log`` if given. Returns the process exit code."""
    command = blender_command(script, blend, args)
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8", newline="\n") as handle:
            return subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, check=False).returncode
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def run_ffmpeg(args: list[str]) -> subprocess.CompletedProcess[str]:
    tools = load()
    return subprocess.run([str(tools.ffmpeg), "-hide_banner", "-loglevel", "error", "-y", *args], cwd=ROOT, capture_output=True, text=True, check=False)
