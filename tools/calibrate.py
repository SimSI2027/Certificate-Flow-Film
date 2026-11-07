"""``python -m tools calibrate <fault>``: discriminator calibration, mutation testing of the hard discriminators (Charter 2.8).

For one fault this command:
1. builds the broken variant with ``blender/calibration.py`` into ``renders/calibration/<fault>/film.blend``;
2. runs the in-Blender hard discriminators (``blender/run_checks.py``) on it and records which checks fail;
3. with ``--packet``, renders the frames a Stage 1 packet shows and builds a blind packet ``qa/calibration/stage1-K<n>``,
   which looks exactly like a round packet, for the subagent discriminators.

Results go to ``qa/calibration/results.json``. The command exits 1 when a hard-check fault is MISSED.
This module and ``blender/calibration.py`` are the only places that know the faults; normal builds never reach them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from tools import frames, packet, pipeline, toolchain

ROOT = toolchain.ROOT
SCRIPT = ROOT / "blender" / "calibration.py"
WORK = ROOT / "renders" / "calibration"
PACKETS = ROOT / "qa" / "calibration"
RESULTS = PACKETS / "results.json"
FAULTS = ("private_key_leak", "root_issues_leaf", "flowchart", "caption_clip")


@dataclass(frozen=True)
class Expectation:
    check: str
    contains: str  # a substring every catching failure line must contain ("" = any failure of that check)


# Which hard discriminators must fail on each fault (Charter 2.8: all except the flowchart, which the cinema discriminator judges).
EXPECTED: dict[str, tuple[Expectation, ...]] = {
    "private_key_leak": (Expectation("key_containment", "KEY-RDP-PRIV"),),
    "root_issues_leaf": (Expectation("root_isolation", "REQ-RDP"), Expectation("root_isolation", "CERT-RDP")),
    "caption_clip": (Expectation("captions", "title-safe"), Expectation("captions", "cap height")),
    "flowchart": (),
}
RELEVANT_DISCRIMINATORS: dict[str, tuple[str, ...]] = {
    "private_key_leak": ("pki-discriminator",),
    "root_issues_leaf": ("pki-discriminator",),
    "flowchart": ("cinema-discriminator",),
    "caption_clip": ("legibility-discriminator",),
}


def frames_dir(fault: str) -> str:
    return f"calibration/{fault}"


def blend_path(fault: str) -> Path:
    return WORK / fault / "film.blend"


def build(fault: str) -> int:
    out = blend_path(fault)
    out.parent.mkdir(parents=True, exist_ok=True)
    return toolchain.run_blender(SCRIPT, args=["--fault", fault, "--out", str(out), "--tier", "animatic"], log=WORK / fault / "build.log")


def run_checks(fault: str) -> list[dict[str, object]]:
    out = WORK / fault / "checks.json"
    out.unlink(missing_ok=True)
    toolchain.run_blender(ROOT / "blender" / "run_checks.py", blend_path(fault), ["--out", str(out)], WORK / fault / "checks.log")
    if not out.exists():
        raise RuntimeError(f"run_checks.py wrote no results for {fault}; see {WORK / fault / 'checks.log'}")
    results: list[dict[str, object]] = json.loads(out.read_text(encoding="utf-8"))
    return results


def judge(fault: str, results: list[dict[str, object]]) -> dict[str, object]:
    failing = {str(r["name"]): [str(line) for line in r["failures"]] for r in results if not r["passed"]}  # type: ignore[attr-defined]
    caught: list[str] = []
    missed: list[str] = []
    for exp in EXPECTED[fault]:
        lines = failing.get(exp.check, [])
        (caught if any(exp.contains in line for line in lines) else missed).append(f"{exp.check}: {exp.contains}")
    return {
        "fault": fault,
        "hard_checks_expected": [f"{e.check}: {e.contains}" for e in EXPECTED[fault]],
        "hard_checks_caught": caught,
        "hard_checks_missed": missed,
        "failing_checks": {name: lines[:4] for name, lines in failing.items()},
        "verdict": "N/A (judged by the cinema discriminator)" if not EXPECTED[fault] else ("CAUGHT" if not missed else "MISSED"),
        "relevant_discriminators": list(RELEVANT_DISCRIMINATORS[fault]),
    }


def render_packet_frames(fault: str) -> int:
    wanted = packet.stage1_frames()
    code = pipeline.render_frame_list("animatic", "beauty", wanted, blend_path(fault), frames_dir(fault))
    if code != 0:
        return code
    captioned = set(frames.caption_frames())
    return pipeline.render_frame_list("animatic", "captions", [f for f in wanted if f in captioned], blend_path(fault), frames_dir(fault))


def next_packet_name() -> str:
    numbers = [int(p.name.rsplit("-K", 1)[1]) for p in PACKETS.glob("stage1-K*") if p.is_dir() and p.name.rsplit("-K", 1)[1].isdigit()]
    return f"stage1-K{max(numbers, default=0) + 1}"


def build_packet(fault: str) -> Path:
    """A fresh blind packet. The first run used K1..K4 in FAULTS order; re-calibrations take the next free number."""
    name = next_packet_name()
    folder = packet.build_stage1(tier=frames_dir(fault), folder=PACKETS / name, round_name=name)
    data: dict[str, object] = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else {}
    mapping = data.setdefault("packets", {})
    assert isinstance(mapping, dict)
    mapping[name] = fault
    RESULTS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return folder


def record(entry: dict[str, object]) -> None:
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else {}
    data[str(entry["fault"])] = entry
    RESULTS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def run(fault: str, make_packet: bool = False, skip_checks: bool = False) -> int:
    if fault not in FAULTS:
        print(f"unknown fault {fault!r}; choose one of {', '.join(FAULTS)}")
        return 2
    code = build(fault)
    if code != 0:
        print(f"calibration build failed (exit {code}); see {WORK / fault / 'build.log'}")
        return code
    entry: dict[str, object] = {"fault": fault}
    if not skip_checks:
        entry = judge(fault, run_checks(fault))
        record(entry)
        print(json.dumps(entry, indent=2, ensure_ascii=False))
    if make_packet:
        code = render_packet_frames(fault)
        if code != 0:
            print(f"render failed (exit {code})")
            return code
        print(f"built {build_packet(fault)}")
    return 1 if entry.get("verdict") == "MISSED" else 0
