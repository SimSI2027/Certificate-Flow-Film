# PROJECT STATE

Updated: 2026-11-14 (Session V5 audit, `claude-fable-5-2`, High, no subagents)

Earlier sessions (F1 to V5b) are in `docs\history\PROJECT-STATE-through-V5b.md`; Sessions 3–4 are in `docs\archive\`.

## SESSION V5 AUDIT DONE (2026-11-14, Fable 5.2, High, no subagents, 13 of 14 images): v1.3.0 RELEASED as the PUBLIC LATEST release

- **Audit (`docs\AUDIT-V5.md`): gate PASS. 0 BLOCKER, 0 MAJOR, 10 MINOR; 33 of 33 PKI beats ACCURATE.** Scores: PKI 9, icons 8.5, realism 8, presentation 7.5, legibility 8.5. Presentation is 0.5 under the charter's score gate of 8; the session gate was "no BLOCKER, no MAJOR".
- Rulings: V5A-R1 (V5B-CIN-03, the darkening at f2451–2456 on entering CA 2's enclosure: accepted as MINOR, no fix); V5A-R2 (V5B-OBS-01, the trust store hides the root card at B-06.2: accepted as MINOR, the viewer still understands the root is already trusted).
- **Final MP4 SHA-256 `ce4cf1fb12fa71d35237463506069c5f80c06b2c6ff15722dc69be43646f15d9`** (confirmed), 110.6 MB, render commit 2666bad. Gitignored (release asset).
- `python -m tools verify` VERIFY GREEN before the audit and after the cleanup: pytest 232, 20 in-Blender checks, both tiers 3270/3270, MP4 on spec, true peak −1.2 dBFS, cut steps 0.5/0.1, MP4 luma gate PASS (B-09.2 mean 58.8).
- **Release:** https://github.com/SimSI2027/Certificate-Flow-Film/releases/tag/v1.3.0, tag `v1.3.0` on `c125bae`, Latest, `isPrerelease=false`, 7 assets. All 7 were downloaded back with equal SHA-256.
- **Pages:** run 43661965682 succeeded. The live `index.html`, `poster.png`, `preview.mp4` and `captions.vtt` are byte-identical to `site\`; the poster, preview and captions equal the release assets. The page says "v1.3.0 is the current release" and has no earlier lab name.
- **Cleanup:**
  - Releases and tags v1.0.0, v1.1.0 and v1.2.0 deleted (`gh release delete <tag> --cleanup-tag --yes`). `gh release list` and `git ls-remote --tags` show only v1.3.0. No history rewrite, no force-push.
  - README, CHANGELOG and the Pages page name only v1.3.0 (a test enforces it for the README and the page).
  - Process history moved to `docs\history\`: `GAN-LEDGER.md`, `CHIEF-OF-STAFF-APPROVALS.md`, `AUDIT-v1.md`, `LOOK-PLAN-v1.2.md`, `rounds\` (was `qa\rounds`), plus the old session log. Paths fixed in CLAUDE.md, the charter, GAN-FRAMEWORK, SESSION-PROMPTS, tests, tools and code comments. `tools packet` now writes rounds to `docs\history\rounds`.
  - Not changed: the frozen `docs\REFERENCE-SPEC.md` still names `docs/GAN-LEDGER.md` (editing it would need an amendment and a new hash; `docs\history\README.md` notes it). `docs\archive\` and the files inside `docs\history\` are left as written, so they keep old paths and the earlier lab name. The frozen calibration packets in `qa\calibration\` also keep the earlier lab name.
- **Enhancement plan:** `docs\ENHANCEMENTS-v1.4.md` (10 ranked items, nothing built). Top 3: seals stamp and chain links lock; a stronger title card; screen UI on the laptop and session window.
- Commits: 914d036 (audit), c125bae (v1.3.0 docs and site; the tag), fb30aa5 (history move), 3f1cecf (enhancement plan), plus this close-out.
- Local only (gitignored): `renders\final` (the v1.3.0 frames), `renders\final-v5b-replaced`, `renders\final-v4-beauty` and `-signs`, `renders\preview-v5a`.
- **Next session: none required. The project is released and in sync.** Optional v1.4 build from `docs\ENHANCEMENTS-v1.4.md`: items 2 and 3 on Sonnet 5.5 (medium to High), item 1 on Opus 5.5 (High); then one encode, `python -m tools verify`, a short audit on Fable 5.2 and a v1.4.0 release.

## Git
- Branch `main`, tracking `origin/main`. Only tag: `v1.3.0`.
- Line endings are pinned to LF (`.gitattributes`) so frozen hashes are checkout-independent.

## URLs
- Repository (public): https://github.com/SimSI2027/Certificate-Flow-Film
- Pages demo: https://simsi2027.github.io/Certificate-Flow-Film/
- Latest release: https://github.com/SimSI2027/Certificate-Flow-Film/releases/tag/v1.3.0
- Related (verified in Session 1): https://github.com/SimSI2027/Certificate-Flow-Lab (Pages: https://simsi2027.github.io/Certificate-Flow-Lab/). Approach A: HTTP 404, not linked.

## Toolchain (details in `docs\TOOLCHAIN.md`; commands in `docs\PIPELINE.md`)
- Blender 5.2.3 LTS with EEVEE (`BLENDER_EEVEE`); Cycles/OptiX is the fallback. Python 3.12.10 `.venv` (pytest 9.2.0, ruff 0.17.4, mypy 2.4.1). FFmpeg 9.0.2. gh 2.103.3 as SimSI2027.
- `pyproject.toml`: ruff line length is 160, with per-file E501 and N806 ignores for stage data tables, theme, tools and Blender builders.
- Note from this session: the PowerShell tool failed with "The system cannot find the path specified" on every call, so commands were run through Git Bash with the same executables.

## Names in use
- Fixed: `MALAWI.LAB`, `MALAWI`, `malawi.lab`, `RDPAuth`, `WebServer-TLS`.
- Fallbacks in use: DC `DC01`, client `CLIENT01`, RDP server `RDP01` (`rdp01.malawi.lab`), web server `WEB01`, site `portal.malawi.lab`, Root CA `MALAWI Root CA`, Issuing CAs `MALAWI Issuing CA 1` / `MALAWI Issuing CA 2`, PKI HTTP host `pki.malawi.lab`.
