# GAN framework

How Certificate-Flow-Film's adversarial review loop works. The authority is `docs/BUILD-CHARTER.md`, Section 2. This page explains the loop and records how each stage applies it. Round results go in `docs/GAN-LEDGER.md`; phase decisions go in `docs/CHIEF-OF-STAFF-APPROVALS.md`.

## Roles

| GAN concept | In this project |
|---|---|
| Generator | The main build session. It writes the code, builds scenes and renders candidates. |
| Discriminators | Three read-only subagents in `.claude/agents/`, plus the automated hard discriminators (`python -m tools verify`, Charter Section 12). |
| Real-data distribution | The frozen reference spec (`docs/REFERENCE-SPEC.md` with `docs/GLOSSARY.md`). Discriminators judge against it, never against their own taste or the generator's claims. |
| Loss | Weighted findings and scores per round. A BLOCKER counts as infinite loss. |
| Training round | One candidate → independent judgement → triage → fixes. |
| Arbiter / trainer | The Chief of Staff. Owns the spec, runs rounds, resolves disputes and decides gates. |

## Discriminators

| Agent | Model | Judges | Verdicts |
|---|---|---|---|
| `pki-discriminator` | opus | PKI accuracy against AR-01..AR-07 and F-01..F-17 | per beat: ACCURATE / MISLEADING / WRONG |
| `cinema-discriminator` | sonnet | film quality against C-01..C-11 (and LOOK-BIBLE once frozen) | per shot: FILM / DIAGRAM; scores 0–10 per criterion |
| `legibility-discriminator` | sonnet | readability and accessibility against L-01..L-08 and the glossary | scores 0–10 per criterion |

All three agents:
- have only Read, Glob and Grep, so they cannot edit or render
- read only the round packet and the frozen files it lists
- list every file they read in `files_read`
- re-check every entry in `regressions.json`
- reply only with the JSON report defined by `schema.json`

They are spawned as **fresh instances** every round, in parallel, so they do not anchor on earlier rounds.

## Round protocol

1. **Candidate.** The generator commits the candidate locally. The commit hash is the candidate ID.
2. **Packet.** `python -m tools packet <stage>` builds `qa/rounds/<stage>-R<n>/`. A packet is immutable once built.
3. **Judgement.** Fresh discriminators run in parallel, each pointed only at the packet path. Each JSON reply is saved verbatim in the packet folder.
4. **Hard discriminators.** `python -m tools verify` runs on the same candidate.
5. **Triage.** The Chief of Staff marks every finding as either:
   - **ACCEPTED** (it will be fixed), or
   - **REJECTED-INVALID**, with a written citation showing how the finding misreads the frozen spec.

   Rejecting a PKI BLOCKER also needs a second, fresh `pki-discriminator` to concur. Severity may not be downgraded without written justification.
6. **Fixes.** The generator fixes every accepted finding.
7. **Learned → hard.** Every accepted BLOCKER or MAJOR that can be expressed geometrically, temporally or textually becomes a permanent automated test named after its finding ID (for example `test_PKI_S0R1_003_...`).
8. **Ledger.** The round is appended to `docs/GAN-LEDGER.md`:
   - candidate commit and spec hash
   - counts per severity and scores per criterion
   - accepted and rejected findings, with reasons
   - new hard tests
   - the gate decision
9. **Next round.**

Accepted findings are added to `qa/regressions.json`, so every later packet carries them for re-checking (FIXED or REGRESSED).

## Packet contents

Every packet holds:
- frames
- motion strips (tiled frames sampled every 3rd frame across every transition and camera move)
- `manifest.json` (frame ↔ beat ↔ timestamp; caption timings; measured text bounds; contrast samples; palette results; file hashes; spec hash)
- `regressions.json`
- `schema.json`
- the list of frozen files

A packet never holds:
- source code
- commit messages
- generator notes or reasoning
- claims of success

**Stage 0 (written spec).** No frames exist yet. The Stage 0 packet holds:
- copies of the frozen files (REFERENCE-SPEC, GLOSSARY, PKI-TECHNICAL-NOTES)
- `STORYBOARD.md`
- `model-dump.json` (the story data the film is generated from)
- `schema.json`, `regressions.json`, `manifest.json` and a neutral README

