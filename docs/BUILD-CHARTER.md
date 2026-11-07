# Certificate-Flow-Film — BUILD CHARTER (Approach B: Blender film pipeline + adversarial review)

> **How to use this charter.**
> - This file is the authoritative project specification. It lives at `docs\BUILD-CHARTER.md`.
> - The project is built across nine separate sessions. `docs\SESSION-PROMPTS.md` gives each session's model, effort and phases.
> - In any session, execute **only** the phases that session assigns. Sections 2–3 (governance and operating rules) always apply.
> - Changes to this charter follow the same change control as the frozen spec (Section 2.2).

You are the **Chief of Staff** for a new project, **Certificate-Flow-Film**. You also act as director, 3D layout and animation lead, technical director (Blender Python), PKI technical architect, test engineer, documentation owner, Git maintainer and release manager.

## What this project is

This is **Approach B** of an A/B comparison.

**Approach A** is a separate project, `Certificate-Flow-Animation`, built with Remotion and React Three Fiber.
- Do **not** read, modify, or depend on its folder or repository.
- The PKI story, beats and duration are deliberately held the same as Approach A, so the two results can be compared fairly.
- What differs is the engine, the production process, the quality-control method and the lab names.

**Approach B** builds the film in three ways:
1. **Blender**, scripted entirely in Python (`bpy`), rendered headless. This gives physically based lighting, real depth of field, motion blur and volumetrics.
2. A **film-production pipeline**: spec → animatic → vertical slice → full production → final, with a quality gate at each stage.
3. A **GAN-style adversarial review loop**. The build session is the *generator*. Independent read-only subagents are *discriminators* that try to prove each candidate is inaccurate, diagram-like or unreadable. The generator iterates until the discriminators can no longer find blocking flaws.

Project location: `E:\ClaudeCode\Projects\Certificate-Flow-Film`

**Final output:** a 1920x1080, 30 FPS H.264/AAC MP4, **100–120 s** long (target 105–115 s). It must feel like one continuous film shot through a stylized 3D world, never a flowchart, slide deck or boxes-and-arrows diagram. It ships with:
- a public GitHub repository
- a GitHub Pages demo
- a v1.0.0 release

---

## 1. PROJECT VARIABLES

All names live in ONE pure-Python module, `cff/config/names.py`. Every scene, caption and document reads them from there.

Values shaped like `<<REPLACE: … | fallback: …>>` are placeholders the owner may fill in later. While a placeholder is unfilled:
- Use its **fallback**.
- **Never render placeholder text.**
- List every fallback in use under "Names in use" in `README.md` and `docs\PROJECT-STATE.md`.

| Variable | Value |
|---|---|
| `AD_DOMAIN_FQDN` | `1SN0S.LAB` (shown in this form on the Active Directory node) |
| `AD_NETBIOS` | `1SN0S` |
| `DNS_SUFFIX` | `1sn0s.lab`. DNS is case-insensitive (RFC 4343); SAN dNSNames are shown lower-case, as they normally appear in certificates. |
| `DC_HOSTNAME` | `<<REPLACE: domain controller hostname \| fallback: DC01>>` |
| `CLIENT_HOSTNAME` | `<<REPLACE: user laptop hostname \| fallback: CLIENT01>>` |
| `RDP_SERVER_HOSTNAME` | `<<REPLACE: RDP server hostname \| fallback: RDP01>>` |
| `WEB_SERVER_HOSTNAME` | `<<REPLACE: web server hostname \| fallback: WEB01>>` |
| `WEB_SITE_DNS_NAME` | `<<REPLACE: website DNS name in the TLS certificate SAN \| fallback: portal.1sn0s.lab>>` |
| `ROOT_CA_NAME` | `<<REPLACE: Root CA common name \| fallback: 1SN0S Root CA>>` |
| `ISSUING_CA1_NAME` | `<<REPLACE: Issuing CA 1 common name \| fallback: 1SN0S Issuing CA 1>>` |
| `ISSUING_CA2_NAME` | `<<REPLACE: Issuing CA 2 common name \| fallback: 1SN0S Issuing CA 2>>` |
| `PKI_HTTP_HOST` | `<<REPLACE: host serving AIA/CDP over HTTP \| fallback: pki.1sn0s.lab>>` |
| `RDP_TEMPLATE` | `RDPAuth` |
| `WEB_TEMPLATE` | `WebServer-TLS` |
| `GITHUB_OWNER` | The account authenticated in GitHub CLI (expected `SimSI2027`). Verify it; if it differs, use the authenticated account and report this. |
| `REPO_NAME` | `Certificate-Flow-Film` (fallback if taken: `1SN0S-Certificate-Flow-Film`) |
| `RELATED_LINKS` | `https://github.com/SimSI2027/Certificate-Flow-Lab`, and the Approach A repository `https://github.com/<GITHUB_OWNER>/Certificate-Flow-Animation` if it exists. Verify each with `gh`. Link only those verified, plus their Pages URLs if `gh api repos/<owner>/<repo>/pages` returns one. |

Derived values (compute, never hard-code):
- `RDP_SERVER_FQDN` = lower-case(`RDP_SERVER_HOSTNAME`) + `.` + `DNS_SUFFIX`
- the same pattern for the other hosts.

**Docs note.** `.lab` is a private suffix for this lab. Before writing the docs, check its current status in the IANA root zone database. Do not assume it.
- Record that private suffixes can collide if they are later delegated publicly.
- Record that ICANN has permanently reserved `.internal` for private use.
- Do not change the lab's names because of this.

---

## 2. GOVERNANCE: CHIEF OF STAFF + GAN-STYLE ADVERSARIAL LOOP

### 2.1 Roles

| GAN concept | Role in this project |
|---|---|
| **Generator** | This main session. It writes the Python, builds scenes and renders candidates. |
| **Discriminators** | Three read-only subagents (2.3) and the automated "hard discriminators" (Section 12). They try to show that a candidate deviates from the reference spec. |
| **Real-data distribution** | The **frozen reference spec** (2.2). Discriminators judge against it, never against their own taste or the generator's claims. |
| **Loss** | The weighted findings and scores from each round. A BLOCKER counts as infinite loss. |
| **Training round** | One candidate → independent judgement → triage → fixes. |
| **Arbiter / trainer** | The Chief of Staff. Owns the spec, runs rounds, resolves disputes, decides gates. |

### 2.2 Frozen reference spec (written before any production rendering)

`docs\REFERENCE-SPEC.md` contains:
- the PKI facts **F-01…F-17** (Section 6)
- the beat list **B-xx** (Section 7)
- the cinematic criteria **C-01…C-11** (2.6)
- the legibility criteria **L-01…L-08** (2.6)
- the glossary (`docs\GLOSSARY.md`)

At the end of Stage 0, record its SHA-256 in `docs\GAN-LEDGER.md`.

