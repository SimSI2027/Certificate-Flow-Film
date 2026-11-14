# Chief of Staff approvals

## Phase 1 — Environment (Session 1)
- **Scope:** Charter 5.1–5.3: inspect and record tools, install and pin Blender 5.2 LTS, headless GPU probe with engine decision, `.venv` and `requirements-dev.txt`, `docs\TOOLCHAIN.md`, `config\toolchain.local.json`.
- **Acceptance criteria:** every tool verified with versions recorded; probe frame not blank; decision recorded.
- **Review performed:** ran each tool's version command; checked `winget show` before installing; opened the EEVEE probe PNG and inspected it (lit blue cube, sphere, floor; not blank); compared numeric metrics from `scripts\gpu_probe.py`.
- **Problems found and corrections:** (1) A draft TOOLCHAIN note claimed two FFmpeg installs. Re-checking with `Get-Command ffmpeg -All` showed one, so the note was corrected. (2) No global git identity existed, so a repo-local identity was set.
- **Tests run (real results):** `blender --version` gives 5.2.3 LTS. EEVEE probe: engine enum `["BLENDER_EEVEE"]`, mean 0.663, std 0.214, 2,670 unique levels, blank=false, exit 0. Cycles probe: OPTIX on RTX 4090, std 0.211, 6,159 unique levels, blank=false. `pytest --version` 9.2.0, `ruff --version` 0.17.4, `mypy --version` 2.4.1. ffmpeg encoders `libx264` and `aac` present. No pytest suite exists yet (nothing to test).
- **Ledger rounds:** n/a (no GAN round yet).
- **Commit / sync:** see Phase 2.
- **Decision: APPROVED** — 2026-11-07T00:55Z. Engine decision: EEVEE primary, Cycles/OptiX verified fallback.

## Phase 2 — Repository (Session 1)
- **Scope:** Charter 5.4 and Session 1 items: `git init` on main, `.gitignore`, GPL-3.0-or-later / CC BY 4.0 split, bundled OFL font, secret scan, public repo, topics, push, sync; charter moved to `docs\`; three discriminator agents; folder skeleton; `CLAUDE.md`, `PROJECT-STATE.md`, this record.
- **Acceptance criteria:** repo public; origin correct; local HEAD equals origin/main; agent files exist exactly as specified.
- **Review performed:** compared the three agent files with the Charter 2.3 blocks by exact string match (all three match); confirmed `git ls-files` contains no gitignored paths (`toolchain.local.json`, `.venv`, `renders`); verified the font and licence texts come from official upstream sources (Inter v4.1 release zip from `rsms/inter`; GPL-3.0 and CC BY 4.0 texts from GitHub's licence API); confirmed `CLAUDE.md` is under 120 lines and covers each Section 13 item.
- **Problems found and corrections:** none blocking. The `python -m tools sync-check` command does not exist yet, so the sync check was done manually with git. `/agents` listing can only be confirmed in a new session.
- **Tests run (real results):** secret scan (regex for tokens, private-key headers, `password`/`secret`/`api_key` assignments) over all staged text files returned no matches. `gh repo view`: visibility PUBLIC, default branch main, 12 required topics set, description set. `git remote -v`: origin is `https://github.com/SimSI2027/Certificate-Flow-Film.git`. Tracking: `main...origin/main`.
- **Ledger rounds:** n/a.
- **Commit / sync:** bootstrap commit `a1cb1d176b148751e58dc56832dc3aef7238ca91`; local HEAD equals `git ls-remote origin refs/heads/main` at that commit. The final docs/state commit and its sync result are given in the Session 1 report and verified after push.
- **Decision: APPROVED** — 2026-11-07T00:55Z.

