# Certificate-Flow-Film — Session Prompts

The project runs as **nine Claude Code sessions**. Each one has its own model and effort level. All the detail lives in `docs\BUILD-CHARTER.md`, so each prompt below stays short and every session works from the same specification.

## Before Session 1 (one-time setup)

1. Create the folder `E:\ClaudeCode\Projects\Certificate-Flow-Film`.
2. Put `BUILD-CHARTER.md` and this file (`SESSION-PROMPTS.md`) in that folder. Session 1 moves both into `docs\`.
3. Open Claude Code **in that folder**, so the project's agents and `CLAUDE.md` load.

## Session plan (Chief of Staff decision)

| # | Session | Model | Effort | Why |
|---|---|---|---|---|
| 1 | Environment + repository | Sonnet 5.5 | Medium | Mechanical setup; mistakes are cheap to fix |
| 2 | Spec freeze | **Opus 5.5** | **High** | Locks every PKI fact, beat and criterion. Errors here spread into everything else |
| 3 | Pipeline + animatic build | Sonnet 5.5 | High | A lot of code against a fixed architecture |
| 4 | Calibration + animatic rounds | **Opus 5.5** | Medium | Triage is the anti-gaming core: deciding which findings are valid |
| 5 | Vertical slice (final look) | **Opus 5.5** | **High** | Sets the look every other scene copies |
| 6 | Full production | Sonnet 5.5 | High | Applies the frozen look to all scenes; long session |
| 7 | Final cut | Sonnet 5.5 | Medium | Mostly rendering, encoding and verification |
| 8 | Docs + Pages | Sonnet 5.5 | Medium | Writing and deployment |
| 9 | Final audit + release | **Opus 5.5** | **High** | Independent final judgement; the public release can't be quietly undone |
| — | Escalation (only if needed) | **Opus 5.5** | **High** | For when a Sonnet session gets stuck |

**Rules:**
- No Extra/Max effort anywhere; it isn't worth the usage on a Pro plan.
- The **pki-discriminator always runs on Opus** (set in its own agent file), even in Sonnet sessions, so PKI accuracy is always judged by the stronger model. The cinema and legibility discriminators run on Sonnet.
- Set the model and effort in Claude Code **before** pasting each prompt. Typing them into a prompt does nothing.
- Start a **new** session for every prompt. Don't continue one session into the next.
- If you hit a usage limit mid-session, wait for the reset, then start a new session on the **same** model and effort and paste the **Resume** prompt.

---

## Session 1 — Environment + Repository
**Model: Sonnet 5.5 · Effort: Medium**

```
You are the Chief of Staff for Certificate-Flow-Film, running Session 1 of 9 (Environment + Repository).

PRE-FLIGHT
- Confirm you are running on Sonnet 5.5. If not, stop and tell me to switch.
- BUILD-CHARTER.md and SESSION-PROMPTS.md are in the project root. Read BUILD-CHARTER.md: the intro and Sections 1, 2, 3, 4, 5, 9, 13 and 17. It is the authoritative spec; follow it exactly.

SCOPE (Phases 1–2 only)
1. Phase 1, Environment: everything in Charter 5.1–5.3, including:
   - Blender 5.2 LTS install and pinning
   - the headless GPU probe with the EEVEE/Cycles decision
   - .venv and requirements-dev.txt
   Record the results in docs\TOOLCHAIN.md and the gitignored config\toolchain.local.json.
2. Phase 2, Repository: everything in Charter 5.4:
   - git init on main, .gitignore
   - the GPL-3.0-or-later / CC BY 4.0 licence split
   - the bundled OFL font
   - a secret scan
   - create the public repository, set topics, push, and verify sync
3. Move BUILD-CHARTER.md and SESSION-PROMPTS.md into docs\ (with git mv once tracked).
4. Create the three discriminator agents in .claude\agents\, copied verbatim from Charter 2.3 (pki on opus, cinema and legibility on sonnet).
5. Create the folder skeleton from Charter Section 9: packages and __init__ files only, with no placeholder logic.
6. Create:
   - CLAUDE.md (at most about 120 lines, meeting every requirement in Charter Section 13; it points to docs\BUILD-CHARTER.md)
   - docs\PROJECT-STATE.md
   - docs\CHIEF-OF-STAFF-APPROVALS.md

