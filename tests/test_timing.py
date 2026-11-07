"""Timing hard discriminators (Charter Section 12)."""

from __future__ import annotations

from itertools import pairwise

import pytest

from cff.story import timing
from cff.story.model import MODEL

EPS = 1e-9


@pytest.mark.covers("B-*")
def test_total_duration_within_bounds_and_target() -> None:
    total = timing.total_duration_s()
    assert timing.TOTAL_MIN_S <= total <= timing.TOTAL_MAX_S
    assert timing.TARGET_MIN_S <= total <= timing.TARGET_MAX_S
    assert abs(total - sum(timing.SCENE_DURATIONS_S.values())) < EPS


@pytest.mark.covers("B-*")
def test_beats_match_model_in_order() -> None:
    assert list(timing.BEAT_DURATIONS_S) == [b.id for b in MODEL.beats]
    assert [s.id for s in MODEL.scenes] == list(timing.SCENE_DURATIONS_S)
    ids = list(timing.BEAT_DURATIONS_S)
    assert ids == sorted(ids, key=lambda b: (int(b[2:4]), int(b.split(".")[1])))


@pytest.mark.covers("B-*")
def test_no_zero_length_beats_and_no_gaps_or_overlaps() -> None:
    assert timing.DECLARED_BEAT_OVERLAPS == ()
    windows = list(timing.beat_windows().values())
    assert windows[0][0] == 0.0
    for start, end in windows:
        assert end - start > 0
    for (_, prev_end), (next_start, _) in pairwise(windows):
        assert abs(prev_end - next_start) < EPS


@pytest.mark.covers("B-*")
def test_scene_durations_equal_sum_of_their_beats() -> None:
    for scene_id, duration in timing.SCENE_DURATIONS_S.items():
        beats = [d for b, d in timing.BEAT_DURATIONS_S.items() if timing.scene_of(b) == scene_id]
        assert beats, scene_id
        assert abs(sum(beats) - duration) < EPS, scene_id
    scene_windows = timing.scene_windows()
    for beat in MODEL.beats:
        s_start, s_end = scene_windows[beat.scene]
        assert s_start - EPS <= beat.start_s and beat.end_s <= s_end + EPS


@pytest.mark.covers("B-*")
def test_all_times_land_on_frames() -> None:
    for beat_id in timing.BEAT_DURATIONS_S:
        start, end = timing.beat_window(beat_id)
        assert timing.is_on_frame(start) and timing.is_on_frame(end)
    for event in MODEL.events:
        assert timing.is_on_frame(event.start_s) and timing.is_on_frame(event.end_s), event.id


def test_every_event_has_timing_and_vice_versa() -> None:
    assert {e.id for e in MODEL.events} == set(timing.EVENT_WINDOWS_S)
    for offset, duration in timing.EVENT_WINDOWS_S.values():
        assert offset >= 0 and duration > 0


def test_frame_conversion() -> None:
    assert timing.FPS == 30
    assert timing.seconds_to_frame(0.0) == timing.FRAME_START
    assert timing.seconds_to_frame(1.0) == timing.FRAME_START + 30
    assert timing.frame_end() == timing.FRAME_START + round(timing.total_duration_s() * timing.FPS) - 1
    assert timing.frame_range(0.0, 1.0) == (1, 30)
    with pytest.raises(ValueError):
        timing.seconds_to_frame(0.01)


@pytest.mark.covers("C-02")
def test_declared_cuts_are_the_flashback_boundaries() -> None:
    flashback = [b.id for b in MODEL.beats if b.flashback]
    assert flashback == ["B-05.2"]
    ids = [b.id for b in MODEL.beats]
    after = ids[ids.index("B-05.2") + 1]
    expected = ("B-05.2", after)
    assert expected == timing.DECLARED_CUT_BEATS
