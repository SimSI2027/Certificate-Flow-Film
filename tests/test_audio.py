"""Audio cue sheet and synth: every event has a cue, cues sit on the story clock, and the synth is deterministic."""

from __future__ import annotations

from cff.audio import cues, synth
from cff.story import model as m


def test_every_event_type_has_a_cue_kind() -> None:
    assert {e.type for e in m.MODEL.events} <= set(cues.CUE_KIND_BY_EVENT)
    assert set(cues.CUE_KIND_BY_EVENT.values()) <= set(synth.KINDS) and set(cues.CUE_GAIN_DB) == set(synth.KINDS)


def test_cue_sheet_is_sorted_and_inside_the_film() -> None:
    sheet = cues.cue_sheet()
    assert sheet and [c.time_s for c in sheet] == sorted(c.time_s for c in sheet)
    assert all(0.0 <= c.time_s < cues.duration_s() for c in sheet)


def test_synth_is_deterministic_and_bounded() -> None:
    for name, build in synth.KINDS.items():
        a, b = build(), build()
        assert a == b, name
        assert a and max(abs(v) for v in a) <= 1.5, name