GATE
- Every tool is verified with versions recorded, and the GPU probe frame is not blank.
- The repository is public; origin is correct; local HEAD equals origin/main.
- The agent files exist exactly as specified.
- Record APPROVED or REJECTED for Phases 1 and 2 in the approvals record.

CLOSE-OUT
- Commit related changes only, push, and run the sync check.
- In PROJECT-STATE.md, set: Next session = 2, Opus 5.5, High.
- Give the 10-line session report (Charter 17).
- Remind me to start a NEW session for Session 2, so Claude Code picks up the new agents.

ESCALATION
If you hit a blocker you cannot resolve in 2 attempts:
- stop
- write an escalation record in PROJECT-STATE.md (what failed, what you tried, the evidence)
- commit and push
- tell me to run the Escalation prompt
```

---

## Session 2 — Spec Freeze (Stage 0)
**Model: Opus 5.5 · Effort: High**

```
You are the Chief of Staff for Certificate-Flow-Film, running Session 2 of 9 (Spec freeze, Stage 0).

PRE-FLIGHT
- Confirm you are running on Opus 5.5. If not, stop and tell me to switch.
- Read CLAUDE.md and docs\PROJECT-STATE.md.
- Read docs\BUILD-CHARTER.md: the intro and Sections 1, 2, 3, 4, 6, 7, 8, 9, 12 (pure-Python part), 13 and 17.
- Confirm Session 1 is APPROVED and local HEAD equals origin/main. If not, stop and report.
- Confirm /agents lists pki-discriminator, cinema-discriminator and legibility-discriminator.

SCOPE (Phase 3 only)
1. Check the current status of .lab in the IANA root zone database, and record the docs note from Charter Section 1.
2. Write:
   - docs\REFERENCE-SPEC.md, with:
     - F-01..F-17
     - every B-xx beat
     - C-01..C-11 and L-01..L-08, each expanded with a measurable threshold
   - docs\GLOSSARY.md
   - docs\PKI-TECHNICAL-NOTES.md: the full meaning of every beat
   - docs\STORYBOARD.md: lens, camera move, focal subject and caption for every beat
   - docs\GAN-FRAMEWORK.md
3. Implement, in pure Python with no bpy:
   - cff\config\names.py
   - cff\story\model.py, timing.py and captions.py
4. Write the pytest suite for model integrity, timing, names and captions (Charter 12, pure-Python part). Make ruff and mypy clean.
5. Generate docs\TRACEABILITY.md from the model, with a test that fails on any missing ID.

GATE
1. Build a spec packet in qa\rounds\stage0-R<n>\ with:
   - the written docs
   - a model dump
   - schema.json
   No source code and no generator notes.
2. Spawn a fresh pki-discriminator on it and triage per Charter 2.4.
3. Fix and repeat until there are 0 BLOCKER/MAJOR findings, with a cap of 5 rounds.
4. Freeze: record the REFERENCE-SPEC SHA-256 and every round in docs\GAN-LEDGER.md.
5. Record APPROVED or REJECTED for Phase 3.

CLOSE-OUT
- Commit, push, and run the sync check.
- In PROJECT-STATE.md, set: Next session = 3, Sonnet 5.5, High.
- Give the 10-line report.

ESCALATION: as in Session 1.
```

---

## Session 3 — Pipeline + Animatic Build (Stage 1, build)
**Model: Sonnet 5.5 · Effort: High**

```
You are the Chief of Staff for Certificate-Flow-Film, running Session 3 of 9 (Pipeline + animatic build).

PRE-FLIGHT
- Confirm you are running on Sonnet 5.5. If not, stop and tell me to switch.
- Read CLAUDE.md and docs\PROJECT-STATE.md.
- Read docs\BUILD-CHARTER.md: the intro and Sections 1–4, 5.2 (Blender rules), 8, 9, 10 (caption layer), 11, 12 and 17.
- Read docs\REFERENCE-SPEC.md and docs\STORYBOARD.md.
- Confirm Session 2 is APPROVED, the spec hash in GAN-LEDGER matches the file, and local HEAD equals origin/main. If not, stop and report.
- The spec is FROZEN. Do not edit it.

