"""The audio cue sheet, derived from the story events (Charter 10). Pure Python.

Every on-screen event maps to one cue kind; the cue sits at the event's start time, so sound and picture share one clock.
There is no narration in v1: the bed leaves headroom in the mid band for a voice later.
"""

from __future__ import annotations

from dataclasses import dataclass

from cff.story import model as m
from cff.story import timing

ET = m.EventType

CUE_KIND_BY_EVENT: dict[m.EventType, str] = {
    **dict.fromkeys(
        (ET.USER_INITIATES, ET.CONNECTION_PULSE, ET.LISTENER_ACTIVATES, ET.CA_DISCOVERY_QUERY, ET.CA_DISCOVERY_RESULT, ET.AIA_INDICATOR,
         ET.TRUST_STORE_RECALL, ET.OCSP_NOTE, ET.VALIDATION_PENDING, ET.CONNECTION_CLOSED), "pulse"),
    **dict.fromkeys((ET.REQUEST_SUBMITTED, ET.OFFLINE_CARRY, ET.CERT_RETURNED, ET.PRESENT_CERT, ET.HANDSHAKE_PROOF_SENT, ET.CRL_FETCH), "whoosh"),
    **dict.fromkeys(
        (ET.KEYPAIR_GENERATED, ET.PRIVATE_KEY_STORED, ET.REQUEST_ASSEMBLED, ET.CERT_INSTALLED, ET.INTERMEDIATE_STORED, ET.POLICY_ASSIGNS_TEMPLATE,
         ET.TEMPLATE_SELECTED, ET.REQUEST_CONSUMED, ET.ISSUER_LINK), "click"),
    **dict.fromkeys((ET.PROOF_OF_POSSESSION, ET.CA_SIGNS, ET.HANDSHAKE_SIGNATURE, ET.SELF_SIGNATURE_SHOWN), "seal"),
    **dict.fromkeys((ET.CA_CHECK, ET.VALIDATION_CHECK, ET.CHAIN_LINK, ET.HANDSHAKE_PROOF_VERIFIED), "tick"),
    ET.CLIENT_CANNOT_VERIFY: "deny",
    **dict.fromkeys((ET.SESSION_ESTABLISHED, ET.TRUST_PATH_REVEAL), "chord"),
    ET.FINAL_FADE: "mark",
}

# Cue gain in dB relative to the bed (the final level is set by loudnorm).
CUE_GAIN_DB: dict[str, float] = {"pulse": -6.0, "whoosh": -5.0, "click": -4.0, "seal": -3.0, "tick": -9.0, "deny": -4.0, "chord": -4.0, "mark": -2.0}
BED_GAIN_DB = -14.0
BED_FADE_IN_S = 2.0
BED_FADE_OUT_S = 3.0


@dataclass(frozen=True)
class Cue:
    time_s: float
    kind: str
    event_id: str


def cue_sheet() -> list[Cue]:
    cues = [Cue(e.start_s, CUE_KIND_BY_EVENT[e.type], e.id) for e in m.MODEL.events if e.on_screen]
    return sorted(cues, key=lambda c: (c.time_s, c.event_id))


def duration_s() -> float:
    return timing.total_duration_s()
