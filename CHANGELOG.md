# Changelog

## v1.1.0 (2026-11-14, pre-release)

The audit-fix release. v1.0.0 was audited (`docs\AUDIT-v1.md`: 0 BLOCKER, 16 MAJOR, 10 MINOR); every finding except the look (V1-CIN-03) was fixed in sessions F1 and F2, the final tier was fully re-rendered, and session F3 re-checked each fix on the rendered film before this release. v1.1.0 is a pre-release because V1-CIN-03 is still open. v1.0.0 is superseded.

Final MP4 SHA-256: `2b56cee7b030528d6bf21cf864c74ced521cbc9c18ba170e7229704fd9d7f78e`.

Fixed:
- **Text on screen.** Signs are no longer motion-blurred (V1-LEG-01). Signs no longer jump or flash: 0 jumps over 96 px, 0 runs under 24 frames (V1-LEG-02; v1.0.0 had 51 and 29). Each check line appears when its own check starts, at one fixed place per list, with its own tick; "Revocation OK" stays pending amber until both CRL fetches have docked (V1-LEG-03). Name plates show only in the beats where they are read; signs cross the focal subject on 1.55% of sign frames, and no frame has more than 9 signs (V1-LEG-04; v1.0.0: 34.8% of frames, 15 signs). The two AIA tags hold longer (V1-LEG-05).
- **PKI clarity.** The client's trust store is gold from the first frame, so trust is not "created" when the chain docks (V1-PKI-01). The marker "Earlier: offline signing ceremony" is on screen for the whole flashback (V1-PKI-02). "Private key" and "Public key" tags name both keys (V1-PKI-03). The handshake proof of possession is 85 px (RDP) and 55 px (web), was 28 and 15 (V1-PKI-04). The two CRL fetches dock beside their own cards at 73–78 px, was 22 (V1-PKI-05). The root's self-signed seal is 120 px, was 50 (V1-PKI-06).
- **Camera.** Tighter framing in the beats with small subjects (V1-CIN-01, residuals below). The hero shot now shows the user, the laptop, both servers, both issuing CAs and the root (V1-CIN-02, residuals below). The two cuts are clean frames, not double exposures (V1-CIN-04). The trusted-session payoff glides in to the laptop: session window 188 px, was 126, with no sign over it (V1-CIN-05). The white flash at 90 s is reduced (V1-CIN-06). The sealed request has a visible seal ring (V1-CIN-07).
- **Colour and sound.** Role colours hold at distance: pending amber and validated green measure 21 and 12 dE2000 from their tokens, was about 35–40 (V1-COL-01). Issuing-CA interiors are no longer twice as bright as the beats around them (V1-CIN-03 step 1). Audio is stereo, with cues panned by their source (V1-AUD-01); the signing cue lands with the press; −15.9 LUFS (V1-AUD-02).
- **Pipeline and file.** `python -m tools verify` checks every rendered tier, the Final MP4 against the delivery spec, and the two cut frames (V1-PIPE-01). The MP4 is H.264 High level 4.1 with BT.709 tags (V1-ENC-01).
- **Pages and docs.** The captions track is opt-in, so captions no longer show twice (V1-DOC-01); wording matches the film (V1-DOC-02, V1-DOC-03).

Known limitations:
- **V1-CIN-03 (MAJOR, open): the look is still a stylised grey-box.** Flat grey props, no material or light design, an empty dark upper frame. The charter's film gate (cinema score of 8 or more, no open MAJOR) is not met. Plan: `docs\LOOK-PLAN-v1.2.md`.
- **Hero shot (V1-CIN-02 residuals).** The whole topology is in frame for the last 2 s of the 6 s beat (from about 102 s) and through the closing title, not for 90% of the beat. Mean luma of the beat is 38.4 (target 50).
- **Focal size (V1-CIN-01 residuals).** Ten beats are below their size target: B-01.2 78 px, B-02.2 99, B-02.3 96, B-04.2 65, B-05.2 55, B-05.3 39, B-06.1 63, B-06.3 53, B-07.4 64, B-08.3 69 (targets 80–150 px). The session window is 188 px (target 220).
- **Luma steps (V1-CIN-06 residual).** 7.7 at 90.27 s (f2709; v1.0.0: 12.2); also 5.6 at 24.83 s, 4.6 at 45.83 s and 6.4 at 81.00 s (target: none above 4.0).
- **Check lists.** The CA 2 list and the RDP list overlap a protected object on 42 and 21 frames.
- **New in the F3 re-audit (all MINOR).** The flashback marker fades out over the first three frames after the cut back to the present (f1396–1398, alpha 0.58 to 0.13). The AAC track's true peak is −0.6 dBFS (WAV mix −1.2 dBFS). `render-metadata.json` records commit `5cdae70`, one commit before the close-out commit `407243a` that holds the hero glow change it was encoded with. The handshake proof is visible but unlabelled.
- **Process.** Lean mode: no discriminator round judged this film. Gate: `python -m tools verify` (pytest 189, 14 in-Blender checks) plus the F3 re-audit of 56 frames. Nobody has reviewed the audio by ear.

## v1.0.0 (2026-11-13)

- First release: 109 s, 1920x1080, 30 FPS film of the ADCS certificate flow (RDP and TLS paths, one trusted root).
- Pipeline: story model -> scripted Blender scene (EEVEE) -> PNG sequences (beauty, signs, captions) -> FFmpeg composite and encode.
- Audio: 88 sound cues derived from the story events, synthesised deterministically in Python, loudness-normalised to -16.0 LUFS.
- Final signs fixes: signs are held parallel to the image plane, plates and text render in separate view layers (no stipple, no sorting errors), signs keep clear of capsules, cards and private keys, trust links grow from nothing.
- Process: finished in "lean finish mode". The Stage 1 adversarial rounds stopped after R1 was triaged and fixed; round R2 was never judged (usage limits). No discriminator subagents ran for the final film. Gate: `python -m tools verify` (pytest, ruff, mypy, audits, 14 in-Blender checks, blank-frame check) plus two contact-sheet reviews.
- Known limits: the look is stylised grey-box-plus (flat shaded actors, bloom, soft shadows); some check-list signs still overlap the focal subject in crowded frames (about 9% of tag frames, below the 10% test limit).
