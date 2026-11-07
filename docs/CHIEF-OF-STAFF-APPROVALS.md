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