## Phase 3 — Stage 0 spec freeze (Session 2)
- **Scope:** Charter 4 Phase 3 and the Session 2 prompt:
  - the `.lab` IANA check and its docs note
  - `docs\REFERENCE-SPEC.md` (AR-01..07, F-01..F-17, B-01.1..B-09.3, C-01..C-11 and L-01..L-08 with measurable thresholds)
  - `GLOSSARY.md`, `PKI-TECHNICAL-NOTES.md`, `STORYBOARD.md` and `GAN-FRAMEWORK.md`
  - pure-Python `cff\config\names.py` and `cff\story\{model,timing,captions,spec_ids,export}.py`
  - the pytest suite; ruff and mypy clean
  - the generated `TRACEABILITY.md` with its missing-ID test
  - the stage0 packet, `pki-discriminator` rounds and the spec freeze
- **Acceptance criteria:**
  - 0 BLOCKER/MAJOR in the latest round, every beat ACCURATE, MINORs fixed
  - hard tests green
  - spec hash recorded in the ledger
  - no `bpy` in `cff`
  - no placeholder text in any output
- **Review performed:**
  - **`.lab` check, verified from primary sources:**
    - the IANA TLD list (v2026110600) does not list LAB
    - `root.zone` (SOA 2026110602) has no `lab.` delegation
    - the IANA root-db page returns 404
    - the ICANN `.internal` resolution 2024.07.29.06 was fetched and confirmed
  - **Discriminator rounds:** three rounds of fresh `pki-discriminator` instances (opus), each pointed only at an immutable packet. Every finding was triaged against the spec, and nothing was rejected.
  - **Verbatim saving:** the first R1 save paraphrased the agent's text. The Chief of Staff caught this and rewrote the file verbatim from the hand-back, because the background transcript file was empty.
- **Problems found and corrections:**
  - **R1:** 2 MAJOR and 6 MINOR.
    - One TLS handshake was shown switching certificates. Fixed: the unverified S2 attempt now closes, and S6 starts a new attempt.
    - The RDP request had no end of life, so the CA request was ambiguous. Fixed: requests are consumed at their destination, and the CA request carries a labelled CA=true band.
  - **R2:** 9 MINOR: intermediate copies, causal ordering, proof verification, request/certificate wording, the CA 2 certificate reveal, Kerberos scope, browser revocation caveat, OCSP host, passive AIA.
  - **R3:** 3 MINOR: distinct intermediate-copy objects and two wording fixes.
  - **Own catches:**
    - the web handshake proof was sent before its signature finished (caught by test)
    - CRLF conversion would have broken the frozen hash; fixed with `.gitattributes` (LF)
    - the C-02 camera threshold was set at 4% of focus distance per frame before the freeze, so camera follows between vaults are feasible
    - the first attempt to write this record failed (non-unique edit anchor) and was re-applied in a follow-up commit
  - **Charter deviation, recorded in the ledger:** B-05.1's seal is revealed statically rather than animated closing (PKI accuracy).
- **Tests run (real results):**
  - `pytest`: 93 passed
  - `ruff check`: all checks passed
  - `mypy --strict` (`cff`, `tools`, `tests`): no issues
  - `python -m tools traceability --check`: current, every ID covered
  - Mutation sanity: both R1 MAJOR tests fail on the R1 model, and `test_missing_coverage_is_detected` proves the traceability check catches missing IDs.
  - `python -m tools spec-hash` = `7cf45afa…6d23`.
- **Ledger rounds:**
  - stage0-R1: 2 MAJOR, 6 MINOR; NOT PASSED
  - stage0-R2: 0/0, 9 MINOR
  - stage0-R3: 0/0, 3 MINOR, 33/33 ACCURATE; PASSED

  **Frozen REFERENCE-SPEC SHA-256:** `7cf45afa01572b7e9d30a6fb376807fb10a4f6a693af41ffed1d96bce2686d23` (`docs\GAN-LEDGER.md`, "Stage 0 freeze").
- **Commit / sync:**
  - freeze commit `fc9edad75f6e3f339b55f1204657634b85de9caf`: pushed, `sync-check` SYNC OK
  - state commit `559ecfdd97dfd6a4307ab4cd585cc83de5f955e2`: pushed, SYNC OK

  This record follows in one more commit, which is sync-checked at close-out.