SCOPE (Phase 4, build part only; no GAN rounds yet)
1. Build tools\__main__.py with these commands:
   - env, verify, build, render, captions, packet, contact, palette, motion, sync-check
   Use the standard Blender invocation form from Charter 5.2 everywhere.
2. Build blender\build_scene.py:
   - grey-box versions of every actor
   - world, lighting blocking
   - the camera rig with final blocking
   - the separate caption-layer scene
   Everything is driven from cff (story model, timing, theme). Verify every API against the installed Blender version's docs.
3. Implement blender\checks\scene_checks.py: every in-Blender hard discriminator in Charter 12.
4. Render the full animatic at the 960x540 tier, in resumable chunks (Charter 3.7).
5. Make `python -m tools packet stage1` build a valid packet: frames, motion strips, manifest.json, regressions.json, schema.json.
6. Open a sample of frames (one per scene, plus every transition) with Read to confirm they are not blank and the timing looks right.

GATE
- `python -m tools verify` is fully green.
- The full animatic is rendered and the packet builds.
- Record "Phase 4 build: APPROVED". The Stage 1 gate itself happens in Session 4.

CLOSE-OUT
- Commit, push, and run the sync check.
- In PROJECT-STATE.md, set: Next session = 4, Opus 5.5, Medium.
- Give the 10-line report.

ESCALATION: as in Session 1.
```

---

## Session 4 — Calibration + Animatic Rounds (Stage 1, gate)
**Model: Opus 5.5 · Effort: Medium**

```
You are the Chief of Staff for Certificate-Flow-Film, running Session 4 of 9 (Calibration + animatic GAN rounds).

PRE-FLIGHT
- Confirm you are running on Opus 5.5. If not, stop and tell me to switch.
- Read CLAUDE.md and docs\PROJECT-STATE.md.
- Read docs\BUILD-CHARTER.md: the intro and Sections 1–4 (all of Section 2, especially 2.4–2.8), 7, 11, 12 and 17.
- Read docs\GAN-LEDGER.md.
- Confirm Session 3's build is APPROVED, the spec hash matches, and local HEAD equals origin/main. If not, stop and report.

SCOPE (Phase 4 gate)
1. Implement blender\calibration.py and `python -m tools calibrate <fault>` for the four faults in Charter 2.8, plus a test proving normal builds never enable a fault.
2. Run calibration:
   - Every discriminator must flag its relevant faults as BLOCKER.
   - The hard discriminators must FAIL on private_key_leak, root_issues_leaf and caption_clip.
   Strengthen and re-run until all are caught, and record the results in GAN-LEDGER.
3. Run GAN rounds on the real animatic exactly per Charter 2.4:
   - fresh discriminators each round, in parallel
   - triage every finding
   - fix the accepted ones
   - turn each automatable BLOCKER/MAJOR into a permanent hard test
   - log the round in the ledger
   Respect the gates, the cap of 5 rounds and the anti-mode-collapse rules in Charter 2.7.

GATE
- Stage 1 gate per Charter 2.7.
- Record APPROVED or REJECTED for Phase 4.

CLOSE-OUT
- Commit, push, and run the sync check.
- In PROJECT-STATE.md, set: Next session = 5, Opus 5.5, High.
- Give the 10-line report.

ESCALATION: if the round cap is reached with open BLOCKER/MAJOR findings, write the escalation record (Charter 2.7) and stop.
```

---

## Session 5 — Vertical Slice (Stage 2)
**Model: Opus 5.5 · Effort: High**

```
You are the Chief of Staff for Certificate-Flow-Film, running Session 5 of 9 (Vertical slice: final look on S4).

