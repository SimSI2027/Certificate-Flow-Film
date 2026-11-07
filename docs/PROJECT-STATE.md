# PROJECT STATE

Updated: 2026-11-07 (end of Session 3)

## Next session
- **Next session = 4**: Calibration + animatic GAN rounds (Phase 4 gate, Stage 1). **Model: Opus 5.5. Effort: Medium.**
- Start it as a NEW Claude Code session and paste the Session 4 prompt from `docs\SESSION-PROMPTS.md`.
- **Exact next action:**
  1. Confirm "Phase 4 build" is APPROVED in `docs\CHIEF-OF-STAFF-APPROVALS.md`, `python -m tools spec-hash` equals the frozen hash in `docs\GAN-LEDGER.md` (`7cf45afa…6d23`), and `python -m tools sync-check` says SYNC OK.
  2. Build `blender\calibration.py` and `python -m tools calibrate <fault>` (Charter 2.8). Nothing in `blender\` may reference calibration except that module (a test checks it).
  3. Run calibration, then GAN rounds on the animatic: `python -m tools build` then `python -m tools render --tier animatic`, commit, then `python -m tools packet stage1`. The verification packet `qa\rounds\stage1-R0` was built in Session 3 and is **not** a round; the first real round is `stage1-R1`.
  4. Open items the rounds must close (below, "Open for the Stage 1 rounds").
- **Do not edit `docs\REFERENCE-SPEC.md`.** The spec is FROZEN; changes need a Chief of Staff amendment in the ledger.

## Phase / stage
- Phase 1 (Environment): APPROVED. Phase 2 (Repository): APPROVED. Phase 3 (Stage 0 spec freeze): APPROVED.
- Phase 4 build (Session 3): **APPROVED** (see `docs\CHIEF-OF-STAFF-APPROVALS.md`). The Stage 1 gate (calibration, then clean rounds) is Session 4.
- Stage 1: not started as a gate. Clean-round counter 0. Calibration (Charter 2.8) is Session 4.
- Spec frozen at SHA-256 `7cf45afa01572b7e9d30a6fb376807fb10a4f6a693af41ffed1d96bce2686d23`. Untouched in Session 3.

## Git
- Branch `main`, tracking `origin/main`. Session 3 commits are listed in the approvals record; the close-out sync result is in the Session 3 report.
- Line endings are pinned to LF (`.gitattributes`) so frozen hashes are checkout-independent.

## URLs
- Repository (public): https://github.com/SimSI2027/Certificate-Flow-Film
- Pages demo: not yet published. Release: not yet published.
- Related (verified in Session 1): https://github.com/SimSI2027/Certificate-Flow-Lab (Pages: https://simsi2027.github.io/Certificate-Flow-Lab/). Approach A: HTTP 404, not linked.

## Toolchain (details in `docs\TOOLCHAIN.md`; commands in `docs\PIPELINE.md`)
- Blender 5.2.3 LTS with EEVEE (`BLENDER_EEVEE`); Cycles/OptiX is the fallback. Python 3.12.10 `.venv` (pytest 9.2.0, ruff 0.17.4, mypy 2.4.1). FFmpeg 9.0.2. gh 2.103.3 as SimSI2027.
- `pyproject.toml`: ruff line length is **160** (raised from 120 in Session 3), with per-file E501 and N806 ignores for stage data tables, theme, tools and Blender builders.

## What exists now
- **`cff\`** (pure Python, no bpy):
  - `config\names.py`, `story\{model,timing,captions,spec_ids,export}.py` (Stage 0)
  - `theme\`: `colour.py`, `palette.py` (+ `PLATE_OPACITY`, revocation amber `#D9A24F`), `palette_check.py`, `motion.py` (easing presets, label and camera-smoothing constants), `shots.py` (33 beat shots, focal stand-ins), `render.py` (tiers)
  - `stage\`: `layout.py`, `tracks.py`, `objects.py` (137-object catalogue, `BASE_ANCHORED`, `centre_offset`), `choreography.py` (every on-screen event -> keyframe tracks, 136 animated objects), `labels.py` (48 placements, sizing from the camera plan), `camera.py` (smoothed plan), `audit.py` (C-02/03/06/09 audits)
- **`blender\`**: `build_scene.py`, `world.py`, `actors\*` (grey-box builder per `Kind`), `materials.py`, `signage.py`, `camera_rig.py`, `lighting.py`, `compositor.py`, `captions_scene.py`, `animation.py`, `render_settings.py`, `render_frames.py`, `run_checks.py`, `checks\scene_checks.py` (11 checks).
- **`tools\`**: `env`, `verify`, `build`, `render`, `captions`, `packet stage0|stage1`, `contact`, `palette`, `motion`, `traceability`, `model-dump`, `spec-hash`, `sync-check` (`pipeline.py`, `frames.py`, `toolchain.py`, `verify.py`).
- **`tests\`**: 140+ pytest tests (Stage 0 suite plus camera, choreography, labels, palette, tooling, Blender static scans).
- **`qa\`**: `schema.json`, `regressions.json` (20 accepted findings), `rounds\stage0-R1..R3`, `rounds\stage1-R0` (verification packet, not a round).
- **`docs\`**: REFERENCE-SPEC (frozen), GLOSSARY, PKI-TECHNICAL-NOTES, STORYBOARD, GAN-FRAMEWORK, GAN-LEDGER, TRACEABILITY (generated), PIPELINE (new).

## Render / verify
- Animatic: 960x540, 30 FPS, 3270 frames (109 s), EEVEE (`BLENDER_EEVEE`), 32 samples, no motion blur or volumetrics. Beauty frames in `renders\animatic\beauty`, caption-layer frames in `renders\animatic\captions` (both gitignored). Full animatic render took about 12 minutes in 300-frame chunks.
- `python -m tools verify` is fully green at the Session 3 close (ruff, mypy --strict, pytest, traceability, palette, motion, 11 in-Blender checks, blank-frame check on all 3270 frames).

## Names in use
- Fixed: `1SN0S.LAB`, `1SN0S`, `1sn0s.lab`, `RDPAuth`, `WebServer-TLS`.
- Fallbacks in use: DC `DC01`, client `CLIENT01`, RDP server `RDP01` (`rdp01.1sn0s.lab`), web server `WEB01`, site `portal.1sn0s.lab`, Root CA `1SN0S Root CA`, Issuing CAs `1SN0S Issuing CA 1` / `1SN0S Issuing CA 2`, PKI HTTP host `pki.1sn0s.lab`.

## Decisions and notes (Session 3)
- **Camera:** one rig. The plan is Gaussian-smoothed (sigma 16 frames, clamp at segment ends) so the moving subject leads the camera. Per-shot parameters (azimuth, elevation, distance, follow, bulge) were found by a seeded random search (seed 20261107) around the authored intent, then hand-tuned; the search script was scratch, the result is data in `cff\theme\shots.py`. The focus pulls onto the beat's subject within 30% of the beat (`FOCUS_PULL_FRACTION`).
- **Focal stand-ins** (`cff\theme\shots.py: FOCAL_BEAT_OBJECTS`): where the subject is born mid-beat, the machine that makes it counts as part of the subject (B-04.4 press + RDP card, B-08.2 press + web card, B-05.2 cartridge + CA request, B-03.1 container + keys, B-07.2 container + capsule). B-06.6's subject is the near end of the RDP channel plus the screen. The discriminators may challenge this reading.
- **Measurement interpretations** (recorded because the spec leaves them open): pops are world-space jumps between consecutive frames with whitelisted fast kinds (pulses, fetches, travelling artefacts: 3.6 m/frame; a route of 27 m in 0.8 s peaks near 3.5), a rising-complex whitelist for the Root CA vault (0.8 m/frame), and a quarter of an object's own size; the screen-space displacement is reported as a metric. Camera jerk is the second difference of the camera position over the focus distance (limit 0.004), judged after the first 6 frames of the film (flat end handles on the first keys). A label counts as "on screen" once its entrance reaches 70% of full size.
- **Label sizing:** each label's cap height is raised until it reaches 26 px at 1080p on the camera plan (`cff\stage\labels.py: effective_caps`); families (a check list, the eligibility tags) share the largest size. All 46 must-read labels now pass L-01, L-03 and facing at their beats. Fonts: Blender's bundled DejaVu Sans Mono for in-world names (the default font made `1` look like `I`) and Inter for captions. Plates are 92% opaque so white text keeps 4.5:1 even over white (tested).
- **Events retimed in `timing.py`** so that must-read labels hold 1.5 s inside their beat and proofs are not teleports: ticks in B-04.3 and B-08.1 (even spacing), B-04.4 compressed (the card exists by 1.1 s), B-06.1 proof travel (E-06.1d/e/f), B-09.1 compressed (proof, docking, ticks, CRL flickers, channel). Ordering of events within beats is unchanged; the 93 Stage 0 tests still pass.
- **Layout:** `WALKWAY` (the flashback footprint trail) now climbs the dais edge and ends at the reader bay; before, it ended inside the root plinth's bounds. The root key module and key appear after the vault has landed (the key never travels outside its owner's bounds). CA check ticks sit nearer the cradle so the first label is on screen.
- **Palette:** revocation amber moved to `#D9A24F` because the old value was only 4.2 dE00 from pending amber under deuteranopia (the spec asks for at least 5 in every condition). The eight key roles still clear 15.8 dE00 in all three conditions.
- **Materials:** glow-only kinds (channels, routes, links, ticks, rings, trim, pulses ...) are dark until their glow channel lights them, so amber and green appear only when the story says so (C-10).
- **Process slips (CLAUDE.md edit rules):** in Session 3 (earlier part) a Python heredoc applied the timing retime (diff reviewed, 34 intended lines); in this part, one Python heredoc removed an unused constant from `cff\theme\render.py` (fixed up with Edit). Everything else used Edit/Write.
- **Frame provenance:** the animatic frames were rendered from commit 91ec326 plus later edits that touch only `blender\checks\scene_checks.py`, `.gitignore` and docs (no effect on frames).

## Open for the Stage 1 rounds
- **C-03 advisory (`cff\stage\audit.py: C03_OPEN_BEATS`):** B-05.1 (focus on the rising root vault 66/75 frames) and B-09.2 (hero: root inside the frame box 130/150, in focus 127/150). A test fails if a listed beat starts passing, and if any other beat starts failing.
- **Not yet implemented as hard checks** (listed in TRACEABILITY): C-04 depth layers, C-07 boundary continuity, C-10 material audit, C-11 silhouette IoU, L-02 sampled contrast on rendered frames (the plate contrast worst case is tested), L-05 caption-vs-focal-bounds overlap, L-06 occlusion and circle of confusion. Several are cheap to add once the first round shows what the discriminators measure.
- Grey-box visuals: labels draw through geometry in some frames, shadows are noisy at 32 samples, the flashback vignette is subtle. None are spec criteria at this stage; expect cinema- and legibility-discriminator findings.
- No audio, encode or MP4 yet (Sessions 5-7).

## Blockers / remaining work
- No blockers. Remaining: Sessions 4-9 per `docs\SESSION-PROMPTS.md`.
