"""Caption timing and text (L-04, L-05; Charter Section 7 caption list)."""

from __future__ import annotations

from itertools import pairwise

import pytest

from cff.story import captions as cap
from cff.story import timing
from cff.story.model import MODEL

EPS = 1e-9

# Charter Section 7 caption wording, scene by scene (with fallback role names).
CHARTER_CAPTIONS = {
    "S1": ["Secure RDP connection"],
    "S2": ["The RDP server needs a trusted identity"],
    "S3": ["The private key stays on the server", "The request is signed, not the key sent"],
    "S4": ["Issuing CA 1 verifies, then signs"],
    "S5": ["The Root CA signs the issuing CA certificate", "The Root CA is the trust anchor"],
    "S6": ["The client validates the whole chain", "Trusted RDP connection established"],
    "S7": ["Different templates can use different issuing CAs"],
    "S8": ["Issuing CA 2 signs the TLS certificate"],
    "S9": ["Different issuing paths. One trusted root.", "Certificate Flow — From request to trust"],
}


def test_word_count() -> None:
    assert cap.word_count("Secure RDP connection") == 3
    assert cap.word_count("The request is signed, not the key sent") == 8
    assert cap.word_count("Certificate Flow — From request to trust") == 6
    assert cap.min_hold_s("one two") == timing.CAPTION_MIN_HOLD_S
    assert abs(cap.min_hold_s(" ".join(["w"] * 10)) - 3.5) < EPS


def test_caption_text_matches_charter_per_scene() -> None:
    by_scene: dict[str, list[str]] = {}
    for c in cap.captions_in_order():
        by_scene.setdefault(c.scene, []).append(c.text)
    assert by_scene == CHARTER_CAPTIONS


def test_every_caption_has_timing_and_vice_versa() -> None:
    assert {c.id for c in cap.CAPTIONS} == set(timing.CAPTION_WINDOWS_S)
    beat_ids = {b.id for b in MODEL.beats}
    for beat, offset, hold in timing.CAPTION_WINDOWS_S.values():
        assert beat in beat_ids and offset >= 0 and hold > 0


@pytest.mark.covers("L-04")
def test_captions_satisfy_l04() -> None:
    for c in cap.CAPTIONS:
        assert c.hold_s + EPS >= c.required_hold_s, f"{c.id}: {c.hold_s} s < {c.required_hold_s} s"


@pytest.mark.covers("L-05")
def test_one_caption_at_a_time_with_clear_gap() -> None:
    ordered = cap.captions_in_order()
    for prev, nxt in pairwise(ordered):
        assert prev.vanish_s + timing.CAPTION_MIN_GAP_S <= nxt.appear_s + EPS, (prev.id, nxt.id)


@pytest.mark.covers("L-04", "L-05")
def test_captions_stay_inside_their_scene_and_the_film() -> None:
    scenes = timing.scene_windows()
    for c in cap.CAPTIONS:
        start, end = scenes[c.scene]
        assert start - EPS <= c.appear_s and c.vanish_s <= end + EPS, c.id
        assert timing.is_on_frame(c.hold_start_s) and timing.is_on_frame(c.hold_end_s)
        assert timing.is_on_frame(c.appear_s) and timing.is_on_frame(c.vanish_s)
    assert max(c.vanish_s for c in cap.CAPTIONS) <= timing.total_duration_s() + EPS


@pytest.mark.covers("C-06")
def test_caption_exit_is_faster_than_entrance() -> None:
    assert timing.CAPTION_FADE_OUT_S < timing.CAPTION_FADE_IN_S


def test_single_title_card_last() -> None:
    titles = [c for c in cap.CAPTIONS if c.kind == cap.CaptionKind.TITLE]
    assert len(titles) == 1 and cap.captions_in_order()[-1] is titles[0]