PRE-FLIGHT
- Confirm you are running on Opus 5.5. If not, stop and tell me to switch.
- Read CLAUDE.md and docs\PROJECT-STATE.md.
- Read docs\BUILD-CHARTER.md: the intro and Sections 1–4, 7 (S4), 8, 10, 11, 12 and 17.
- Read docs\GAN-LEDGER.md.
- Confirm Phase 4 is APPROVED, the spec hash matches, and local HEAD equals origin/main. If not, stop and report.

SCOPE (Phase 5 only)
1. Bring S4 (beats B-04.1 to B-04.5) to the FINAL look:
   - materials, motivated key/rim lighting
   - depth of field, motion blur
   - compositor Glare-node bloom, restrained haze, vignette and grain
   - AgX on the beauty pass
2. Run the AgX palette test frame and the L-07 ΔE + CVD check. Tune material values until they pass.
3. Implement cff\audio\cues.py and synth.py, and produce S4's audio cues.
4. Measure seconds per frame at final settings, and write docs\RENDER-BUDGET.md with the full-film projection and any reductions (Charter 11).
5. Run GAN rounds on the S4 slice until the Stage 2 gate passes (Charter 2.4 and 2.7).

GATE
- Stage 2 is clean.
- Freeze docs\LOOK-BIBLE.md with the approved reference frames and their exact settings, and record its hash in GAN-LEDGER.
- Record APPROVED or REJECTED for Phase 5.

CLOSE-OUT
- Commit, push, and run the sync check.
- In PROJECT-STATE.md, set: Next session = 6, Sonnet 5.5, High.
- Give the 10-line report.

ESCALATION: as in Session 4.
```

---

## Session 6 — Full Production (Stage 3)
**Model: Sonnet 5.5 · Effort: High**

```
You are the Chief of Staff for Certificate-Flow-Film, running Session 6 of 9 (Full production).

PRE-FLIGHT
- Confirm you are running on Sonnet 5.5. If not, stop and tell me to switch.
- Read CLAUDE.md and docs\PROJECT-STATE.md.
- Read docs\BUILD-CHARTER.md: the intro and Sections 1–4, 7, 8, 9, 11, 12 and 17.
- Read docs\LOOK-BIBLE.md and docs\GAN-LEDGER.md.
- Confirm Phase 5 is APPROVED, the spec and look-bible hashes match, and local HEAD equals origin/main. If not, stop and report.
- The spec and the look bible are FROZEN. Match the look bible; do not reinvent it.

SCOPE (Phase 6 only)
1. Apply the final look to every scene, S1 to S9, including the S5 flashback treatment and the S9 hero shot.
2. Generate audio cues for every scene from the story events.
3. Render the full film at the preview tier (1280x720), in resumable chunks.
4. Run GAN rounds until the Stage 3 gate passes (Charter 2.4 and 2.7). All regressions from earlier rounds must stay FIXED.

GATE
- Stage 3 is clean; verify is green.
- Record APPROVED or REJECTED for Phase 6.

CLOSE-OUT
- Commit, push, and run the sync check.
- In PROJECT-STATE.md, set: Next session = 7, Sonnet 5.5, Medium.
- Give the 10-line report.

ESCALATION: if a BLOCKER needs a PKI or creative judgement call you can't make confidently, or the round cap is reached:
- write the escalation record
- commit and push
- tell me to run the Escalation prompt
```

---

## Session 7 — Final Cut (Stage 4)
**Model: Sonnet 5.5 · Effort: Medium**

```
You are the Chief of Staff for Certificate-Flow-Film, running Session 7 of 9 (Final cut).

PRE-FLIGHT
- Confirm you are running on Sonnet 5.5. If not, stop and tell me to switch.
- Read CLAUDE.md and docs\PROJECT-STATE.md.
- Read docs\BUILD-CHARTER.md: the intro and Sections 1–4, 10, 11, 12 and 17.
- Read docs\RENDER-BUDGET.md and docs\GAN-LEDGER.md.
- Confirm Phase 6 is APPROVED, the hashes match, and local HEAD equals origin/main. If not, stop and report.

SCOPE (Phase 7 only)
1. Render the full film at the final tier (1920x1080), in resumable chunks.
   - Poll progress at long intervals to save usage.
   - Record progress in PROJECT-STATE.md so an interrupted render can resume.
