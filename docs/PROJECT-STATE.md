# PROJECT STATE

Updated: 2026-11-06 (end of Session 2)

## Next session
- **Next session = 3**: Pipeline + animatic build (Phase 4, build part). **Model: Sonnet 5.5. Effort: High.**
- Start it as a NEW Claude Code session and paste the Session 3 prompt from `docs\SESSION-PROMPTS.md`.
- **Exact next action:**
  1. Confirm Phase 3 is APPROVED in `docs\CHIEF-OF-STAFF-APPROVALS.md`.
  2. Confirm `python -m tools spec-hash` equals the "Frozen REFERENCE-SPEC SHA-256" in `docs\GAN-LEDGER.md` (`7cf45afa…6d23`); `tests\test_spec_freeze.py` also enforces this.
  3. Confirm `python -m tools sync-check` reports SYNC OK.
  4. Then build `tools\__main__.py`'s remaining commands (env, verify, build, render, captions, packet stage1, contact, palette, motion), `blender\build_scene.py`, the grey-box actors and `blender\checks\scene_checks.py`, all driven from `cff`.
- **Do not edit `docs\REFERENCE-SPEC.md`.** The spec is FROZEN; changes need a Chief of Staff amendment in the ledger.

## Phase / stage
- Phase 1 (Environment): APPROVED. Phase 2 (Repository): APPROVED. Phase 3 (Stage 0 spec freeze): **APPROVED**.
- Stage 0: converged in 3 of 5 rounds.
  - stage0-R1: NOT PASSED
  - stage0-R2: clean, but its MINOR fixes changed the text
  - stage0-R3: PASSED
- Stage 1: not started. Clean-round counter 0. Calibration (Charter 2.8) is Session 4.
- Last approved milestone: Phase 3. Spec frozen at SHA-256 `7cf45afa01572b7e9d30a6fb376807fb10a4f6a693af41ffed1d96bce2686d23`.

## Git
- Branch `main`, tracking `origin/main`.
- Freeze commit `fc9edad75f6e3f339b55f1204657634b85de9caf` was pushed and sync-checked (SYNC OK). The closing docs commit (approvals and this file) is verified with `python -m tools sync-check` at close-out.
- Line endings are pinned to LF (`.gitattributes`) so frozen hashes are checkout-independent.

## URLs
- Repository (public): https://github.com/SimSI2027/Certificate-Flow-Film
- Pages demo: not yet published. Release: not yet published.
- Related (verified in Session 1): https://github.com/SimSI2027/Certificate-Flow-Lab (Pages: https://simsi2027.github.io/Certificate-Flow-Lab/). Approach A: HTTP 404, not linked.

## Toolchain (details in `docs\TOOLCHAIN.md`)
- Blender 5.2.3 LTS with EEVEE (`BLENDER_EEVEE`); Cycles/OptiX is the fallback.
- Python 3.12.10 `.venv` (pytest 9.2.0, ruff 0.17.4, mypy 2.4.1).
- FFmpeg 9.0.2.
- gh 2.103.3 as SimSI2027.
- `pyproject.toml` holds the ruff, mypy (strict) and pytest config, including the `covers` marker.

## What exists now
- **`cff\`** (pure Python, no bpy):
  - `config\names.py`
  - `story\model.py`: actors, keys, certificates (including intermediate copies), CRLs, templates, CAs, requests, discoveries, chains, labels, and 96 events
  - `story\timing.py`: 109 s, frames 1–3270 at 30 fps
  - `story\captions.py`: 13 captions, all meeting L-04
  - `story\spec_ids.py` and `story\export.py` (the model dump)
- **`tools\`:** `traceability [--check]`, `model-dump`, `packet stage0`, `spec-hash`, `sync-check`. (`sync-check` was built early, in Session 2, for close-out.)
- **`tests\`:** 93 pytest tests, covering model integrity, timing, names, captions, terminology, purity, spec docs, traceability, spec freeze and the GAN-finding hard tests (`test_gan_findings.py`; never delete these).
- **`qa\`:**
  - `schema.json` (the findings JSON Schema)
  - `regressions.json` (20 accepted findings)
  - `rounds\stage0-R1..R3` (packets plus verbatim reports)
- **`docs\`:** REFERENCE-SPEC (frozen), GLOSSARY, PKI-TECHNICAL-NOTES, STORYBOARD (with non-binding world blocking), GAN-FRAMEWORK, GAN-LEDGER and TRACEABILITY (generated).

## Render / verify
- Latest render: none (only the Session 1 GPU probe).
- `python -m tools verify` is not implemented yet (Session 3). Latest pure-Python results: pytest 93 passed, ruff clean, mypy clean.

## Names in use
- Fixed: `1SN0S.LAB`, `1SN0S`, `1sn0s.lab`, `RDPAuth`, `WebServer-TLS`.
- Fallbacks in use: DC `DC01`, client `CLIENT01`, RDP server `RDP01` (`rdp01.1sn0s.lab`), web server `WEB01`, site `portal.1sn0s.lab`, Root CA `1SN0S Root CA`, Issuing CAs `1SN0S Issuing CA 1` / `1SN0S Issuing CA 2`, PKI HTTP host `pki.1sn0s.lab`.

## Decisions and notes (Session 2)
- **`.lab`:** not delegated in the DNS root as of 2026-11-06. The evidence and the collision note are in PKI-TECHNICAL-NOTES. Names unchanged.
- **Event and caption timings** live in `timing.py`, keyed by event or caption ID. Semantics live in `model.py`.
- **AIA/CDP URLs** are built from parts in `model.extension_url`, which is allowlisted in `tests\test_purity.py`. These are lab-internal illustrative data and are never fetched.
- **The Stage 0 packet** excludes TRACEABILITY and GAN-FRAMEWORK: they describe test coverage and process, which would amount to generator claims.
- **Reports are saved as delivered** in the agent hand-back. The background transcript file was empty in R1, so the hand-back was the only copy.
- **The world blocking** in STORYBOARD is non-binding; Session 3 may tune distances but must keep the topology. The C-02 camera threshold is 4% of focus distance per frame.
- **The root seal** is revealed statically, not animated closed (accuracy deviation from Charter 7's wording; recorded in the ledger).
- **Spec constraints the animatic must honour:**
  - one connection attempt per certificate (S2 closes; S6 is a new pulse)
  - requests are consumed at their CA
  - the CA request carries a CA=true band and a tag
  - each server presents its own intermediate copy, and the crown originals never move
  - the handshake proof is a signature impression and is verified at the client
  - the root's module and press stay dark in the present

## Blockers / remaining work
- No blockers. Remaining: Sessions 3–9 per `docs\SESSION-PROMPTS.md`.
