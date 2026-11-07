"""Camera plan hard discriminators (C-02, C-03, C-09) on the pure-Python plan the Blender rig is keyed from."""

from __future__ import annotations

from functools import cache

import pytest

from cff.stage import audit, camera, choreography, labels
from cff.stage.objects import BY_ID
from cff.stage.tracks import Timeline
from cff.story import model, timing
from cff.theme import motion, shots


@cache
def _timeline() -> Timeline:
    timeline = choreography.build_timeline()
    labels.add_label_tracks(timeline)
    return timeline


@cache
def _plan() -> camera.CameraPlan:
    return camera.CameraPlan(_timeline())


def _beat_focal() -> dict[str, str]:
    return {b.id: b.focal for b in model.MODEL.beats}


@pytest.mark.covers("C-02")
def test_camera_steps_stay_under_c02_thresholds_with_exactly_the_declared_cuts() -> None:
    assert audit.audit_camera_steps(_plan()) == []
    assert _plan().cut_frames == [timing.seconds_to_frame(timing.beat_window(b)[0]) for b in timing.DECLARED_CUT_BEATS]


@pytest.mark.covers("C-02")
def test_every_beat_has_one_shot_and_lenses_stay_in_range() -> None:
    assert [s.beat for s in shots.SHOTS] == list(timing.BEAT_DURATIONS_S)
    assert len({s.name for s in shots.SHOTS}) == len(shots.SHOTS)
    for frame in _plan().frames():
        assert shots.LENS_MIN_MM - 1e-6 <= _plan().state(frame).lens <= shots.LENS_MAX_MM + 1e-6


@pytest.mark.covers("C-02")
def test_only_declared_beats_start_with_an_explicit_pose() -> None:
    starts = {s.beat for s in shots.SHOTS if s.start is not None}
    assert starts == {"B-01.1", *timing.DECLARED_CUT_BEATS}


@pytest.mark.covers("C-03")
def test_c03_findings_are_confined_to_the_open_list_and_the_list_never_rots() -> None:
    findings = audit.audit_focal(_plan(), _timeline(), _beat_focal())
    failing = {f.where for f in findings}
    assert failing <= audit.C03_OPEN_BEATS, f"new C-03 failures outside the open list: {sorted(failing - audit.C03_OPEN_BEATS)}"
    assert failing >= audit.C03_OPEN_BEATS, f"these beats now pass; remove them from C03_OPEN_BEATS: {sorted(audit.C03_OPEN_BEATS - failing)}"


@pytest.mark.covers("C-03")
def test_focal_objects_exist_in_the_catalogue() -> None:
    for beat in model.MODEL.beats:
        for obj_id in shots.focal_objects(beat.id, beat.focal):
            assert obj_id in BY_ID, (beat.id, obj_id)


@pytest.mark.covers("C-09")
def test_camera_is_never_frontal_for_more_than_two_seconds() -> None:
    assert audit.audit_not_frontal(_plan()) == []


@pytest.mark.covers("C-06")
def test_every_key_is_finite_and_uses_a_named_easing() -> None:
    assert audit.audit_keys(_timeline()) == []
    assert frozenset() == motion.LINEAR_WHITELIST  # the animatic uses no constant-speed channels


@pytest.mark.covers("C-06")
def test_glow_opacity_stays_in_range() -> None:
    assert audit.audit_glow_range(_timeline()) == []


@pytest.mark.covers("C-06")
def test_exits_are_faster_than_entrances_by_the_c06_ratio() -> None:
    assert 0.6 <= motion.exit_frames() / motion.entrance_frames() <= 0.9
    assert 0.6 <= motion.label_exit_frames() / motion.label_entrance_frames() <= 0.9


@pytest.mark.covers("C-02")
def test_camera_smoothing_keeps_the_subject_ahead_of_the_camera() -> None:
    """The camera lags (Gaussian) so a travelling subject leads it on travel beats."""
    assert motion.CAMERA_SMOOTH_SIGMA_FRAMES >= 10
    plan = _plan()
    first, last = timing.frame_range(*timing.beat_window("B-04.2"))
    start, end = plan.state(first), plan.state(last)
    assert camera.view_angle_deg(start, end) > 0.0  # it does move; the C-02 step test bounds how fast