2. Render the caption layer.
3. Master the audio: adelay placement, two-pass loudnorm to about −16 LUFS with true peak ≤ −1 dBTP. Verify with ebur128 and astats.
4. Encode per Charter 11 (libx264, yuv420p, BT.709 tags, AAC 48 kHz, faststart).
5. Produce every output in Charter 11:
   - Final MP4, Preview MP4 (≤ about 25 MB)
   - poster, contact sheet
   - render-metadata.json, captions.vtt, transcript.md
6. Run the determinism test.
7. Run GAN rounds on the final cut. The gate needs TWO consecutive clean rounds with fresh discriminators.

GATE
- The Stage 4 gate passes, verify is green, and the FFprobe checks pass.
- Record APPROVED or REJECTED for Phase 7.

CLOSE-OUT
- Commit, push, and run the sync check. Never commit the full MP4.
- In PROJECT-STATE.md, set: Next session = 8, Sonnet 5.5, Medium.
- Give the 10-line report.

ESCALATION: as in Session 6.
```

---

## Session 8 — Docs + GitHub Pages
**Model: Sonnet 5.5 · Effort: Medium**

```
You are the Chief of Staff for Certificate-Flow-Film, running Session 8 of 9 (Documentation + GitHub Pages).

PRE-FLIGHT
- Confirm you are running on Sonnet 5.5. If not, stop and tell me to switch.
- Read CLAUDE.md and docs\PROJECT-STATE.md.
- Read docs\BUILD-CHARTER.md: the intro and Sections 1–4, 13, 14 and 17.
- Confirm Phase 7 is APPROVED and local HEAD equals origin/main. If not, stop and report.

SCOPE (Phase 8 only)
1. Complete every document in Charter Section 13:
   - README.md, with every item listed
   - CHANGELOG.md, CONTRIBUTING.md
   - every docs\ file, and the Tests\ documents
   Every doc must match the final render: names in use, durations, outputs.
2. Verify the related links with gh (Certificate-Flow-Lab, and Approach A if it exists). Link only the verified ones.
3. Build the site in site\ per Charter 14, and deploy it with the GitHub Actions Pages workflow.
4. Verify:
   - the Actions run succeeded
   - the live URL serves the new content
   - the preview video plays
   - the captions track loads
   - the layout works at mobile width

GATE
- Documentation is complete and current, Pages is live and matches main, and all links resolve.
- Record APPROVED or REJECTED for Phase 8.

CLOSE-OUT
- Commit, push, and run the sync check.
- In PROJECT-STATE.md, set: Next session = 9, Opus 5.5, High.
- Give the 10-line report.

ESCALATION: as in Session 1.
```

---

## Session 9 — Final Audit + Release
**Model: Opus 5.5 · Effort: High**

```
You are the Chief of Staff for Certificate-Flow-Film, running Session 9 of 9 (Final audit + v1.0.0 release).

PRE-FLIGHT
- Confirm you are running on Opus 5.5. If not, stop and tell me to switch.
- Read CLAUDE.md and docs\PROJECT-STATE.md.
- Read docs\BUILD-CHARTER.md: the intro and Sections 1–4, 14, 15, 16 and 17.
- Read docs\GAN-LEDGER.md and docs\CHIEF-OF-STAFF-APPROVALS.md.
- Confirm Phases 1–8 are APPROVED and local HEAD equals origin/main. If not, stop and report.

SCOPE (Phase 9)
1. Run the full final audit in Charter Section 16, recording PASS or FAIL with evidence for every item. Re-run verify and the FFprobe checks yourself; do not trust earlier results.
2. Spawn one more fresh pki-discriminator on the final-cut packet as an independent final check.
3. If ANY required item fails:
   - mark the project REJECTED
   - fix what can be fixed
   - re-audit
   Do not release on a FAIL.
4. Only after every item PASSES, release per Charter 15:
   - create the annotated tag v1.0.0 on the audited commit
   - gh release create, with complete notes
   - attach all the assets
   - download them back and compare SHA-256 hashes
   - check everything in the pre-release list