**Change control after the freeze:**
- Any change needs a written amendment from the Chief of Staff, giving the reason, in the ledger.
- The new hash is recorded.
- The current stage's clean-round counter resets to zero.

The generator may never edit the spec to make a finding go away.

### 2.3 Discriminator subagents

Create these three files in `.claude\agents\`. Verify that Claude Code lists them in `/agents`, starting a fresh session if needed.

All three:
- have `tools: Read, Glob, Grep` (read-only; they cannot edit or render)
- use the model set in their own file: **pki-discriminator on `opus`** (accuracy is critical), and **cinema-discriminator and legibility-discriminator on `sonnet`** (to conserve usage)
- return a JSON report as their final message
- are spawned as **fresh instances** every round, so they don't anchor on earlier rounds

**`pki-discriminator.md`**
```
---
name: pki-discriminator
description: Adversarial PKI accuracy judge for Certificate-Flow-Film. Use only when the Chief of Staff runs a discriminator round. Read-only.
tools: Read, Glob, Grep
model: opus
---
You are an adversarial ADCS/PKI reviewer. Your goal is to prove the candidate misrepresents PKI.
Read ONLY the round packet folder you are given and the frozen files it lists
(docs/REFERENCE-SPEC.md, docs/GLOSSARY.md, docs/PKI-TECHNICAL-NOTES.md). Reading anything else is a protocol violation.
List every file you read in "files_read".
View every frame image in the packet. For each beat, judge ACCURATE / MISLEADING / WRONG against facts F-01..F-17,
citing frame files. Hunt especially for: a private key moving or leaving its owner; a request reaching the Root CA;
the Root CA issuing an end-entity certificate or appearing online; an issuing CA or AIA presented as the trust anchor;
a request sent to a CA that does not publish its template; chain building presented as proof of identity;
revocation shown for the root itself; wrong EKU; wrong terminology.
Also re-check every finding listed in the packet's regressions.json and report FIXED or REGRESSED.
Output only the JSON report defined in the packet's schema.json.
```

**`cinema-discriminator.md`**
```
---
name: cinema-discriminator
description: Adversarial film-quality judge for Certificate-Flow-Film. Decides per shot whether it reads as FILM or DIAGRAM. Read-only.
tools: Read, Glob, Grep
model: sonnet
---
You are a demanding animation director. Your goal is to prove the candidate looks like a diagram, slide deck or template
rather than a film. Read ONLY the round packet and docs/REFERENCE-SPEC.md (criteria C-01..C-11) and docs/LOOK-BIBLE.md
if the packet lists it. View every frame and every motion strip (tiled consecutive frames).
For each shot give a verdict FILM or DIAGRAM with reasons. Hunt for: arrows or connector-line diagram grammar,
static or flat cameras, hard cuts, missing focal subject, flat lighting, opacity-only entrances, pops or jitter visible in strips,
broken continuity between scenes, excessive glow, particles or haze, grid-of-cards layouts, inconsistent colour language.
Score each criterion 0-10. Re-check regressions.json. Output only the JSON report defined in schema.json.
```

**`legibility-discriminator.md`**
```
---
name: legibility-discriminator
description: Adversarial readability and accessibility judge for Certificate-Flow-Film. Read-only.
tools: Read, Glob, Grep
model: sonnet
---
You are an accessibility and broadcast-QC reviewer. Your goal is to prove viewers cannot read or follow the film.
Read ONLY the round packet and docs/REFERENCE-SPEC.md (criteria L-01..L-08) and docs/GLOSSARY.md.
Use the packet's manifest.json (caption text, on-screen start/end times, measured text bounds, sampled contrast ratios,
palette check results) together with the frames. Hunt for: text too small, low contrast, text outside title-safe,
captions shown too briefly for their word count, captions overlapping the focal action, unreadable in-world labels that matter,
colours that are hard to distinguish (including the colour-vision-deficiency results), terminology that contradicts the glossary.
Score each criterion 0-10. Re-check regressions.json. Output only the JSON report defined in schema.json.
```

### 2.4 Round protocol

1. **Generator builds a candidate** for the current stage and commits it locally (the commit hash is the candidate ID).
2. **Packet.** `python -m tools packet <stage>` assembles `qa\rounds\<stage>-R<n>\` containing:
   - the frames
   - motion strips (tiled frames sampled every 3rd frame across every transition and camera move)
   - `manifest.json` (frame ↔ beat ID ↔ timestamp; caption timings; measured text bounds; contrast samples; palette results)
   - `regressions.json` (all previously accepted findings)
   - `schema.json`
   - the list of frozen files
   
   The packet must contain **no** source code, commit messages, generator notes or claims of success.
3. **Judgement.** Spawn the three discriminators as fresh instances, in parallel, each pointed only at the packet path. Save each JSON reply verbatim to the packet folder.
4. **Hard discriminators.** Run `python -m tools verify` (Section 12) on the same candidate.
5. **Triage by the Chief of Staff.** Every finding is either:
   - **ACCEPTED** (it will be fixed), or
   - **REJECTED-INVALID**, which needs a written citation showing the finding misreads the frozen spec.
   
   Rejecting a PKI BLOCKER also needs a second, fresh `pki-discriminator` to concur. Severity may not be downgraded without written justification.
6. **Generator fixes** all accepted findings.
7. **Learned → hard.** Every accepted BLOCKER/MAJOR that can be expressed geometrically, temporally or textually becomes a permanent automated test named after its finding ID.
8. **Ledger.** Append the round to `docs\GAN-LEDGER.md`:
   - candidate commit, spec hash
   - counts per severity, scores per criterion
   - accepted and rejected findings with reasons
   - new hard tests added
   - the gate decision
9. **Next round.**

### 2.5 Findings schema (`schema.json`)

```
{ "discriminator": "", "round": "", "spec_sha256": "",
  "verdicts": [ { "beat": "B-04.2", "frames": [""], "verdict": "ACCURATE|MISLEADING|WRONG|FILM|DIAGRAM", "reason": "" } ],
  "findings": [ { "id": "", "severity": "BLOCKER|MAJOR|MINOR", "criterion": "F-xx|C-xx|L-xx",
                  "beat": "", "frames": [""], "evidence": "what is visible", "why": "", "direction": "what would fix it, not how to code it" } ],
  "scores": { "C-01": 0 },
  "regressions_checked": [ { "finding": "", "status": "FIXED|REGRESSED" } ],
  "files_read": [""] }
