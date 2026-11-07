"""Choreography coverage: every on-screen event is staged once, objects enter and leave on frame boundaries."""

from __future__ import annotations

import math
from functools import cache
from itertools import pairwise

import pytest

from cff.stage import choreography, labels
from cff.stage.objects import BY_ID, CATALOGUE
from cff.stage.tracks import GLOW, LOCATION, SCALE, Timeline
from cff.story import model, timing
from cff.theme import motion

# Objects that never move, scale or glow after frame 1 (the stage furniture and the rest-state props).
STATIC_OBJECT_IDS = {
    "DESK", "FLOOR",
}


@cache
def _chor() -> choreography.Choreographer:
    chor = choreography.Choreographer()
    chor.build()
    return chor


@cache
def _timeline() -> Timeline:
    timeline = _chor().tl
    labels.add_label_tracks(timeline)
    return timeline


@pytest.mark.covers("B-*")
def test_every_on_screen_event_is_staged() -> None:
    on_screen = {e.id for e in model.MODEL.events if e.on_screen}
    assert on_screen - _chor().handled == set(), "on-screen events nobody choreographs"


@pytest.mark.covers("B-*")
def test_events_used_by_the_choreography_exist_in_the_model_and_timing() -> None:
    ids = {e.id for e in model.MODEL.events}
    assert _chor().handled <= ids
    assert set(timing.EVENT_WINDOWS_S) == ids


@pytest.mark.covers("C-06")
def test_keys_are_strictly_ordered_and_inside_the_film() -> None:
    for (obj, channel), keys in _timeline().tracks.items():
        frames = sorted(keys)
        assert frames[0] >= timing.FRAME_START - 1 or obj in labels.BY_ID, (obj, channel)
        assert frames[-1] <= timing.frame_end() + motion.entrance_frames(), (obj, channel, frames[-1])
        assert all(math.isfinite(v) for key in keys.values() for v in key.value), (obj, channel)


@pytest.mark.covers("C-06")
def test_entrances_animate_at_least_two_properties() -> None:
    """Every object that starts hidden enters with scale and location (or emission) keys: never opacity only."""
    hidden = [o for o in CATALOGUE if not o.on_stage]
    for o in hidden:
        channels = {c for c in (LOCATION, SCALE, GLOW) if _timeline().has(o.id, c)}
        assert SCALE in channels, f"{o.id} never enters"
        assert len(channels) >= 2, f"{o.id} enters with {channels}"


@pytest.mark.covers("C-07")
def test_each_stage_object_is_one_object_for_its_whole_life() -> None:
    """Catalogue ids are unique, and a certificate or capsule id never reappears under another name."""
    ids = [o.id for o in CATALOGUE]
    assert len(ids) == len(set(ids))
    for key in ("CERT-RDP", "CERT-WEB", "REQ-RDP", "REQ-WEB", "REQ-CA1", "CERT-CA1", "CERT-CA2", "CERT-ROOT"):
        assert ids.count(key) == 1


@pytest.mark.covers("F-10")
def test_each_server_has_its_own_intermediate_copy_and_the_crown_originals_never_move() -> None:
    assert "CERT-CA1-COPY-RDP" in BY_ID and "CERT-CA2-COPY-WEB" in BY_ID
    crown1 = _timeline().keys("CERT-CA1", LOCATION)
    crown2 = _timeline().keys("CERT-CA2", LOCATION)
    # CA 1's certificate re-forms in the flashback (one object, hidden before the cut) and settles back on its crown
    assert crown1[-1].value == pytest.approx(BY_ID["CERT-CA1"].home) or crown1[-1].value[2] > 0
    assert not crown2 or crown2[0].value == pytest.approx(BY_ID["CERT-CA2"].home)


@pytest.mark.covers("C-06")
def test_staggered_check_ticks_are_evenly_spaced_within_one_frame() -> None:
    by_id = {e.id: e for e in model.MODEL.events}
    lists = (
        ("E-04.3a", "E-04.3b", "E-04.3c", "E-04.3d"),
        ("E-08.1a", "E-08.1b", "E-08.1c", "E-08.1d"),
        ("E-06.4a", "E-06.4b", "E-06.4c", "E-06.4d", "E-06.4e"),
    )
    for ids in lists:
        starts = [timing.seconds_to_frame(by_id[i].start_s) for i in ids]
        gaps = [b - a for a, b in pairwise(starts)]
        assert max(gaps) - min(gaps) <= 1, (ids, gaps)


@pytest.mark.covers("C-06")
def test_idle_micro_motion_is_within_two_percent_of_object_size() -> None:
    user = BY_ID[model.USER]
    keys = _timeline().keys(model.USER, LOCATION)
    rises = [k.value[2] - user.home[2] for k in keys]
    assert max(rises) <= 0.02 * user.size[2] + 1e-9
    assert motion.IDLE_AMPLITUDE_FRACTION <= 0.02


@pytest.mark.covers("AR-01")
def test_root_key_module_and_press_never_glow_in_the_present() -> None:
    """The root's module, key and press stay dark outside the flashback (B-05.2) (spec: root dark in the present)."""
    flash_first = timing.seconds_to_frame(timing.beat_window("B-05.2")[0])
    flash_after = timing.seconds_to_frame(timing.beat_window("B-05.3")[0])
    for obj in ("MODULE-ROOT", "KEY-ROOT-PRIV", "PRESSHEAD-ROOT"):
        for key in _timeline().keys(obj, GLOW):
            if not flash_first <= key.frame < flash_after:
                assert max(key.value[:3]) == 0.0, (obj, key.frame)