CLOSE-OUT
- Record the final APPROVED or REJECTED decision.
- Commit, push, and run the sync check, including the Pages check.
- In PROJECT-STATE.md, set: project complete, or the exact remaining work.
- Give the full final report from Charter Section 17.

ESCALATION: you are the escalation level. Make the call and record it.
```

---

## Session F2 — v1.1.0 fixes + the single final re-render (after the v1 audit)
**Model: Opus 5.5 · Effort: High** (lean mode: no subagents, no GAN rounds)

Added on 2026-11-13 because session F3 was run twice before F2 existed as a prompt. Run this once, then run F3 (the targeted re-audit and the v1.1.0 pre-release).

```
You are the Chief of Staff for Certificate-Flow-Film, session F2: the remaining audit fixes and the single final re-render for v1.1.0. No subagents, at most 8 images. Do NOT tag or release anything: session F3 does that after a re-audit.

1. Read docs\PROJECT-STATE.md. In docs\AUDIT-v1.md read the "F1 status" table, both "F3 targeted re-audit" records, Section 7 and Appendix A. Read each finding's own section only when you fix it. Do not re-read the spec documents.
2. Fix in this order. One commit per finding, pushed. Every testable fix gets a test named after its finding ID in tests\test_audit_v1.py. `python -m tools verify` must be green after each group.
   a. Camera: V1-CIN-01, V1-CIN-02, V1-CIN-05, V1-PKI-04, V1-PKI-05, V1-CIN-06.
   b. Signs: V1-LEG-03, then V1-LEG-05, then V1-LEG-02. Lower CROSSING_LIMIT to 0.02 in tests\test_gan_findings_stage1.py (the V1-LEG-04 residual).
   c. Small: V1-PKI-06, V1-CIN-07, V1-COL-01, V1-AUD-01, V1-AUD-02, and V1-CIN-03 step 1 only.
   If a target cannot be reached, do not relax a test silently: keep the best passing value and record the achieved number in docs\GAN-LEDGER.md as a residual.
3. `python -m tools render --tier animatic --rebuild`. Review 1 contact sheet and 3 strips (54 s, 62 s, 100 s). Fix what the tests missed.
4. Delete renders\final\beauty, renders\final\signs and renders\final\captions (gitignored build output). Run `python -m tools render --tier final --rebuild` in the background (300-frame chunks) and record progress in PROJECT-STATE. Then `python -m tools audio`, `python -m tools encode`, `python scripts\build_site.py`.
5. Set MP4_PENDING_RERENDER = False in tools\verify.py. `python -m tools verify` must be GREEN with no PENDING line: f1246 and f1396 are not blends, ffprobe shows level <= 41 and color_transfer=bt709.
6. Review 1 contact sheet, 2 strips (one cut, one sign-heavy move) and the poster.
7. Commit, push, `python -m tools sync-check`. Set PROJECT-STATE "Next session" to F3. Report in at most 8 lines. If the final render or the encode cannot finish, record the exact state and stop.
```

---

## Session L1 — v1.2 look pass + the single final render (after v1.1.0)
**Model: Sonnet 5.5 · Effort: High** (lean mode: no subagents, no GAN rounds)

Added on 2026-11-14 by session F3. The plan is `docs\LOOK-PLAN-v1.2.md`. Run L1 once, then L2.

```
You are the Chief of Staff for Certificate-Flow-Film, session L1: the v1.2 look pass. No subagents, at most 6 images. Do NOT tag or release anything: session L2 does that after a re-audit.

