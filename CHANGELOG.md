# Changelog

## v1.0.0 (2026-11-13)

- First release: 109 s, 1920x1080, 30 FPS film of the ADCS certificate flow (RDP and TLS paths, one trusted root).
- Pipeline: story model -> scripted Blender scene (EEVEE) -> PNG sequences (beauty, signs, captions) -> FFmpeg composite and encode.
- Audio: 88 sound cues derived from the story events, synthesised deterministically in Python, loudness-normalised to -16.0 LUFS.
- Final signs fixes: signs are held parallel to the image plane, plates and text render in separate view layers (no stipple, no sorting errors), signs keep clear of capsules, cards and private keys, trust links grow from nothing.
- Process: finished in "lean finish mode". The Stage 1 adversarial rounds stopped after R1 was triaged and fixed; round R2 was never judged (usage limits). No discriminator subagents ran for the final film. Gate: `python -m tools verify` (pytest, ruff, mypy, audits, 14 in-Blender checks, blank-frame check) plus two contact-sheet reviews.
- Known limits: the look is stylised grey-box-plus (flat shaded actors, bloom, soft shadows); some check-list signs still overlap the focal subject in crowded frames (about 9% of tag frames, below the 10% test limit).