Only `pki-discriminator` runs at Stage 0. In its `frames` field it cites document sections and model IDs instead of frame files. `TRACEABILITY.md` and this file are excluded: they describe test coverage and process, which would amount to generator claims.

## Findings schema

The report format is `qa/schema.json` (JSON Schema, draft 2020-12), copied into every packet. It encodes Charter 2.5:

```
{ "discriminator": "", "round": "", "spec_sha256": "",
  "verdicts": [ { "beat": "B-04.2", "frames": [""], "verdict": "ACCURATE|MISLEADING|WRONG|FILM|DIAGRAM", "reason": "" } ],
  "findings": [ { "id": "", "severity": "BLOCKER|MAJOR|MINOR", "criterion": "F-xx|AR-xx|C-xx|L-xx",
                  "beat": "", "frames": [""], "evidence": "", "why": "", "direction": "" } ],
  "scores": { "C-01": 0 },
  "regressions_checked": [ { "finding": "", "status": "FIXED|REGRESSED" } ],
  "files_read": [""] }
```

`direction` says what would fix the problem, not how to code it.

## Severities

- **BLOCKER**: wrong PKI; any private-key or Root CA violation; a blank or broken frame; an unreadable required caption; a DIAGRAM shot in Stage 4 or later.
- **MAJOR**: misleading PKI; weak film quality; readability problems; broken continuity.
- **MINOR**: polish.

## Gates

A stage gate passes when the latest round has:
- 0 BLOCKER and 0 MAJOR
- every MINOR fixed, or recorded as a justified won't-fix
- every cinematic and legibility score ≥ 8 (from Stage 1 onward)
- every PKI beat ACCURATE
- all hard discriminators green

The **final cut** (Stage 4) needs **two consecutive** clean rounds, each with fresh instances.

| Stage | Discriminators | Gate |
|---|---|---|
| 0 — Spec freeze | `pki-discriminator` on the written spec | 0 BLOCKER/MAJOR, every beat ACCURATE, pytest/ruff/mypy green; then the spec hash is frozen |
| 1 — Animatic | all three, after calibration | the standard gate |
| 2 — Vertical slice (S4) | all three | the standard gate; LOOK-BIBLE and RENDER-BUDGET frozen |
| 3 — Full production | all three | the standard gate |
| 4 — Final cut | all three, twice | two consecutive clean rounds |

## Caps and escalation

At most 5 rounds per stage. If a stage has not converged by then:
- the Chief of Staff writes an escalation record with the best candidate and its open findings
- open MINORs may be documented as known limitations
- open BLOCKERs or MAJORs never ship; the session stops and reports them

## Anti-gaming (anti-mode-collapse)

The generator may not win by removing difficulty:
- no deleting or merging beats
- no shrinking or shortening captions
- no moving content out of frame
- no cutting checks
- no dimming the scene to hide flaws

The generator aims at the frozen spec, not at the wording of the discriminator prompts. Discriminators never see the generator's reasoning. `docs/TRACEABILITY.md`, generated from the model, maps every ID to its scene, frames and tests. A hard test fails if any beat goes missing.

## Frozen-spec change control

`docs/REFERENCE-SPEC.md` is frozen at the end of Stage 0, and its SHA-256 is recorded in the ledger. After that, any change needs:
- a written Chief of Staff amendment in the ledger, with its reason
- the new hash
- a reset of the current stage's clean-round counter

The generator never edits the spec to make a finding go away.

## Calibration (before the first Stage 1 round)

`python -m tools calibrate <fault>` builds deliberately broken animatic variants:

| Fault | Expected catch |
|---|---|
| `private_key_leak` (the RDP private key rides inside the request capsule) | `pki-discriminator` BLOCKER; hard discriminators FAIL |
| `root_issues_leaf` (the request flies to the Root CA, which stamps the server certificate) | `pki-discriminator` BLOCKER; hard discriminators FAIL |
| `flowchart` (a static, top-down orthographic shot of flat boxes and lines) | `cinema-discriminator` BLOCKER/DIAGRAM |
| `caption_clip` (a 14 px caption outside the safe area) | `legibility-discriminator` BLOCKER; hard discriminators FAIL |

If anything misses its fault, the Chief of Staff strengthens that prompt or test and re-calibrates. Fault code paths are reachable only from `calibrate`, and a test confirms that normal builds never enable a fault. Results are recorded in the ledger.
