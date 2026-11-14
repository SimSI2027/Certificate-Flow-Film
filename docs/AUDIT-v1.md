# AUDIT v1 — Certificate-Flow-Film v1.0.0

Date: 2026-11-13. Auditor: Chief of Staff (read-only audit, one session, no subagents, model `claude-fable-5-2`).
Subject: `output\Certificate-Flow-Film-Final.mp4` as released in v1.0.0 (59 318 891 bytes), plus README, Pages text and audio reports.
Outcome in one line: **0 BLOCKER, 16 MAJOR, 10 MINOR. v1.0.0 stays a pre-release. Verdict: ship as v1.1.0 after fixes** (Section 7).

## 1. Method and limits

- Read: PROJECT-STATE, CHANGELOG, REFERENCE-SPEC (hash unchanged: `7cf45afa…6d23`), STORYBOARD, PKI-TECHNICAL-NOTES, Charter 6–8.
- Re-ran: `python -m tools verify`, `ffprobe`, FFmpeg `signalstats`, `scdet`, `freezedetect`, `ebur128`, `astats`, `silencedetect` on the Final MP4.
- Images viewed: 12 of 12, all cut from the Final MP4 with FFmpeg.
  - 1 contact sheet (33 tiles, one per beat, taken 60% into each beat).
  - 6 motion strips (8 frames, every 3rd frame): key sealing f667–688, AD lookup f742–763, CA signing f1015–1036, root reveal and flashback cut f1234–1255, chain docking f1621–1642, hero f3001–3022.
  - 5 close-up sheets: f1621/f1700/f1964/f1747; f1275/f1305/f1345/f1385; f3105/f2085/f318/f2905; f960/f2370/f2540/f1130; f468/f1568/f1470/f2703.
- Numbers marked "plan" come from the project's own sign plan and camera plan (`cff.stage.signs`, `cff.stage.camera`), read by scratch scripts. Each MAJOR finding built on plan numbers also cites a viewed frame or the code that causes it. The scratch scripts are not in the repository; Appendix A holds what is needed to rebuild them as tests.
- Limits. I cannot listen: the audio audit is measurements only. Close-ups were viewed at half resolution, except two crops. Frames not listed above were not viewed.
- Frame numbers are 1-based (frame 1 = 0.00 s). Time = (frame − 1) / 30.
- Severities follow REFERENCE-SPEC. "Beat verdict" uses ACCURATE / MISLEADING / WRONG from the spec; "NOT READABLE" means the beat's PKI point is on screen but too small or too smeared to be seen.

## 2. Re-verification (nothing from earlier sessions was trusted)

| Check | Result |
|---|---|
| `python -m tools verify` | VERIFY GREEN: ruff, mypy --strict (60 files), pytest 158, traceability, palette 87 pairs, planned-film audits 0 hard / 3 advisory, 14 in-Blender checks, frames 3270/3270. **But the frame check ran on the `animatic` tier, not on the shipped `final` tier** (finding V1-PIPE-01). |
| ffprobe, video | H.264 High, level 5.0, 1920x1080, yuv420p, 30/1 fps, 3270 frames (counted by decode), 109.000 s, 4.15 Mb/s, `color_transfer=iec61966-2-1` (V1-ENC-01). |
| ffprobe, audio | AAC LC, 48 kHz, stereo, 192 kb/s, 109.000 s. |
| Cuts | `scdet` finds exactly two cuts, at 41.50 s and 46.50 s (C-02 holds). Both cut frames are blends (V1-CIN-04). |
| Blank or frozen frames | None. Near-black only from f3229 (the closing fade). |
| Loudness of the MP4 | −16.1 LUFS integrated, LRA 4.8 LU, true peak −3.4 dBFS. `loudness.json` (−16.0 LUFS, −3.7 dBFS for the WAV) is truthful. |
| Captions | 13 captions. Wording matches the spec. L-04 holds for all (shortest: CAP-S6b 2.5 s, CAP-S5b 2.6 s). Plates inside title-safe. Plan says 0 caption frames over the focal subject. `captions.vtt` is valid UTF-8. |
| Pages | Live `index.html` is byte-identical to `site\index.html`; preview, poster and VTT return 200 with matching sizes. Pages build type is `workflow`; last deploy succeeded. |
| Release | `gh release edit v1.0.0 --prerelease` done; `isPrerelease=true`. |

## 3. Findings at a glance (priority order)

| # | ID | Sev | Where | One line |
|---|---|---|---|---|
| 1 | V1-LEG-01 | MAJOR | every camera move; worst 50.0–57.0 s, 64.0–66.4 s, 70.0–73.0 s | Signs are rendered with motion blur in the final tier; must-read labels are smeared and unreadable. One-line bug. |
| 2 | V1-PIPE-01 | MAJOR | gate | `tools verify` never inspects the final tier or the MP4, so final-only defects shipped. |
| 3 | V1-LEG-03 | MAJOR | 29.4–33.0, 59.4–66.4, 82.4–85.5 s | Check lists: results are printed before the checks happen ("Revocation OK" 5 s early), rows appear out of order, ticks sit up to 480 px from their lines. |
| 4 | V1-LEG-02 | MAJOR | 51 frames, listed | Signs jump up to 654 px in one frame; name plates flicker on and off. |
| 5 | V1-LEG-04 | MAJOR | 34.8% of frames | Signs cover the focal subject (the "9%" counts only tags). Name plates appear before their object is introduced and can label the wrong object. |
| 6 | V1-PKI-01 | MAJOR | 53.0–56.6 s | The client's trust store turns from grey to gold when the chain docks, and the root card is hidden during docking. Reads as "trust is created now". |
| 7 | V1-PKI-02 | MAJOR | 41.5–44.3 s | The flashback marker "Earlier: offline signing ceremony" is missing for the first 2.8 s of the 5 s flashback. |
| 8 | V1-PKI-03 | MAJOR | 14.0–21.0, 73.0–76.0 s | Nothing identifies which object is the private key; the big bright object under "The private key stays on the server" is the public key. |
| 9 | V1-PKI-04 | MAJOR | 50.9–52.5, 94.0–95.5 s | Handshake proof of possession is 28x23 px (RDP) and 15x16 px (web): not perceivable (F-10). |
| 10 | V1-PKI-05 | MAJOR | 64.0–66.4 s | The two CRL fetches are 22x33 px each; "one per link, none for the root" cannot be seen (F-13). |
| 11 | V1-CIN-01 | MAJOR | 11 beats, table | Focal subjects are tiny: under 1% of the frame in 17 of 33 beats. |
| 12 | V1-CIN-02 | MAJOR | 98.0–104.0 s | Hero shot: user and laptop are off frame, the RDP server is under the caption, the root is 0.8% of the frame, and it is the darkest shot of the film. |
| 13 | V1-CIN-03 | MAJOR | whole film | Look: grey-box. Flat, over-bright CA interiors; grey-on-grey server interiors; empty black upper frame. Deferred (Section 7). |
| 14 | V1-CIN-04 | MAJOR | f1246, f1396 | Both cut frames are double exposures (motion blur blends the two shots). |
| 15 | V1-CIN-05 | MAJOR | 66.4–70.0 s | The payoff "Trusted RDP connection established" has no staging: the session window is 126x101 px and sits under three label plates. |
| 16 | V1-DOC-01 | MAJOR | Pages | Captions show twice on the page: burned into the preview and again from the default-on VTT track. |
| 17 | V1-LEG-05 | MINOR | 42.0, 57.4, 83.7 s | Three must-read tags are on screen for less than 0.35 s per word. |
| 18 | V1-PKI-06 | MINOR | 9.0–12.0, 38.0–41.5 s | Self-signed seals are not perceivable (root seal 50x14 px). |
| 19 | V1-CIN-06 | MINOR | 90.0–90.2 s | A 6-frame white flash as the camera passes a defocused white object. |
| 20 | V1-CIN-07 | MINOR | 21.0–24.0 s | The sealed request barely differs from the unsealed one. |
| 21 | V1-COL-01 | MINOR | wide shots | Amber renders salmon and green renders pale mint at distance. |
| 22 | V1-AUD-01 | MINOR | whole film | Audio is dual mono. |
| 23 | V1-AUD-02 | MINOR | whole film | Loudness normalisation fell back to dynamic mode; signing cue lands about 0.5 s before the stamp. |
| 24 | V1-ENC-01 | MINOR | file | Transfer tag is sRGB although the code asks for BT.709; H.264 level 5.0 is higher than needed. |
| 25 | V1-DOC-02 | MINOR | README, Pages | Wording does not match the film or its status. |
| 26 | V1-DOC-03 | MINOR | PROJECT-STATE | Stale sections contradict the top of the file. |

### F1 status (session F1, Sonnet medium; commits 77b8119, 50fe77e, d7544fc)

"FIXED" = fixed in code/docs with a regression test; frame-level effects show only after the F2 re-render.