```

**Severities:**
- **BLOCKER** — any of:
  - wrong PKI
  - a violation involving a private key or the Root CA
  - a blank or broken frame
  - an unreadable required caption
  - a shot judged DIAGRAM in Stage 4 or later
- **MAJOR** — any of:
  - misleading PKI
  - weak film quality
  - readability problems
  - broken continuity
- **MINOR** — polish.

### 2.6 Criteria (copy into REFERENCE-SPEC.md and expand with measurable thresholds)

**Cinematic:**
- **C-01** No arrows or connector-diagram grammar. Relationships are shown by motion, docking, light and the camera.
- **C-02** One continuous camera. No hard cuts, except the motivated flashback in S5.
- **C-03** Every shot has one clear focal subject, established with depth of field, light and composition.
- **C-04** Depth: foreground, midground and background layers with parallax.
- **C-05** Motivated key/rim lighting. No flat, ambient-only lighting.
- **C-06** Eased motion. No pops or jitter. Exits are slightly faster than entrances.
- **C-07** Object continuity across scenes.
- **C-08** Restraint in glow, haze and particles.
- **C-09** Never template-like or slide-like.
- **C-10** Consistent colour language (Section 8).
- **C-11** Shape vocabulary that stays distinct even in greyscale.

**Legibility:**
- **L-01** Caption cap height ≥ 30 px at 1080p. In-world labels that must be read: ≥ 18 px cap height when on screen.
- **L-02** Contrast ≥ 4.5:1 against the sampled local background.
- **L-03** All text inside the 90% title-safe area.
- **L-04** Each caption stays on screen for ≥ max(2.5 s, 0.35 s per word).
- **L-05** One caption at a time, never covering the focal action.
- **L-06** In-world names (hosts, templates, CAs) are readable at the moment they matter.
- **L-07** Key colours are distinguishable (CIEDE2000 ΔE ≥ 15 between role colours), including under simulated deuteranopia and protanopia.
- **L-08** Terminology matches the glossary.

### 2.7 Convergence, caps and anti-gaming

**Gates:**
- A stage gate passes when the latest round has:
  - **0 BLOCKER and 0 MAJOR**
  - every MINOR either fixed or recorded as a justified won't-fix
  - all cinematic and legibility scores ≥ 8
  - every PKI beat ACCURATE
  - all hard discriminators green
- The **final-cut gate** (Stage 4) needs **two consecutive clean rounds**, each with fresh discriminator instances.

**Round cap:** 5 rounds per stage. If the stage has not converged by then:
- The Chief of Staff writes an escalation record with the best candidate and its open findings.
- Open MINORs may be documented as known limitations.
- Open BLOCKERs or MAJORs may **never** ship. Stop and report them to the user.

**Anti-mode-collapse.** The generator must not win by removing difficulty. That rules out:
- deleting or merging beats
- shrinking or shortening captions
- moving content out of frame
- cutting checks
- dimming the scene to hide flaws

`docs\TRACEABILITY.md`, generated from the story model, maps every F, B, C and L ID to its scene, frames and tests. A hard test fails if any beat is missing from the render or from the packet.

**Independence:**
- Discriminators never see the generator's reasoning.
- The generator aims at the frozen spec, not at the wording of the discriminator prompts.

### 2.8 Discriminator calibration ("pre-training") — before the first real round

Implement `python -m tools calibrate <fault>`. It builds deliberately broken variants of the animatic:

| Fault | What it does |
|---|---|
| `private_key_leak` | The RDP private key rides inside the request capsule. |
| `root_issues_leaf` | The request flies to the Root CA and the root stamps the server certificate. |
| `flowchart` | A static, top-down, orthographic shot of flat boxes joined by lines. |
| `caption_clip` | A caption extends outside the safe area at 14 px. |

**Requirements:**
- Each discriminator must flag its relevant faults as BLOCKER.
- The hard discriminators must **fail** on `private_key_leak`, `root_issues_leaf` and `caption_clip`. This is mutation testing of the test suite.
- If anything misses a fault, strengthen that discriminator's prompt or test and re-calibrate.
- Calibration code paths only run under the explicit `calibrate` command. Tests confirm that normal builds never enable a fault.

Record the results in `docs\GAN-LEDGER.md`.

### 2.9 Chief of Staff approvals

For each phase, record the following in `docs\CHIEF-OF-STAFF-APPROVALS.md`:
- phase, scope, acceptance criteria
- review performed
- problems found and corrections made
- tests run, with real results
- ledger round references
- commit hash and sync result
- decision (APPROVED/REJECTED) and timestamp

Never approve a first attempt automatically.

Never approve or claim any of the following:
- placeholders or major TODOs
- unrendered or uninspected output
- broken builds
- fake results
- invented URLs, pushes or deployments
- unsynchronized GitHub state

---

## 3. OPERATING RULES

1. Inspect the directory first. Preserve legitimate existing work. Never touch the Approach A project.
2. Windows + PowerShell. Use PowerShell-compatible commands. Put automation in Python modules under `tools\` and `scripts\`, not in shell one-liners.
3. Source edits use the Edit/Write tools only.
   - No Bash heredocs.
   - No `sed`.
   - No Python one-liners.
   - No PowerShell `-replace` on source files.
4. Do not ask routine questions. Make defensible decisions and record them.
5. Stop and ask the user only for:
   - credentials or authentication
   - elevation you cannot perform
   - destructive operations
   - an unrecoverable blocker
   
   Give the exact single command needed, then resume.
6. Never force-push. Never rewrite public history.
7. **Long renders.**
   - Render in background chunks (for example 300 frames per chunk).
   - Set `scene.render.use_overwrite = False` and `scene.render.use_placeholder = True`, so an interrupted render resumes by skipping frames that are already done.
   - Poll progress and record it in `PROJECT-STATE.md`.
   - Never rely on one command running longer than the tool's time limit.
8. **Session continuity.** Keep `docs\PROJECT-STATE.md` accurate enough that a brand-new session can resume from it alone. If the conversation context is getting long:
   - finish the current atomic step
   - update `PROJECT-STATE.md` with the exact next action
   - commit and push
   - record the current session number, model, effort and remaining steps
   - tell the user to start a new session on that same model and effort, using the Resume prompt in `docs\SESSION-PROMPTS.md`
   
   `CLAUDE.md` must contain the same instruction.
9. Do not reduce PKI accuracy to simplify the film. Do not add complexity beyond the story.
10. Install no unvetted third-party Claude skills or Blender add-ons. Use Blender's official Python API documentation for the **exact installed version** (`https://docs.blender.org/api/<major.minor>/`) and the official release notes.

---

## 4. PRODUCTION PIPELINE (stage gates)

| Phase | Stage | Output | Gate |
|---|---|---|---|
| 1 | Environment | Toolchain verified and pinned | Chief of Staff checklist |
| 2 | Repository | Public repository bootstrapped and synchronized | Sync verified |
| 3 | **Stage 0 — Spec freeze** | REFERENCE-SPEC, GLOSSARY, PKI notes, storyboard, story model with pytest, TRACEABILITY | `pki-discriminator` reviews the **written** spec (cheapest place to catch errors); spec hash frozen |
| 4 | **Stage 1 — Animatic** | Grey-box geometry, final camera blocking, final timing, captions in place; fast 960x540 renders | Calibration (2.8), then GAN rounds until clean |
| 5 | **Stage 2 — Vertical slice** | S4 (CA evaluation and signing) at **final look**: materials, lighting, depth of field, motion blur, bloom, haze, audio cues | GAN rounds until clean. Freeze `docs\LOOK-BIBLE.md` (approved reference frames) and `docs\RENDER-BUDGET.md` |
| 6 | **Stage 3 — Full production** | All scenes at final look, rendered at preview quality | GAN rounds until clean |
| 7 | **Stage 4 — Final cut** | Final-quality render, caption layer, audio master, encode | **Two consecutive** clean GAN rounds |
| 8 | Docs + Pages | Documentation complete; live demo | Chief of Staff checklist; live site verified |
| 9 | Release + audit | v1.0.0 tag and release; final audit | All items PASS |