- **Decision: APPROVED** — 2026-11-06. This was not a first attempt: Stage 0 took 3 rounds.

## Phase 4 build — Pipeline + animatic build (Session 3)
- **Scope:** build part only (no GAN rounds): `tools` commands (env, verify, build, render, captions, packet, contact, palette, motion, sync-check), `blender\build_scene.py` with grey-box actors, world, lighting, camera rig and the separate caption scene, `blender\checks\scene_checks.py`, full 960x540 animatic render in resumable chunks, `packet stage1`, sample frame inspection.
- **Acceptance criteria:** `python -m tools verify` fully green; the full animatic rendered; the packet builds; sample frames inspected.
- **Review performed:**
  - Pre-flight: Phase 3 APPROVED, spec hash `7cf45afa…6d23` matches, HEAD equalled origin/main, spec untouched.
  - Every Blender API checked by running it on 5.2.3: slotted actions and channelbags, `compositing_node_group`, material nodes without `use_nodes`, enum detection of `BLENDER_EEVEE`, bundled fonts.
  - Camera plan audited against C-02 (every frame, exactly 2 cuts) and C-03 (framing and focus per beat); the audit found real failures (411 frames over C-02 at first) that were fixed by smoothing and per-shot tuning, not by loosening thresholds.
  - In-Blender checks found real defects, fixed in the model not the check: the flashback walkway ended inside the root plinth's bounds; the root key rose through the floor; event timings left 12 must-read labels on screen under 1.5 s; the revocation amber was 4.2 dE00 from pending under deuteranopia.
  - Opened the contact sheet of all 33 beats, both sides of the S5 cut, the B-04.4 strip and the B-09.2 hero frame: not blank, flashback desaturated at the cut, captions and labels in place.
- **Problems found and corrections:**
  - C-03 is still below threshold on B-05.1 and B-09.2: kept as an advisory ratchet (`C03_OPEN_BEATS`; a test fails on regressions and on stale entries), handed to the Stage 1 rounds.
  - Several measurements needed an interpretation (pops, jerk, "on screen"); recorded in PROJECT-STATE.
  - First blank-frame check failed on a path escape and then flagged the intended black ending; both fixed.
  - Process slips against the edit rules: a heredoc retime (reviewed), one heredoc removing a constant, and one no-op heredoc call; all source changes since used Edit/Write.
  - Not yet implemented as hard checks (listed in PROJECT-STATE): C-04, C-07, C-10 material audit, C-11 IoU, sampled L-02 contrast, L-05 overlap, L-06 occlusion/CoC.
- **Tests run (real results):**
  - `python -m tools verify`: ruff all checks passed; mypy --strict no issues (50 files); pytest 139 passed; traceability current; palette 87 pairs 0 failing (worst 15.8 dE00 across 8 key roles; revocation vs pending at least 11.7); planned-film audits 0 hard findings, 3 advisory; in-Blender scene checks 11 of 11 passed (30,217 keys, 1,188 F-curves; cuts at frames 1246 and 1396; max camera step 0.0398 of focus distance, 1.35 deg, 0.33 mm; 46 must-read labels legible); rendered frames 3270 of 3270 present, 0 blank.
  - Render: 3270 beauty frames and 1990 caption frames at 960x540; `packet stage1 --round 0` built `qa\rounds\stage1-R0` (103 frames, 33 strips, manifest with SHA-256 for 145 files, regressions.json, schema.json). R0 is a build check, not a GAN round.
- **Ledger rounds:** none (the Stage 1 gate is Session 4).
- **Commit / sync:** commits c040282, b5d507c, be0f4c1, 91ec326, bb483a2 plus the close-out commit; the sync result is in the Session 3 report.
- **Decision: APPROVED** (Phase 4 build only; the Stage 1 gate is not approved and the clean-round counter is 0) — 2026-11-07. First attempt at this phase, accepted because every gate item is evidenced above.

