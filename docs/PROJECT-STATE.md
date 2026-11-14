# PROJECT STATE

Updated: 2026-11-14 (Session L1, `claude-sonnet-5-5`, no subagents, 5 of 6 images)

## SESSION L1 DONE (2026-11-14, Sonnet 5.5, High, no subagents, 5 of 6 images) — no tag, no release
- Items A, C, E, B (second change), D, F done, one commit each, plus `tools look-test` and `tools\luma.py`. Gate passed on attempt 2 of 3. Full final render, audio, encode, site build done. **Final MP4 SHA-256 `84097e10311daafa6b9d6b72bb94a31380357a82aee3006cf56536ad25093f44`**, 70.3 MB, grain 3, `dirty: false`. The Final MP4 is gitignored (release asset); Preview, poster, contact sheet and site are committed.
- `python -m tools verify` VERIFY GREEN, no waiver (`MP4_PENDING_RERENDER = False`): pytest 200, 15 in-Blender checks, both tiers 3270/3270, true peak −1.2 dBFS.
- Measured: B-09.2 mean YAVG 51.3 (was 38.4); film mean 57.7; f2431 step 0.3; f2695–2712 max 3.7. Still over 4.0: f746 8.0, f1376 10.6 (flashback), f1157 4.0, f1534/1535 4.4/6.7, f2454/2455 5.6/5.1. Per-beat table: `docs\GAN-LEDGER.md` "Session L1".
- Shortfalls for L2 to rule on: `RESIDUAL_PX` has 10 entries (plan: ≤ 6); F3-PKI-01 label removed (36 of 45 frames), finding open; soft haze glow near the rim light; flashback steps.
- **Housekeeping (2026-11-14, Sonnet 5.5):** v1.1.0 promoted to public latest release (not pre-release). Pages `site\poster.png` and `site\preview.mp4` restored to the v1.1.0 assets (the L1 commit had put the unaudited v1.2 render live); README, CHANGELOG, Pages text say v1.1.0 is current. Release rule added to CLAUDE.md. The v1.2 render stays in git history (1a20816) and is NOT on Pages until it passes audit.
- **Next session: L2 (Fable 5.2, High): re-audit the Final MP4 (SHA-256 `84097e10…3f44`) and release v1.2.0 (Plan Section 6).** Do not re-render unless the audit demands it. On a pass: publish v1.2.0 as latest, rebuild site from v1.2 assets (`git checkout 1a20816 -- site/poster.png site/preview.mp4`), update README, CHANGELOG, Pages, verify the live page.

## L2 pre-flight (2026-11-14, Sonnet 5.5, no code changes)
- `tools verify`: **FAIL** (1 step). All stages pass except pytest: 1 failed, 199 passed. Failing test: `tests/test_audit_v1.py::test_V1_DOC_02_wording_matches_the_film_and_its_status`. It still asserts the README says "v1.1.0 pre-release" and never "released". v1.1.0 is now the public latest release, so the test is stale. Fix the test (not the README) before L2 gates on verify.
- Final MP4 SHA-256 `84097e10311daafa6b9d6b72bb94a31380357a82aee3006cf56536ad25093f44`: this is the **L1 render**, not v1.1.0 (`2b56cee7…`).
- `site\poster.png` (`f9d07ca7…`) and `site\preview.mp4` (`7c66720a…`) match the v1.1.0 release assets Poster and Preview.