After every approved phase:
1. Commit related changes only.
2. Push to `origin/main`.
3. Verify that local HEAD equals the remote HEAD (`python -m tools sync-check`).
4. Update and push `PROJECT-STATE.md`.

Do not accumulate the whole project into one commit.

**Session plan.** The phases run across nine sessions, each with its own prompt in `docs\SESSION-PROMPTS.md`:

| Session | Work |
|---|---|
| 1 | Environment + Repository (Phases 1–2) |
| 2 | Spec freeze (Phase 3) |
| 3 | Pipeline foundation + animatic build (Phase 4, build part) |
| 4 | Calibration + animatic rounds (Phase 4, gate) |
| 5 | Vertical slice (Phase 5) |
| 6 | Full production (Phase 6) |
| 7 | Final cut (Phase 7) |
| 8 | Docs + Pages + release candidate (Phase 8) |
| 9 | Final audit + release (Phase 9) |

Each session:
- starts by checking that the previous session's phases are APPROVED
- keeps the current session number, model, effort and remaining steps in `PROJECT-STATE.md`
- ends by setting `Next session` in `PROJECT-STATE.md`

---

## 5. ENVIRONMENT, TOOLCHAIN AND REPOSITORY (Phases 1–2)

### 5.1 Inspect and record (in `docs\TOOLCHAIN.md` and `PROJECT-STATE.md`)

- Current directory and its contents
- Git, GitHub CLI (with authentication status and account), FFmpeg and FFprobe (with available encoders: `libx264`, `aac`)
- Python 3 (3.12 or later) and free disk space (estimate frame storage needs: about 3,300 PNG frames per full-length pass)
- GPU model and driver
- Claude Code project agent and skill directories

### 5.2 Blender

- Use the **Blender 5.2 LTS** line for reproducibility.
- Install with `winget install -e --id BlenderFoundation.Blender`. Check the version winget offers. If it is not 5.2.x, find the correct LTS package ID or version with `winget search Blender` or `winget show`, and pin a 5.2.x release.
- Record the exact version and `blender.exe` path in `config\toolchain.local.json` (gitignored), and read it from there.
- Quote paths containing spaces.

Every Blender invocation uses this form:
`"<blender.exe>" -b [file.blend] --factory-startup --python-exit-code 1 -P <script.py> -- <args>`

Script errors must fail the process. `--factory-startup` ignores user preferences and add-ons.

**Blender 5.x API rules.** Verify each of these against the installed version's docs. Prefer detecting capabilities over checking version numbers.
- Video Sequence Editor collections are `strips` / `strips_all`, not `sequences`.
- The compositor tree is `scene.compositing_node_group` (a standalone `CompositorNodeTree` ID). `scene.node_tree` is gone, and the group output replaces the old Composite node.
- Animation uses **slotted actions**: access F-curves through the channelbag API, not legacy `action.fcurves`. Use `keyframe_insert` for keys.
- The EEVEE engine identifier changed between versions: detect it from the available render-engine enum rather than hard-coding it.
- Do **not** use Blender's internal FFmpeg output. Render PNG sequences and encode with the FFmpeg CLI (Section 11).

**GPU probe.** Render one test frame headless with EEVEE and check that it is not blank.
- If EEVEE cannot render headless, fall back to Cycles on the GPU (OptiX/CUDA/HIP as available), with a fixed seed and denoising.
- Record the decision and the backend.

### 5.3 Python tooling

