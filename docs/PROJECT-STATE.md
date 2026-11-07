# PROJECT STATE

Updated: 2026-11-07T00:55Z (end of Session 1)

## Next session
- **Next session = 2** — Spec freeze (Phase 3) — **Model: Opus 5.5 — Effort: High**
- Start it as a NEW Claude Code session so the new `.claude\agents\` discriminators are loaded.
- Exact next action: start Session 2 using its prompt in `docs\SESSION-PROMPTS.md`. First check that Phases 1 and 2 are APPROVED in `docs\CHIEF-OF-STAFF-APPROVALS.md` (they are). Then write `docs\REFERENCE-SPEC.md`, GLOSSARY, PKI-TECHNICAL-NOTES, STORYBOARD, the story model with pytest, and TRACEABILITY, and have `pki-discriminator` review the written spec. Also: check the `.lab` status in the IANA root zone database before writing docs (Charter Section 1 Docs note).

## Phase / stage
- Phase 1 (Environment): APPROVED. Phase 2 (Repository): APPROVED.
- Stage: none started. Current GAN round: n/a (spec not yet written).
- Last approved milestone: Phase 2 — repository bootstrapped, public, synchronized.

## Git
- Branch: `main`, tracking `origin/main`.
- Bootstrap commit: `a1cb1d1` (pushed). Docs/state commit follows it; the final local and remote commit is recorded in `docs\CHIEF-OF-STAFF-APPROVALS.md` and was verified equal at close-out.

## URLs
- Repository (public): https://github.com/SimSI2027/Certificate-Flow-Film
- Pages demo: not yet published. Release: not yet published.
- Related, verified with `gh`: https://github.com/SimSI2027/Certificate-Flow-Lab (Pages: https://simsi2027.github.io/Certificate-Flow-Lab/)
- Approach A (`SimSI2027/Certificate-Flow-Animation`): HTTP 404, not linked.

## Toolchain (details in `docs\TOOLCHAIN.md`)
Blender 5.2.3 LTS (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`); EEVEE (`BLENDER_EEVEE`) headless probe OK and non-blank; Cycles/OptiX fallback verified. Python 3.12.10 `.venv` (pytest 9.2.0, ruff 0.17.4, mypy 2.4.1). FFmpeg 9.0.2 (libx264, aac). gh 2.103.3 as SimSI2027. RTX 4090, driver 621.14. Local paths in gitignored `config\toolchain.local.json`.

## Render / verify
- Latest render: none (only the GPU probe frame in gitignored `renders\probe\`). Latest `tools verify`: not yet implemented. Render progress: n/a.

## Names in use
Fixed: `1SN0S.LAB`, `1SN0S`, `1sn0s.lab`, `RDPAuth`, `WebServer-TLS`.
Fallbacks in use: DC `DC01`, client `CLIENT01`, RDP server `RDP01`, web server `WEB01`, site `portal.1sn0s.lab`, Root CA `1SN0S Root CA`, Issuing CAs `1SN0S Issuing CA 1` / `1SN0S Issuing CA 2`, PKI HTTP host `pki.1sn0s.lab`.

## Decisions and notes
- Blender pin: winget offered 5.2.3 for `BlenderFoundation.Blender`, which is on the 5.2 LTS line, so no other package ID was needed.
- Git identity is set repo-locally (user `SimSI2027`, GitHub noreply email); no global git identity existed.
- The skeleton has package `__init__.py` files only. `python -m tools sync-check` does not exist yet (built in Session 3), so the sync check this session was done with `git rev-parse HEAD` against `git ls-remote origin refs/heads/main`.
- The three agent files were compared with the Charter 2.3 text and match verbatim. `/agents` listing can only be verified in a fresh session (Session 2 start).
- The README is a stub (status, licence split, names in use, links); the full README is Session 8.

## Blockers / remaining work
- No blockers. Remaining: Sessions 2–9 per `docs\SESSION-PROMPTS.md`.
