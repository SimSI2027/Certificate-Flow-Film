"""Frame utilities built on FFmpeg: blank-frame detection, caption compositing, motion strips and contact sheets.

Frame sets live in ``renders/<tier>/beauty`` and ``renders/<tier>/captions`` as ``f_####.png``.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from cff.story import captions as story_captions
from cff.story import model, timing
from cff.theme import render
from tools import toolchain

ROOT = toolchain.ROOT
BLANK_LUMA_SPREAD = 4.0  # a frame whose luma max-min is below this (0-255) is blank
BLANK_LUMA_MEAN = 2.0  # ... or whose mean luma is below this, except on the final black frames
STRIP_FRAMES = 6
STRIP_TILE_WIDTH = 480


def tier_dir(tier: str) -> Path:
    return ROOT / "renders" / tier


def frame_path(tier: str, layer: str, frame: int) -> Path:
    return tier_dir(tier) / layer / f"f_{frame:04d}.png"


def present_frames(tier: str, layer: str = "beauty") -> set[int]:
    folder = tier_dir(tier) / layer
    out: set[int] = set()
    for path in folder.glob("f_*.png"):
        if path.stat().st_size > 0:
            out.add(int(path.stem.split("_")[1]))
    return out


def missing_frames(tier: str, first: int = timing.FRAME_START, last: int | None = None) -> list[int]:
    last = timing.frame_end() if last is None else last
    have = present_frames(tier)
    return [f for f in range(first, last + 1) if f not in have]


def caption_frames() -> list[int]:
    """Frames on which some caption has any opacity (the only caption frames that need rendering)."""
    frames: set[int] = set()
    for caption in story_captions.CAPTIONS:
        first = timing.seconds_to_frame(caption.appear_s)
        last = timing.seconds_to_frame(caption.vanish_s)
        frames.update(range(first, last + 1))
    return sorted(f for f in frames if timing.FRAME_START <= f <= timing.frame_end())


def ranges(frames: list[int]) -> list[tuple[int, int]]:
    """Collapse sorted frames into inclusive contiguous ranges."""
    out: list[tuple[int, int]] = []
    for f in frames:
        if out and f == out[-1][1] + 1:
            out[-1] = (out[-1][0], f)
        else:
            out.append((f, f))
    return out


def chunk_ranges(frames: list[int], size: int = render.CHUNK_FRAMES) -> list[tuple[int, int]]:
    """Contiguous ranges of ``frames`` split into blocks of at most ``size`` frames."""
    out: list[tuple[int, int]] = []
    for a, b in ranges(frames):
        out.extend(render.chunks(a, b, size))
    return out


# --- blank-frame detection -----------------------------------------------------------------------


@dataclass(frozen=True)
class FrameStats:
    frame: int
    luma_min: float
    luma_max: float
    luma_mean: float

    @property
    def blank(self) -> bool:
        return (self.luma_max - self.luma_min) < BLANK_LUMA_SPREAD


def frame_stats(tier: str, first: int, last: int) -> list[FrameStats]:
    """Luma statistics for a contiguous frame range, from one FFmpeg signalstats pass."""
    source = tier_dir(tier) / "beauty" / "f_%04d.png"
    log = tier_dir(tier) / "stats.txt"
    result = toolchain.run_ffmpeg(["-start_number", str(first), "-framerate", str(timing.FPS), "-i", str(source), "-frames:v", str(last - first + 1),
                                   "-vf", f"signalstats,metadata=print:file={log.as_posix()}", "-f", "null", "-"])
    if result.returncode != 0:
        raise RuntimeError(f"signalstats failed: {result.stderr}")
    text = log.read_text(encoding="utf-8")
    log.unlink()
    stats: list[FrameStats] = []
    for index, block in enumerate(re.split(r"^frame:", text, flags=re.MULTILINE)[1:]):
        values = dict(re.findall(r"lavfi\.signalstats\.(YMIN|YMAX|YAVG)=([0-9.]+)", block))
        stats.append(FrameStats(first + index, float(values["YMIN"]), float(values["YMAX"]), float(values["YAVG"])))
    return stats


def blank_frames(tier: str, first: int, last: int) -> list[int]:
    """Frames that are blank, ignoring the deliberate black ending (the world fade, event E-09.3a, ends in black)."""
    fade = next(e for e in model.MODEL.events if e.id == "E-09.3a")
    fade_end = timing.seconds_to_frame(fade.end_s)
    return [s.frame for s in frame_stats(tier, first, last) if s.blank and s.frame < fade_end]


# --- compositing, strips, contact sheets -------------------------------------------------------------


def composite(tier: str, frame: int, out: Path) -> Path:
    """Beauty frame with its caption layer overlaid (straight alpha), as a PNG."""
    out.parent.mkdir(parents=True, exist_ok=True)
    beauty = frame_path(tier, "beauty", frame)
    caption = frame_path(tier, "captions", frame)
    if not caption.exists():
        shutil.copyfile(beauty, out)
        return out
    result = toolchain.run_ffmpeg(["-i", str(beauty), "-i", str(caption), "-filter_complex", "[0:v][1:v]overlay=format=auto,format=rgb24", "-frames:v", "1", str(out)])
    if result.returncode != 0:
        raise RuntimeError(f"composite failed for frame {frame}: {result.stderr}")
    return out


def tile(images: list[Path], out: Path, columns: int, width: int) -> Path:
    """Tile images into one PNG, each scaled to ``width`` pixels wide."""
    out.parent.mkdir(parents=True, exist_ok=True)
    args: list[str] = []
    for path in images:
        args += ["-i", str(path)]
    scaled = "".join(f"[{i}:v]scale={width}:-2[s{i}];" for i in range(len(images)))
    inputs = "".join(f"[s{i}]" for i in range(len(images)))
    graph = f"{scaled}{inputs}xstack=inputs={len(images)}:layout={_layout(len(images), columns, width)}:fill=black"
    result = toolchain.run_ffmpeg([*args, "-filter_complex", graph, "-frames:v", "1", str(out)])
    if result.returncode != 0:
        raise RuntimeError(f"tile failed: {result.stderr}")
    return out


def _layout(count: int, columns: int, width: int) -> str:
    height = round(width * 9 / 16)
    return "|".join(f"{(i % columns) * width}_{(i // columns) * height}" for i in range(count))


def beat_frames(beat_id: str) -> tuple[int, int]:
    return timing.frame_range(*timing.beat_window(beat_id))


def strip_frames(beat_id: str, count: int = STRIP_FRAMES) -> list[int]:
    first, last = beat_frames(beat_id)
    return [first + round((last - first) * i / (count - 1)) for i in range(count)]


def sample_frames(beat_id: str) -> list[int]:
    """Three judged frames per beat: just after entry, the middle, just before exit."""
    first, last = beat_frames(beat_id)
    return [first + 3, (first + last) // 2, last - 3]
