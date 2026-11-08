"""In-world signage: every model label is placed once, windows are valid, names come only from the model."""

from __future__ import annotations

import pytest

from cff.stage import labels
from cff.stage.objects import BY_ID
from cff.story import model, timing
from cff.story.model import LabelKind
from cff.theme import motion, typography


@pytest.mark.covers("L-06")
def test_every_model_label_has_exactly_one_placement() -> None:
    placed = [p.label_id for p in labels.PLACEMENTS]
    assert len(placed) == len(set(placed))
    assert set(placed) == {label.id for label in model.MODEL.labels}


@pytest.mark.covers("L-06")
def test_placement_parents_exist_and_text_comes_from_the_model() -> None:
    for p in labels.PLACEMENTS:
        assert p.parent is None or p.parent in BY_ID, p.label_id
        assert p.text == labels.LABELS[p.label_id].text
        assert "<<" not in p.text and "REPLACE" not in p.text


@pytest.mark.covers("L-06")
def test_windowed_labels_have_room_for_entrance_and_exit_and_sit_in_their_beat() -> None:
    enter, leave = motion.label_entrance_frames(), motion.label_exit_frames()
    for p in labels.PLACEMENTS:
        if p.window is None:
            continue
        first, last = labels.window_frames(p.window)
        beat_first = timing.seconds_to_frame(timing.beat_window(p.window.beat)[0])
        beat_after = timing.seconds_to_frame(timing.beat_window(p.window.until or p.window.beat)[1])
        assert beat_first <= first and last <= beat_after, p.label_id
        assert last - first > enter + leave, p.label_id
        assert p.window.beat in labels.LABELS[p.label_id].must_read_beats or labels.LABELS[p.label_id].kind is not LabelKind.TAG, p.label_id


@pytest.mark.covers("B-09.3")
def test_signs_leave_before_the_world_fades_under_the_title_card() -> None:
    from cff.stage import signs  # noqa: PLC0415  (builds the sign plan)

    fade = signs.world_fade_frame()
    for label_id, plan in signs.plan_signs().items():
        assert all(frame < fade for frame in plan.frames), label_id


@pytest.mark.covers("L-01")
def test_signs_are_held_at_a_cap_height_above_the_l01_minimum() -> None:
    assert typography.SIGN_CAP_PX >= 18.0 + 2.0  # margin over L-01's 18 px at 1080p
    assert typography.CAPTION_CAP_PX >= 30.0 + 2.0


@pytest.mark.covers("L-06")
def test_check_labels_hang_from_their_tick_in_the_model_order() -> None:
    by_id = {e.id: e for e in model.MODEL.events}
    for i, event_id in enumerate(("E-04.3a", "E-04.3b", "E-04.3c", "E-04.3d")):
        check = by_id[event_id].check
        assert check is not None
        assert labels.BY_ID[f"LBL-ISSUING_CA1-{check.name}"].parent == f"TICK-CA1-{'abcd'[i]}"
    for i, event_id in enumerate(("E-09.1j", "E-09.1k", "E-09.1l", "E-09.1o")):
        check = by_id[event_id].check
        assert check is not None
        assert labels.BY_ID[f"LBL-CHAIN-WEB-{check.name}"].parent == f"TICK-WEB-{'abcd'[i]}"


