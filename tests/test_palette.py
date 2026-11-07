"""Palette hard discriminators (L-07, C-10): role tokens and CIEDE2000 under normal and colour-vision-deficient simulation."""

from __future__ import annotations

import pytest

from cff.story.model import ColourRole
from cff.theme import colour, palette, palette_check


@pytest.mark.covers("C-10")
def test_every_colour_role_has_one_token() -> None:
    assert set(palette.ROLE_HEX) == set(ColourRole)
    assert all(len(value) == 7 and value.startswith("#") for value in palette.ROLE_HEX.values())


@pytest.mark.covers("L-07")
def test_key_roles_stay_at_least_15_delta_e_apart_in_all_three_conditions() -> None:
    assert palette_check.failures() == []
    assert palette_check.worst().delta_e >= palette.L07_MIN_DELTA_E


@pytest.mark.covers("L-07")
def test_revocation_amber_clears_five_from_pending_amber_in_all_conditions() -> None:
    pairs = [p for p in palette_check.pairs() if p.minimum == palette.L07_REVOCATION_MIN_DELTA_E]
    assert {p.condition for p in pairs} == set(colour.CVD_CONDITIONS)
    assert all(p.delta_e >= 5.0 for p in pairs)


@pytest.mark.covers("L-07")
def test_cvd_condition_set_is_normal_deuteranopia_protanopia() -> None:
    assert set(colour.CVD_CONDITIONS) == {"normal", "deuteranopia", "protanopia"}


@pytest.mark.covers("L-02")
def test_white_text_on_a_plate_keeps_4_5_to_1_even_over_a_white_background() -> None:
    """Worst case for a translucent plate: the scene behind it is white (the 95th-percentile background, L-02)."""
    text = colour.relative_luminance(colour.hex_to_rgb(palette.TEXT_HEX))
    plate = colour.relative_luminance(colour.hex_to_rgb(palette.PLATE_HEX))
    worst_background = palette.PLATE_OPACITY * plate + (1.0 - palette.PLATE_OPACITY) * 1.0
    assert colour.contrast_ratio(text, worst_background) >= 4.5


@pytest.mark.covers("C-08")
def test_ambient_stays_far_below_the_key_light() -> None:
    assert palette.WORLD_STRENGTH <= palette.AMBIENT_TO_KEY_MAX * 0.2