| ID | Status | Note |
|---|---|---|
| V1-LEG-01 | FIXED (77b8119) | `apply_tier`: `and not transparent`; test `test_V1_LEG_01_...`. The optional in-Blender check was not added (static test only). Final signs pass must be re-rendered (F2). |
| V1-CIN-04 | FIXED (77b8119) | `motion_blur_position = "START"`; `verify` "cut frames" step measures it (v1.0.0 MP4: steps 14.3 and 30.1). Re-render needed (F2); if f1246/f1396 still fail, render them without blur. |
| V1-PIPE-01 | FIXED (77b8119) | `verify` runs the frame check per tier, a "final MP4" step and a "cut frames" step. While `tools.verify.MP4_PENDING_RERENDER` is True the two MP4 steps report the v1.0.0 problems but pass. **F2 must set it to False after the final re-render.** |
| V1-ENC-01 | FIXED (77b8119) | `setparams` BT.709 tags, `-refs 4 -level:v 4.1` on both encodes. Verified only after the F2 encode. |
| V1-PKI-01 | FIXED (50fe77e) | Trust-store cradle gold from frame 1; shimmer returns to rest. |
| V1-PKI-02 | FIXED (50fe77e) | `LBL-FLASHBACK` fixed at (960, 975) with `Placement.screen_px`. |
| V1-PKI-03 | FIXED (50fe77e) | Four key tags added. Deviation (the audit's offsets overlapped): RDP tags sit at x ∓0.45 m (`PRIV` −0.45, `PUB` +0.45), the RDP public-key window opens at 0.1 s (not 0.4 s, or fewer than 45 frames can be fully shown), web private-key tag at z −0.34. |
| V1-LEG-04 | FIXED for plates (50fe77e); residual NEEDS-F2 | `PLATE_BEATS` table and `_clear_of` on every family are in. Crossing ratio now 297/7120 = 4.2%, not 2%: 258 frames are the CA check lists and the CA 2 note (f932–990, f2503–2565), which need V1-LEG-03's fixed list places. `CROSSING_LIMIT` is 0.045; F2 must lower it to 0.02. `test_V1_LEG_04_at_most_10_signs` passes. |
| V1-LEG-05 | NEEDS-F2 | A longer hold for the two AIA tags collides with the first line of the RDP check list (f1783+), so `LBL-AIA-1` stays at 1.5 s. It resolves with V1-LEG-03 (lines appear when their check starts). Change reverted. |
| V1-DOC-01 | FIXED (d7544fc) | `default` removed from the `<track>`; `site\index.html` rebuilt. **The live page changes only when this is pushed and Pages deploys; confirm once after the F2 deploy.** |
| V1-DOC-02 | FIXED (d7544fc) | README, Pages and CHANGELOG wording. The README no longer says "released". |
| V1-DOC-03 | FIXED (d7544fc) | Stale sections moved to `docs\archive\PROJECT-STATE-sessions-3-4.md`; Git, URLs, Toolchain and Names kept. |

All other findings (V1-LEG-02, -03, V1-PKI-04, -05, -06, V1-CIN-01, -02, -03, -05, -06, -07, V1-COL-01, V1-AUD-01, -02) are unchanged and belong to F2.

### F3 targeted re-audit (2026-11-13, Opus 5.5; 1 image used) — RESULT: GATE FAILED, v1.1.0 NOT released

**Session F2 never ran.** HEAD is the F1 close-out (e2c9269). `output\Certificate-Flow-Film-Final.mp4` is dated 20:10 and the final beauty/sign passes are dated 19:41/20:01. The F1 fixes were committed at 21:12, so the film on disk and in the release is the v1.0.0 film. No F1 frame-level fix can be seen in it.

Re-run evidence:
- `python -m tools verify`: VERIFY GREEN (ruff, pytest 170, 14 in-Blender checks, animatic and final tiers 3270/3270, 0 blank). The green result relies on the waiver `MP4_PENDING_RERENDER = True`: "final MP4: PENDING F2 re-render: 2 known v1.0.0 problem(s)" and "cut frames: ... blends (14.3, 30.1)". Without the waiver verify would be RED. `tests\test_audit_v1.py`: 12 passed.
- ffprobe Final MP4: H.264 High **level 5.0**, 1920x1080, 30/1, **color_transfer=iec61966-2-1**; AAC LC 48 kHz stereo; 109.000 s.
- One 3x3 strip of the Final MP4 (f450, f600, f1246, f1260, f1290, f1396, f1560, f1620, f2100). A whole-film contact sheet was not made: the film is byte-for-byte the v1.0.0 film, so it cannot show F1 regressions.

| ID | Sev | Checked at | F3 result | Evidence |
|---|---|---|---|---|
| V1-LEG-01 | MAJOR | 52.0 s, 54.0 s | **FAIL** | f1560/f1620: `CLIENT01`, `rdp01.1sn0s.lab` and `Remote Desktop Authentication` are smeared and unreadable. The code fix is in, but no re-render was done. |
| V1-CIN-04 | MAJOR | f1246, f1396 | **FAIL** | The verify cut-frame step measures steps of 14.3 and 30.1 (blended). f1246 shows a faded caption over a cross-blend. |
| V1-PIPE-01 | MAJOR | gate | **FAIL (in effect)** | The checks exist but are waived by `MP4_PENDING_RERENDER = True`, so the gate still passes a film with known defects. |
| V1-PKI-01 | MAJOR | 53–56.6 s | **FAIL (not rendered)** | Code fix is not in the film. |
| V1-PKI-02 | MAJOR | 41.5–44.3 s | **FAIL** | f1246 (41.5 s) and f1290 (43.0 s) have no "Earlier: offline signing ceremony" marker. It shows at f1260 only. |
| V1-PKI-03 | MAJOR | 15.0 s, 20.0 s | **FAIL** | f450/f600 have no private-key or public-key tag. "The private key stays on the server" still sits over the unnamed objects. |
| V1-LEG-04 | MAJOR | sign-heavy moves | **FAIL** | Not rendered. The residual (CA check lists, `CROSSING_LIMIT` 0.045 → 0.02) is still open. |
| V1-DOC-01 | MAJOR | live Pages | **PASS** | The live `<track>` has no `default` and matches `site\index.html`. Pages run 43545038707 succeeded. |
| V1-ENC-01 | MINOR | file | **FAIL** | Level 5.0 and sRGB transfer are still in the file. |
| V1-DOC-02 | MINOR | README/Pages | PASS | The pre-release wording is live. |
| V1-DOC-03 | MINOR | PROJECT-STATE | PASS | |
| V1-LEG-05 | MINOR | 42.0/57.4/83.7 s | FAIL | NEEDS-F2 (still open). |

Also open and untouched, MAJOR: V1-LEG-02, -03, V1-PKI-04, -05, V1-CIN-01, -02, -05 (and V1-CIN-03, deferred).

**Decision (Chief of Staff): stop.** 7 MAJOR fixed items fail and 7 MAJOR are untouched. No tag and no v1.1.0 release were made. README, CHANGELOG and Pages were not changed. V1-CIN-03 is not yet recorded as a v2.0 limitation; that is done at release.

**Exact fix instructions: run session F2 as written in Section 7. Model: Opus 5.5, High effort (it needs judgement on rendered frames; Sonnet 5.5 High is the fallback).**
1. Camera: V1-CIN-01, -02, -05, V1-PKI-04, -05, V1-CIN-06. Then signs: V1-LEG-03 (fixed list places, lines appear when their check starts), then V1-LEG-05 (raise the `LBL-AIA-1` hold once LEG-03 removes the collision), then V1-LEG-02. Then the small ones: V1-PKI-06, V1-CIN-07, V1-COL-01, V1-AUD-01, -02. Lower `CROSSING_LIMIT` to 0.02 in `tests\test_gan_findings_stage1.py`.
2. Run `python -m tools render animatic --rebuild`, then review 1 contact sheet and strips at 54, 62 and 100 s.
3. Delete `renders\final\beauty`, `renders\final\signs` and `renders\final\captions`. Run `python -m tools render --tier final` in background chunks of about 300 frames, then `python -m tools audio`, `python -m tools encode` and `python scripts\build_site.py`.
4. Set `tools\verify.py` `MP4_PENDING_RERENDER = False`. `python -m tools verify` must be GREEN with no PENDING lines: the cut-frame steps must not be blends, ffprobe must show level ≤ 4.1 and transfer `bt709`.
5. Then run session F3 again (this targeted re-audit) before any release.

### F3 targeted re-audit, second run (2026-11-13 22:15, `claude-fable-5-2`, High; 1 image used) — RESULT: GATE FAILED AGAIN, v1.1.0 NOT released

**Nothing has changed since the first F3 run. Session F2 still has not run.** HEAD at the start was 3a49773 (the first F3 record), the tree was clean, and there is no other branch, stash or worktree that could hold F2 work.

Re-run evidence (nothing was taken from the first run):
- **The film on disk is the v1.0.0 film, byte for byte.** SHA-256 of the five local outputs equals the digests of the v1.0.0 release assets: Final `5470c46c…f193a`, Preview `df5a1bbe…effbb`, poster `94611603…2fafc`, contact sheet `361b9ff8…86461`, `captions.vtt` `3ad631f2…38404`.
- File times: final beauty 19:05–19:41, signs up to 20:01, captions up to 20:09, Final MP4 20:10. The F1 fixes were committed at 21:12.
- `tools\verify.py` still has `MP4_PENDING_RERENDER = True`; `CROSSING_LIMIT` is still 0.045.
- `python -m tools verify`: VERIFY GREEN (ruff, mypy --strict 61 files, pytest 170, traceability, palette 87 pairs, planned-film audits 0 hard / 3 advisory, 14 in-Blender checks, animatic and final tiers 3270/3270, 0 blank). It is green only through the waiver: "final MP4: PENDING F2 re-render: 2 known v1.0.0 problem(s)" (transfer `iec61966-2-1`, level 50) and "cut frames: PENDING F2 re-render: v1.0.0 cut frames are blends (14.3, 30.1)".
- ffprobe Final MP4: H.264 High, **level 50**, 1920x1080, yuv420p, 30/1, 3270 frames (decoded), **color_transfer=iec61966-2-1**; AAC LC, 48 kHz, stereo; 109.000 s; 59 318 891 bytes.
- One 3x3 strip cut from the Final MP4: f450, f600, f1246, f1290, f1396, f1560, f1620, f1700, f1964. A whole-film contact sheet was not made: the hashes prove that this is the v1.0.0 film, so it cannot contain a regression from the F1 fixes.
- Live Pages: HTTP 200, byte-identical to `site\index.html`; Pages run 43545038707 succeeded.

| ID | Sev | Checked at | Result | What the frame shows |
|---|---|---|---|---|
| V1-LEG-01 | MAJOR | 52.0, 54.0, 65.4 s | **FAIL** | f1560, f1620: `CLIENT01`, `rdp01.1sn0s.lab`, `Remote Desktop Authentication` smeared. f1964: all six check lines and "OCSP if deployed" are unreadable. |
| V1-CIN-04 | MAJOR | f1246, f1396 | **FAIL** | f1396 is a heavy double exposure (gold root smeared over the cyan vault). Verify measures luma steps of 14.3 and 30.1 at the two cuts (limit 3). |
| V1-PIPE-01 | MAJOR | gate | **FAIL (in effect)** | The checks exist and report the defects, but the waiver turns them into PASS. |
| V1-PKI-01 | MAJOR | 54.0, 56.6 s | **FAIL** | f1620: the trust-store cradle is grey while the chain docks. f1700: it is gold. It still reads as "trust is created now". |
| V1-PKI-02 | MAJOR | 41.5, 43.0 s | **FAIL** | f1246 and f1290 have no "Earlier: offline signing ceremony" marker. |
| V1-PKI-03 | MAJOR | 15.0, 20.0 s | **FAIL** | f450 and f600 have no "Private key" or "Public key" tag; the caption "The private key stays on the server" sits over two unnamed shapes. |
| V1-LEG-04 | MAJOR | 54.0, 56.6 s | **FAIL** | f1620 and f1700: `CLIENT01`, the SAN and the EKU plates still sit on the laptop and the user. Residual (`CROSSING_LIMIT` 0.045) still open. |
| V1-DOC-01 | MAJOR | live Pages | **PASS** | The live `<track>` has no `default`. |
| V1-ENC-01 | MINOR | file | FAIL | Level 50 and sRGB transfer tag. |
| V1-DOC-02 | MINOR | README, Pages | PASS | Pre-release wording is live. |
| V1-DOC-03 | MINOR | PROJECT-STATE | PASS | |
| V1-LEG-05 | MINOR | plan | FAIL | NEEDS-F2, untouched. |

Still open and untouched, MAJOR: V1-LEG-02, V1-LEG-03, V1-PKI-04, V1-PKI-05, V1-CIN-01, V1-CIN-02, V1-CIN-05 (and V1-CIN-03, deferred to v2.0).

**Decision (Chief of Staff): stop. 7 fixed MAJORs fail in the film and 7 MAJORs are untouched.** Not done, on purpose: tag v1.1.0, release, README, CHANGELOG, Pages text, the V1-CIN-03 "known limitation" record, the asset hash round-trip. v1.0.0 stays the only release, as a pre-release.

**Why F3 ran twice without F2:** the repository had no ready-to-paste F2 prompt (`docs\SESSION-PROMPTS.md` ended at Session 9). One has been added there as "Session F2". **Model needed: Opus 5.5, High effort.** The fix list is unchanged from the first run (steps 1–5 above), with one correction to the commands: the render CLI takes `--tier`, so use `python -m tools render --tier animatic --rebuild` and `python -m tools render --tier final --rebuild` (the form `tools render animatic` is not accepted).

**Running F3 a third time before F2 has finished will give the same result.** F2 is finished when all four are true: the Final MP4 is newer than the last source commit; its SHA-256 is not `5470c46c…f193a`; `MP4_PENDING_RERENDER = False`; `python -m tools verify` prints no PENDING line.

## 4. Findings in detail

### V1-LEG-01 (MAJOR) Signs are motion-blurred in the final tier

- **Where:** every beat with camera or sign motion. Confirmed on f1555, f1568, f1621–1642, f1663, f1747, f1964, f2155, f2703; mild on f1015–1036.
- **What is wrong:** in-world labels are smeared sideways. Unreadable examples: "CLIENT01", "rdp01.1sn0s.lab", "Remote Desktop Authentication" (50.0–56.0 s); "Installed earlier by policy" as it enters (54.7 s); both AIA tags (58.2 s); all six validation lines and "OCSP if deployed" (65.4 s).
- **Cause (verified in code):** `blender\signs_scene.py` line 101 and `blender\captions_scene.py` line 53 set `use_motion_blur = False`, but `blender\render_frames.py` calls `apply_tier()` again just before rendering, and `blender\render_settings.py` line 44 sets `render.use_motion_blur = tier.motion_blur` for every scene. The `final` tier has `motion_blur=True`. The animatic tier has it off, which is why no check ever saw this.
- **Why it matters:** L-06 fails for most must-read labels in S6 and S7. The film has no narration, so the labels are the story.
- **Exact fix:**
  1. `blender\render_settings.py`, in `apply_tier`: replace `render.use_motion_blur = tier.motion_blur` with `render.use_motion_blur = tier.motion_blur and not transparent`.
  2. Delete the folder `renders\final\signs` (build output, gitignored). Re-run `python -m tools render --tier final`; it skips frames already on disk, so only the signs pass renders. Then `python -m tools encode`.
- **Files:** `blender\render_settings.py`, `tests\test_blender_static.py`, `blender\checks\scene_checks.py`.
- **Verify:**
  - New test `test_V1_LEG_01_overlay_scenes_never_use_motion_blur` in `tests\test_blender_static.py`: the source of `apply_tier` contains `and not transparent` on the `use_motion_blur` line.
  - New in-Blender check: for scenes `SIGNS` and `CAPTIONS`, call `apply_tier(scene, render.tier("final"), transparent=True)` and assert `scene.render.use_motion_blur is False`.
  - One strip of f1621–1642 after the re-render: every label is sharp.

### V1-PIPE-01 (MAJOR) The gate never looked at what shipped

- **Where:** `python -m tools verify` output: `rendered frames (animatic): 3270/3270`.
- **What is wrong:** the only frame check runs on the 960x540 animatic. Nothing checks the final frames or the MP4. V1-LEG-01 and V1-CIN-04 exist only in the final tier.
- **Why it matters:** CLAUDE.md forbids releasing uninspected output. The CHANGELOG's "gate: tools verify" was true but did not cover the release.
- **Exact fix:**
  1. `tools\verify.py`: run the existing frame check for every tier that has a `beauty` folder with frames (`animatic`, `final`), one report line per tier.
  2. Add a step "final MP4" that runs only if `output\Certificate-Flow-Film-Final.mp4` exists. Use `tools.film.probe()` and fail unless: video `h264`, 1920x1080, `r_frame_rate` `30/1`, `nb_frames` 3270; audio `aac`, 48000 Hz, 2 channels; `format.duration` within 0.05 s of `timing.total_duration_s()`.
  3. Add a step "cut frames" (V1-CIN-04) using the measurement in Appendix A.4.
- **Files:** `tools\verify.py`, `tools\film.py`, `tests\test_tools.py`.
- **Verify:** `python -m tools verify` prints the three new lines and is green after the re-render; temporarily renaming the MP4 makes only the MP4 step report "skipped".

### V1-LEG-03 (MAJOR) Check lists state results before the checks happen

- **Where (plan, confirmed on f960, f1861, f2540):**
  - B-04.3: all four lines appear together at f883 (29.40 s); the ticks resolve at 29.1, 29.7, 30.3 and 30.9 s.
  - B-06.4: lines 3–6, including "Revocation OK", appear at f1783 (59.40 s). Lines 1–2 appear at f1833 (61.07 s), after their own ticks. All lines vanish f1807–1823. The CRL fetches run 64.1–65.6 s and the revocation tick resolves at 65.6 s, so "Revocation OK" is on screen about 5 s before revocation is checked.
  - B-08.1: all four lines at f2473 (82.40 s).
  - Ticks are 3D objects and lines are overlay signs. The layout engine moves the lines up to 457 px (CA 1) and 480 px (CA 2) from their ticks. On f960 and f2540 only two of four ticks are visible and neither lines up with a row.
  - The tick mesh is a ring with two horizontal bars (`blender\actors\artifacts.py`, `tick`). It reads as "⊖", not as a check mark.
- **Why it matters:** F-06 and F-12 are sequences of distinct checks. The film shows a static bullet list (slide grammar, C-09) and asserts "Revocation OK" before the check (beat B-06.4: MISLEADING).
- **Exact fix (four parts; do them in this order):**
  1. **Each line appears when its own check starts.** In `cff\stage\labels.py`, `_check_placements`: replace the shared window with one window per line.
     - Add `def _check_window(beat, event_id, until=None)`: `start = event.start_s − timing.beat_window(beat)[0]`; return `Window(beat, max(0.1, round(start * FPS) / FPS), until=until)`.
     - CA lines: event `f"E-04.3{'abcd'[index]}"` for CA 1 and `f"E-08.1{'abcd'[index]}"` for CA 2.
     - RDP lines: the event that already supplies `rdp_check` (iterate the `E-06.4*` events and keep `e.id`), with `until="B-06.5"`.
     - Web lines: the `event_id` already in the loop.
     - `LBL-CA2-NOTE`: `Window("B-08.1", 1.1)` (with the Enroll check, E-08.1c).
     - Delete `LIST_LEAD_S` and `_list_window`.
  2. **Each list gets one fixed place on screen for its whole life.** In `cff\stage\signs.py` add `fixed_list_positions()` (cached) exactly as in Appendix A.3. It returns `label_id -> (x, y)` for the rows of these four lists, in this row order:
     - CA 1: REQUESTER_AUTHENTICATED, TEMPLATE_PUBLISHED_ON_CA, ENROLL_PERMISSION, TEMPLATE_POLICY.
     - CA 2: the same four, with `LBL-CA2-NOTE` inserted after ENROLL_PERMISSION.
     - RDP chain: CHAIN_TO_TRUSTED_ROOT, SIGNATURES, VALIDITY, NAME_MATCH, EKU, REVOCATION, then `LBL-OCSP`.
     - Web chain: NAME_MATCH, EKU, VALIDITY, REVOCATION.

     In `_frame_candidates`, right after the `exists` test: if the label is in that map, build its rect with `_rect_for(placement, x, y)`, use `state.focus_distance` as depth, append the candidate with `must=True`, and `continue`. Skip `_clear_of` and the list-pitch loop for these labels. Remove `"LBL-ISSUING_CA1-"`, `"LBL-ISSUING_CA2-"`, `"LBL-CA2-NOTE"`, the `("LBL-CHAIN-RDP-", "LBL-OCSP")` entry and `("LBL-CHAIN-WEB-",)` from `LISTS`.
  3. **The tick belongs to its line.** In `blender\signs_scene.py`, `_sign`: for the 18 check lines (not the note, not OCSP) add a child mesh in the `TEXT` collection, in sign units (1 unit = cap height), text origin at x = 0:
     - ring: flat annulus, outer radius 0.55, inner 0.42, 24 segments, centre (−1.1, 0);
     - check mark: two flat quads 0.12 wide, from (−1.35, 0.02) to (−1.15, −0.22) and from (−1.15, −0.22) to (−0.80, 0.26);
     - for `LBL-CHAIN-RDP-REVOCATION` only, also a disc of radius 0.14 at (−1.1, 0) (the pending dot);
     - material: a copy of `materials.caption_material("text")` with the colour of the list's role from the role table in `cff\theme\palette.py` (CA 1 cyan, CA 2 violet, both chain lists validated green);
     - widen the plate of these lines by 1.6 cap heights on the left, in `ty.sign_plate_size_px` callers and in `_rect_for`;
     - key the tick's alpha with the line's alpha. For REVOCATION: from the line's first frame the ring and dot are pending amber and the check mark has alpha 0; at the first frame of E-06.5d the dot goes to alpha 0 and the ring and check mark turn validated green.
  4. **Stop rendering the 3D ticks.** Where the Blender objects are created from the catalogue (search `blender\` for the loop that calls the actor builders; `tick` is in `blender\actors\artifacts.py`), set `hide_render = True` on every object of `Kind.TICK`. Leave the model, catalogue and timeline unchanged so the existing tick tests still run.
- **Chief of Staff ruling:** this does not change REFERENCE-SPEC text (ticks still resolve one by one, check 6 still appears pending). No amendment. Record the ruling in the ledger.
- **Tried and rejected in this audit (do not repeat):** moving the CA tick rail up 0.9–1.2 m pushes rows 1–2 outside title-safe; a tighter row pitch with a longer shot still leaves lines 324–351 px from their ticks; right-aligning the lines to the left of the rail makes the engine move them further (up to 1016 px). With today's camera, Appendix A.3 finds a fully free fixed place for the CA 1 list (x0 = 268, y0 = 58) and the web list (x0 = 1036, y0 = 466), and places with 45 and 15 blocked frames for the CA 2 and RDP lists.
- **Files:** `cff\stage\labels.py`, `cff\stage\signs.py`, `cff\theme\typography.py`, `blender\signs_scene.py`, `blender\materials.py`, `blender\build_scene.py`, `tests\test_labels.py`, `tests\test_gan_findings_stage1.py`.
- **Verify (new tests in `tests\test_audit_v1.py`):**
  - `test_V1_LEG_03_no_check_line_before_its_check`: for each of the 18 lines, the first frame with any alpha is ≥ the first frame of its event.
  - `test_V1_LEG_03_check_lines_never_move`: within a list, each line's rect is identical on every frame.
  - `test_V1_LEG_03_revocation_ok_after_fetches`: the REVOCATION line's check mark is keyed visible no earlier than the first frame of E-06.5d.
  - `python -m tools legibility` exits 0.
  - Review one frame each at 31.5 s, 62.0 s, 65.8 s and 84.6 s (one 2x2 image).

### V1-LEG-02 (MAJOR) Signs jump and flicker

- **Where (plan):** 51 frames on which a visible sign moves more than 96 px (5% of the frame width, the C-06 pop limit) in one frame. Largest: f1905 (63.47 s) six lines 654 px; f2331 (77.67 s) 585 px; f305 (10.13 s) 516 px; f2483 and f2503 (82.7, 83.4 s) 477–513 px; f882, f932, f991 (29.4, 31.0, 33.0 s) 346–453 px; f1958 (65.23 s) 505 px. 29 runs shorter than 1 s (a name flashes and goes), for example `LBL-AD` six times, `LBL-CA2` at 9.07 s and 12.17 s, `LBL-FLASHBACK` f1254–1267.
- **Confirmed on frames:** "rdp01.1sn0s.lab" fades in at f748 and is fading out at f763 (AD-lookup strip); "Earlier: offline signing ceremony" shows faintly at f1255 and is gone by f1275.
- **Why it matters:** a pop is a C-06 violation; a label that moves cannot be read (L-06); it looks like a layout bug, not a film.
- **Cause:** `_clear_of` and `_nudge_block` in `cff\stage\signs.py` choose the shortest move independently on every frame, so the choice flips between sides.
- **Exact fix:**
  1. `cff\theme\typography.py`: add `SIGN_JUMP_PX = 48.0`; change `SIGN_MIN_RUN_FRAMES` from 12 to 24.
  2. `cff\stage\signs.py`, `plan_signs`: replace `_runs(sorted(by_frame))` with `_steady_runs(by_frame)` from Appendix A.2. A run now also ends where a sign's rect moves more than `SIGN_JUMP_PX` between two consecutive frames, so the existing fade-out and fade-in hide the move, and pieces shorter than 24 frames are dropped.
  3. Hysteresis. Give `_clear_of` two more parameters, `memory: dict[int, tuple[float, float]] | None` and `key: int` (the family number). When `memory` holds a previous `(dx, dy)` for `key`, choose the `good` option nearest to it (`min` by `math.hypot(dx − pdx, dy − pdy)`) instead of the shortest; store the choice; clear the entry when no move is needed. Thread `memory` from `plan_signs` (one dict for the whole pass, frames in ascending order) through `_visible_set` and `_frame_candidates`. All other callers pass `None`.
- **Files:** `cff\stage\signs.py`, `cff\theme\typography.py`, `tests\test_audit_v1.py`.
- **Verify:** `test_V1_LEG_02_no_sign_jumps` (Appendix A.2: 0 frames with a move over 96 px at alpha ≥ 0.5) and `test_V1_LEG_02_no_sign_flashes` (no run shorter than 24 frames); `python -m tools legibility` exits 0. If a must-read label now fails, do not relax the test: report the label and its hidden reasons in the ledger.

### V1-LEG-04 (MAJOR) Signs cover the focal subject; names appear too early

- **Where (plan):**
  - The CHANGELOG's "about 9%" is 276 of 2946 tag frames (9.4%), and it counts only windowed tags. 258 of the 276 are the two CA check lists and the CA 2 note over the evaluation cradle and the request capsule on it: f932–990 (31.0–33.0 s) and f2503–2565 (83.4–85.5 s). Confirmed on f960 and f2540: the capsule is behind the lines "Template published on this CA" and "Enroll permission granted".
  - Counting name plates too, **1137 of 3270 frames (34.8%)** have at least one sign over the focal subject's bounds (bounding boxes, so this is an upper limit on covered pixels). Longest: `LBL-CERT-RDP-SAN` and `LBL-HOST-CLIENT` over the chain and laptop f1591–1710 and f1771–1898 (confirmed on f1621–1642); three plates over the laptop f1997–2100 (confirmed on f2085); `LBL-ROOT` over the root plinth f2969–3117 (confirmed on f3001–3022); eleven different name plates over the focal bounds within f2791–2832.
  - Names show before their object is introduced: "1SN0S Issuing CA 1", "1SN0S Issuing CA 2" and "pki.1sn0s.lab" at 9–12 s (f318), "WEB01" and "portal.1sn0s.lab" at 5.6 s. On f318 "1SN0S Issuing CA 2" sits directly above "rdp01.1sn0s.lab" on the RDP server; on f742–763 "1SN0S Issuing CA 1" sits on the RDP server's open door. Both read as a wrong name for the server.
  - Up to 15 signs on screen (B-07.3) and 12–14 in B-06.1, B-07.1, B-07.4 and B-09.1.
- **Why it matters:** L-05/L-06 intent (text never covers the action), C-03 (one clear subject), and a wrong-looking name on a PKI actor is a PKI risk.
- **Exact fix:**
  1. Persistent plates show only in listed beats. In `cff\stage\labels.py` add the table below as `PLATE_BEATS: dict[str, tuple[str, ...]]`. In `cff\stage\signs.py`, `exists()`: for a placement with `window is None`, return `False` unless `beat_of_frame().get(frame)` is in `PLATE_BEATS[label_id]`.
  2. In `_frame_candidates`, apply `_clear_of` to every family, not only to families with a windowed member (delete the `if any(c.placement.window is not None …)` condition).
  3. Tighten `test_CIN_S1R1_04_…`: count every sign (drop the `window is None` skip) and require `crossing / shown <= 0.02`.

  | Label | Beats in which it may show |
  |---|---|
  | `LBL-HOST-CLIENT` | B-01.1, B-02.2, B-06.2, B-09.1, B-09.2 |
  | `LBL-HOST-RDP` | B-02.1, B-02.3, B-04.5, B-06.1, B-09.2 |
  | `LBL-HOST-WEB` | B-07.1, B-08.2, B-09.2 |
  | `LBL-SITE-WEB` | B-07.1, B-09.1 |
  | `LBL-AD` | B-02.3, B-04.1, B-07.3 |
  | `LBL-DC` | B-02.3, B-04.1 |
  | `LBL-PKI` | B-06.3, B-06.5 |
  | `LBL-ROOT` | B-05.1, B-05.2, B-05.3, B-08.3, B-09.2 |
  | `LBL-CA1` | B-04.1, B-04.2, B-04.3, B-04.4, B-05.2, B-05.3, B-07.3, B-09.2 |
  | `LBL-CA2` | B-07.3, B-07.4, B-08.1, B-08.2, B-08.3, B-09.2 |
  | `LBL-TPL-RDP` | B-02.3, B-04.1 |
  | `LBL-TPL-WEB` | B-07.1, B-07.3 |
  | `LBL-SELF` | B-02.2 |
  | `LBL-CERT-RDP-SAN`, `LBL-CERT-RDP-EKU` | B-04.4, B-04.5, B-06.4 |
  | `LBL-CERT-WEB-SAN`, `LBL-CERT-WEB-EKU` | B-08.2, B-09.1 |
  | `LBL-REQ-CA1` | B-05.2 |

- **Anti-gaming note:** every label's `must_read_beats` is inside its row, so no must-read text is removed. Add a test that asserts this.
- **Files:** `cff\stage\labels.py`, `cff\stage\signs.py`, `tests\test_gan_findings_stage1.py`, `tests\test_labels.py`, `tests\test_audit_v1.py`.
- **Verify:** the tightened crossing test; `test_V1_LEG_04_plate_beats_cover_must_read`; `test_V1_LEG_04_at_most_10_signs` (no frame with more than 10 signs at any alpha; v1.0.0 peaks at 15); `python -m tools legibility` exits 0. If the crossing test cannot reach 0.02, do not relax it silently: record the achieved ratio and the remaining label and frame ranges in the ledger.

### V1-PKI-01 (MAJOR) The trust store appears to become trusted when the chain arrives

- **Where:** B-06.2, 53.0–56.6 s. Frames f1621–1642, f1700.
- **What is wrong:** during docking (54.0–54.7 s) the root card is hidden behind the grey side of its cradle. Then the cradle itself turns gold at 55.2–56.6 s and stays gold. In code: `TS-CLIENT-ROOT` is `R.NEUTRAL` and `choreography.py` line 599 does `glow_to("TS-CLIENT-ROOT", …, glow_value(R.ROOT, 0.25))`, a permanent change. The only visible change on the trust store is grey to gold, right after the cards dock.
- **Why it matters:** F-11 and B-06.2 require a gold root that is **already** there. Beat verdict: MISLEADING.
- **Exact fix (`cff\stage\choreography.py`):**
  1. In `initial()`, add `("TS-CLIENT-ROOT", glow_value(R.ROOT, 0.25)),` to the tuple, so the cradle is gold from frame 1.
  2. Replace line 599 with `self.glow_pulse("TS-CLIENT-ROOT", f0c, f1c, glow_value(R.ROOT, 0.6), rest=glow_value(R.ROOT, 0.25))`, so the shimmer returns to the same state.
- **Files:** `cff\stage\choreography.py`, `tests\test_audit_v1.py`.
- **Verify:** `test_V1_PKI_01_trust_store_is_gold_before_docking`: the glow track of `TS-CLIENT-ROOT` has the same value at frame 1, at the first frame of E-06.2a and at the last frame of B-06.6. One frame at 54.3 s shows a gold cradle.

### V1-PKI-02 (MAJOR) The flashback is not marked as "earlier" for its first 2.8 s

- **Where:** B-05.2, f1246–1395. Plan: `LBL-FLASHBACK` shows f1254–1267 (14 frames, faint), then only from f1330 (44.30 s). Confirmed: absent on f1275 and f1305, present on f1345 and f1385.
- **Why it matters:** for 2.8 s the viewer reads "The Root CA signs the issuing CA certificate" over a live-looking scene. AR-01 says the root signs nothing in the present. Desaturation helps, but the spec asks for a clear marker and makes the tag must-read.
- **Exact fix:**
  1. `cff\stage\labels.py`: add a field `screen_px: tuple[float, float] | None = None` to `Placement`. Change the `LBL-FLASHBACK` placement to `Placement("LBL-FLASHBACK", None, (0.0, 0.0, 0.0), CAP_TAG * 1.4, window=Window("B-05.2", 0.1, 4.9), screen_px=(960.0, 975.0))` (the window is unchanged).
  2. `cff\stage\signs.py`, `_frame_candidates`, right after the `exists` test: if `placement.screen_px` is set, build the rect with `_rect_for(placement, *placement.screen_px)`, depth `state.focus_distance`, `must=True`, append and `continue`; never pass it to `_clear_of`.
  3. Measured in this audit: the 617x52 px plate centred at (960, 975) is inside title-safe, never in a caption band (the flashback caption is in the top band), and touches a protected rect on 1 of 150 frames.
- **Files:** `cff\stage\labels.py`, `cff\stage\signs.py`, `tests\test_audit_v1.py`.
- **Verify:** `test_V1_PKI_02_flashback_marker_whole_flashback`: `LBL-FLASHBACK` has alpha 1.0 on at least 125 of the 150 frames f1246–1395, and alpha > 0 by f1250.

### V1-PKI-03 (MAJOR) The private key is never identified

- **Where:** B-03.1–B-03.3 (14.0–21.0 s) and B-07.2. Frames f457, f468, f526.
- **What is wrong:** two white shapes form. The public key is a large glowing hexagon; the private key is a small key shape that goes into the container. The caption says "The private key stays on the server" while the largest, brightest object on screen is the public key, which then travels into the request. No label names either key.
- **Why it matters:** F-03 and F-04 are the film's central claim. A viewer can take the travelling hexagon for the private key. The glossary already has both terms.
- **Exact fix:**
  1. `cff\story\model.py`, next to `LBL-FLASHBACK` in the label list, add:
     - `Label("LBL-KEY-RDP-PRIV", LabelKind.TAG, "Private key", "KEY-RDP-PRIV", ("B-03.1", "B-03.2"))`
     - `Label("LBL-KEY-RDP-PUB", LabelKind.TAG, "Public key", "KEY-RDP-PUB", ("B-03.1",))`
     - `Label("LBL-KEY-WEB-PRIV", LabelKind.TAG, "Private key", "KEY-WEB-PRIV", ("B-07.2",))`
     - `Label("LBL-KEY-WEB-PUB", LabelKind.TAG, "Public key", "KEY-WEB-PUB", ("B-07.2",))`
  2. `cff\stage\labels.py`, in the windowed tags:
     - `Placement("LBL-KEY-RDP-PRIV", "KEY-RDP-PRIV", (0.0, -0.12, 0.34), CAP_TAG, window=Window("B-03.1", 0.4, until="B-03.4"))`
     - `Placement("LBL-KEY-RDP-PUB", "KEY-RDP-PUB", (0.0, -0.12, 0.34), CAP_TAG, window=Window("B-03.1", 0.4, until="B-03.3"))`
     - `Placement("LBL-KEY-WEB-PRIV", "KEY-WEB-PRIV", (0.0, -0.12, 0.34), CAP_TAG, window=Window("B-07.2", 0.2))`
     - `Placement("LBL-KEY-WEB-PUB", "KEY-WEB-PUB", (0.0, -0.12, 0.34), CAP_TAG, window=Window("B-07.2", 0.2))`
  3. Add "Private key" and "Public key" to the must-read lines of B-03.1 and B-07.2 in `docs\STORYBOARD.md`; regenerate `docs\TRACEABILITY.md` with `python -m tools traceability`.
- **Chief of Staff ruling:** the spec does not enumerate labels, and both terms are in the glossary. No amendment; note it in the ledger.
- **Files:** `cff\story\model.py`, `cff\stage\labels.py`, `docs\STORYBOARD.md`, `docs\TRACEABILITY.md`, `tests\test_audit_v1.py`.
- **Verify:** `python -m tools legibility` lists the four labels as OK; `test_V1_PKI_03_private_key_tag_never_leaves_the_server`: on every frame the projected anchor of `LBL-KEY-RDP-PRIV` is inside the projected bounds of `RDP_SERVER` expanded by 100 px. One frame at 15.5 s.

### V1-PKI-04 (MAJOR) Proof of possession in the handshake cannot be seen

- **Where (plan):** `HS-RDP` median 28x23 px over 50.9–52.5 s; the key container during its key pulse (50.9–51.2 s) 30x32 px; `HS-WEB` 15x16 px over 94.0–95.5 s. Confirmed on f1568: the proof is not identifiable and the server is out of frame.
- **Why it matters:** F-10, "a certificate alone proves nothing". Beat verdict for B-06.1: NOT READABLE.
- **Exact fix:**
  1. `cff\stage\objects.py`: multiply the `size` of `HS-RDP` and `HS-WEB` by 2.5 on every axis.
  2. `cff\theme\shots.py`, shot `present-follow` (B-06.1): change `dist` 6.0 to 4.5 and `follow` 0.5 to 0.7. Shot `browser-arc` (B-09.1): change `dist` 7.4 to 6.0 and `follow` 0.25 to 0.4.
  3. Run `python -m tools verify`. If a camera audit (C-02, C-03, C-06, C-09) fails, step back toward the old values in halves (for example `dist` 5.25, `follow` 0.6) until it passes.
  4. Apply the size rule in V1-CIN-01 to these two beats as well.
- **Files:** `cff\stage\objects.py`, `cff\theme\shots.py`, `tests\test_audit_v1.py`.
- **Verify:** `test_V1_PKI_04_handshake_proof_is_visible`: median longer side of `HS-RDP` over E-06.1d–f ≥ 60 px and of `HS-WEB` over E-09.1d–q ≥ 45 px (Appendix A.1). If the first passing camera values give less, keep them, set the test to the achieved value rounded down to 5 px, and record both numbers in the ledger as a residual.

### V1-PKI-05 (MAJOR) Revocation per link cannot be seen

- **Where (plan):** `CRL-CA1` 22x33 px and `CRL-ROOT` 22x27 px over 64.1–65.6 s. Confirmed on f1964: two specks near the stack, with every label smeared.
- **Why it matters:** F-13 (one fetch per non-root link, none for the root) is a headline fact. Beat verdict for B-06.5: NOT READABLE.
- **Exact fix:**
  1. `cff\stage\objects.py`: `CRL-CA1`, `CRL-ROOT` (and any web CRL scroll objects, if the catalogue has them): `size` from `(0.34, 0.12, 0.12)` to `(0.85, 0.30, 0.30)`.
  2. `cff\stage\choreography.py`, B-06.5: change the dock points `dock_cert` and `dock_copy` from `(0.62, 0.0, 0.0)` to `(0.95, 0.0, 0.0)` beside `STACK_CERT` and `STACK_INTERMEDIATE`, so the larger scrolls do not enter the cards. Do the same for web CRL docks in B-09.1, if present.
  3. `cff\theme\shots.py`, `revocation-pan`: `dist` 13.5 to 11.0. Same audit rule as V1-PKI-04 step 3.
- **Files:** `cff\stage\objects.py`, `cff\stage\choreography.py`, `cff\theme\shots.py`, `tests\test_audit_v1.py`.
- **Verify:** `test_V1_PKI_05_crl_fetches_are_visible`: median longer side of each CRL scroll during its own fetch event ≥ 60 px; at the last frame of each fetch the scroll's centre is within 1.0 m of the card it checks and at least 0.6 m from the root card. Same residual rule as V1-PKI-04.

### V1-CIN-01 (MAJOR) Focal subjects are too small

- **Where (plan, median projected size during the beat hold; confirmed on the contact sheet and on f1470, f1568, f1621, f3105):**

  | Beat | Focal object | Size px | % of frame |
  |---|---|---|---|
  | B-05.3 | `CERT-CA1` | 39 x 26 | 0.05 |
  | B-07.4 | `REQ-WEB` | 46 x 16 | 0.04 |
  | B-08.3 | `CERT-CA2` | 49 x 45 | 0.11 |
  | B-06.1 | `CERT-RDP` | 53 x 43 | 0.11 |
  | B-06.3 | `AIA-RDP` | 49 x 53 | 0.12 |
  | B-05.2 | `CARTRIDGE` + `REQ-CA1` | 55 x 34 | 0.09 |
  | B-04.2 | `REQ-RDP` | 65 x 22 | 0.07 |
  | B-01.2 | `PULSE-RDP-1` | 78 x 66 | 0.25 |
  | B-02.3 | `TPL-RDPAUTH` | 96 x 23 | 0.11 |
  | B-02.2 | `CERT-RDP-SELF` | 99 x 68 | 0.32 |
  | B-04.5 | `CERT-RDP` | 145 x 96 | 0.67 |

  The hero beats B-09.2 and B-09.3 (root 141x120 and 91x85 px) are handled by V1-CIN-02. Also under 1% of the frame, but above the size target: B-03.3, B-03.4, B-06.5, B-09.1.

- **Why it matters:** C-03 asks for one clear focal subject. A 50 px subject in a dark 1920 px frame is not a subject. This is the main reason the film reads as a wide diagram with labels.
- **Exact fix (mechanical; do it before the sign fixes, because sign layout depends on the camera):**
  1. Add `python -m tools focal` that prints Appendix A.1 for every beat.
  2. Targets for the median longer side during the beat hold: 150 px by default; 90 px for the travel beats B-01.2, B-04.2 and B-07.4; 80 px for B-05.3 and B-08.3 (both ends of a trust link must stay in frame).
  3. For each failing beat, in `cff\theme\shots.py`: multiply that shot's `dist` by 0.85, run `python -m tools focal` and `python -m tools verify`. Repeat up to 6 times. If a camera audit fails, undo the last step, raise `follow` by 0.1 (maximum 0.9) and try the step once more. Keep the best passing value. Do not touch `lens`, `az` or `el`.
  4. Beats that still miss the target go in the ledger with their achieved size.
- **Files:** `cff\theme\shots.py`, `tools\__main__.py`, new `tools\focal_audit.py`, `tests\test_audit_v1.py`.
- **Verify:** `test_V1_CIN_01_focal_subject_size` with the targets above (or the recorded residuals); camera audits green; one contact sheet.

### V1-CIN-02 (MAJOR) The hero shot does not show the complete topology

- **Where:** B-09.2, f2941–3120 (98.0–104.0 s). Frames f3001–3022, f3049, f3105.
- **What is wrong:**
  - Plan: the user and the laptop project to about (100, 1428) and (−51, 1441), below and left of the frame. The RDP server sits at the bottom edge (centre y ≈ 1042), behind or below the bottom caption band (y 893–1007) until 103.3 s. On f3001–3022 and f3105 neither the user nor the desk can be seen.
  - The root vault is 141x120 px (0.82% of the frame). On f3105 the servers are smaller than their own name plates.
  - It is the darkest shot of the film: mean luma 40.0 against a film mean of 55.7 (8-bit video range).
  - Eleven name plates; the root's own plate covers its plinth on f2969–3117.
  - The top 22% of the frame is empty black on f3001–3022.
- **Why it matters:** B-09.2 requires "the user consuming both services" and both servers under their CAs. This is the image the poster is taken from. Beat content is incomplete (not a PKI error).
- **Exact fix:**
  1. `cff\theme\shots.py`, shot `hero`: try `el` 28, 32, 36, 40 with `dist` 40, 44, 48, 52 (inner loop `dist`). Take the first pair that passes the test below with camera audits green. Give `close` (B-09.3) the same `el` and `dist + 2`.
  2. Put CAP-S9a in the top band: in `cff\stage\caption_layout.py`, `bands()`, force `"CAP-S9a": TOP` after the automatic choice. If `caption_layout.focal_overlaps()` then reports CAP-S9a, move on to the next (`el`, `dist`) pair in step 1.
  3. V1-LEG-04's table already cuts the hero to six plates (`LBL-ROOT`, `LBL-CA1`, `LBL-CA2`, `LBL-HOST-RDP`, `LBL-HOST-WEB`, `LBL-HOST-CLIENT`).
  4. Brightness: after the re-render, B-09.2 must have mean `YAVG` ≥ 50 (Appendix A.4). If it does not, in `cff\stage\choreography.py` raise the glow level of the two green channels and the three trust links during B-09.2 from `GLOW_ACTIVE` to `GLOW_PEAK`. Do not change world or lamp energy (that belongs to V1-CIN-03).
- **Files:** `cff\theme\shots.py`, `cff\stage\caption_layout.py`, `cff\stage\choreography.py`, `tests\test_audit_v1.py`.
- **Verify:** `test_V1_CIN_02_hero_holds_the_whole_topology`: on at least 90% of the B-09.2 hold frames the projected bounds of `USER`, `CLIENT`, `RDP_SERVER`, `WEB_SERVER`, `ISSUING_CA1`, `ISSUING_CA2` and `ROOT_CA` lie fully inside x 96–1824 and y 200–1026 (below a top caption); root width ≥ 110 px. One hero strip and the new poster.

### V1-CIN-03 (MAJOR, deferred) The look is still a grey-box

- **Where:** whole film. Measured: mean luma 105.3 in B-04.3, 90.1 in B-04.4 and 83.8 in B-08.1, against 44–52 in the beats around them (a 2x brightness step at 29.0 s and 82.0 s); mean saturation 33.7 there against 8–12 elsewhere. Seen on f960, f1015–1036, f2540 (a flat, evenly lit cyan or violet box), f457–f685 (grey props on grey walls, soft black shadow blobs on the back wall), f1234–1243 (plain box on a plain cone and disc, empty black above).
- **Why it matters:** C-05 (motivated key and rim light), C-08, C-09 and the charter's "film, not diagram" goal. My estimate of the cinema score is 4 of 10.
- **Fix:** this needs look development (materials, light design, set dressing) and judgement on rendered frames. It cannot be written as a no-judgement recipe. It is **out of scope for v1.1.0**; see Section 7. Two bounded steps that are safe to take now:
  1. `blender\materials.py`: where the CA vault's inner walls get their role colour, multiply the base colour value by 0.45, so B-04.3 and B-08.1 land at mean `YAVG` 55–75.
  2. Keep the CHANGELOG line that calls the look "stylised grey-box-plus".
- **Verify:** Appendix A.4 per-beat luma; no beat mean more than 1.6x the mean of the beat before it, except B-05.2 (flashback).

### V1-CIN-04 (MAJOR) Both cut frames are double exposures

- **Where:** f1246 and f1396. Mean luma f1245–1247: 43.6, **97.3**, 111.5. f1395–1397: 102.6, **85.3**, 55.2. `scdet` reports two scene changes at each cut. f1246 is visibly smeared in the cut strip.
- **Cause:** final-tier motion blur with Blender's default centred shutter samples both sides of a cut.
- **Why it matters:** a one-frame ghost at the only two cuts in the film. Under a strict reading it is a "broken frame"; I rate it MAJOR because the frame is a blend, not a corrupt image.
- **Exact fix:** `blender\render_settings.py`, `apply_tier`, after the motion-blur line: `if hasattr(render, "motion_blur_position"): render.motion_blur_position = "START"`. The key before each cut is already CONSTANT, so a shutter that opens at the frame samples one side only. Re-render the beauty pass. If f1246 or f1396 still fails the check, render those two frames with motion blur off through `render_list`.
- **Files:** `blender\render_settings.py`, `tools\verify.py`.
- **Verify:** the "cut frames" step of V1-PIPE-01: `|YAVG(1246) − YAVG(1247)| ≤ 3` and `|YAVG(1396) − YAVG(1397)| ≤ 3`; `scdet=threshold=6` reports exactly two times.

### V1-CIN-05 (MAJOR) The trusted-session payoff is not staged

- **Where:** B-06.6, f1993–2100. Frame f2085.
- **What is wrong:** the session window is 126x101 px. "CLIENT01", "rdp01.1sn0s.lab" and "Remote Desktop Authentication" sit on the laptop and the user for f1997–2100. The storyboard asks for a glide "toward the laptop screen"; the camera stays 9 m away.
- **Why it matters:** this is the moment the first half of the film works toward. C-03, and the film's entertainment value.
- **Exact fix:** `cff\theme\shots.py`, `green-glide`: `dist` 9.0 to 5.0. V1-LEG-04's table removes all three plates in B-06.6. Same camera-audit rule as V1-PKI-04 step 3.
- **Files:** `cff\theme\shots.py`, `tests\test_audit_v1.py`.
- **Verify:** `test_V1_CIN_05_session_window_is_visible`: `SCREEN-RDP` median longer side ≥ 220 px during the B-06.6 hold, and no sign rect intersects it. One frame at 69.0 s.

### V1-DOC-01 (MAJOR) Captions show twice on the Pages demo

- **Where:** `site\index.html` line 34: `<track kind="captions" … default>`. The preview is encoded from the Final MP4, which has the captions burned in.
- **Why it matters:** every visitor sees each caption twice, and the browser's cue overlaps the burned-in bottom band (L-05 on the page).
- **Exact fix:** in `scripts\build_site.py` remove the word `default` from the `<track>` template and set its label to `English captions (same text as on screen)`. Rebuild with `python scripts\build_site.py`.
- **Files:** `scripts\build_site.py`, `site\index.html`, `tests\test_tools.py`.
- **Verify:** `test_V1_DOC_01_caption_track_is_opt_in`: the built page contains `<track` and does not contain ` default`. After the deploy, load the live page once and confirm the same.

### V1-LEG-05 (MINOR) Three tags are too brief for their length

- **Where (plan, full-opacity time):** "Issuing CA 1's own CA request" 1.77 s (6 words, 2.1 s at 0.35 s per word); "Missing intermediate? AIA can fetch it" 1.50 s (6 words); "Name supplied in request — enrollment restricted" 1.90 s (6 words). All pass L-06's 1.5 s.
- **Exact fix:** `cff\stage\labels.py`: `LBL-AIA-1` and `LBL-AIA-2` windows get `end_s=3.0` (they hold 1 s into B-06.4, when only the first check line is up). `LBL-CA2-NOTE` is covered by V1-LEG-03 step 1 (it now starts at 1.1 s). Leave `LBL-REQ-CA1`.
- **Verify:** `python -m tools legibility`; the two AIA tags show at full opacity for at least 2.1 s.

### V1-PKI-06 (MINOR) Self-signed seals are not perceivable

- **Where:** the root seal is 50x14 px in B-05.1 (f1234–1243: a small double circle on the vault face); the self-seal on the pale card in B-02.2 cannot be made out on f318. No sweep of light is evident in f1234–1243.
- **Why it matters:** B-02.2 ("signed only by itself") and B-05.1 rest on the tags "Self-signed" and "1SN0S Root CA" alone. Accurate, but weak.
- **Exact fix:** `cff\stage\objects.py`, `SEAL-ROOT`: `size` from `(0.5, 0.5, 0.06)` to `(1.2, 1.2, 0.06)`. In the card builder for the `self_signed` variant in `blender\actors\artifacts.py`, double the ring radius of the self-seal. The seal must stay static (B-05.1 constraint).
- **Verify:** `SEAL-ROOT` median longer side ≥ 110 px in the B-05.1 hold; existing "root seal never animates" checks stay green.

### V1-CIN-06 (MINOR) White flash at 90.0 s

- **Where:** f2700–2705: mean luma 48.8, 52.5, 58.3, 65.1, 68.6, 58.9. On f2703 a defocused white object fills the bottom of the frame as B-08.3 starts.
- **Exact fix:** `cff\theme\shots.py`, `same-root`: raise `bulge` from 1.8 in steps of 1.0 (maximum 6.8) until Appendix A.4 shows no frame-to-frame luma step above 4.0 in f2695–2710 on an animatic render.
- **Verify:** Appendix A.4, "luma steps": none above 4.0 outside the two cuts. Also look at f641, f746, f1253, f1376 and f2440, which step by 4.1–5.4 today.

### V1-CIN-07 (MINOR) Sealing changes almost nothing

- **Where:** f667–688. The beam is clear and the container flashes white, but the seal is a ring with a 2 cm tube, and the capsule is opaque white, not glass, so its contents cannot be seen.
- **Exact fix:** `blender\actors\network.py`, `seal_ring`: tube radius 0.02 to 0.045. In `cff\stage\choreography.py`, where the ring closes, end on `glow_value(R.REQUEST, palette.GLOW_PEAK)` and settle to `GLOW_ACTIVE` over 12 frames.
- **Verify:** one frame at 23.0 s; C-11 silhouette test stays green.

### V1-COL-01 (MINOR) Role colours wash out at distance

- **Where:** pending channel sampled at f163: `#E3A28E` (salmon) against the token `#D95C00`. Validated channel sampled at f2058: `#90B2B3` (pale mint) against `#26B985`. Trust links on f3001–3022 look white, not gold-to-cyan and gold-to-violet. Close views (f1747, f2085, f2905) read as orange and green.
- **Exact fix:** `cff\theme\palette.py`: `EMISSION_STRENGTH` 2.4 to 1.8 and `TRUST_LINK_EMISSION` 1.8 to 1.2. Run `python -m tools palette`.
- **Verify:** palette check green; after the re-render the two samples above differ from their tokens by ΔE00 ≤ 25 (today about 35–40), measured with the project's own colour functions.

### V1-AUD-01 (MINOR) Audio is dual mono

- **Where:** left minus right has RMS −63 dBFS over the whole film.
- **Exact fix:** in `cff\audio\synth.py`, pan each cue by the world x of the event's `from` actor: `pan = max(-0.6, min(0.6, x / 20.0))`, constant-power gains `cos((pan + 1) * pi / 4)` left and `sin((pan + 1) * pi / 4)` right. Keep the bed centred.
- **Verify:** new test in `tests\test_audio.py`: the L−R difference of the raw mix has RMS above −40 dBFS; `loudness.json` stays within −16 ± 0.5 LUFS and true peak ≤ −1 dBFS.

### V1-AUD-02 (MINOR) Dynamics and one cue timing

- **Where:** `loudness.json` reports `normalization_type: dynamic` and LRA 7.7 in, 4.9 out: the linear pass was refused because the raw mix peaks at −1.0 dBFS and needs +5.4 dB. The `seal` cue for `CA_SIGNS` sits at the event start (33.5 s, and 86.2 s for CA 2), but the press comes down at about 34.0–34.1 s (f1021–1024).
- **Exact fix:** `cff\audio\cues.py`: for events of type `CA_SIGNS`, place the cue at `e.start_s + 0.5`. Lower every value in `CUE_GAIN_DB` by 3.0 and re-run `python -m tools audio`. If `loudness.json` still says `dynamic`, leave it: dynamic loudnorm is acceptable, and a larger change to the balance needs someone who can listen.
- **Verify:** cue-sheet test updated; `loudness.json` within −16 ± 0.5 LUFS. I could not listen: the owner should play 33–35 s once.

### V1-ENC-01 (MINOR) Stream tags

- **Where:** ffprobe: `color_transfer=iec61966-2-1` although `tools\film.py` passes `-color_trc bt709`; `level=50`.
- **Exact fix:** `tools\film.py`: end the filter graph with `format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv[v]`; add `"-refs", "4", "-level:v", "4.1"` after the `-crf` argument for both encodes.
- **Verify:** ffprobe shows `color_transfer=bt709` and `level=41`; add both to the MP4 step of V1-PIPE-01.

### V1-DOC-02 (MINOR) README and Pages wording

- README line 3 and the Pages header say "one continuous shot". The film has two cuts. Use "one continuous camera move, with a single flashback".
- README line 3 says the film is "checked by … a GAN-style adversarial review loop". Use "checked by automated hard checks; an adversarial review loop judged the story spec and the first animatic round only".
- README status and the release link text say "v1.0.0 released". It is now a pre-release. Until v1.1.0 use "v1.0.0 pre-release, under audit (`docs\AUDIT-v1.md`)".
- Pages: "which was itself signed by the 1SN0S Root CA" should read "whose CA certificate was signed offline by the 1SN0S Root CA". "only the public key travels" should read "the request carries only the public key".
- **Files:** `README.md`, `scripts\build_site.py`, `CHANGELOG.md`. **Verify:** `tests\test_spec_docs.py`-style string tests for the three phrases; live page matches `site\index.html`.

### V1-DOC-03 (MINOR) PROJECT-STATE has stale sections

- "What exists now" (139 tests, 11 checks), "Render / verify", "Open for the Stage 1 rounds" ("No audio, encode or MP4 yet") and "Blockers / remaining work" ("Sessions 4–9") describe Session 3–4 and contradict the top of the file.
- **Exact fix:** move everything below "Session 4 part 2 handoff" into `docs\archive\PROJECT-STATE-sessions-3-4.md` and keep a one-line pointer.

## 5. PKI accuracy

No frame I viewed contradicts F-01..F-17, and no private key travels in any frame or strip I viewed. The problems are what the film fails to show clearly.

| Beat | Time s | Verdict | Note |
|---|---|---|---|
| B-01.1 | 0–3 | ACCURATE | User, `CLIENT01`, "Connect to rdp01.1sn0s.lab". |
| B-01.2 | 3–7 | ACCURATE | Pending pulse on a floor channel. |
| B-02.1 | 7–9 | ACCURATE | Listener lights on the server. |
| B-02.2 | 9–12 | ACCURATE | "Self-signed", "Unverified"; channel goes dark. Seal not perceivable (V1-PKI-06). Early CA names (V1-LEG-04). |
| B-02.3 | 12–14 | ACCURATE | Badge arrives with no connection pending. Badge is 96x23 px. |
| B-03.1 | 14–16 | ACCURATE, unclear | Keys are not identified (V1-PKI-03). |
| B-03.2 | 16–18.5 | ACCURATE | Container closes on the key. |
| B-03.3 | 18.5–21 | ACCURATE, unclear | Viewer cannot tell that the travelling key is the public one (V1-PKI-03). |
| B-03.4 | 21–24 | ACCURATE | Beam from the closed container; nothing key-shaped moves (f667–688). |
| B-04.1 | 24–27 | ACCURATE | Capsule waits at the port; separate query pulse to AD and back (f742–763). |
| B-04.2 | 27–29 | ACCURATE | Capsule is 65x22 px. |
| B-04.3 | 29–33 | ACCURATE, unclear | Four results printed before the checks (V1-LEG-03). |
| B-04.4 | 33–36 | ACCURATE | Module stays shut; press stamps the card (f1015–1036). |
| B-04.5 | 36–38 | ACCURATE | Card locks beside the container (f1130). |
| B-05.1 | 38–41.5 | ACCURATE | No cables; root module and press dark. Seal tiny (V1-PKI-06). |
| B-05.2 | 41.5–46.5 | ACCURATE, unclear | Sequence correct (f1275–1385); marker late (V1-PKI-02). |
| B-05.3 | 46.5–50 | ACCURATE | Link is a thin pale line; card 39x26 px. |
| B-06.1 | 50–53 | NOT READABLE | Proof of possession invisible (V1-PKI-04); labels smeared. |
| B-06.2 | 53–57 | **MISLEADING** | Trust store turns gold on docking (V1-PKI-01). |
| B-06.3 | 57–59 | ACCURATE | Nothing is fetched; tags smeared (V1-LEG-01). |
| B-06.4 | 59–64 | **MISLEADING** | "Revocation OK" 5 s before the check (V1-LEG-03). |
| B-06.5 | 64–66.4 | NOT READABLE | Fetches are specks (V1-PKI-05). |
| B-06.6 | 66.4–70 | ACCURATE | Green only after the checks. Payoff weak (V1-CIN-05). |
| B-07.1 | 70–73 | ACCURATE | Twelve plates on screen. |
| B-07.2 | 73–76 | ACCURATE, unclear | Same as B-03.1 (V1-PKI-03). |
| B-07.3 | 76–79.5 | ACCURATE | The clearest frame of the film (f2370). |
| B-07.4 | 79.5–82 | ACCURATE | Capsule is 46x16 px. |
| B-08.1 | 82–85.5 | ACCURATE, unclear | As B-04.3; the note sits under the policy line, not by the Enroll line (fixed by V1-LEG-03 row order). |
| B-08.2 | 85.5–90 | ACCURATE | |
| B-08.3 | 90–93 | ACCURATE | Root module and press dark (f2703). |
| B-09.1 | 93–98 | ACCURATE | Four ticks readable on f2905; proof invisible (V1-PKI-04). |
| B-09.2 | 98–104 | ACCURATE, incomplete | User not in frame (V1-CIN-02). |
| B-09.3 | 104–109 | ACCURATE | Title card, clean fade. |

Gate status: 2 beats MISLEADING, 2 NOT READABLE. The charter gate ("all PKI beats ACCURATE") is not met.

Facts: F-01, F-02, F-05, F-06, F-07, F-08, F-09, F-14, F-15, F-17 are shown correctly. F-03 and F-04 are shown but depend on V1-PKI-03. F-10 and F-13 are not readable. F-11 is undermined by V1-PKI-01. F-12 is undermined by V1-LEG-03. F-16 is docs-only and is covered in the notes.

## 6. What is good, and my scores

- Story order, caption wording, caption timing and placement are right. Captions are sharp and readable in every frame viewed.
- The flashback is the best-staged sequence: the grade, the footprint trail, the cartridge and the root press all read (f1305, f1345).
- B-07.3 (f2370) shows eligibility clearly. The AD lookup (f742–763) shows the query as separate from the request.
- The pipeline is deterministic and re-renders in layers, so most fixes are cheap.
- Estimates on the charter's 10-point scale: PKI 7, legibility 4, cinema 4. After the Section 7 fixes I expect PKI 9, legibility 8, cinema 5–6. The gate is 8 on each.
- Is it entertaining? Not yet. It is a careful, accurate animatic. The camera spends long stretches far from small objects in the dark, the payoffs (green channel, session window, hero) are not staged, and the labels do the storytelling.

## 7. Verdict and fix plan

**Verdict: ship as v1.1.0 after fixes.**

- v1.1.0 is an accuracy, legibility and framing release. Every MAJOR except V1-CIN-03 has a bounded, testable fix above, and most are data edits.
- v1.1.0 will **not** meet the charter's film gate (cinema ≥ 8, no open MAJOR). V1-CIN-03 is the "bigger rework": look development with judgement on rendered frames. Shipping v1.1.0 with V1-CIN-03 open is a lean-mode decision for the owner; the CHANGELOG must list it as a known limit. If the goal is the charter gate rather than a clear explainer, plan a separate v2.0 look pass after v1.1.0.
- Until then v1.0.0 stays a pre-release.

**Cost-aware plan (Claude Pro; no subagents, no GAN rounds, at most 8 images in total).**

Rules for both sessions: read only this file, PROJECT-STATE and the files named in the finding being fixed. Do not re-read the spec documents. Let the new tests do the judging. Render only at the points listed.

- **Session F1 (Sonnet, medium effort): no-judgement fixes, no image needed until the end.**
  1. README status line (V1-DOC-02, third bullet) so the repository matches the pre-release.
  2. V1-LEG-01, V1-CIN-04, V1-PIPE-01, V1-ENC-01.
  3. V1-PKI-01, V1-PKI-02, V1-PKI-03, V1-LEG-04, V1-LEG-05.
  4. V1-DOC-01, V1-DOC-02, V1-DOC-03.
  5. Add `tests\test_audit_v1.py` with Appendix A; `python -m tools verify` green; commit per finding; push; sync-check.
- **Session F2 (Opus, medium effort, or Sonnet at high effort): the iterative fixes.**
  1. Camera first: V1-CIN-01, V1-CIN-02, V1-CIN-05, V1-PKI-04, V1-PKI-05, V1-CIN-06.
  2. Then signs: V1-LEG-03 (the largest change, about 150 lines), V1-LEG-02.
  3. Then the small ones: V1-PKI-06, V1-CIN-07, V1-COL-01, V1-AUD-01, V1-AUD-02, V1-CIN-03 step 1.
  4. `python -m tools render animatic --rebuild` (about 13 minutes, no tokens while it runs). Review 1 contact sheet and 3 strips (docking 54 s, checks 62 s, hero 100 s). Fix what the tests missed.
  5. Delete `renders\final\beauty`, `renders\final\signs` and `renders\final\captions`; `python -m tools render --tier final` in background chunks (about 1 hour of GPU, no tokens); `python -m tools audio`; `python -m tools encode`; `python scripts\build_site.py`.
  6. Review 1 contact sheet, 2 strips (one cut, one sign-heavy move) and the poster: 4 images. `python -m tools verify` green on the final tier and the MP4.
  7. CHANGELOG v1.1.0 with residuals and the open V1-CIN-03; release v1.1.0 as a full release; leave v1.0.0 as a pre-release and mark it superseded in its notes; Pages deploy; sync-check; PROJECT-STATE.
- If only one session is affordable, do F1 plus step 5–7 of F2. That alone removes the smeared labels, the blended cut frames, the misleading trust store, the late flashback marker, the unnamed keys, the label clutter and the doubled captions, at the cost of one final render.

## Appendix A. Measurements to keep as tests (`tests\test_audit_v1.py`)

All use the plan, so they run in pytest without Blender. Common setup:

```python
tl = choreography.build_timeline()
plan = camera.CameraPlan(tl)
beats = beat_of_frame()            # cff.stage.audit
sp = signs.plan_signs()            # label id -> SignPlan(frames: dict[int, SignFrame])
```

### A.1 Projected size of an object or of a beat's focal subject

```python
def longer_side(obj_ids, first, last):
    sides = []
    for f in range(first, last + 1):
        r = caption_layout.objects_rect(tl, plan, tuple(obj_ids), f)   # 1080p px, or None
        if r is not None and r[2] > r[0] and r[3] > r[1]:
            sides.append(max(r[2] - r[0], r[3] - r[1]))
    return statistics.median(sides) if sides else 0.0
```

For a beat: `obj_ids = shots.focal_objects(beat.id, beat.focal)` and `first, last = timing.frame_range(start + 0.5, end - 0.5)`.
An object is "fully inside" a box when `objects_rect` is not None and all four edges are inside the box and none is clamped to 0, 1920 or 1080.

### A.2 Sign jumps, flashes and steady runs

```python
def jumps(limit=96.0, alpha=0.5):
    out = []
    for label_id, sign in sp.items():
        for f in sorted(sign.frames):
            a, b = sign.frames.get(f - 1), sign.frames[f]
            if a and min(a.alpha, b.alpha) >= alpha and math.hypot(b.rect[0] - a.rect[0], b.rect[1] - a.rect[1]) > limit:
                out.append((f, label_id))
    return out            # v1.0.0: 51 distinct frames. Target: []

def _steady_runs(by_frame):   # replaces _runs(sorted(by_frame)) in plan_signs
    out, prev = [], None
    for f in sorted(by_frame):
        joined = prev is not None and f == prev + 1 and math.hypot(
            by_frame[f].rect[0] - by_frame[prev].rect[0], by_frame[f].rect[1] - by_frame[prev].rect[1]) <= ty.SIGN_JUMP_PX
        if joined:
            out[-1] = (out[-1][0], f)
        else:
            out.append((f, f))
        prev = f
    return out
```

A "flash" is a maximal run of consecutive frames in `sign.frames` shorter than 24 frames. v1.0.0 has 29 runs under 30 frames.

### A.3 One fixed place for a check list

```python
STEP, PAD = 24, 12.0

def fixed_block(ids):                      # ids in row order; returns (x0, y0, row_height)
    sizes = [ty.sign_plate_size_px(labels.BY_ID[i].text) for i in ids]   # add the tick width for check lines
    w, row_h = max(s[0] for s in sizes), max(s[1] for s in sizes)
    h = len(ids) * row_h + (len(ids) - 1) * ty.SIGN_GAP_PX
    first = min(labels.window_frames(labels.BY_ID[i].window)[0] for i in ids)
    last = max(labels.window_frames(labels.BY_ID[i].window)[1] for i in ids) + 8
    frames = [f for f in range(first, last + 1) if f in beats]
    m = ty.SIGN_SAFE_MARGIN_PX
    sx0, sy0, sx1, sy1 = ty.TITLE_SAFE_PX[0] + m, ty.TITLE_SAFE_PX[1] + m, ty.TITLE_SAFE_PX[2] - m, ty.TITLE_SAFE_PX[3] - m
    forbidden, ax, ay = [], 0.0, 0.0
    for f in frames:
        rects = [(r[0] - PAD, r[1] - PAD, r[2] + PAD, r[3] + PAD) for r in _protected_rects(tl, plan, beats[f], f)]
        c = ty.CAPTION_BAND_CLEARANCE_PX
        rects += [(0.0, r[1] - c, float(ty.FRAME_W_PX), r[3] + c) for r in caption_rects(f)]
        forbidden.append(rects)
        px, py, _ = camera.project(plan.state(f), anchor(tl, labels.BY_ID[ids[0]], f))
        ax += px * ty.FRAME_W_PX / len(frames); ay += py * ty.FRAME_H_PX / len(frames)
    best = None                            # (blocked frames, distance to the mean tick anchor, y0, x0)
    x = sx0
    while x + w <= sx1:
        y = sy0
        while y + h <= sy1:
            block = (x, y, x + w, y + h)
            blocked = sum(any(_intersects(block, r) for r in rects) for rects in forbidden)
            key = (blocked, math.hypot(x + w / 2 - ax, y + h / 2 - ay), y, x)
            best = key if best is None or key < best else best
            y += STEP
        x += STEP
    return best[3], best[2], row_h
```

Row `i` of the list is left-aligned at `x = x0`, centre `y = y0 + row_h / 2 + i * (row_h + ty.SIGN_GAP_PX)`. Rows keep their slot even while earlier rows are not yet shown. The search is deterministic. With the v1.0.0 camera it returns 0 blocked frames for the CA 1 and web lists, 45 for CA 2 and 15 for RDP; re-run it after the camera fixes and record the blocked-frame counts in the ledger.

### A.4 Signal checks on rendered frames or on the MP4 (FFmpeg)

- Per-frame mean luma: `ffmpeg -i <mp4> -an -vf signalstats,metadata=print:file=stats.txt -f null -`, then read `lavfi.signalstats.YAVG` per frame (8-bit video range: black 16, white 235).
- Cut frames: see V1-CIN-04.
- Luma steps: `|YAVG(n) − YAVG(n−1)| > 4.0` outside f1246, f1247, f1396, f1397. v1.0.0: f641, f746, f1253, f1376, f2440, f2701, f2702, f2704, f2705.
- Per-beat mean luma. v1.0.0: film 55.7; B-04.3 105.3; B-04.4 90.1; B-05.2 98.0; B-08.1 83.8; B-09.2 40.0; all others 44–64 except B-09.3 (fade).
- Cuts: `-vf scdet=threshold=6` must report scene changes only at 41.5 s and 46.5 s (v1.0.0 also reports 41.533 s and 46.533 s).
- Loudness: `-af ebur128=peak=true`. Stereo width: `-af "pan=mono|c0=c0-c1,astats"`.
