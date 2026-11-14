"""Luma measurement (docs/LOOK-PLAN-v1.2.md, Appendix A): FFmpeg ``signalstats`` on PNG stills and on the Final MP4.

Stills are converted the way the encode does (BT.709, video range, 8-bit) so that YAVG on a PNG matches YAVG on the MP4.
Film frame numbers are 1-based, as in the render folders.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from cff.story import timing
from tools import toolchain

ROOT = toolchain.ROOT
CUT_FRAMES = frozenset({1246, 1247, 1396, 1397})  # the two cuts and their next frames; luma jumps there by design
STEP_LIMIT = 4.0
STATS_FILE = ROOT / "renders" / "luma-stats.txt"
PNG_FILTER = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,signalstats,metadata=print:file="


@dataclass(frozen=True)
class Still:
    yavg: float
    ylow: float
    satavg: float


def _parse(text: str, keys: tuple[str, ...]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for line in text.splitlines():
        if line.startswith("frame:"):
            rows.append({})
            continue
        m = re.match(r"lavfi\.signalstats\.(\w+)=([\d.]+)", line)
        if m and m.group(1) in keys and rows:
            rows[-1][m.group(1)] = float(m.group(2))
    return rows


def png_stats(path: Path) -> Still:
    """YAVG, YLOW (10th percentile of luma) and SATAVG of one PNG still."""
    rel = STATS_FILE.relative_to(ROOT).as_posix()
    done = toolchain.run_ffmpeg(["-i", str(path), "-vf", PNG_FILTER + rel, "-frames:v", "1", "-f", "null", "-"])
    if done.returncode != 0 or not STATS_FILE.exists():
        raise RuntimeError(f"signalstats failed on {path}: {done.stderr[-200:]}")
    rows = _parse(STATS_FILE.read_text(encoding="utf-8"), ("YAVG", "YLOW", "SATAVG"))
    STATS_FILE.unlink()
    return Still(rows[0]["YAVG"], rows[0]["YLOW"], rows[0]["SATAVG"])


def mp4_yavg(mp4: Path) -> dict[int, float]:
    """YAVG per film frame (1-based) of an MP4."""
    rel = STATS_FILE.relative_to(ROOT).as_posix()
    done = toolchain.run_ffmpeg(["-i", str(mp4), "-an", "-vf", f"signalstats,metadata=print:file={rel}", "-f", "null", "-"])
    if done.returncode != 0 or not STATS_FILE.exists():
        raise RuntimeError(f"signalstats failed on {mp4}: {done.stderr[-200:]}")
    rows = _parse(STATS_FILE.read_text(encoding="utf-8"), ("YAVG",))
    STATS_FILE.unlink()
    return {i + 1: row["YAVG"] for i, row in enumerate(rows)}


def beat_means(yavg: dict[int, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for beat, (start, end) in timing.beat_windows().items():
        first, last = timing.frame_range(start, end)
        values = [yavg[f] for f in range(first, last + 1) if f in yavg]
        out[beat] = sum(values) / len(values) if values else 0.0
    return out


def steps_above(yavg: dict[int, float], limit: float = STEP_LIMIT) -> list[tuple[int, float]]:
    """Frame-to-frame YAVG steps above ``limit``, excluding the cut frames."""
    return [(f, abs(yavg[f] - yavg[f - 1])) for f in sorted(yavg) if f - 1 in yavg and f not in CUT_FRAMES and abs(yavg[f] - yavg[f - 1]) > limit]
