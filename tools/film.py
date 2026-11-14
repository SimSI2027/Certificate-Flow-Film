"""Audio mix, encode and deliverables (Charter 10, 11).

``audio``  : synthesise the cue mix (cff.audio), then two-pass loudnorm to about -16 LUFS / -1 dBTP; writes output/audio/.
``encode`` : overlay the signs and caption layers on the beauty frames, mux the audio, write the Final MP4, the 720p Preview,
             the poster, the contact sheet and render-metadata.json.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cff.audio import cues, synth
from cff.story import model, timing
from tools import frames, packet, pipeline, toolchain

ROOT = toolchain.ROOT
OUTPUT = ROOT / "output"
AUDIO_DIR = OUTPUT / "audio"
FINAL_MP4 = OUTPUT / "Certificate-Flow-Film-Final.mp4"
PREVIEW_MP4 = OUTPUT / "Certificate-Flow-Film-Preview.mp4"
POSTER_PNG = OUTPUT / "Certificate-Flow-Film-Poster.png"
CONTACT_PNG = OUTPUT / "Certificate-Flow-Film-Contact-Sheet.png"
METADATA = OUTPUT / "render-metadata.json"
TARGET_LUFS = -16.0
TARGET_TP = -1.0
TARGET_LRA = 11.0
CRF_FINAL = 17
CRF_PREVIEW = 27
PREVIEW_MAXRATE = "1700k"
HERO_BEAT = "B-09.2"
AAC_BITRATE = "192k"
PREVIEW_AAC_BITRATE = "96k"
BT709 = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]


def _ffmpeg(args: list[str], info: bool = False) -> subprocess.CompletedProcess[str]:
    tools = toolchain.load()
    level = "info" if info else "error"
    return subprocess.run([str(tools.ffmpeg), "-hide_banner", "-nostats", "-loglevel", level, "-y", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def _loudness_json(stderr: str) -> dict[str, str]:
    start = stderr.rindex("{")
    return json.loads(stderr[start : stderr.index("}", start) + 1])  # type: ignore[no-any-return]


def build_audio() -> dict[str, object]:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    raw = synth.write_wav(synth.mix(), AUDIO_DIR / "mix-raw.wav")
    target = f"I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}"
    first = _ffmpeg(["-i", str(raw), "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"], info=True)
    if first.returncode != 0:
        raise RuntimeError(first.stderr)
    m = _loudness_json(first.stderr)
    measured = f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}"
    out = AUDIO_DIR / "mix.wav"
    second = _ffmpeg(["-i", str(raw), "-af", f"loudnorm={target}:{measured}:linear=true:print_format=json,aformat=sample_rates={synth.SAMPLE_RATE}:channel_layouts=stereo",
                      "-ar", str(synth.SAMPLE_RATE), "-ac", "2", str(out)], info=True)
    if second.returncode != 0:
        raise RuntimeError(second.stderr)
    # verify the written file with ebur128
    check = _ffmpeg(["-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"], info=True)
    summary = check.stderr[check.stderr.rindex("Summary:") :] if "Summary:" in check.stderr else check.stderr[-600:]
    report: dict[str, object] = {"first_pass": m, "second_pass": _loudness_json(second.stderr), "ebur128_summary": summary.strip(), "cues": len(cues.cue_sheet()), "duration_s": cues.duration_s()}
    (AUDIO_DIR / "loudness.json").write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")
    return report


def _concat_list(tier: str, layer: str, blank: Path, path: Path) -> Path:
    have = frames.present_frames(tier, layer)
    step = 1 / timing.FPS
    lines = ["ffconcat version 1.0"]
    for frame in range(timing.FRAME_START, timing.frame_end() + 1):
        image = frames.frame_path(tier, layer, frame) if frame in have else blank
        lines += [f"file '{image.as_posix()}'", f"duration {step:.6f}"]
    lines.append(f"file '{blank.as_posix()}'")  # the concat demuxer needs the last file repeated
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path


def encode(tier: str = "final") -> dict[str, object]:
    work = frames.tier_dir(tier) / "encode"
    work.mkdir(parents=True, exist_ok=True)
    missing = frames.missing_frames(tier)
    if missing:
        raise RuntimeError(f"{len(missing)} beauty frames missing (first {missing[0]}); render first")
    blank = work / "blank.png"
    res = _ffmpeg(["-f", "lavfi", "-i", "color=c=black@0.0:s=1920x1080:r=1,format=rgba", "-frames:v", "1", str(blank)])
    if res.returncode != 0:
        raise RuntimeError(res.stderr)
    signs = _concat_list(tier, "signs", blank, work / "signs.txt")
    caps = _concat_list(tier, "captions", blank, work / "captions.txt")
    beauty = (frames.tier_dir(tier) / "beauty" / "f_%04d.png").as_posix()
    fps = str(timing.FPS)
    graph = ("[1:v]format=rgba[s];[2:v]format=rgba[c];[0:v]format=rgba[b];[b][s]overlay=format=auto[o1];[o1][c]overlay=format=auto[o2];"
             "[o2]scale=out_color_matrix=bt709:out_range=tv:flags=lanczos,format=yuv420p[v]")
    args = ["-framerate", fps, "-start_number", str(timing.FRAME_START), "-i", beauty,
            "-f", "concat", "-safe", "0", "-i", str(signs), "-f", "concat", "-safe", "0", "-i", str(caps),
            "-i", str(AUDIO_DIR / "mix.wav"), "-filter_complex", graph, "-map", "[v]", "-map", "3:a", "-r", fps,
            "-c:v", "libx264", "-preset", "slow", "-crf", str(CRF_FINAL), *BT709, "-c:a", "aac", "-b:a", AAC_BITRATE, "-ar", "48000",
            "-t", f"{timing.frame_end() / timing.FPS:.3f}", "-movflags", "+faststart", str(FINAL_MP4)]
    done = _ffmpeg(args)
    if done.returncode != 0:
        raise RuntimeError(done.stderr)
    prev = _ffmpeg(["-i", str(FINAL_MP4), "-vf", "scale=1280:720:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", str(CRF_PREVIEW),
                    "-maxrate", PREVIEW_MAXRATE, "-bufsize", "3400k", *BT709, "-c:a", "aac", "-b:a", PREVIEW_AAC_BITRATE, "-movflags", "+faststart", str(PREVIEW_MP4)])
    if prev.returncode != 0:
        raise RuntimeError(prev.stderr)
    hero = frames.sample_frames(HERO_BEAT)[1]
    frames.composite(tier, hero, POSTER_PNG)
    CONTACT_PNG.write_bytes(pipeline.contact_sheet(tier).read_bytes())
    pipeline.write_captions()
    return write_metadata(tier)


def probe(path: Path) -> dict[str, object]:
    tools = toolchain.load()
    out = subprocess.run([str(tools.ffprobe), "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)  # type: ignore[no-any-return]


def write_metadata(tier: str) -> dict[str, object]:
    from cff.config import names  # noqa: PLC0415

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    spec = packet.sha256(packet.SPEC)
    loud = json.loads((AUDIO_DIR / "loudness.json").read_text(encoding="utf-8"))
    progress = json.loads((frames.tier_dir(tier) / "progress.json").read_text(encoding="utf-8")) if (frames.tier_dir(tier) / "progress.json").exists() else {}
    data: dict[str, object] = {
        "commit": commit, "tier": tier, "blender": toolchain.load().blender_version, "engine": "BLENDER_EEVEE", "frames": timing.frame_end(),
        "fps": timing.FPS, "duration_s": timing.total_duration_s(), "beats": len(model.MODEL.beats), "spec_sha256": spec,
        "last_render_progress": progress, "loudness": loud, "names": {k: v for k, v in vars(names).items() if k.isupper() and isinstance(v, str)},
        "final": probe(FINAL_MP4), "preview": probe(PREVIEW_MP4),
    }
    METADATA.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8", newline="\n")
    return data