## Phase 4 gate — Calibration + animatic GAN rounds (Session 4, part 1)

- **Scope:** Charter 2.8 calibration (`blender\calibration.py`, `python -m tools calibrate`, test that normal builds never enable a fault), then Stage 1 GAN rounds per Charter 2.4 until the Stage 1 gate (Charter 2.7).
- **Acceptance criteria:** every discriminator flags its relevant faults as BLOCKER; the hard discriminators fail on private_key_leak, root_issues_leaf and caption_clip; then a Stage 1 round with 0 BLOCKER, 0 MAJOR, scores >= 8, every PKI beat ACCURATE and hard discriminators green.
- **Review performed:** four faults built and checked; blind packets stage1-K1..K6 judged by fresh discriminators; every reply read, saved verbatim and triaged against the frozen spec (details in `docs\GAN-LEDGER.md`, "Stage 1 — Discriminator calibration"). Packet frames were inspected by the Chief of Staff before judging (this caught the unevaluated caption layer in the first K packets).
- **Problems found and corrections:** the hard checks missed root_issues_leaf and caption_clip (vacuous title-safe check, root isolation limited to vault and plinth). Both were strengthened, and now all three are caught. The packet still renderer dropped the caption layer, which is fixed. pki-discriminator missed private_key_leak three times (K1, K5, K6); its definition and the packet judging protocol were strengthened twice, and that is still not enough.
- **Tests run (real results):** `python -m tools verify` VERIFY GREEN on the normal film (ruff clean; mypy --strict clean, 51 files; pytest 141 passed; traceability current; palette 87 pairs 0 failing; planned-film audits 0 hard; in-Blender 12 of 12 checks passed; 3270 of 3270 frames, 0 blank). `tools calibrate all`: private_key_leak, root_issues_leaf and caption_clip CAUGHT by the hard checks; flowchart judged by the cinema discriminator. Spec hash `7cf45afa…6d23` unchanged.
- **Ledger round references:** calibration packets stage1-K1..K6. No Stage 1 GAN round was judged (stage1-R1 was built, then withdrawn unjudged before the README protocol change).
- **Commit / sync:** cf3cf8a, fe33f99, c42b786, cf3ed52, 1cd847f plus the close-out commit; sync result in the Session 4 report.
- **Decision: REJECTED** (gate not reached; work carried over) — 2026-11-07. Calibration has not passed (pki-discriminator has not caught private_key_leak) and no Stage 1 round has run. Next action: add the measured object-locator evidence to packets, re-calibrate private_key_leak, then run stage1-R1.

## v1.1.0 release gate — targeted re-audit of the re-rendered film (Session F3, third run, 2026-11-14)

Lean mode (no discriminator round). Sessions F1 and F2 and the first two F3 runs are recorded in `docs\AUDIT-v1.md` and `docs\PROJECT-STATE.md`, not in this file.

