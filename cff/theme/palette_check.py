"""L-07 palette check: CIEDE2000 between the key role colours, in three colour-vision conditions (pure Python)."""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from cff.story.model import ColourRole
from cff.theme import colour, palette


@dataclass(frozen=True)
class Pair:
    a: ColourRole
    b: ColourRole
    condition: str
    delta_e: float
    minimum: float

    @property
    def passed(self) -> bool:
        return self.delta_e >= self.minimum


def lab_of(role: ColourRole, condition: str) -> colour.Rgb:
    srgb = colour.hex_to_rgb(palette.role_hex(role))
    return colour.rgb_to_lab(colour.simulate_cvd(srgb, colour.CVD_CONDITIONS[condition]))


def pairs() -> list[Pair]:
    out: list[Pair] = []
    for condition in colour.CVD_CONDITIONS:
        for a, b in itertools.combinations(palette.KEY_ROLES, 2):
            out.append(Pair(a, b, condition, colour.delta_e_2000(lab_of(a, condition), lab_of(b, condition)), palette.L07_MIN_DELTA_E))
        # revocation amber is the one allowed close pair: it only needs 5 against pending amber
        out.append(Pair(ColourRole.REVOCATION, ColourRole.PENDING, condition,
                        colour.delta_e_2000(lab_of(ColourRole.REVOCATION, condition), lab_of(ColourRole.PENDING, condition)), palette.L07_REVOCATION_MIN_DELTA_E))
    return out


def failures() -> list[Pair]:
    return [p for p in pairs() if not p.passed]


def worst() -> Pair:
    return min((p for p in pairs() if p.minimum == palette.L07_MIN_DELTA_E), key=lambda p: p.delta_e)
