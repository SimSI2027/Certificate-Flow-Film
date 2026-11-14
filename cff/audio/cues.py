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

# Cue gain in dB relative to the bed (the final level is set by loudnorm). V1-AUD-02: every cue 3 dB lower than v1.0.0, so
# the raw mix has headroom for a linear loudnorm pass.
CUE_GAIN_DB: dict[str, float] = {"pulse": -9.0, "whoosh": -8.0, "click": -7.0, "seal": -6.0, "tick": -12.0, "deny": -7.0, "chord": -7.0, "mark": -5.0}
BED_GAIN_DB = -14.0
BED_FADE_IN_S = 2.0
BED_FADE_OUT_S = 3.0
CA_SIGNS_CUE_DELAY_S = 0.5  # the press comes down about 0.5 s into a CA_SIGNS event; its seal cue lands with it (V1-AUD-02)
CUE_DELAY_S: dict[m.EventType, float] = {ET.CA_SIGNS: CA_SIGNS_CUE_DELAY_S}
# V1-AUD-01: each cue is panned by the world x of the event's source actor (constant power); the bed stays centred.
PAN_X_M = 20.0  # world x that maps to a full pan of 1.0
PAN_LIMIT = 0.6


@dataclass(frozen=True)
class Cue:
    time_s: float
    kind: str
    event_id: str
    pan: float = 0.0  # -1 left .. +1 right


def pan_of(actor_id: str | None) -> float:
    from cff.stage.objects import BY_ID  # noqa: PLC0415  (stage positions; pure Python)

    if actor_id is None or actor_id not in BY_ID:
        return 0.0
    return max(-PAN_LIMIT, min(PAN_LIMIT, BY_ID[actor_id].home[0] / PAN_X_M))


def cue_sheet() -> list[Cue]:
    cues = [Cue(e.start_s + CUE_DELAY_S.get(e.type, 0.0), CUE_KIND_BY_EVENT[e.type], e.id, pan_of(e.from_)) for e in m.MODEL.events if e.on_screen]
    return sorted(cues, key=lambda c: (c.time_s, c.event_id))


def duration_s() -> float:
    return timing.total_duration_s()