- Create a virtual environment `.venv`.
- `requirements-dev.txt` pins `pytest`, `ruff` and `mypy`.
- The pure-Python package `cff\` must never import `bpy`, so it can be tested with system Python.
- Blender-side code lives in `blender\` and imports `cff`.

### 5.4 Repository bootstrap (early)

1. Run `git init` with default branch `main`.
2. Add `.gitignore`. It must ignore:
   - `.venv`
   - `renders\`, `qa\rounds\**\frames`
   - generated `.blend` files
   - `output\*.mp4`
   - `config\toolchain.local.json`
   - `.env*`
3. **Licensing.** Code is **GPL-3.0-or-later**, because scripts that import `bpy` should be GPL-compatible; this removes any ambiguity. The rendered film and images are **CC BY 4.0**. Put both in `LICENSE` and `LICENSES\`, and explain the split in the README.
4. Bundle one OFL-licensed UI font (for example Inter) from its official upstream release, together with its OFL text. No font downloads at render time.
5. Scan for secrets before the first push.
6. Create the **public** repository with `gh repo create`, using `REPO_NAME` (with its fallback if taken).
7. Set a description and these topics: blender, bpy, python, pki, adcs, certificates, certificate-authority, rdp, tls, animation, motion-graphics, 3d.
8. Push.
9. Verify all of the following:
   - the repository is public
   - `origin` is correct
   - tracking is set up
   - local HEAD equals the remote HEAD
10. Record the URLs in `README.md` and `PROJECT-STATE.md`.

---

## 6. PKI REFERENCE MODEL (facts F-01…F-17 — the film must never contradict them)

**Architecture:**
- **`ROOT_CA_NAME`** — an offline, standalone, non-domain-joined Root CA. It has a self-signed certificate and is the **trust anchor**. It signs only the issuing CA certificates (in an offline ceremony during setup) and its own CRL (published periodically). It has no live network connection.
- **`ISSUING_CA1_NAME`** and **`ISSUING_CA2_NAME`** — enterprise subordinate (intermediate) issuing CAs. Their CA certificates are signed by the Root and have Basic Constraints CA=true. They are not trust anchors.
  - `RDPAuth` is published only on Issuing CA 1.
  - `WebServer-TLS` is published only on Issuing CA 2.
- **Active Directory `1SN0S.LAB` (`DC_HOSTNAME`)**:
  - authenticates requesters (Kerberos, computer accounts)
  - stores templates and their permissions
  - stores the Enrollment Services objects that list which CA publishes which template
  - distributes the root certificate to domain members' Trusted Root store (via AD publication or Group Policy)
- **AIA and CDP** are HTTP locations on `PKI_HTTP_HOST`, embedded as extensions in the issued certificates:
  - AIA gives the issuer certificate's location.
  - CDP gives the CRL location.
  - OCSP appears only as "if an Online Responder is deployed".

**Facts:**
- **F-01** The user initiates RDP. The **RDP server** owns and presents the RDP certificate.
- **F-02** Out of the box, RDP uses a **self-signed** certificate the client cannot verify. That is the problem being solved.
- **F-03** Each server generates its key pair locally. **Private keys never leave their owner.** CA private keys never leave their CA either.
- **F-04** A request (PKCS#10, inside CMC for ADCS) contains the public key and request information. It is **signed with the requester's private key** (proof of possession). It never contains the private key.
- **F-05** For RDP, enrollment is triggered by policy (Group Policy's RDP server authentication certificate template setting). The enrollment client **discovers eligible CAs from AD before sending**. It never sends to a CA that does not publish the template, and it never picks a CA arbitrarily.
- **F-06** Before signing, the issuing CA:
  - **authenticates the requester**
  - confirms the **template is published on this CA**
  - confirms **Enroll permission** (on the template, plus Request Certificates on the CA)
  - confirms the **request satisfies the template's policy**
  
  Arriving at a CA is never sufficient.
- **F-07** Subject and identity:
  - RDPAuth **builds the subject and SAN from AD** (the computer object's DNS name).
  - WebServer-TLS is based on Web Server, so the **subject is supplied in the request**. Because of that, Enroll permission is restricted to authorized web-server accounts.
- **F-08** RDPAuth uses the **Remote Desktop Authentication EKU (1.3.6.1.4.1.311.54.1.2)**. RDP also accepts Server Authentication (1.3.6.1.5.5.7.3.1); document both. WebServer-TLS uses **Server Authentication**.
- **F-09** The issued certificate goes into the computer's Personal store (LocalMachine\My), associated with the existing private key, which never moves. (Docs only: the Remote Desktop service needs read access to that private key.)
- **F-10** During the TLS handshake, the server sends its certificate, normally together with the issuing CA certificate. It also **proves possession of the private key** by signing as part of the handshake. A certificate alone proves nothing.
- **F-11** The client builds the chain upward to a root **already present** in its Trusted Root store.
  - If the intermediate certificate is missing, **AIA may fetch it. AIA never creates trust.**
  - Building a chain does not prove identity.
- **F-12** Validation is a set of distinct checks:
  - the chain terminates at a trusted root
  - each signature verifies with its issuer's public key
  - each certificate is within its validity period
  - Basic Constraints are correct
  - unknown critical extensions cause rejection
  - **the name matches the SAN dNSName** (identity — a separate check)
  - the **EKU** permits the purpose
  - **revocation** is acceptable
- **F-13** **Revocation is checked for each link:**
  - the end-entity certificate against the issuing CA's CRL (via CDP)
  - the issuing CA certificate against the Root's CRL
  - the root is not revocation-checked
  
  CDP/CRL is the ADCS default; OCSP is optional.
- **F-14** Different templates can be issued by different eligible issuing CAs.
- **F-15** Both issuing paths terminate at the same Root CA.
- **F-16** **Kerberos scope (docs, not on screen):** a domain-joined client connecting by FQDN with NLA can authenticate the server through Kerberos, and may then not warn even about a self-signed certificate. The film depicts **certificate-based server authentication**, for example where Kerberos server authentication is unavailable or policy requires a trusted certificate.
- **F-17** Terminology:
  - "end-entity certificate", never "sub certificate"
  - "subordinate/intermediate issuing CA"
  - "trust anchor" for the root only

**Single source of truth.** `cff\story\model.py` encodes as typed data:
- actors and their bounds roles
- keys and their owners
- certificates (issuer, subject/SAN, EKU, Basic Constraints)
- templates and the CAs that publish them
- beats (with IDs)
- events `{id, beat, type, object, from, to, start_s, end_s}`

Scenes, captions, audio cues, manifests and TRACEABILITY are all generated from it. Write the full technical meaning of every beat in `docs\PKI-TECHNICAL-NOTES.md`, including the full explanation behind any shortened on-screen wording.

---

## 7. STORYBOARD (same beats as Approach A; target ≈109 s; one continuous camera)

Timings are named constants in seconds, converted to frames via FPS in `cff\story\timing.py`. Captions follow L-04. Beat IDs are stable. `docs\STORYBOARD.md` expands each beat with shot description, lens, camera move, focal subject and caption.

**S1 — The connection begins (7 s)**
- **B-01.1** A night-lit desk; the stylized low-poly user at `CLIENT_HOSTNAME` opens RDP.
- **B-01.2** An amber connection pulse travels along a floor light-channel toward a distant rack; the camera follows it.
- Caption: *Secure RDP connection*

**S2 — An identity the client can't verify (7 s)**
- **B-02.1** Arrive at `RDP_SERVER_FQDN`; the RDP listener lights up.
- **B-02.2** A pale, unsealed self-signed card at the listener; the client side shows it as unverified. The connection stays amber; nothing has been accepted.
- **B-02.3** An `RDPAuth` template badge drops in from policy.
- Caption: *The RDP server needs a trusted identity*

**S3 — Keys born locally, request sealed (10 s)**
- **B-03.1** A key pair forms inside the server chassis.
- **B-03.2** The private key (distinct shape, lock motif) settles into a locked key container, visibly anchored.
- **B-03.3** The public key and request information enter a glass request capsule.
- **B-03.4** A beam from the private key **seals** the capsule (proof of possession); the key does not move.
- Captions: *The private key stays on the server* → *The request is signed, not the key sent*

**S4 — Finding the right CA, then evaluation (14 s)** (the vertical slice)
- **B-04.1** The capsule pauses at the AD node (`1SN0S.LAB`); a lookup for "who publishes RDPAuth?" lights a route to Issuing CA 1 only.
- **B-04.2** The capsule travels into the Issuing CA 1 vault (cyan).
- **B-04.3** Four checks resolve with staggered ticks:
  1. Requester authenticated
  2. Template published on this CA
  3. Enroll permission granted
  4. Request meets template policy
- **B-04.4** The CA's own key stays in a sealed module and drives a signing press, which stamps a certificate card. The card shows the SAN `RDP_SERVER_FQDN`, the Remote Desktop Authentication EKU, a validity bar and small AIA/CDP ports.
- **B-04.5** The card returns and locks into the server **beside** the existing private key, forming one identity.
- Caption: *Issuing CA 1 verifies, then signs*

**S5 — The hierarchy and the trust anchor (12 s)**
- **B-05.1** The camera cranes up to a sealed gold vault on its own plinth, **with no cables**: `ROOT_CA_NAME`. Its self-signed seal closes on itself.
- **B-05.2** A desaturated flashback: Issuing CA 1's request is carried to the root on removable media, signed offline and carried back.
- **B-05.3** Back in the present: a gold-to-cyan link joins Issuing CA 1's certificate to the root. No end-entity request ever travels to the root.
- Captions: *The Root CA signs the issuing CA certificate* → *The Root CA is the trust anchor*

**S6 — Presentation and validation (20 s)**
- **B-06.1** The server presents its certificate together with Issuing CA 1's certificate. A key pulse shows proof of possession; the key does not move.
- **B-06.2** On the laptop side the cards dock upward: server certificate → Issuing CA 1 → a gold root **already** in the Trusted Root store, shown with a brief "installed earlier by policy" memory shimmer.
- **B-06.3** A small AIA indicator shows the "missing intermediate? fetch it" possibility, clearly not a trust source.
- **B-06.4** Staggered checks:
  1. Chain ends at a trusted root
  2. Signatures verify
  3. Currently valid
  4. Name matches `RDP_SERVER_FQDN`
  5. EKU permits RDP
  6. Revocation OK
- **B-06.5** During check 6, two amber CRL fetches from the CDP, one for each link. A small "OCSP if deployed" tag.
- **B-06.6** The channel turns from amber to green and the session window opens.
- Captions: *The client validates the whole chain* → *Trusted RDP connection established*

**S7 — A second workload (12 s)**
- **B-07.1** The camera glides to `WEB_SERVER_HOSTNAME` (serving `WEB_SITE_DNS_NAME`), with a `WebServer-TLS` badge.
- **B-07.2** A local key pair; the private key is locked and anchored; the request is sealed by proof of possession.
- **B-07.3** The AD lookup shows both CAs:
  - Issuing CA 1 dims to muted grey ("WebServer-TLS not published here").
  - Issuing CA 2 illuminates in violet.
  - Eligibility tags: template published, enrollment policy, permissions, CA available.
- **B-07.4** The capsule travels **only** to Issuing CA 2.
- Caption: *Different templates can use different issuing CAs*

**S8 — Issuing CA 2 signs (11 s)**
- **B-08.1** Faster, compressed checks, including the note "name supplied in request — enrollment restricted".
- **B-08.2** CA 2's key-driven press stamps the TLS certificate (SAN `WEB_SITE_DNS_NAME`, Server Authentication EKU). It returns and locks beside the web server's private key.
- **B-08.3** Reveal Issuing CA 2's own certificate, linked in gold to the **same** root.
- Caption: *Issuing CA 2 signs the TLS certificate*

**S9 — Full picture and close (16 s)**
- **B-09.1** A quick browser validation (about 5 s): `WEB_SITE_DNS_NAME` → Issuing CA 2 → Root, with compressed ticks (name, EKU, validity, revocation); the channel turns green.
- **B-09.2** A wide hero shot of the complete topology:
  - the Root on top
  - Issuing CA 1 and Issuing CA 2 below it
  - the RDP server under CA 1 and the web server under CA 2
  - the user consuming both services
  - two trust paths (cyan and violet) rising and converging in gold at the single root
- **B-09.3** Captions: *Different issuing paths. One trusted root.* → title card *Certificate Flow — From request to trust*. A gentle settle and fade, with a clean end.

---

## 8. LOOK AND WORLD (Blender)

- **World.** A stylized, low-to-mid-poly technical world built procedurally from primitives, modifiers, geometry nodes or materials, all in code:
  - a dark navy / near-black environment with a subtle floor grid
  - light-channel conduits in the floor
  - restrained volumetric haze
  - vignette
  - very restrained film grain
  
  "Windows-style" infrastructure must be generic. **No Microsoft, Windows or other vendor logos or trademarks.** No realistic humans: the user is a stylized low-poly figure. No external models, textures, HDRIs or footage.
- **Camera.**
  - One rig: a dolly/crane path with a "look-at" target and an animated focus target.
  - Real lens values (24–50 mm).
  - Depth of field with restrained f-stops, to guide focus.
  - Named shots in `cff\theme\shots.py`, connected by eased moves.
- **Rendering.**
  - EEVEE (engine detected at runtime), unless the GPU probe forced Cycles.
  - Motion blur in the final quality tier only, if the render budget allows.
  - Bloom via the compositor **Glare node in Bloom mode**.
  - Volumetric haze kept within budget.
- **Colour management.** AgX for the 3D beauty pass.
  - Verify the colour language survives AgX: render a palette test frame, run the L-07 ΔE check, and adjust material values rather than abandoning the palette.
  - The caption layer uses the Standard view transform, so text colours are exact.
- **Colour language** (central tokens in `cff\theme\palette.py`):
  - Root: warm gold
  - Issuing CA 1: cyan
  - Issuing CA 2: violet
  - requests: bright neutral white
  - validated paths: green
  - pending connection: amber
  - revocation checks: restrained amber
  - ineligible routes: muted grey
  - AD node: steel blue
- **Shape vocabulary** (C-11). Each of these must be distinct in silhouette:
  - request capsule
  - certificate card
  - public key
  - private key
  - key container
  - template badge
  - CA vault
  - root vault (on a plinth, cable-free)
  - trust link
  - network channel
  - validation tick
  - CRL scroll fetch
  - AIA indicator
- **In-world labels.** Blender text objects placed as physical signage (host plates, template badges, CA nameplates) using the bundled font. Orient them toward the camera when they matter (L-06).
- **Avoid:**
  - arrows
  - generic purple AI gradients
  - glass-card overload
  - fake terminals
  - constant particle noise
  - slide-like moves
  - opacity-only entrances
  - linear easing
  - excessive glow
  - misleading metaphors

---

## 9. CODE ARCHITECTURE

```
cff\                      pure Python, no bpy (tested with system Python + pytest + mypy)
  config\names.py         Section 1 variables, placeholder resolution
  story\model.py          actors, keys, certs, templates, beats, events (single source of truth)
  story\timing.py         seconds -> frames, named beat offsets
  story\captions.py       caption text, timing, word counts
  theme\palette.py        colours, materials parameters, glow levels
  theme\motion.py         named easing presets and durations (entrance/exit/idle), spring-like overshoot presets
  theme\shots.py          named camera shots and lenses
  audio\cues.py, synth.py cue sheet from events; deterministic WAV synthesis (stdlib only, seeded)
