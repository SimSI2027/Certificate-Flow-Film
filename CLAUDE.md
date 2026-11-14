# Certificate-Flow-Film — project rules (loads every session)

Authoritative spec: `docs\BUILD-CHARTER.md`. Session plan/prompts: `docs\SESSION-PROMPTS.md`.
Current status and exact next action: `docs\PROJECT-STATE.md`. Read PROJECT-STATE first, then only the charter sections your session needs.
Goal: a 1920x1080, 30 FPS, 100-120 s H.264/AAC film of an ADCS PKI flow, built with scripted Blender (`bpy`), a staged film pipeline and a GAN-style adversarial review loop.
Never read, modify or depend on the Approach A project (`Certificate-Flow-Animation`).

## Environment
- Windows + PowerShell. Use PowerShell-compatible commands. Automation lives in Python under `tools\` and `scripts\`, not shell one-liners.
- Paths and tool versions: `config\toolchain.local.json` (gitignored) and `docs\TOOLCHAIN.md`. Use `.venv\Scripts\python.exe`.
- Blender is pinned to 5.2.x LTS. Every call: `"<blender.exe>" -b [file.blend] --factory-startup --python-exit-code 1 -P <script.py> -- <args>`. Script errors must fail the process.
- Blender 5.x API rules (verify against docs.blender.org/api/5.2 for the installed version; detect capabilities, not versions):
  - VSE: `strips` / `strips_all`, not `sequences`.
  - Compositor: `scene.compositing_node_group` (no `scene.node_tree`, no Composite node).
  - Animation uses slotted actions: channelbag API, not `action.fcurves`; use `keyframe_insert`.
  - EEVEE engine id: detect from the render-engine enum (currently `BLENDER_EEVEE`).
  - Never use Blender's internal FFmpeg output. Render PNG sequences and encode with the FFmpeg CLI.
- No unvetted third-party Claude skills or Blender add-ons.

## Source-editing rules
- Edit source only with the Edit/Write tools. No Bash heredocs, no `sed`, no Python one-liners, no PowerShell `-replace` on source.
- `cff\` is pure Python and must never import `bpy`. Blender code lives in `blender\` and imports `cff`.
- Do not ask routine questions. Decide, and record the decision. Ask only for credentials, elevation, destructive operations or an unrecoverable blocker.
- Never force-push. Never rewrite public history.

## Architecture rules
- The story model (`cff\story\model.py`) is the single source of truth. Captions, timing, audio cues, traceability and checks derive from it.
- Names live only in `cff\config\names.py`. Unfilled `<<REPLACE: ...>>` placeholders use their fallback. Never render placeholder text.
- Named timing constants only (`cff\story\timing.py`). Central theme (`cff\theme\`). No inline colours, easings, durations or frame literals outside them. A test enforces this.
- Determinism: seeded `random.Random(seed)` with seeds documented, no wall-clock logic, `--factory-startup` always.
- Motion: Bezier keyframes with named easing presets. LINEAR only for whitelisted constant-speed effects.
- Do not reduce PKI accuracy to simplify the film. Do not add complexity beyond the story. PKI facts F-01..F-17 must never be contradicted.

## Quality control (GAN loop)
- Hard discriminators (`python -m tools verify`) are persistent. Never delete a useful test. Every accepted BLOCKER/MAJOR that can be tested becomes a test named after its finding ID.
- Round protocol: candidate commit -> `tools packet` (no source, no commit messages, no generator claims) -> three fresh read-only discriminators in parallel (`pki-discriminator` opus; `cinema-` and `legibility-discriminator` sonnet) -> `tools verify` -> Chief of Staff triage -> fixes -> ledger entry in `docs\GAN-LEDGER.md`.
- Gate: 0 BLOCKER, 0 MAJOR, scores >= 8, all PKI beats ACCURATE, hard tests green. Stage 4 needs two consecutive clean rounds with fresh instances. Cap 5 rounds per stage; open BLOCKER/MAJOR never ships.
- Anti-gaming: never win by deleting or merging beats, shrinking captions, moving content out of frame, cutting checks or dimming the scene. Aim at the frozen spec, not at discriminator wording.
- Frozen-spec change control: `docs\REFERENCE-SPEC.md` changes only by written Chief of Staff amendment in the ledger with a new SHA-256; the stage's clean-round counter resets. The generator never edits the spec to remove a finding.
- Chief of Staff approval: record every phase in `docs\CHIEF-OF-STAFF-APPROVALS.md` with real test results and commit/sync. Never auto-approve a first attempt. Never claim placeholders, uninspected output, fake results, invented URLs or unsynced GitHub state.

## Delivery
- After every milestone: commit related changes only, push to `origin/main`, run `python -m tools sync-check` (local HEAD == origin/main), update and push `docs\PROJECT-STATE.md`. Never accumulate the project into one commit.
- Long renders: background chunks (about 300 frames); `use_overwrite=False`, `use_placeholder=True`; poll and record progress in PROJECT-STATE.
- GitHub Pages must stay in sync with `main`.
- No release without rendered, inspected, discriminator-cleared assets. The project is complete only when everything in Charter 17 is true.

## Release rule
Release rule: after every session, push and verify sync (local HEAD = origin/main). The Pages demo always shows the newest AUDITED release. When an audit passes, publish that version as the public latest release (not a pre-release), update the README, CHANGELOG and Pages in the same session, and verify the live page.

## Session continuity
Keep `docs\PROJECT-STATE.md` accurate enough for a brand-new session to resume from it alone. If context gets long: finish the current atomic step, update PROJECT-STATE with the exact next action, commit and push, record session number, model, effort and remaining steps, then tell the user to start a new session on the same model and effort with the Resume prompt in `docs\SESSION-PROMPTS.md`.
Each session starts by checking the previous session's phases are APPROVED, and ends by setting `Next session` in PROJECT-STATE and giving a report of at most 10 lines (Charter 17).
Discriminator agents live in `.claude\agents\`; Claude Code loads them at session start.