## Session F3, third run DONE (2026-11-14) — GATE PASSED, v1.1.0 released as a PRE-RELEASE
- Gate: Final MP4 SHA-256 `2b56cee7…f78e` confirmed. `python -m tools verify` VERIFY GREEN twice (before and after the doc changes): pytest 189, 14 in-Blender checks, both tiers 3270/3270, final MP4 on spec, cut-frame steps 0.4 / 0.0. ffprobe: H.264 High 4.1, bt709, 3270 frames, 109.000 s; exactly two cuts.
- Every FIXED finding passes on the rendered film (15 MAJOR, 10 MINOR); 56 frames viewed in 8 images. Per-item table: `docs\AUDIT-v1.md` "F3 targeted re-audit, third run". 33 of 33 PKI beats ACCURATE. Estimated scores: PKI 9, legibility 8, cinema 5.
- Known limitations recorded (README, CHANGELOG, ledger "Session F3"): V1-CIN-03 (open MAJOR), the F2 residuals, and four new MINORs: F3-LEG-01 (flashback marker fades over f1396–1398), F3-AUD-01 (AAC true peak −0.6 dBFS), F3-PIPE-02 (metadata commit one behind), F3-PKI-01 (handshake proof unlabelled).
- Release: tag `v1.1.0` on `a036067`; https://github.com/SimSI2027/Certificate-Flow-Film/releases/tag/v1.1.0 (`isPrerelease=true`), 7 assets. All 7 downloaded back with matching SHA-256. v1.0.0 notes marked "superseded".
- Pages: run 43578886004 succeeded; live page, preview, poster and captions are byte-identical to `site\`.
- Part 2: `docs\LOOK-PLAN-v1.2.md` written. Its values come from a scratch prototype (final-tier stills, no project file changed): hero beat mean luma 37.8 → 53.1. Motion was not tested; the plan's stills-and-strips gate covers it.

## Session F2 DONE (2026-11-13/14, Opus 5.5 High) — no tag, no release
- Code: 242c363 (camera), 107159a (signs), 60a60b3 (small fixes), 13a7cde (V1-CIN-06 bulge, loudnorm TP), close-out commit (V1-CIN-02 step 4 glow; `MP4_PENDING_RERENDER = False`). Per-finding status: `docs\AUDIT-v1.md` "F2 status" and "F2 final render"; residuals: `docs\GAN-LEDGER.md` "Session F2".
- Final tier fully re-rendered (3270 beauty, 2773 sign, 1933 caption frames), audio -15.9 LUFS / TP -1.2 dBFS, encoded, site rebuilt. **Final MP4 SHA-256 `2b56cee7b030528d6bf21cf864c74ced521cbc9c18ba170e7229704fd9d7f78e`** (was `5470c46c…f193a`). ffprobe: level 41, bt709 primaries/transfer/space.
- `python -m tools verify`: VERIFY GREEN, no PENDING line (pytest 189, 14 in-Blender checks, both tiers 3270/3270, final MP4 matches spec, cut-frame luma steps 0.4 / 0.0).
- Reviewed: final contact sheet, cut strip (f1245-1247, f1395-1397: clean), sign strip (f1625-1645, f1955-1975: sharp, fixed check list), poster.
- Known residuals for F3 to judge: B-09.2 mean YAVG 38.4 (target 50; more light is V1-CIN-03), luma steps f2709 7.7 / f2431 6.4 / f746 5.6 / f1376 4.6 on the MP4, focal sizes in 10 beats (V1-CIN-01), hero topology whole only from ~102 s.
- The Final MP4 is gitignored (release asset); Preview, poster, contact sheet, captions and site are committed.

## (superseded) F2 was the next session here; it is now done.
- **F3 second run (2026-11-13 22:15): GATE FAILED AGAIN, same cause.** F2 has still not run. The five local outputs have the same SHA-256 as the v1.0.0 release assets (Final `5470c46c…f193a`), `MP4_PENDING_RERENDER` is still True, `CROSSING_LIMIT` is still 0.045. Verify is GREEN only through that waiver (pytest 170, 14 in-Blender checks, final tier 3270/3270; MP4 level 50, transfer sRGB; cut-frame steps 14.3 and 30.1). Per-item results are in `docs\AUDIT-v1.md` under "F3 targeted re-audit, second run": 7 fixed MAJORs FAIL in the film, V1-DOC-01 PASSES.
- No tag, release, README, CHANGELOG or Pages change. v1.0.0 stays a pre-release. The only source change in this session: the F2 prompt was added to `docs\SESSION-PROMPTS.md` (it did not exist, which is why F3 was run twice).
- **F2 is finished when all four are true:** the Final MP4 is newer than the last source commit; its SHA-256 is not `5470c46c…f193a`; `tools\verify.py` has `MP4_PENDING_RERENDER = False`; `python -m tools verify` prints no PENDING line. Only then run F3.
- Render commands take `--tier`: `python -m tools render --tier animatic --rebuild`, `python -m tools render --tier final --rebuild`.

## Session F3, first run (2026-11-13, Opus 5.5) — GATE FAILED, no release. NEXT: session F2 (Opus 5.5, High), then F3 again
- F3 found that F2 never ran: the Final MP4 and the final passes predate the F1 fixes, so the shipped film is still v1.0.0. Per-item results and the exact fix list are in `docs\AUDIT-v1.md` under "F3 targeted re-audit". 7 fixed MAJORs FAIL in the film (LEG-01, CIN-04, PIPE-01 waived, PKI-01/02/03, LEG-04); only V1-DOC-01 PASSES (no default track on the live page). Verify is GREEN only because of `MP4_PENDING_RERENDER = True`.
- No tag, release, README, CHANGELOG or Pages change was made. v1.0.0 stays a pre-release.
- **Next action:** run session F2 exactly as described below and in AUDIT-v1 Section 7. After that, run F3 again (re-audit, then release v1.1.0 as a pre-release with Final, Preview, poster, contact sheet and captions.vtt; then check the SHA-256 round-trip).

## Session F1 DONE (2026-11-13, Sonnet 5.5 medium) — F2 still pending
- F1 fixes are in commits 77b8119, 50fe77e, d7544fc; per-finding status is in `docs\AUDIT-v1.md` ("F1 status"). `python -m tools verify`: VERIFY GREEN (pytest 170, 14 in-Blender checks, final tier 3270/3270). No render was done; the Final MP4 on disk is still the v1.0.0 file; release and tags untouched.
- **F2 must:** do everything marked NEEDS-F2 or not yet touched (V1-LEG-05 and LEG-02/03, PKI-04/05/06, CIN-01/02/05/06/07, COL-01, AUD-01/02, CIN-03 step 1, the LEG-04 residual); lower `CROSSING_LIMIT` in `tests\test_gan_findings_stage1.py` to 0.02; after the single final re-render + encode set `tools.verify.MP4_PENDING_RERENDER = False` (then `verify` must be green with the real MP4 checks); delete `renders\final\signs` and `renders\final\beauty` (and captions if needed) before rendering; rebuild the site; confirm the live Pages page has no default caption track.
- Older stale material (Sessions 3-4) is in `docs\archive\PROJECT-STATE-sessions-3-4.md`.

## v1 AUDIT — v1.0.0 is a provisional pre-release
- **v1.0.0 is a provisional pre-release pending the v1 audit.** `gh release edit v1.0.0 --prerelease` was run on 2026-11-13; GitHub reports `isPrerelease=true`. README, CHANGELOG and the Pages page still say "released" (audit finding V1-DOC-02; this session was allowed to change only this file and the audit file).
- Audit report: `docs\AUDIT-v1.md`. Result: 0 BLOCKER, 16 MAJOR, 10 MINOR. Verdict: **ship as v1.1.0 after fixes**; the grey-box look (V1-CIN-03) stays open and is the "bigger rework" for a later v2.0.
- Re-verified in the audit: `python -m tools verify` VERIFY GREEN (pytest 158, 14 in-Blender checks, 3270/3270 **animatic** frames; the final tier is not checked by verify, finding V1-PIPE-01); Final MP4 is H.264/AAC, 1920x1080, 30 FPS, 3270 frames, 109.000 s, −16.1 LUFS; spec hash unchanged; live Pages page identical to `site\index.html`.
- Top findings: signs motion-blurred in the final tier (one-line bug in `apply_tier`), check lists printed before the checks, sign jumps, signs over the focal subject on 34.8% of frames, trust store turns gold on docking, late flashback marker, unnamed keys, tiny focal subjects, hero shot without the user, blended cut frames, doubled captions on the Pages page.
- **Next session (F1 in `docs\AUDIT-v1.md` Section 7):** Sonnet, medium effort, no subagents. Read only `docs\AUDIT-v1.md`, this file and the files named in each finding. Do, in order: README status line; V1-LEG-01, V1-CIN-04, V1-PIPE-01, V1-ENC-01; V1-PKI-01, V1-PKI-02, V1-PKI-03, V1-LEG-04, V1-LEG-05; V1-DOC-01..03; add `tests\test_audit_v1.py` from Appendix A; verify green; commit per finding; push; sync-check. Session F2 (iterative camera and sign fixes, one animatic render, one final render, release v1.1.0) follows.
- No source, test, render or site file was changed in the audit session. `tools verify` rebuilt `renders\film.blend` (gitignored).

## LEAN FINISH MODE (history; overrode the charter governance)
- The user switched to lean finish: no subagents, no GAN rounds, `python -m tools verify` is the quality gate, at most 2 contact-sheet reviews, one final-quality render, a simple Pages page and v1.0.0 release.
- Review agents archived to `docs\archive\agents\` (not auto-invoked). The R2 discriminator replies in `qa\rounds\stage1-R2` are partial/unjudged and are not used.
- Step 1 DONE: the pending R2 fixes (signs parallel to the image plane, blended plates in a PLATES/TEXT view-layer split, sign clearance of capsules/cards/private keys, trust links grow from nothing) were completed; build bug fixed (`view_layer.update()`), tag crossing falls back to focal-only. VERIFY GREEN (pytest 155, 14 in-Blender checks, 3270/3270 animatic frames).
- **Remaining, in order:** 2 final look (bloom/grain/volumetrics via the `final` tier), 3 render final 1920x1080 + captions + audio (`cff\audio` is empty: synth, cue sheet, mix needed), encode, 4 one contact sheet review, 5 outputs, 6 Pages + v1.0.0.
- Step 2 DONE: contact-sheet review 1 of 2 at the `final` tier (`scripts\render_sheet.py final` -> `output\final\contact-sheet.png`): lit, captions/signs in place, no blank frames; accepted.
- Audio DONE: `cff\audio\{cues,synth}.py` (88 cues from the story events, stdlib synth, seeds 5101-5103) + `python -m tools audio` -> `output\audio\mix.wav` (-16.0 LUFS, true peak -3.7 dBFS; `loudness.json`). Tests in `tests\test_audio.py`.
- Encode tooling DONE: `python -m tools encode` (Final MP4, 720p Preview, poster, contact sheet, `render-metadata.json`); site builder `scripts\build_site.py`; Pages workflow `.github\workflows\pages.yml`.
- Final render DONE (3270 beauty, 2788 sign, 1933 caption frames; 0 blank); encoded (Final 59 MB, Preview 11 MB, 109 s, 1080p30 H.264/AAC); contact-sheet review 2 of 2 accepted. Pages live: https://simsi2027.github.io/Certificate-Flow-Film/ (verified 200 for page, preview, poster, captions). Release v1.0.0 created with the Final MP4.
- **Next action:** superseded by the v1 AUDIT section above (the project is not complete; v1.0.0 is a pre-release).


## Git
- Branch `main`, tracking `origin/main`. Session 3 commits are listed in the approvals record; the close-out sync result is in the Session 3 report.
- Line endings are pinned to LF (`.gitattributes`) so frozen hashes are checkout-independent.

## URLs
- Repository (public): https://github.com/SimSI2027/Certificate-Flow-Film
- Pages demo: https://simsi2027.github.io/Certificate-Flow-Film/. Latest pre-release: https://github.com/SimSI2027/Certificate-Flow-Film/releases/tag/v1.1.0 (v1.0.0 superseded)
- Related (verified in Session 1): https://github.com/SimSI2027/Certificate-Flow-Lab (Pages: https://simsi2027.github.io/Certificate-Flow-Lab/). Approach A: HTTP 404, not linked.

## Toolchain (details in `docs\TOOLCHAIN.md`; commands in `docs\PIPELINE.md`)
- Blender 5.2.3 LTS with EEVEE (`BLENDER_EEVEE`); Cycles/OptiX is the fallback. Python 3.12.10 `.venv` (pytest 9.2.0, ruff 0.17.4, mypy 2.4.1). FFmpeg 9.0.2. gh 2.103.3 as SimSI2027.
- `pyproject.toml`: ruff line length is **160** (raised from 120 in Session 3), with per-file E501 and N806 ignores for stage data tables, theme, tools and Blender builders.

## Names in use
- Fixed: `1SN0S.LAB`, `1SN0S`, `1sn0s.lab`, `RDPAuth`, `WebServer-TLS`.
- Fallbacks in use: DC `DC01`, client `CLIENT01`, RDP server `RDP01` (`rdp01.1sn0s.lab`), web server `WEB01`, site `portal.1sn0s.lab`, Root CA `1SN0S Root CA`, Issuing CAs `1SN0S Issuing CA 1` / `1SN0S Issuing CA 2`, PKI HTTP host `pki.1sn0s.lab`.

