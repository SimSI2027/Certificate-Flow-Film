# Changelog

## Unreleased (toward v1.1.0; audit fixes, session F1, no re-render yet)

- v1.0.0 is a pre-release under audit (`docs\AUDIT-v1.md`: 0 BLOCKER, 16 MAJOR, 10 MINOR).
- Fixed in code (takes effect at the next render): signs no longer motion-blurred in the final tier (V1-LEG-01); shutter opens at the frame so the two cuts are not blends (V1-CIN-04); client trust store gold from frame 1 (V1-PKI-01); "Earlier" marker on screen for the whole flashback (V1-PKI-02); "Private key" / "Public key" tags (V1-PKI-03); persistent name plates limited to the beats where they are read (V1-LEG-04); encode tags BT.709 transfer, level 4.1 (V1-ENC-01).
- `python -m tools verify` now checks every rendered tier, the Final MP4 and the two cut frames (V1-PIPE-01). The MP4 steps report, but do not fail on, the known v1.0.0 problems until the F2 re-render.
- Pages: captions track is opt-in (no doubled captions); wording corrected (V1-DOC-01, V1-DOC-02).
- Known limits (open): the grey-box look (V1-CIN-03), camera framing, check-list timing and sign jumps (F2).

## v1.0.0 (2026-11-13)

- First release: 109 s, 1920x1080, 30 FPS film of the ADCS certificate flow (RDP and TLS paths, one trusted root).
- Pipeline: story model -> scripted Blender scene (EEVEE) -> PNG sequences (beauty, signs, captions) -> FFmpeg composite and encode.
- Audio: 88 sound cues derived from the story events, synthesised deterministically in Python, loudness-normalised to -16.0 LUFS.
- Final signs fixes: signs are held parallel to the image plane, plates and text render in separate view layers (no stipple, no sorting errors), signs keep clear of capsules, cards and private keys, trust links grow from nothing.
- Process: finished in "lean finish mode". The Stage 1 adversarial rounds stopped after R1 was triaged and fixed; round R2 was never judged (usage limits). No discriminator subagents ran for the final film. Gate: `python -m tools verify` (pytest, ruff, mypy, audits, 14 in-Blender checks, blank-frame check) plus two contact-sheet reviews.
- Known limits: the look is stylised grey-box-plus (flat shaded actors, bloom, soft shadows); some check-list signs still overlap the focal subject in crowded frames (about 9% of tag frames, below the 10% test limit).
