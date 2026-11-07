"""Tooling: the Blender invocation form, render chunking, caption files, render tiers, packet preconditions."""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

import pytest

from cff.story import captions, timing
from cff.theme import render
from tools import frames, packet, pipeline, toolchain


def test_blender_command_uses_the_charter_invocation_form() -> None:
    command = toolchain.blender_command(Path("blender/build_scene.py"), Path("renders/film.blend"), ["--out", "x.blend"])
    assert command[1] == "-b"
    assert command[2].endswith("film.blend")
    assert command[3:7] == ["--factory-startup", "--python-exit-code", "1", "-P"]
    assert command[-3:] == ["--", "--out", "x.blend"]


def test_render_tiers_match_the_charter() -> None:
    assert (render.tier("animatic").width, render.tier("animatic").height) == (960, 540)
    assert (render.tier("final").width, render.tier("final").height) == (1920, 1080)
    assert render.tier("animatic").motion_blur is False and render.tier("animatic").volumetrics is False
    assert render.FPS == 30 == timing.FPS


def test_render_chunks_cover_the_film_in_300_frame_blocks() -> None:
    chunks = render.chunks(timing.FRAME_START, timing.frame_end())
    assert chunks[0][0] == 1 and chunks[-1][1] == timing.frame_end()
    assert all(b - a + 1 <= 300 for a, b in chunks)
    assert sum(b - a + 1 for a, b in chunks) == timing.frame_end()
    assert all(nxt[0] == prev[1] + 1 for prev, nxt in pairwise(chunks))


def test_chunk_ranges_split_contiguous_runs_only() -> None:
    assert frames.ranges([1, 2, 3, 7, 8, 20]) == [(1, 3), (7, 8), (20, 20)]
    assert frames.chunk_ranges(list(range(1, 701))) == [(1, 300), (301, 600), (601, 700)]


def test_caption_frames_cover_each_caption_and_stay_inside_the_film() -> None:
    wanted = set(frames.caption_frames())
    for cap in captions.CAPTIONS:
        assert timing.seconds_to_frame(cap.appear_s) in wanted or cap.appear_s < 0
        assert timing.seconds_to_frame(cap.hold_start_s) in wanted
    assert min(wanted) >= timing.FRAME_START and max(wanted) <= timing.frame_end()


def test_vtt_and_transcript_come_from_the_caption_module() -> None:
    vtt, transcript = pipeline.captions_vtt(), pipeline.transcript_md()
    assert vtt.startswith("WEBVTT")
    for cap in captions.CAPTIONS:
        assert cap.text in vtt and cap.text in transcript
    assert "<<" not in vtt and "<<" not in transcript
    assert pipeline.vtt_time(3661.5) == "01:01:01.500"


def test_sample_frames_are_three_per_beat_inside_the_beat() -> None:
    for beat_id in timing.BEAT_DURATIONS_S:
        first, last = frames.beat_frames(beat_id)
        picks = frames.sample_frames(beat_id)
        assert len(picks) == 3 and all(first <= f <= last for f in picks)
        strip = frames.strip_frames(beat_id)
        assert strip[0] == first and strip[-1] == last and len(strip) == frames.STRIP_FRAMES


def test_stage1_packet_refuses_to_build_without_rendered_frames(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="not rendered"):
        packet.build_stage1(9999, tier="no-such-tier")


def test_progress_and_output_locations_are_untracked_build_products() -> None:
    gitignore = (toolchain.ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "renders" in gitignore