1. Read docs\PROJECT-STATE.md and docs\LOOK-PLAN-v1.2.md. Read a source file only when its item names it. Do not re-read the spec documents.
2. Follow the plan exactly. It gives every value and every rule; where it says "stop", stop and record the value. Do not tune by eye.
3. Work order: Item A, C, E, B (second change), D, F. One commit per item, pushed, with `python -m tools verify --skip-blender` green; full `python -m tools verify` after A and after E.
4. Stills-and-strips gate (plan Section 5): `python -m tools build --tier final`, `python -m tools look-test`, view the 2 images named there. Test frames go to renders\look-test, never to renders\final. At most three attempts.
5. Only if the gate passes: commit everything, delete renders\final\beauty, renders\final\signs and renders\final\captions, run `python -m tools render --tier final --rebuild` in the background (300-frame chunks, progress in PROJECT-STATE), then `python -m tools audio`, `python -m tools encode`, `python scripts\build_site.py`, `python -m tools verify`. This is the only full render.
6. View the final contact sheet, a strip of f2700-2710 and the poster. Record the per-beat luma and the luma steps of the Final MP4 (plan Appendix A).
7. Record rulings, gate numbers and stop-rule values in docs\GAN-LEDGER.md "Session L1"; record the phase in docs\CHIEF-OF-STAFF-APPROVALS.md. Commit, push, `python -m tools sync-check`. Set PROJECT-STATE "Next session" to L2. Report in at most 8 lines.
If the gate fails three times, or usage runs short, record the exact state and stop.
```

## Session L2 — v1.2 targeted re-audit + release
**Model: Opus 5.5 · Effort: Medium** (or Fable 5.2; lean mode: no subagents)

```
You are the Chief of Staff for Certificate-Flow-Film, session L2: a targeted re-audit of the v1.2 film and its release. No subagents, at most 8 images.

1. Read docs\PROJECT-STATE.md, docs\LOOK-PLAN-v1.2.md and the "Session L1" entry of docs\GAN-LEDGER.md.
2. Re-run `python -m tools verify` and ffprobe. Record the Final MP4 SHA-256.
3. Check every plan item on the film at its timestamps (hero 98-104 s, flash 81.0 s and 90.0-90.3 s, cut at 46.5 s, proof tag 50.9-52.7 s, the ten focal beats), plus one full-film contact sheet for regressions and every v1.1.0 fix that the look could have broken (sign legibility over haze, caption contrast, cut frames, the trust store being gold before docking). PASS or FAIL per item.
4. Judge V1-CIN-03 on the frames: is the grey-box look closed? Give PKI, legibility and cinema scores.
5. If any BLOCKER or MAJOR fails: write exact fix instructions, name the model needed, and stop without a release.
6. If all pass: update README, CHANGELOG and the Pages text; tag v1.2.0; release it (a full release only if V1-CIN-03 is closed and no new MAJOR exists, otherwise a pre-release) with all assets; download the assets and compare SHA-256; check that Pages is current.
7. Commit, push, `python -m tools sync-check`. Report in at most 8 lines.
```

---

## Resume prompt (any session, after a usage limit or a long context)
**Model and effort: the same as the session being resumed**

```
Continue Certificate-Flow-Film from docs\PROJECT-STATE.md.
- Confirm you are on the model recorded there for the current session. If not, stop and tell me.
- Read CLAUDE.md, docs\PROJECT-STATE.md, and the docs\BUILD-CHARTER.md sections that session needs (listed in docs\SESSION-PROMPTS.md).
- Verify that local HEAD equals origin/main and check for interrupted renders.
- Resume at the recorded "exact next action". Stay within that session's scope, and finish with its gate and close-out.
```

---

## Escalation prompt (only when a session stops with an escalation record)
**Model: Opus 5.5 · Effort: High**

```
You are the Chief of Staff for Certificate-Flow-Film, running an ESCALATION session.

PRE-FLIGHT
- Confirm you are running on Opus 5.5. If not, stop and tell me to switch.
- Read CLAUDE.md, docs\PROJECT-STATE.md (the escalation record), docs\GAN-LEDGER.md, and the BUILD-CHARTER sections relevant to the blocked session.

SCOPE
1. Diagnose the root cause of the escalation, using the evidence, not assumptions.
2. Resolve it within the frozen spec and look bible. If the spec itself is wrong, make a formal amendment per Charter 2.2: written reason, new hash, and reset the clean-round counter.
3. Re-run the blocked session's gate checks until they pass, or document why they can't.

CLOSE-OUT
- Record the decision in the approvals record and the ledger.
- Commit, push, and run the sync check.
- In PROJECT-STATE.md, set Next session to the original session's number, model and effort (or the next session's, if the gate now passes).
- Give the 10-line report.
```