blender\                  bpy-dependent
  build_scene.py          builds the .blend from cff (entry point)
  actors\*.py             UserLaptop, RdpServer, WebServer, DirectoryNode, IssuingCaVault, RootCaVault,
                          RequestCapsule, CertificateCard, PublicKey, PrivateKey, KeyContainer, TemplateBadge,
                          TrustLink, NetworkChannel, SigningPress, ValidationTick, CrlFetch, AiaIndicator
  world.py, lighting.py, camera_rig.py, materials.py, compositor.py
  captions_scene.py       separate orthographic caption-layer scene, transparent film, Standard view transform
  calibration.py          fault injection, only reachable from `tools calibrate`
  checks\scene_checks.py  in-Blender hard discriminators (Section 12)
tools\__main__.py         CLI: env, verify, build, render, captions, audio, encode, packet, contact, calibrate,
                          palette, motion, sync-check, site, release-verify
tests\                    pytest (model, timing, captions, names, traceability, tooling)
.claude\agents\           the three discriminators
site\                     GitHub Pages demo
docs\, output\, qa\
```

**Rules:**
- No literal colours, easings, durations or frame numbers outside `cff\theme` and `cff\story\timing.py`. A test enforces this with a pattern scan of `blender\` for hex colours and numeric frame literals, with a documented allowlist.
- **Determinism:**
  - every random choice uses a seeded `random.Random(seed)`, with the seeds documented
  - no wall-clock or time-dependent logic
  - `--factory-startup` on every Blender call
- **Motion (C-06):**
  - Keyframes use Bézier interpolation with named easing presets from `cff\theme\motion.py`.
  - LINEAR interpolation only for whitelisted constant-speed effects (for example, conduit flow).
  - Entrances animate several properties (location, scale, emission).
  - Exits are slightly faster than entrances; consistent staggering.
  - Subtle idle micro-motion.
  - Key objects carry continuity into the next beat. The moving capsule or trust link leads the camera.

---

## 10. CAPTIONS, EDIT AND AUDIO

- **Beauty pass:** PNG frames to `renders\beauty\`.
- **Caption layer:**
  - A separate Blender scene with an orthographic camera and transparent film.
  - Captions are animated with the same motion presets: eased rise plus fade, one at a time.
  - Rendered as RGBA PNGs to `renders\captions\`.
  - Kept separate from the 3D scene so depth of field and motion blur never soften the text.
- **Composite:** the FFmpeg `overlay` filter (straight alpha) during encoding.
- **Captions file:** `captions.vtt` and `transcript.md` are generated from `cff\story\captions.py`.
- **Audio** (deterministic, local, no copyrighted music, no narration in v1):
  - `cff\audio\synth.py` generates each cue as a WAV from seeded parameters:
    - soft connection pulses
    - capsule whoosh
    - key-lock click
    - signing seal
    - validation ticks
    - low ambient bed
    - trust-resolve chord
    - final mark
  - The cue sheet derives from story events.
  - A Python-built FFmpeg filtergraph places each cue at its exact sample offset (`adelay`) and mixes them with the bed. Two-pass `loudnorm` brings the mix to about −16 LUFS integrated with true peak ≤ −1 dBTP.
  - Verify with `ebur128` and `astats` and record the numbers.
  - Leave structural room for narration later.
- Document all of this in `docs\AUDIO.md`.

---

## 11. RENDER TIERS, BUDGET AND OUTPUTS

**Tiers:**
- `animatic`: 960x540, low samples, no motion blur or volumetrics
- `preview`: 1280x720, reduced samples
- `final`: 1920x1080, full look

**Budget:**
- At Stage 2, measure seconds per frame at final settings on the vertical slice, and project the full render time in `docs\RENDER-BUDGET.md`.
- If the projection exceeds 8 hours, reduce cost in this order:
  1. volumetrics
  2. motion-blur steps
  3. samples
  
  Document each reduction and confirm with the cinema discriminator that the look still passes.

**Encode** (FFmpeg CLI):
- libx264, `-preset slow`, CRF around 16–18
- `yuv420p`, 30 FPS
- BT.709 conversion and tags (for example `scale=out_color_matrix=bt709:out_range=tv`, plus `-colorspace bt709 -color_primaries bt709 -color_trc bt709`)
- AAC 48 kHz
- `-movflags +faststart`

**Determinism test:** render the same frame twice and compare the two with FFmpeg `ssim`/`psnr`. Record the result; small GPU noise is acceptable within a documented tolerance.

**Outputs:**
- `output\Certificate-Flow-Film-Final.mp4`
- `output\Certificate-Flow-Film-Preview.mp4` (720p, ≤ about 25 MB, for Pages)
- `output\Certificate-Flow-Film-Poster.png` (from the hero shot)
- `output\Certificate-Flow-Film-Contact-Sheet.png` (FFmpeg `tile` filter, covering every beat)
- `output\render-metadata.json`:
  - FFprobe facts
  - Blender version and engine
  - commit hash
  - render times per tier
  - loudness numbers
  - names in use
  - spec hash
- `output\captions.vtt`, `output\transcript.md`

Do not commit the full MP4 (GitHub blocks files over 100 MB). Ship it as a release asset.

---

## 12. HARD DISCRIMINATORS (`python -m tools verify` — persistent; never delete useful tests)

**Pure Python (pytest, ruff, mypy):**
- Model integrity:
  - no private-key event has `to` ≠ owner
  - no request event targets the Root CA
  - the Root CA issues only the issuing CA certificates and its own CRL
  - Issuing CA 1 issues RDPAuth; Issuing CA 2 issues WebServer-TLS
  - each request goes only to a CA that publishes its template, and discovery precedes sending
  - each request is preceded by a proof-of-possession event
  - both issuing CA certificates chain to the same root
  - AIA is never a trust source
  - the identity check is a separate event from chain building
  - a revocation check exists for each non-root link
  - the RDP server presents the RDP certificate; the web server owns the WebServer-TLS key
- Timing:
  - total duration within 100–120 s
  - beats ordered, with no gaps or overlaps unless declared
  - no zero-length beats
  - captions satisfy L-04
- Names: every placeholder resolves; no placeholder text in any caption, label or document output.
- TRACEABILITY: every F/B/C/L ID has coverage. A missing beat fails.
- Theme and literal scan (Section 9).
- No network URLs in `cff\` or `blender\`, except in comments or metadata on the allowlist.
- Calibration code is unreachable from normal builds.

**In Blender (`blender\checks\scene_checks.py`, evaluated on every frame via the evaluated depsgraph):**
- **Key containment:** every private key's world-space bounds stay inside its owner's chassis bounds (with a small tolerance) on every frame. The same applies to CA keys.
- **Root isolation:**
  - no request capsule intersects the Root vault's bounds at any frame
  - no network-channel geometry connects to the root plinth
  - only trust-link geometry touches it
- **Route integrity:** request capsules never intersect the bounds of actors other than their source, the AD node and their destination CA.
- **Motion:**
  - camera per-frame velocity and jerk stay below thresholds, except at declared transitions
  - visible objects never jump more than a threshold distance in one frame (no pops)
  - no NaN or Infinity in any F-curve
  - keyframes are ordered
  - LINEAR interpolation only on whitelisted channels
- **Captions:**
  - projected text bounds stay inside the 90% title-safe area
  - cap height ≥ the L-01 threshold
  - one caption visible at a time
- **Frame range:** scene frame range and FPS match timing.

**Image and output checks:**
- palette ΔE, including CVD simulation (Machado et al. 2009 matrices, documented)
- sampled caption contrast
- blank-frame detection
- FFprobe validation: codec, dimensions, FPS, pixel format, colour tags, audio stream, sample rate, duration and size
- loudness and peaks

**Repository checks:**
- clean working tree
- local HEAD equals `origin/main`
- Pages is live and current (Section 14)

**Persistent `Tests\` documents:**
- `README.md`
- `PKI-Accuracy-Checklist.md`
- `Visual-QA-Checklist.md`
- `Render-Verification.md`
- `GitHub-Synchronization.md`
- `Release-Verification.md`

---

## 13. DOCUMENTATION

**`README.md`:**
- overview and what the film teaches
- the A/B context (link to Approach A only if verified)
- PKI architecture and scene summary
- stack: Blender version, Python, FFmpeg
- prerequisites
- install and setup
- all `tools` commands
- render tiers and budget
- the GAN review loop, briefly
- testing
- outputs
- licensing split (GPL-3.0-or-later code / CC BY 4.0 film)
- names in use and how to change them
- known limitations
- repository, demo and release URLs
- related links

**`CLAUDE.md`** must stay under about 120 lines, because it loads into every session. It points to `docs\BUILD-CHARTER.md` for detail, and must require:
- Windows/PowerShell compatibility
- the source-editing bans from Section 3
- the Blender invocation form and the 5.x API rules
- the story model as the source of truth
- named timing constants; central theme; no inline colours, easings or frame literals
- determinism
- persistent hard discriminators
- the GAN round protocol and its anti-gaming rules
- frozen-spec change control
- Chief of Staff approval
- commit, push and sync verification after each milestone
- Pages kept in sync with `main`
- no release without rendered, inspected, discriminator-cleared assets
- the session-continuity instruction

**`docs\`:**
- `ARCHITECTURE.md`
- `STORYBOARD.md`
- `PKI-TECHNICAL-NOTES.md`
- `GLOSSARY.md`
- `REFERENCE-SPEC.md`
- `TRACEABILITY.md`
- `GAN-FRAMEWORK.md` (how the loop works, with roles, schema, severities, gates and calibration)
- `GAN-LEDGER.md`
- `CHIEF-OF-STAFF-APPROVALS.md`
- `LOOK-BIBLE.md`
- `RENDER-BUDGET.md`
- `TOOLCHAIN.md`
- `AUDIO.md`
- `RENDER-QA.md` (frames and strips inspected, problems, fixes, limitations)
- `RELEASE-CHECKLIST.md`
- `PROJECT-STATE.md`, which always holds:
  - phase and stage, current round
  - last approved milestone
  - branch, local commit, remote commit
  - URLs
  - latest render and latest verify result
  - render progress
  - names in use
  - blockers, remaining work
  - exact next action

**Also:** `CHANGELOG.md`, `CONTRIBUTING.md`.

---

## 14. GITHUB PAGES DEMO

A lightweight static site in `site\`, deployed by a GitHub Actions Pages workflow (`actions/upload-pages-artifact` + `actions/deploy-pages`) on pushes to `main`. Set the Pages source to GitHub Actions through `gh api`. Use relative paths.

**Content:**
- title and short description
- the poster image
- the preview video, with controls, `poster`, no autoplay with sound, and the `captions.vtt` track
- a link to the full MP4 release asset
- summaries of the RDP path (RDPAuth → Issuing CA 1 → Root) and the TLS path (WebServer-TLS → Issuing CA 2 → Root), and the one-trusted-root point
- the transcript
- links to the repository, the PKI technical notes and the storyboard
- a short "How it was made: generator vs discriminators" note
- the verified related links

**Requirements:** responsive; accessible.

**Sync rule.** Any change to the film, poster, captions, technical text, links or version updates the site in the same milestone. After pushing:
1. Verify the Actions run succeeded.
2. Fetch the live URL and confirm it serves the new content.
3. Record the result in `PROJECT-STATE.md`.

---

## 15. RELEASE

1. Create the annotated tag `v1.0.0` on the audited commit.
2. Create the release with `gh release create v1.0.0` and complete release notes, including the spec hash, the GAN round summary and the Blender version.
3. Attach these assets:
   - Final MP4
   - Preview MP4
   - Poster
   - Contact sheet
   - `render-metadata.json`
   - `captions.vtt`
4. Download every asset back to a temporary folder and compare SHA-256 hashes with the inspected files in `output\`.

**Before release, confirm all of the following:**
- no secrets in the repository
- the repository is public
- README and docs links resolve
- Pages is live and current; the preview video plays
- the full MP4 downloads
- the tag points to the intended commit
- local equals remote
- the working tree is clean

---

## 16. FINAL CHIEF OF STAFF AUDIT

Check every item below and record PASS or FAIL with evidence. If any required item fails, the project is REJECTED. Fix everything that can be fixed, then re-audit.

- **Toolchain:**
  - versions pinned and documented
  - Blender invocations use the standard form
  - clean setup from `requirements-dev.txt` works
- **GAN loop:**
  - calibration passed
  - every stage converged within its caps
  - the final cut had two consecutive clean rounds with fresh instances
  - every accepted BLOCKER/MAJOR either has a hard test or a written reason it can't be automated
  - the spec hash matches, or every amendment is logged
  - the ledger is complete
- **Code:**
  - verify green (pytest, ruff, mypy, in-Blender checks)
  - no placeholders or major TODOs
  - no runtime network
  - theme, timing and names centralized
  - determinism recorded
- **Film:**
  - Final is 1920x1080, 30 FPS, 100–120 s, H.264 yuv420p with BT.709 tags + AAC 48 kHz
  - loudness on target, no clipping
  - frames, strips and transitions inspected
  - contact sheet, poster and metadata exist
- **PKI:** F-01…F-17 satisfied on screen and in the docs; every beat ACCURATE in the last two rounds.
- **Documentation:** complete and current.
- **Git and GitHub:**
  - public repository; correct `origin`; `main` is the default branch
  - local equals remote; clean tree
  - milestones were pushed
  - tag and release exist, with hash-verified assets
  - Pages is live and reflects `main`
  - links are correct

## 17. REPORTS

Every session except Session 9 ends with a session report of at most 10 lines: phases approved, commits pushed, sync result, open issues, next session.

At the end of Session 9, give the final report. Report concisely:
1. Chief of Staff decision.
2. Summary.
3. Paths: Final, Preview, Poster, Contact sheet, metadata.
4. Duration, resolution, FPS, video codec, audio codec, loudness, file size.
5. Blender version, render engine, render times per tier.
6. GAN summary: rounds per stage, findings by severity, what each discriminator caught, hard tests added, calibration results.
7. Automated test results.
8. Visual inspections performed.
9. PKI checks completed.
10. URLs: repository, Pages, release.
11. Tag, final local commit, final remote commit, and confirmation that they match.
12. Confirmation that Pages reflects `main`.
13. Paths to the approval record and the ledger.
14. Names in use, flagging which are fallbacks.
15. Remaining limitations, and anything that could not be tested.

Do not report completion because the scripts run. The project is complete only when the film is built, rendered, inspected, cleared by the discriminators, tested, PKI-approved, documented, published (repository, Pages and release) and given final approval.
