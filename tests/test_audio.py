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


def test_V1_AUD_01_cues_are_panned_by_their_source_actor() -> None:  # noqa: N802
    import math  # noqa: PLC0415

    pans = [c.pan for c in cues.cue_sheet()]
    assert min(pans) <= -0.3 and max(pans) >= 0.3, (min(pans), max(pans))  # the client (west) and CA 2 (east) sit apart
    assert all(abs(p) <= cues.PAN_LIMIT for p in pans)
    for p in (-0.6, 0.0, 0.6):
        left, right = synth.pan_gains(p)
        assert math.isclose(left * left + right * right, 1.0)  # constant power
    # L-R difference of a cue at the widest pan: well above the -40 dBFS floor of a stereo image (v1.0.0: -63 dBFS, dual mono)
    left, right = synth.pan_gains(cues.PAN_LIMIT)
    tone = synth.pulse()
    diff = math.sqrt(sum((v * (left - right)) ** 2 for v in tone) / len(tone))
    assert 20 * math.log10(diff) > -40.0


def test_V1_AUD_02_seal_cue_lands_with_the_press() -> None:  # noqa: N802
    sheet = {c.event_id: c for c in cues.cue_sheet()}
    for e in m.MODEL.events:
        if e.type is m.EventType.CA_SIGNS and e.on_screen:
            assert sheet[e.id].time_s == e.start_s + cues.CA_SIGNS_CUE_DELAY_S == e.start_s + 0.5
    assert max(cues.CUE_GAIN_DB.values()) <= -5.0  # every cue 3 dB below v1.0.0 (seal was -3, mark -2)


def test_synth_is_deterministic_and_bounded() -> None:
    for name, build in synth.KINDS.items():
        a, b = build(), build()
        assert a == b, name
        assert a and max(abs(v) for v in a) <= 1.5, name
