"""Deterministic plain-data export of the story model (model dump for packets and manifests)."""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any

from cff.config import names as n
from cff.story import captions as cap
from cff.story import spec_ids, timing
from cff.story.model import MODEL, StoryModel, aia_url, cdp_url

JsonValue = Any


def _plain(value: object) -> JsonValue:
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name.rstrip("_"): _plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, tuple | list):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    return value


def _window(start_s: float, end_s: float) -> dict[str, JsonValue]:
    first, last = timing.frame_range(start_s, end_s)
    return {"start_s": round(start_s, 3), "end_s": round(end_s, 3), "frame_start": first, "frame_end": last}


def model_dump(model: StoryModel = MODEL) -> dict[str, JsonValue]:
    beats = []
    for beat in model.beats:
        entry = _plain(beat)
        entry["scene"] = beat.scene
        entry.update(_window(beat.start_s, beat.end_s))
        entry["events"] = [e.id for e in model.events_in(beat.id)]
        beats.append(entry)
    events = []
    for event in model.events:
        entry = _plain(event)
        entry.update(_window(event.start_s, event.end_s))
        events.append(entry)
    certificates = []
    for cert in model.certificates:
        entry = _plain(cert)
        entry["issuer_actor"] = model.issuer_actor(cert.id)
        entry["aia_url"] = aia_url(model, cert)
        entry["cdp_url"] = cdp_url(model, cert)
        certificates.append(entry)
    captions = []
    for c in cap.captions_in_order():
        captions.append(
            {
                "id": c.id,
                "kind": c.kind.value,
                "text": c.text,
                "scene": c.scene,
                "anchor_beat": c.anchor_beat,
                "words": c.words,
                "required_hold_s": round(c.required_hold_s, 3),
                "appear_s": round(c.appear_s, 3),
                "hold": _window(c.hold_start_s, c.hold_end_s),
                "vanish_s": round(c.vanish_s, 3),
            }
        )
    scene_windows = timing.scene_windows()
    return {
        "film": {
            "fps": timing.FPS,
            "frame_start": timing.FRAME_START,
            "frame_end": timing.frame_end(),
            "duration_s": timing.total_duration_s(),
            "declared_cut_beats": list(timing.DECLARED_CUT_BEATS),
        },
        "names": {nv.variable: {"value": nv.value, "is_fallback": nv.is_fallback} for nv in n.names_in_use()},
        "derived_names": n.derived_names(),
        "spec_ids": {
            "architecture": spec_ids.ARCHITECTURE,
            "facts": spec_ids.FACTS,
            "cinematic": spec_ids.CINEMATIC,
            "legibility": spec_ids.LEGIBILITY,
        },
        "scenes": [
            {**_plain(s), **_window(*scene_windows[s.id])} for s in model.scenes
        ],
        "beats": beats,
        "actors": _plain(model.actors),
        "key_pairs": _plain(model.key_pairs),
        "keys": _plain(model.keys),
        "templates": [
            {**_plain(t), "published_on": list(model.publishing_cas(t.id))} for t in model.templates
        ],
        "cas": _plain(model.cas),
        "certificates": certificates,
        "crls": _plain(model.crls),
        "requests": _plain(model.requests),
        "discoveries": _plain(model.discoveries),
        "chains": _plain(model.chains),
        "channels": _plain(model.channels),
        "handshake_proofs": _plain(model.handshake_proofs),
        "services": _plain(model.services),
        "trust_store": _plain(model.trust_store),
        "labels": _plain(model.labels),
        "events": events,
        "captions": captions,
    }