- **Scope:** re-check every v1 audit finding marked FIXED on the Final MP4 of the F2 render; if no fixed BLOCKER or MAJOR fails, release v1.1.0 as a pre-release.
- **Acceptance criteria:** Final MP4 SHA-256 `2b56cee7…f78e`; `python -m tools verify` green with no waiver; each FIXED item passes at its timestamp; no regression on a full-film contact sheet; assets round-trip with equal SHA-256; Pages current.
- **Review performed:** 8 images cut from the Final MP4 (56 distinct frames): a 33-tile contact sheet, six 2x2 check sheets, one full-resolution crop sheet of the handshake proofs. FFmpeg `signalstats`, `scdet`, `freezedetect`, `blackdetect`, `ebur128`, `astats`; plan numbers from `cff.stage.signs` and `cff.stage.camera`. Two attempts at this gate had been rejected before (F2 had not run).
- **Problems found and corrections:** four new MINORs (F3-LEG-01, F3-AUD-01, F3-PIPE-02, F3-PKI-01), recorded with exact fixes and carried into `docs\LOOK-PLAN-v1.2.md` Item E. V1-CIN-03 stays an open MAJOR, so the charter's film gate is not met and the release is a pre-release. V1-LEG-02 was judged on plan tests only. The audio was not heard.
- **Tests run (real results):** `python -m tools verify` VERIFY GREEN before and after the doc changes: ruff clean; mypy --strict clean (62 files); pytest 189 passed; traceability current; palette 87 pairs, 0 failing; planned-film audits 0 hard, 3 advisory; in-Blender 14 of 14; animatic and final tiers 3270 of 3270, 0 blank; final MP4 matches the delivery spec; cut-frame luma steps 0.4 and 0.0. ffprobe: H.264 High level 41, bt709, 3270 frames, 109.000 s. Loudness −15.9 LUFS, true peak −0.6 dBFS (AAC). Film mean luma 50.3; B-09.2 38.4; steps f746 5.6, f1376 4.6, f2431 6.4, f2709 7.7.
- **Release and sync:** commits b128263 and a036067; tag `v1.1.0` on a036067; release https://github.com/SimSI2027/Certificate-Flow-Film/releases/tag/v1.1.0, `isPrerelease=true`, 7 assets; all 7 downloaded back with equal SHA-256. Pages run 43578886004 succeeded; the live page, preview, poster and captions equal `site\`. The close-out commit and its sync result are in the Session F3 report.
- **Decision: APPROVED as a pre-release** — 2026-11-14. Third attempt at this gate. Not approved: the charter's film gate (V1-CIN-03 open; cinema estimate 5 of 10).

## v1.2 look pass, session L1 (Sonnet 5.5, high, 2026-11-14)

Lean mode (no discriminator round, no tag, no release). Details, rulings and stop-rule values: `docs\GAN-LEDGER.md` "Session L1".

- **Scope:** `docs\LOOK-PLAN-v1.2.md` Items A, C, E, B (second change), D, F; one commit each; `python -m tools verify --skip-blender` green on each, full verify after A and after E.
- **Gate (stills-and-strips):** passed on attempt 2 of 3. Attempt 1 failed on the flash steps (4.8 and 4.6 at badge glow 0.25); at 0.15 they are 3.9 and 3.8. Hero mean YAVG 53.0.
- **Full final render (the only one):** 3270 beauty, 2770 sign and 1933 caption frames; audio −15.9 LUFS; Final MP4 `84097e10…3f44`, 70.3 MB, on spec.
- **Tests run (real results):** `python -m tools verify` VERIFY GREEN with no waiver: ruff clean; mypy --strict clean (66 files); pytest 200 passed; traceability current; palette 87 pairs, 0 failing; planned-film audits 0 hard, 3 advisory; in-Blender 15 of 15; animatic and final tiers 3270/3270, 0 blank; final MP4 on spec, true peak −1.2 dBFS; cut-frame steps 0.3 and 0.1.
- **Measured on the MP4:** B-09.2 mean YAVG 51.3 (was 38.4; target 50 met); film mean 57.7; f2431 step 0.3, f2695–2712 largest 3.7. f746 8.0 and f1376 10.6 (flashback entry and exit) are over 4.0 and not tuned.
- **Shortfalls, recorded and not hidden:** F3-PKI-01 label tried and removed (36 of 45 frames), finding stays open; Item D left 10 `RESIDUAL_PX` entries (plan: at most 6) because three beats cannot take a longer lens; a soft glow near the rim light is left for L2 to rule on.
- **Decision: LOOK PASS DELIVERED, release held for L2** — first attempt at this gate; not auto-approved as a release. L2 re-audits the Final MP4 and decides v1.2.0.

## v1.2 targeted re-audit and release, session L2 (Opus 5.5, 2026-11-14)

