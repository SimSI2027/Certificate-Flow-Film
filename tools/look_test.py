"""``python -m tools look-test``: the stills-and-strips gate of docs/LOOK-PLAN-v1.2.md, Section 5.

Renders the beauty pass at the final tier into ``renders/look-test`` (never ``renders/final``: the final render skips frames that
are already on disk), measures them with ``signalstats`` and prints PASS or FAIL for the checks of Items A and C and the haze
stability strip. Run ``python -m tools build --tier final`` first. Also writes the two images the gate views.
"""

from __future__ import annotations

import shutil

from cff.theme import look
from tools import frames, luma, pipeline

LOOK_TEST = "look-test"
STILLS = (457, 943, 1204, 1700, 2058, 2950, 2980, 3010, 3040, 3070, 3100, 3118)
HERO_FRAMES = (2950, 2980, 3010, 3040, 3070, 3100, 3118)  # the seven-frame stand-in for the B-09.2 mean
HERO_STRIP = tuple(range(3040, 3111, 10))  # eight frames for the strip image
STRIPS = {"flash at 81 s (item C)": (2420, 2440), "flash at 90 s (item C)": (2695, 2715), "chain docking (haze stability)": (1600, 1623)}
HERO_MEAN_RANGE = (50.0, 62.0)
HERO_YLOW_MAX = 40.0
HERO_SATAVG_MIN = 12.0
F457_MIN, F2058_MAX = 45.0, 70.0
F943_RANGE = (55.0, 75.0)
STILL_MAX = 75.0
STEP_MAX = luma.STEP_LIMIT
SHEET_COLUMNS, SHEET_TILE_PX = 4, 480
OUT_DIR = frames.tier_dir(LOOK_TEST)
SHEET = OUT_DIR / "stills-sheet.png"
STRIP = OUT_DIR / "hero-strip.png"


def wanted_frames() -> list[int]:
    out = set(STILLS) | set(HERO_STRIP)
    for first, last in STRIPS.values():
        out |= set(range(first, last + 1))
    return sorted(out)


def _verdict(name: str, ok: bool, detail: str, results: list[bool]) -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)  # existing frames would be skipped by the renderer
    wanted = wanted_frames()
    print(f"rendering {len(wanted)} final-tier beauty frames into {OUT_DIR}")
    code = pipeline.render_frame_list("final", "beauty", wanted, pipeline.BLEND, LOOK_TEST)
    if code != 0:
        print("render failed")
        return code
    stats = {f: luma.png_stats(frames.frame_path(LOOK_TEST, "beauty", f)) for f in wanted}
    results: list[bool] = []
    print("\nframe   YAVG   YLOW  SATAVG")
    for f in STILLS:
        s = stats[f]
        print(f"f{f:<5} {s.yavg:6.1f} {s.ylow:6.1f} {s.satavg:6.1f}")
    hero_mean = sum(stats[f].yavg for f in HERO_FRAMES) / len(HERO_FRAMES)
    print()
    _verdict("hero mean YAVG (B-09.2, seven frames)", HERO_MEAN_RANGE[0] <= hero_mean <= HERO_MEAN_RANGE[1], f"{hero_mean:.1f} (want {HERO_MEAN_RANGE[0]}..{HERO_MEAN_RANGE[1]})", results)
    if hero_mean < HERO_MEAN_RANGE[0]:
        print(f"      tuning rule: raise HAZE_DENSITY from {look.HAZE_DENSITY} by {look.HAZE_DENSITY_STEP} (max {look.HAZE_DENSITY_MAX})")
    elif hero_mean > HERO_MEAN_RANGE[1]:
        print(f"      tuning rule: lower HAZE_DENSITY from {look.HAZE_DENSITY} by {look.HAZE_DENSITY_STEP} (min {look.HAZE_DENSITY_MIN})")
    _verdict("f3100 YLOW", stats[3100].ylow <= HERO_YLOW_MAX, f"{stats[3100].ylow:.1f} (want <= {HERO_YLOW_MAX})", results)
    _verdict("f3100 SATAVG", stats[3100].satavg >= HERO_SATAVG_MIN, f"{stats[3100].satavg:.1f} (want >= {HERO_SATAVG_MIN})", results)
    _verdict("f457 YAVG", stats[457].yavg >= F457_MIN, f"{stats[457].yavg:.1f} (want >= {F457_MIN})", results)
    _verdict("f2058 YAVG", stats[2058].yavg <= F2058_MAX, f"{stats[2058].yavg:.1f} (want <= {F2058_MAX})", results)
    _verdict("f943 YAVG", F943_RANGE[0] <= stats[943].yavg <= F943_RANGE[1], f"{stats[943].yavg:.1f} (want {F943_RANGE[0]}..{F943_RANGE[1]})", results)
    brightest = max(STILLS, key=lambda f: stats[f].yavg)
    _verdict("no still above the cap", stats[brightest].yavg <= STILL_MAX, f"brightest f{brightest} {stats[brightest].yavg:.1f} (want <= {STILL_MAX})", results)
    for name, (first, last) in STRIPS.items():
        steps = [(f, abs(stats[f].yavg - stats[f - 1].yavg)) for f in range(first + 1, last + 1)]
        worst = max(steps, key=lambda item: item[1])
        _verdict(f"largest YAVG step, {name} f{first}-{last}", worst[1] <= STEP_MAX, f"{worst[1]:.1f} at f{worst[0]} (want <= {STEP_MAX})", results)
    frames.tile([frames.frame_path(LOOK_TEST, "beauty", f) for f in STILLS], SHEET, SHEET_COLUMNS, SHEET_TILE_PX)
    frames.tile([frames.frame_path(LOOK_TEST, "beauty", f) for f in HERO_STRIP], STRIP, SHEET_COLUMNS, SHEET_TILE_PX)
    print(f"\nimages to view: {SHEET} and {STRIP}")
    print("GATE PASS (numbers); now view the two images" if all(results) else "GATE FAIL")
    return 0 if all(results) else 1