Lean mode (no subagents, no discriminator round). Details and rulings: `docs\GAN-LEDGER.md` "Session L2".

- **Scope:** re-audit the L1 Final MP4 (`84097e10…3f44`) item by item; rule on the rim haze glow, the luma steps (f746, f1376, f1534–1535, f2454–2455), F3-PKI-01 and the 10 focal residuals; if no BLOCKER or MAJOR fails, release v1.2.0 as the public latest release.
- **Review performed:** 7 images (step pairs, proof window, flash and hero strip, ten focal beats, cuts and trust store, contact sheet, poster); per-frame `signalstats` on the MP4; rig-light positions recomputed from the camera plan.
- **Problems found and corrections:** new MINOR L2-CIN-01 (rim light passes through the AD tower and the Root CA complex: pops at 24.83 s and 45.83 s; cause found, exact fix written for v1.3). F3-PKI-01 stays an open MINOR (the film is accurate without the label). Focal residuals accepted. f2454–2455 is camera motion, not a defect. `scripts\build_site.py` still printed "v1.1.0 pre-release" (the housekeeping session had edited only `site\index.html`); it is now the source of the v1.2.0 text, and the V1-DOC-02 test checks v1.2.0 and that the page links no older release.
- **Tests run (real results):** `python -m tools verify` VERIFY GREEN before the edits (pytest 200, 15 in-Blender checks, both tiers 3270/3270, MP4 on spec, true peak −1.2 dBFS, cut-frame steps 0.3 / 0.1) and `verify --skip-blender` GREEN after them (pytest 200).
- **Decision: APPROVED as the public latest release v1.2.0** — 2026-11-14. 0 BLOCKER, 0 MAJOR open; V1-CIN-03 closed (cinema estimate 7). Not approved: the charter's film gate (scores ≥ 8, two clean discriminator rounds). Release, asset round-trip and Pages results are in PROJECT-STATE "Session L2".

## v1.3 finishing pass, session V3 (Opus 5.5, 2026-11-14)

Lean mode (no subagents, no discriminator round, no tag, no release). Details, per-item results and rulings: `docs\GAN-LEDGER.md` "Session V3".

- **Scope:** L2-CIN-01; interiors to the v1.2 look; hero whole from 98.5 s with B-09.2 mean ≥ 50; F3-PKI-01 proof tag. Pages stays on v1.2.0.
- **Gate before the render:** preview-tier contact sheet and strips (renders\preview); the first strip exposed a bug (every dressing rib glowed white) that was fixed before any final frame was made.
- **Final renders:** three beauty passes. Verify caught interior pops in the first (f477, f595, f600). The second passed verify, but a full scan found the pops at other frames, which proved them non-deterministic. Cause found (shadow-pool overflow, V3-CIN-01) and fixed. The third pass is the film. Signs re-rendered only for the 442 changed frames; captions and audio kept.
- **Tests run (real results):** `python -m tools verify` VERIFY GREEN on the third pass: ruff clean; mypy --strict 68 files; pytest 205 passed; traceability current; palette 87 pairs, 0 failing; planned-film audits 0 hard; in-Blender 16 of 16; both tiers 3270/3270, 0 blank; final MP4 on spec, true peak −1.2 dBFS; cut steps 0.4 / 0.1; MP4 luma gate f746 0.1, f1376 0.6, f1534 1.4, f1535 2.0, f477 1.8, f595 0.1, f600 0.1, f671 0.5, f705 0.0, f719 0.0, B-09.2 mean 56.3.
- **Final MP4:** SHA-256 `e5050765e7633399b04b3c3014fd811da7ccff6d3871d36216015001bfd330b6`, 70.3 MB, `dirty: false`. Reviewed: 1 final contact sheet (accepted).
- **Decision: v1.3 PASS DELIVERED, release held for the V3 audit.** This is the first attempt at the gate, so it is not approved as a release. Not approved: the charter's film gate (no discriminator round).
