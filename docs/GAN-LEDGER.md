# GAN ledger

Every adversarial round is recorded here, in order (Charter 2.4 step 8). This file also records spec freezes, amendments and calibration results. Discriminator replies are saved verbatim in each round's packet folder under `qa/rounds/`.

## Stage 0 — Spec freeze

Only `pki-discriminator` runs at Stage 0, and it judges the written spec (no frames). Cinematic and legibility scores start at Stage 1. Changes made between Stage 0 rounds are pre-freeze drafting, not amendments: the spec is frozen only when this stage's gate passes.

### stage0-R1

- **Candidate:** `948d0c9869c0c8e8a92b07e5ee90d1d9f314573c`
- **Spec SHA-256 (candidate):** `cf5b596203deb0978544c52460d66afae35f3be73551ee0a92ecccc51b3bf2a7`
- **Packet:** `qa/rounds/stage0-R1/`
- **Discriminator report:** `qa/rounds/stage0-R1/pki-discriminator.json`. Saved as delivered in the agent's hand-back message: the agent's background transcript file was empty, so the hand-back was the only copy.
- **Discriminator:** fresh `pki-discriminator` (opus). It read only packet files, as its `files_read` shows.
- **Beat verdicts:**
  - 30 ACCURATE
  - 3 MISLEADING: B-05.2, B-06.1, B-06.6
  - 0 WRONG
- **Findings:** 0 BLOCKER, 2 MAJOR, 6 MINOR.
- **Scores:** L-08 = 9 (advisory; it is not a Stage 0 gate criterion).
- **Hard discriminators:** `pytest` 81 passed; `ruff check` clean; `mypy --strict` clean.

**Triage (Chief of Staff).** All 8 findings are ACCEPTED; none misreads the frozen-spec candidate. No severity was changed.

| Finding | Sev | Decision | Reason / fix |
|---|---|---|---|
| PKI-S0R1-01 | MAJOR | ACCEPTED | Correct: one TLS handshake presents one server Certificate message, and RDP enrollment is driven by server-side policy, not by the connection. Fixes: the S2 attempt now closes (`E-02.2c`); S6 opens with a new connection pulse (`E-06.1a`); spec, notes and storyboard state that enrollment is server-side and policy-driven, with no pending connection during it. Beats were neither deleted nor merged. |
| PKI-S0R1-02 | MAJOR | ACCEPTED | Correct: REQ-RDP had no end of life inside Issuing CA 1, so a white capsule leaving Issuing CA 1 for the root was ambiguous. Fixes: `REQUEST_CONSUMED` events at each destination (`E-04.4a`, `E-05.2c`, `E-08.2a`); the CA request carries a cyan CA=true band and the must-read tag `LBL-REQ-CA1` ("Issuing CA 1's own CA request"); it is sealed by Issuing CA 1's own key module. |
| PKI-S0R1-03 | MINOR | ACCEPTED | The root's seal is revealed by light as an existing property, with no key-module glow and no press motion in the present. |
| PKI-S0R1-04 | MINOR | ACCEPTED | A "handshake proof (signature impression)" shape was added to C-11 (14 shapes), with IoU ≤ 0.6 against both keys. The B-06.1 wording now says no key material travels. |
| PKI-S0R1-05 | MINOR | ACCEPTED | `E-06.2c` transport changed to `none` (era recall); the shimmer plays on the card in place. |
| PKI-S0R1-06 | MINOR | ACCEPTED | B-04.1's opening sentence was reworded to "pauses at the server's outbound port, framed with the AD node". This was done before the freeze, so no amendment is needed. |
| PKI-S0R1-07 | MINOR | ACCEPTED | The model's `CERT-RDP-SELF` SAN was set to empty; the notes say no SAN is modelled or shown. |
| PKI-S0R1-08 | MINOR | ACCEPTED | The notes (B-02.3, B-03.1) now say the template definition is read from the AD enrollment policy before key generation, and that B-04.1 is the CA-selection lookup. |

**Charter deviation, recorded.** Charter 7 words B-05.1 as "Its self-signed seal closes on itself". The spec keeps the closed-ring seal but reveals it statically (PKI-S0R1-03), because a present-tense closing animation would misrepresent the offline root (Charter 3.9: do not reduce PKI accuracy).

**New hard tests** (in `tests/test_gan_findings.py`; never delete):
- `test_PKI_S0R1_01_one_certificate_per_connection_attempt` (MAJOR)
- `test_PKI_S0R1_02_requests_end_at_their_destination_and_the_ca_request_is_labelled` (MAJOR)
- `test_PKI_S0R1_03_root_performs_no_operation_in_the_present`
- `test_PKI_S0R1_04_handshake_proof_is_not_key_material`
- `test_PKI_S0R1_05_trust_store_recall_does_not_travel`
- `test_PKI_S0R1_07_self_signed_certificate_contents_match_notes`

PKI-S0R1-06 is covered by the existing discovery and route test. PKI-S0R1-08 is documentation only.

Both MAJOR tests fail on the R1 candidate model (two leaf certificates in one CH-RDP attempt; no request consumption events), so they really discriminate.

**Regressions registry:** all 8 findings were added to `qa/regressions.json`.

**Gate decision: NOT PASSED** (2 MAJOR, 3 MISLEADING beats). Proceed to R2 with fixes.

### stage0-R2

- **Candidate:** `8b38d1c` (full hash in `qa/rounds/stage0-R2/manifest.json`)
- **Spec SHA-256 (candidate):** `6e9e1c368bc3a20a910dccb66b52e99aeac8465e33a53ec9e8e6ca367d430f7e`
- **Packet:** `qa/rounds/stage0-R2/`. The report `pki-discriminator.json` was saved as delivered in the hand-back.
- **Discriminator:** fresh `pki-discriminator` (opus). It read only packet files.
- **Beat verdicts:** 33 ACCURATE, 0 MISLEADING, 0 WRONG.
- **Findings:** 0 BLOCKER, 0 MAJOR, 9 MINOR.
- **Regressions:** all 8 R1 findings FIXED.
- **Hard discriminators:** `pytest` 87 passed; `ruff check` clean; `mypy --strict` clean.

**Triage (Chief of Staff).** All 9 MINORs are ACCEPTED.
- 01 (intermediate copy), 02 (causal ordering) and 03 (proof verification) are real model gaps.
- 04 is a request/certificate wording error that F-04 and L-08 forbid.
- 05 (CA 2 certificate reveal), 06 (Kerberos scope honesty) and 07 (browser revocation caveat) are valid accuracy refinements.
- 08 (OCSP host) and 09 (passive AIA kiosk) are valid.

The browser claim in 07 was checked against known behaviour: Chromium does not check revocation online by default, the `RequireOnlineRevocationChecksForLocalAnchors` policy exists, and Firefox does not use CDP CRLs. For 06, these notes do not claim a named Windows setting for "policy requires a trusted certificate"; the charter's F-16 text is kept, and the notes clarify it.

| Finding | Fix |
|---|---|
| PKI-S0R2-01 | `INTERMEDIATE_STORED` events `E-04.5c` and `E-08.2e`: each server receives its own copy of the issuing CA certificate with the enrollment response. Spec B-04.5/B-08.2, notes and storyboard updated. |
| PKI-S0R2-02 | B-09.1 retimed: presentation starts after the pulse arrives (0.6 s), and the revocation tick starts at 3.9 s, after both fetches (ending 3.8 and 3.9 s). |
| PKI-S0R2-03 | `HANDSHAKE_PROOF_VERIFIED` events `E-06.1f` and `E-09.1q`: the client matches the impression against the server card's public key, and the proof dissolves (end of life). |
| PKI-S0R2-04 | Reworded in spec B-05.2, the glossary "Offline root ceremony", the notes and the model summary: "the root issues and signs Issuing CA 1's CA certificate". |
| PKI-S0R2-05 | CERT-CA2 is present (dimmed) on Issuing CA 2's crown from B-07.3. B-08.3 is a reveal sweep. The root's module and press stay dark in B-08.3 and B-09.2 (spec constraint added). |
| PKI-S0R2-06 | The notes for B-02.2 and the F-16 section state that this lab would usually use Kerberos; "Unverified" means not PKI-validated; no named policy is claimed. |
| PKI-S0R2-07 | Browser revocation caveat added to the notes for B-09.1. |
| PKI-S0R2-08 | `SVC-OCSP.host` set to none; `LBL-OCSP` attached to the client chain (the revocation slot). |
| PKI-S0R2-09 | Storyboard B-06.3: the kiosk is only passively highlighted; nothing requests or answers. |

**New hard tests:**
- `test_PKI_S0R2_01_server_holds_the_intermediate_it_presents`
- `test_PKI_S0R2_02_presentation_and_revocation_follow_causal_order`
- `test_PKI_S0R2_03_handshake_proof_is_verified_with_the_certificate_key`
- `test_PKI_S0R2_08_undeployed_responder_has_no_host_and_its_tag_is_on_the_client`

**Gate decision.** R2 itself met the Stage 0 criteria (0 BLOCKER/MAJOR, every beat ACCURATE), but the MINOR fixes changed the spec text. The Chief of Staff requires a confirming round (R3) on the exact text to be frozen before recording the freeze hash.

### stage0-R3

- **Candidate:** `96d6bdb397b517a6d9c7d183008b0b5a00f60132`
- **Spec SHA-256 (candidate):** `7cf45afa01572b7e9d30a6fb376807fb10a4f6a693af41ffed1d96bce2686d23`
- **Packet:** `qa/rounds/stage0-R3/`. The report `pki-discriminator.json` was saved as delivered in the hand-back.
- **Discriminator:** fresh `pki-discriminator` (opus). It read only packet files.
- **Beat verdicts:** 33 ACCURATE, 0 MISLEADING, 0 WRONG.
- **Findings:** 0 BLOCKER, 0 MAJOR, 3 MINOR.
- **Regressions:** all 17 earlier findings (R1 and R2) FIXED.
- **Scores:** L-08 = 9 (advisory).
- **Hard discriminators:** `pytest` 91 passed; `ruff check` clean; `mypy --strict` clean.

**Triage (Chief of Staff).** All 3 MINORs are ACCEPTED. None of them changes `docs/REFERENCE-SPEC.md`, so the spec text R3 judged is exactly the text being frozen.

| Finding | Fix |
|---|---|
| PKI-S0R3-01 | Each server's intermediate is now its own model object: `CERT-CA1-COPY-RDP` and `CERT-CA2-COPY-WEB` (`copy_of`, `holder`, store `Intermediate Certification Authorities`). `INTERMEDIATE_STORED`, `PRESENT_CERT`, `CHAIN_LINK` and `CRL_FETCH` events and both chains reference the copies, so the crown originals never move (C-07). |
| PKI-S0R3-02 | Glossary "Standalone CA": "does not require AD and does not use certificate templates"; the lab's root is standalone and not domain-joined. |
| PKI-S0R3-03 | Notes for B-02.2: "no CA that chains to a trusted root vouches for it". |

**New hard tests:**
- `test_PKI_S0R3_01_servers_present_their_own_copy_and_crown_originals_never_move`
- `tests/test_spec_freeze.py::test_reference_spec_matches_latest_frozen_hash`. This makes the freeze enforceable: any spec edit without a recorded amendment fails.

After the fixes: `pytest` 93 passed, `ruff check` clean, `mypy --strict` clean, and `python -m tools traceability --check` current.

**Gate decision: PASSED.** The latest round has:
- 0 BLOCKER and 0 MAJOR
- every PKI beat ACCURATE (33/33)
- every MINOR fixed
- all hard discriminators green

Stage 0 converged in 3 of 5 rounds. The cinematic and legibility scores (≥ 8) are Stage 1+ criteria; no frames exist at Stage 0.

## Stage 0 freeze

- **Frozen REFERENCE-SPEC SHA-256:** `7cf45afa01572b7e9d30a6fb376807fb10a4f6a693af41ffed1d96bce2686d23`
- **Frozen at:** 2026-11-06, after stage0-R3. This is the same hash stage0-R3 judged.
- **Companion frozen files:** same change control; hashes recorded here for audit.
  - `docs/GLOSSARY.md`: `f8bf9613c99c53889f42aff220f9a8f27a1da0b6e24a23a979445646fd3f0346`
  - `docs/PKI-TECHNICAL-NOTES.md`: `fa2bad9bd8e974a21015b5d0d724052c6f65bda8d6187f318e7f53f83cbdfb12`

  Both include the R3 MINOR fixes applied after the round, exactly as the discriminator directed.
- **Line endings** are pinned to LF by `.gitattributes`, so these hashes hold on every checkout.
- **Clean-round counter for Stage 1:** 0.
- **Amendments:** none yet. Any future change follows Charter 2.2: a written Chief of Staff amendment here, a new "Frozen REFERENCE-SPEC SHA-256" line, and a reset of the stage's clean-round counter.

## Stage 1 — Discriminator calibration (Charter 2.8), Session 4

`python -m tools calibrate <fault>` builds a deliberately broken animatic with `blender/calibration.py` (build hooks that the normal entry point never sets; every scene is tagged `cff_fault`), runs the in-Blender hard discriminators on it, and with `--packet` builds a blind packet `qa/calibration/stage1-K<n>`. The packet is identical in form to a round packet, and it carries no fault name. Results and the packet-to-fault mapping are in `qa/calibration/results.json`; each discriminator reply is saved verbatim in its packet folder. Spec hash for every packet: `7cf45afa…6d23` (unchanged).

| Fault | What the variant does |
|---|---|
| `private_key_leak` | After B-03.3 the RDP private key leaves its locked container, rides with the request capsule, and is left at Issuing CA 1's press when the capsule is consumed. |
| `root_issues_leaf` | The root complex rises early (during B-04.1); the RDP request flies to the root's press; the root's module lights and its press stamps CERT-RDP, which then travels back; Issuing CA 1's press stays still. |
| `flowchart` | A static, top-down, orthographic camera over flat boxes (the actor names) joined by straight lines; the 3D world is hidden. |
| `caption_clip` | CAP-S4 is drawn at 14 px cap height and shifted so its plate starts at x = 30 px (title-safe starts at 96 px). |

### Hard discriminators (mutation testing)

First run (commit `cf3cf8a`, before strengthening):
- `private_key_leak`: **CAUGHT** by `key_containment` (KEY-RDP-PRIV leaves RDP_SERVER's bounds from frame 731).
- `root_issues_leaf`: **MISSED.** `root_isolation` tested only the vault and plinth, so a request parked at the root's press and a server certificate stamped there both passed. Unrelated checks failed only because of the mutation's side effects.
- `caption_clip`: **MISSED.** The caption scene is not the context scene, so in background mode `frame_set` did not evaluate its matrices or colours. The title-safe check measured every plate at the frame centre, which made it vacuous. Cap height was read from a stored tag, not the glyphs.

Strengthening (same commit):
- **Captions:** the check now evaluates caption alpha and transforms directly from the F-curves, tests title-safe for the plate and the glyphs on every visible frame, measures cap height from the glyph geometry, and fails when the glyphs disagree with the tag.
- **Root isolation:** end-entity requests and certificates that the root did not issue may not touch any part of the root complex (dais, reader, press, module, plinth, vault).
- **New `build_provenance` check:** fails on any scene tagged `cff_fault`.
- **Tests:** `tests/test_blender_static.py::test_normal_builds_never_enable_a_fault` and `::test_fault_lists_agree_and_every_fault_has_a_hard_expectation_or_a_discriminator`.

Re-run: all three required faults are **CAUGHT**: `key_containment: KEY-RDP-PRIV`; `root_isolation: REQ-RDP` and `root_isolation: CERT-RDP`; `captions: title-safe` and `captions: cap height`. `flowchart` also fails `one_camera` (orthographic) and `camera_motion`. The normal film stays green: `tools verify` passes with 12 of 12 in-Blender checks, pytest 141 passed, ruff and mypy clean.

The same unevaluated-scene problem was found in the packet still renderer, which rendered the caption layer with every caption at alpha 0. The fix (commit `fe33f99`) renders every still through the animation path. The real animatic's caption frames were rendered with the range renderer and were never affected.

### Subagent discriminators

| Packet | Fault | Discriminator | Result |
|---|---|---|---|
| stage1-K3 | flowchart | cinema (sonnet) | **CAUGHT.** All 33 shots DIAGRAM; BLOCKERs on C-01, C-09, C-02, C-03, C-07 and C-10. Protocol note: its `files_read` lists 16 of 33 strips and 18 of 103 frames, so it sampled. |
| stage1-K2 | root_issues_leaf | pki (opus) | **CAUGHT.** B-04.2, B-04.3 and B-04.4 judged WRONG; BLOCKERs PKI-S1K2-01/02 (AR-02) and PKI-S1K2-03 (F-05). |
| stage1-K4 | caption_clip | legibility (sonnet) | **CAUGHT.** LEG-K4-01 BLOCKER (L-01, also L-03) on CAP-S4. |
| stage1-K1 | private_key_leak | pki (opus) | **MISSED.** B-03.3 to B-04.2 judged ACCURATE ("the private key stays in its closed container"). |
| stage1-K5 | private_key_leak | pki (opus), after strengthening 1 | **MISSED.** The leaked key at Issuing CA 1's press was flagged only as MAJOR (PKI-K5-01: "if it is key material, BLOCKER"); B-03.x judged ACCURATE. |
| stage1-K6 | private_key_leak | pki (opus), after strengthening 2 | **MISSED.** Its per-beat key log says the RDP key stays locked. It saw the leaked key at the capsule and at the press and explained both away as port and press fixtures. |
| stage1-K7 | private_key_leak | pki (opus), after strengthening 3 (locator evidence) | **CAUGHT.** Six BLOCKERs, PKI-K7-01..06 (F-03, F-09, F-10): the key on the capsule from B-03.3, carried into Issuing CA 1, left at its press, an emptied container in B-04.5, and the key never back home. B-03.3 to B-09.3 judged WRONG, each citing locator boxes checked against the image. It also read all 103 frames and 33 strips. |

Strengthening applied so far:
1. After K1 (commit `cf3ed52`):
   - private-key and capsule tracking duties, and "open every file and list it", in `.claude/agents/pki-discriminator.md`;
   - "open every file" in the cinema and legibility agents;
   - a judging protocol in every packet README, so it reaches a fresh instance even if agent definitions are not reloaded mid-session.
2. After K5 (commit `1cd847f`):
   - every PKI beat reason must locate each formed private key;
   - an unlocatable key, or a key-like shape outside a container or module, is WRONG and BLOCKER unless positively identified as something else.

**Chief of Staff diagnosis.** The fault is visible: the strips show the key at the capsule, and K5 and K6 both describe the leaked shape. But at 960x540 the grey-box key, the port plate and the press fixtures cannot be told apart, so the judge cannot tell which shape is which object. More prompt wording aimed at this one fault would overfit the calibration (Charter 2.7, independence).

The next strengthening is evidence, not wording: a per-frame locator file in every packet, giving the measured screen bounds of each private key, request capsule and certificate card. These are measurements with no pass or fail claim, like the legibility manifest's text bounds, and the judge can verify each box against the frame.

Strengthening 3 (commit `f7a93a6`): `blender/locate.py` writes `locator.json` into every packet: the projected screen bounds of each visible private key, request capsule, certificate card, key container and key module for every packet frame, measured on the built `.blend` (the fault blend for calibration, `renders/film.blend` for rounds). It carries no verdict and no occlusion claim; `tests/test_tools.py::test_packet_locator_is_measurement_only_with_no_pass_or_fail_claims` keeps it that way. No discriminator wording was changed for K7.

**Calibration status after K6 (historical): NOT PASSED.**

**Calibration status after K7: PASSED** (Session 4, after strengthening 3).
- All four subagent faults are caught as BLOCKER by their relevant discriminator: flowchart (K3, cinema), root_issues_leaf (K2, pki), caption_clip (K4, legibility) and private_key_leak (K7, pki).
- All three hard-check faults are caught: private_key_leak, root_issues_leaf and caption_clip.

K7 side findings (PKI-K7-07..10: no visible handshake proof or B-09.1 CRL fetches, white trust links, occluded check 1, early S6 caption) concern content that the calibration variant shares with the real film. They are not accepted here, because calibration findings are not round findings; stage1-R1 judges the real film. The K7 reply also reports PKI-S0R1-04 and PKI-S0R2-03 as REGRESSED, for the same shared reason (proof not visible), and R1 re-checks both. Clean-round counter: 0.

## Stage 1 — Animatic rounds

### stage1-R1 (round 1 of 5)

- **Candidate:** `00b1f74504fe00d15da94c0d408e36feece9fbd1`. The animatic frames are from commit 91ec326; later commits changed only checks, calibration hooks, packet tooling and docs, none of which affect frames.
- **Spec SHA-256:** `7cf45afa…6d23` (frozen, unchanged).
- **Packet:** `qa/rounds/stage1-R1/`, the first round packet with `locator.json`.
- **Discriminators:** three fresh instances, run in parallel: pki (opus), cinema (sonnet) and legibility (sonnet). Each read only packet files and listed every frame and strip in `files_read`.
- **Replies** are saved verbatim in the packet folder, with one exception: the cinema reply's B-06.3 `frames` field held a non-JSON expression, `["B-06.3_a_f1714","B-06.3_b_f1740","B-06.3_c_f1767"].map ? [ ...the three .png names... ] : []`. It was saved as its evident value, the three `.png` names, so the file parses.
- **Hard discriminators** (`tools verify` on the candidate): VERIFY GREEN. ruff and mypy clean; pytest 142 passed; traceability current; palette 87 pairs, 0 failing; planned-film audits 0 hard; in-Blender 12 of 12 checks passed; 3270 of 3270 frames, 0 blank.

| Discriminator | BLOCKER | MAJOR | MINOR | Verdicts |
|---|---|---|---|---|
| pki | 0 | 6 | 6 | 21 ACCURATE, 12 MISLEADING, 0 WRONG |
| cinema | 1 | 13 | 2 | 25 FILM, 8 DIAGRAM (B-05.3, B-06.3, B-06.4, B-06.5, B-07.3, B-08.2, B-08.3, B-09.2) |
| legibility | 2 | 11 | 2 | 26 MISLEADING, 4 FILM, 3 WRONG (B-03.2, B-03.3, B-07.2) |

- **Scores, cinema:** C-01 5, C-02 6, C-03 4, C-04 5, C-05 5, C-06 6, C-07 6, C-08 5, C-09 4, C-10 5, C-11 6.
- **Scores, legibility:** L-01 3, L-02 3, L-03 3, L-04 9, L-05 4, L-06 2, L-07 4, L-08 8.
- **Scores, pki (advisory):** C-07 6, C-10 5, C-11 7, L-06 6, L-08 9.
- **Regressions reported:** PKI-S0R1-06 and PKI-S0R2-03 REGRESSED (pki); PKI-S0R1-02 and PKI-S0R1-04 REGRESSED (legibility); everything else FIXED.

**Triage: PENDING** (Session 4 resume). Notes for the triage, not decisions:
- LEG-S1R1-02 (BLOCKER, F-03) says the RDP key never enters its container in B-03.2. The pki reply, which cites locator boxes, reports the key inside the locked KC-RDP from B-03.2 tile 3 onward, so LEG-S1R1-02 may misread the image. Rejecting a BLOCKER that concerns a private key needs the written citation and a second fresh pki concurrence (Charter 2.4 step 5). The ring and pill that stay on the server plate (PKI-S1R1-01, CIN-S1R1-11) are the seal ring left behind, which is a real defect.
- Overlapping themes: the white trust links (PKI-05, CIN-02, CIN-03); label, plate and check occlusion and sizes (PKI-03, LEG-04 to LEG-10, CIN-07, CIN-08); the screen-space check HUD (CIN-04, LEG-06); caption speckle and grain (CIN-05, LEG-01, LEG-15); the camera on the WEB01 label plane in B-08.2/B-08.3 (CIN-01, CIN-10, LEG-08); proof of possession not visible (PKI-06); the seal ring left behind (PKI-01); the capsule overlapping AD (PKI-02); the check list inside the flashback (PKI-04, CIN-15).
- LEG-S1R1-13 (L-07) asks for palette results in the packet. The packet does not carry `tools palette` output, so adding it is likely accepted as a packet change.

**Gate decision: NOT PASSED** (3 BLOCKER, 30 MAJOR). Rounds used: 1 of 5. Clean-round counter: 0.

**Triage (Chief of Staff, Session 4 part 3, Opus 5.5, effort High by the user's instruction).** All 43 findings are **ACCEPTED**; none is rejected, so no second pki concurrence is needed. Severities are kept as filed. Root causes verified by the Chief of Staff before acceptance:
- **Caption damage (LEG-01, CIN-05 captions, LEG-15):** the caption materials used EEVEE's `DITHERED` render method, which stipples the text and the 92% plate. A probe render of frame 1650 with `BLENDED` is clean (same scene, same samples). The label plates use the same method.
- **Text size (LEG-03, CIN-14, LEG-11):** the bundled fonts' capital height is 0.509 (Inter) and 0.520 (DejaVu Sans Mono) of the Blender font size, measured from the evaluated 'H' glyph mesh. The code assumed 0.72, and the hard check computed cap height from that same constant rather than from the glyph geometry. Captions were about 27 px at 1080p (< 30), labels about 72% of their planned size.
- **LEG-02 (BLOCKER, F-03):** the shape the reply tracks in B-03.2 is `KEY-RDP-PUB` (the public key: a ring bow with teeth), not the private key; the locator puts `KEY-RDP-PRIV` in `KC-RDP`. The finding is still accepted, re-scoped: the public key is drawn as a key, so a viewer cannot tell which key stays home, which defeats F-03 on screen and C-11 (private vs public key silhouette). Direction: the public key takes a non-key silhouette (the storyboard's "open, notched form"), visibly enters the capsule, and the occupied container reads as holding the private key.
- **Seal left behind (PKI-01, CIN-11):** `SEAL-*` rings are keyed to the capsule's home and stay at the server when the capsule travels.

| Finding | Sev | Decision | Fix theme |
|---|---|---|---|
| PKI-S1R1-01 | MAJOR | ACCEPTED | seal ring travels with its capsule and is consumed with it |
| PKI-S1R1-02 | MAJOR | ACCEPTED | capsule held at the server's outbound port, framed clear of AD; query pulse readable |
| PKI-S1R1-03 | MAJOR | ACCEPTED | check lists laid out unoccluded, one line each |
| PKI-S1R1-04 | MAJOR | ACCEPTED | present-tense check lists exit before the flashback |
| PKI-S1R1-05 | MAJOR | ACCEPTED | trust links: gold at the root blending into the CA colour; not white |
| PKI-S1R1-06 | MAJOR | ACCEPTED | proof of possession framed at film scale in B-06.1 and B-09.1 |
| PKI-S1R1-07..12 | MINOR | ACCEPTED | FQDN at the client; card validity bar and ports; CA 1 grey in B-07.3; CA=true band; B-09.1 CRL fetches; B-06.6 caption after green |
| CIN-S1R1-01 | BLOCKER | ACCEPTED | no label may approach the lens: labels hold a fixed on-screen size and fade when too near |
| CIN-S1R1-02, -03 | MAJOR | ACCEPTED | trust links curved, gradient, grown when introduced. CIN-03's "make CA-to-server segments neutral" is scoped by B-09.2, which asks for cyan and violet trust paths rising to gold; network routes stay neutral when not lit |
| CIN-S1R1-04 | MAJOR | ACCEPTED | check lists compact, beside the subject |
| CIN-S1R1-05 | MAJOR | ACCEPTED | dithered speckle removed (captions, plates); render noise reduced |
| CIN-S1R1-06 | MAJOR | ACCEPTED | tighter framing for B-02.2, B-06.1, B-06.5 |
| CIN-S1R1-07, -08 | MAJOR | ACCEPTED | label overlap and title-safe (shared with LEG-08/09) |
| CIN-S1R1-09 | MAJOR | ACCEPTED | caption clear of the focal subject (shared with LEG-12) |
| CIN-S1R1-10 | MAJOR | ACCEPTED | camera kept out of label space; smoother B-07.3/B-08.2 moves |
| CIN-S1R1-11 | MAJOR | ACCEPTED | same defect as PKI-01 |
| CIN-S1R1-12 | MAJOR | ACCEPTED | stronger key and rim; less emissive wash (C-05 applies at every tier) |
| CIN-S1R1-13 | MAJOR | ACCEPTED | background layer (far set geometry, horizon) and near layers (C-04) |
| CIN-S1R1-14 | MAJOR | ACCEPTED | flashback tags readable (shared with LEG-11) |
| CIN-S1R1-15, -16 | MINOR | ACCEPTED | no check text in the flashback; tapered, fading proof-of-possession beam |
| LEG-S1R1-01 | BLOCKER | ACCEPTED | caption materials `BLENDED`; caption layer composited last |
| LEG-S1R1-02 | BLOCKER | ACCEPTED (re-scoped above) | public key non-key silhouette; key states unambiguous |
| LEG-S1R1-03 | MAJOR | ACCEPTED | real cap ratio; captions >= 30 px and labels >= 18 px measured from glyph meshes |
| LEG-S1R1-04..11 | MAJOR | ACCEPTED | label pass: unoccluded, fixed on-screen size, title-safe, no overlaps, root name on a plate |
| LEG-S1R1-12 | MAJOR | ACCEPTED | caption vs focal-subject bounds (L-05) measured and cleared |
| LEG-S1R1-13 | MAJOR | ACCEPTED | packet carries the palette and CVD results |
| LEG-S1R1-14, -15 | MINOR | ACCEPTED | client tags offset; opaque caption plate |

Hard tests named after these IDs are listed with the R2 candidate.


## Session F2 (2026-11-13, Opus 5.5 High; lean mode, no discriminator round): v1 audit fixes, residuals and rulings

Chief of Staff rulings (no REFERENCE-SPEC change, no amendment, spec hash unchanged):
- V1-LEG-03: check lines appear with their own check, at one fixed place per list, each with its own tick on the sign plate; the 3D tick slots are not rendered. Ticks still resolve one by one and check 6 (revocation) still waits pending until E-06.5d.
- V1-PKI-03: "Private key" / "Public key" tags (glossary terms; the spec does not enumerate labels).
- RDP check lines are must-read in B-06.4 and B-06.5 (the list is held through B-06.5). This adds must-read frames; it removes none.
- V1-CIN-02: the hero moved to az -45 / el 30 / dist 42 looking at a single centre (-0.5, 4, 6.5); el and dist alone (the audit's search grid) never fitted the user and the root at >= 110 px from az -105.
- V1-LEG-02: layout moves glide at SIGN_JUMP_PX (48 px) per frame instead of fading out and in; a run ends (or dips to alpha 0.3 for 4 frames) only at a forced step larger than the C-06 pop limit (96 px). The audit's split-at-48-px rule cost must-read labels up to 30 frames each.

Residuals (targets not reached with every camera audit green; tests hold the achieved values):
| Finding | Target | Achieved | Why |
|---|---|---|---|
| V1-CIN-01 | 150 px (90 travel, 80 trust links) | B-01.2 78, B-02.2 99, B-02.3 96, B-04.2 65, B-05.2 55, B-05.3 39, B-06.1 63, B-06.3 53, B-07.4 64 | each further `dist` step failed C-02/C-03, or (B-01.2) started B-02.1 too near the RDP plate. Fixed: B-04.5 155; B-08.3 69 after V1-CIN-06; 10 of 11 still short, all larger than v1.0.0 except B-02.2/-02.3/-04.2/-05.2/-06.3 (unchanged) |
| V1-CIN-05 | session window 220 px | 188 px (dist 8.5, 50 mm) | dist <= 8.0 breaks C-02 on the move into B-07.1 (f2091+) |
| V1-CIN-02 | topology whole on 90% of the B-09.2 hold | 16% of the hold; 100% of the last 2 s of B-09.2 and of B-09.3; root 112 px | the camera pulls back from the B-09.1 close-up and arrives at the end of the beat |
| V1-LEG-03 | 0 blocked frames per list | CA 1 0, web 0, CA 2 42, RDP 21 | Appendix A.3 search with the F2 camera |
| V1-LEG-04 | crossing <= 2% | 1.55% (107 of 6899) | met; CROSSING_LIMIT now 0.02 |
| V1-PKI-04 | HS-RDP >= 60, HS-WEB >= 45 px | met (85, 55) | |
| V1-PKI-05 | CRL >= 60 px | met (78, 73) | |
| V1-CIN-06 | no luma step > 4.0 in f2695-2710 | 4.2 (v1.0.0 12.2) on the F2 animatic; bulge 4.8 (5.8 gives 4.8) | costs B-08.3 its 80 px target: 69 px (residual 65) |
| V1-CIN-06 (final tier) | as above, on the Final MP4 | f2709 7.7 (v1.0.0 12.2); other steps > 4.0 outside the cuts: f746 5.6, f1376 4.6, f2431 6.4 (v1.0.0 had f641, f746, f1253, f1376, f2440, f2701-2705) | bloom in the final tier sharpens the passing highlight; the bulge search ran on the animatic as the finding prescribes |
| V1-CIN-02 step 4 | B-09.2 mean YAVG >= 50 | 38.4 (38.1 before step 4; v1.0.0 40.0); B-09.3 27.9 (fade to black) | the prescribed fix (both green channels and the trust paths/links at GLOW_PEAK) was applied and adds only 0.3: the wider hero is mostly dark floor. More light needs world or lamp energy, which the finding reserves for V1-CIN-03 (deferred to v2.0) |

## Session F3 (2026-11-14, `claude-fable-5-2`; lean mode, no discriminator round): targeted re-audit and v1.1.0 pre-release

- **Subject:** the Final MP4 from the F2 final render, SHA-256 `2b56cee7b030528d6bf21cf864c74ced521cbc9c18ba170e7229704fd9d7f78e`. Spec hash unchanged (`7cf45afa…6d23`); no amendment.
- **Hard discriminators:** `python -m tools verify` VERIFY GREEN (pytest 189, 14 in-Blender checks, both tiers 3270/3270, final MP4 on spec, cut-frame steps 0.4 / 0.0).
- **Review:** Chief of Staff only, 8 images (56 distinct frames) cut from the Final MP4. Per-item table: `docs\AUDIT-v1.md`, "F3 targeted re-audit, third run".
- **Result:** every FIXED finding passes on the rendered film (15 MAJOR, 10 MINOR). 33 of 33 PKI beats ACCURATE on the frames viewed. Scores (Chief of Staff estimate, not a discriminator score): PKI 9, legibility 8, cinema 5.
- **Gate decision:** the F3 release gate passes; the charter film gate does **not** (V1-CIN-03 open, cinema below 8). v1.1.0 ships as a pre-release.

Known limitations accepted for v1.1.0 (Chief of Staff ruling: each is recorded, none is hidden by a relaxed test):

| ID | Sev | Limitation | Measured |
|---|---|---|---|
| V1-CIN-03 | MAJOR, open | grey-box look; no material or light design | cinema estimate 5 of 10 |
| V1-CIN-02 residual | (MAJOR, fixed with residual) | hero: whole topology only from about 102 s; dark | 16% of the hold; B-09.2 mean YAVG 38.4 (target 50) |
| V1-CIN-01 residual | (MAJOR, fixed with residual) | 10 beats under the focal size target | B-01.2 78, B-02.2 99, B-02.3 96, B-04.2 65, B-05.2 55, B-05.3 39, B-06.1 63, B-06.3 53, B-07.4 64, B-08.3 69 px |
| V1-CIN-05 residual | (MAJOR, fixed with residual) | session window under target | 188 px (target 220) |
| V1-CIN-06 residual | MINOR | luma steps over 4.0 on the Final MP4 | f2709 7.7, f2431 6.4, f746 5.6, f1376 4.6 |
| V1-LEG-03 residual | (MAJOR, fixed with residual) | check lists over a protected object | CA 2 list 42 frames, RDP list 21 frames |
| F3-LEG-01 | MINOR, new | flashback marker fades out after the cut | f1396–1398, alpha 0.58 / 0.30 / 0.13 |
| F3-AUD-01 | MINOR, new | AAC true peak above −1 dBFS | −0.6 dBFS (WAV −1.2) |
| F3-PIPE-02 | MINOR, new | metadata commit is one commit behind the encoded tree | `5cdae70` recorded; glow change in `407243a` |
| F3-PKI-01 | MINOR, new | handshake proof visible but unlabelled | 85 px (RDP), 55 px (web) |

Next: `docs\LOOK-PLAN-v1.2.md` (materials and lighting, hero brightness, the 90 s flash, focal sizes, and the four F3 MINORs).

## Session L1 (2026-11-14, `claude-sonnet-5-5`, high; no subagents, 5 of 6 images): v1.2 look pass

- **Scope:** `docs\LOOK-PLAN-v1.2.md` Items A, C, E, B (second change), D, F, in that order, one commit each (a79760f, 88bcf24, 25aaf11, d297079, 798e44f, 776e83a), plus the gate tooling `tools look-test` and `tools\luma.py` (8491152). No tag, no release (L2 does that). Spec hash unchanged; no amendment.
- **Final MP4:** SHA-256 `84097e10311daafa6b9d6b72bb94a31380357a82aee3006cf56536ad25093f44`, 70.3 MB (limit 120), grain strength 3. `python -m tools verify` VERIFY GREEN with `MP4_PENDING_RERENDER = False`: pytest 200, ruff and mypy clean, 15 in-Blender checks, both tiers 3270/3270, final MP4 on spec, true peak −1.2 dBFS (AAC; was −0.6), render metadata `dirty: false`, cut-frame steps 0.3 / 0.1. Loudness −15.9 LUFS, TP −1.7 dBFS (WAV).

### Rulings

| ID | Ruling |
|---|---|
| L1-R1 | The plan's 25 dE test between pool light colours and state colours is unreachable: `POOL_ROOT_HEX` is 15.9 dE from REVOCATION. The test uses the palette's own floor `palette.L07_MIN_DELTA_E` (15). Pools never use a state colour. |
| L1-R2 | Pool lights are set dressing, not a state signal: they are static, one per actor, and never change colour or intensity. The root's pool is a pale gold tint (`POOL_ROOT_HEX`), always on from the start, so it does not signal state either. |
| L1-R3 | Haze, horizon glow and bloom are set dressing: they live only on volumetric tiers, carry no state colour, and the ambient stays at 0.02 (C-05 unchanged). |
| L1-R4 | A longer lens is an allowed focal-size lever inside the charter's 24–50 mm range. A lens step that fails C-02/C-03, a sign hold or a legibility audit is undone (stop rule), not tuned. |

### Gate (`tools build --tier final`, `tools look-test`, frames in `renders\look-test`)

| Attempt | Result |
|---|---|
| 1 | Hero mean, f3100 YLOW and SATAVG, f457, f943, f2058 all in range; **FAIL**: largest YAVG step in the flash strips 4.8 (f2430) and 4.6 (f2709) at `BADGE_REST_GLOW` 0.25. Stop rule: lower to 0.15. |
| 2 | **PASS** at 0.15: steps 3.9 (f2430) and 3.8 (f2709), both ≤ 4.0. Hero mean YAVG 53.0 (before 37.8; want 50–62). Images viewed: no white floor blob, no hidden subject, no visible noise or banding. |

Haze density stayed at `HAZE_DENSITY` 0.004 (the tuning rule never fired).

### Stop-rule values recorded

- **Badge rest glow:** 0.25 → 0.15 (steps 4.8 / 4.6 → 3.9 / 3.8).
- **Hero follow (Item B, second change):** kept at 0.45. 0.3, 0.2 and 0.1 each gave 62 frames with the whole topology in frame against 63 at 0.45, and failed camera tests.
- **F3-PKI-01 (handshake proof label):** tried and removed. The label reached 36 of the 45 required frames; the plan says remove it. The storyboard and traceability net diff is none. Finding stays open as MINOR.
- **Item D (lens as a lever).** Lenses: B-01.2 35→39, B-02.3 35→39, B-04.2 35→50, B-05.2 35→50, B-06.1 40→44, B-07.4 35→50; B-06.3 took `AIA-RDP` 1.5x instead (50 mm already). B-08.3 (28 mm), B-05.3 (28 mm) and B-02.2 (42 mm) cannot go longer: the next lens step pushes B-09.1, B-06.1 or B-02.3 out of the C-03 box, or fails a sign hold.

| Beat | F3 px | L1 px | Plan target | Met |
|---|---|---|---|---|
| B-01.2 | 78 | 83.8 | 150 | no |
| B-02.2 | 99 | 99.3 | 150 | no |
| B-02.3 | 96 | 103.2 | 150 | no |
| B-04.2 | 65 | 81.4 | 150 | no |
| B-05.2 | 55 | 75.0 | 150 | no |
| B-05.3 | 39 | 38.7 | 150 | no |
| B-06.1 | 63 | 63.8 | 150 | no |
| B-06.3 | 53 | 80.0 | 150 | no |
| B-07.4 | 64 | 72.5 | 150 | no |
| B-08.3 | 69 | 69.2 | 150 | no |

  Shortfall: `RESIDUAL_PX` in `tools\focal_audit.py` still has **10** entries; the plan asked for at most 6. Every value was raised or kept to the size now reached, so `python -m tools focal` prints 0 beats under target. L2 to rule whether the V1-CIN-01 residual is accepted for v1.2.0.

### Measured on the Final MP4 (`tools\luma.py`, BT.709 video range)

- **Per-beat mean YAVG:** B-01.1 47.7, B-01.2 54.6, B-02.1 50.8, B-02.2 58.6, B-02.3 51.0, B-03.1 48.4, B-03.2 57.8, B-03.3 54.4, B-03.4 60.6, B-04.1 56.0, B-04.2 58.5, B-04.3 61.0, B-04.4 68.7, B-04.5 60.0, B-05.1 60.6, **B-05.2 104.1** (pale flashback, by design), B-05.3 61.5, B-06.1 60.3, B-06.2 44.8, B-06.3 51.5, B-06.4 47.9, B-06.5 50.4, B-06.6 55.6, B-07.1 61.9, B-07.2 61.9, B-07.3 60.7, B-07.4 56.5, B-08.1 51.7, B-08.2 61.0, B-08.3 60.9, B-09.1 58.7, **B-09.2 51.3** (was 38.4; target ≥ 50 met), B-09.3 39.2. Film mean 57.7 (was 50.3).
- **Frame-to-frame steps over 4.0 (cut frames excluded):** f746 8.0, f1157 4.0, f1376 10.6, f1534 4.4, f1535 6.7, f2454 5.6, f2455 5.1. Targets met: f2431 step 0.3 (was 6.4), f2695–2712 largest 3.7 at f2709 (was 7.7). **Not met / new:** f746 (8.0, was 5.6) and f1376 (10.6, was 4.6) are the flashback entry and exit; f1534–1535 and f2454–2455 were not measured before L1. Recorded, not tuned.
- **F3 MINORs:** F3-LEG-01 fixed (marker ends at the cut), F3-AUD-01 fixed (−1.2 dBFS, check added), F3-PIPE-02 fixed (`dirty` flag and commit check), F3-PKI-01 still open.

### Notes for L2

- **Soft glow:** a soft haze glow shows around the key/rim light above the root in some wide frames (the poster's upper right). It reads as atmosphere, not a blob; L2 to rule whether it is acceptable.
- Frames viewed on the Final MP4: the 33-tile contact sheet, a 3x4 strip of f2700–2710 (no flash, no pop; the Root CA label fades in as designed) and the poster (pool cones and haze visible, all five labels legible).
- Not heard: the audio. Not re-run: a discriminator round (lean mode).

Next: L2 (Opus 5.5, medium): re-audit the Final MP4 and release v1.2.0 per `docs\LOOK-PLAN-v1.2.md` Section 6.

## Session L2 (2026-11-14, `claude-opus-5-5`; lean mode, no subagents, 7 of 10 images): targeted re-audit and v1.2.0 release

- **Subject:** the L1 Final MP4, SHA-256 `84097e10311daafa6b9d6b72bb94a31380357a82aee3006cf56536ad25093f44`, render commit `51a87aa`, `dirty: false`. Source changed since then: only the V1-DOC-02 test and `tools\verify.py` (no render input). Spec hash unchanged (`7cf45afa…6d23`); no amendment.
- **Hard discriminators:** `python -m tools verify` VERIFY GREEN (ruff, mypy 66 files, pytest 200, traceability, palette 87/0, planned-film audits 0 hard, 15 in-Blender checks, both tiers 3270/3270, final MP4 on spec, true peak −1.2 dBFS, cut-frame steps 0.3 / 0.1). ffprobe: H.264 High level 41, yuv420p, bt709 ×3, 1920x1080, 30/1, 3270 frames, 109.000 s; AAC LC 48 kHz stereo.
- **Review:** Chief of Staff only. 7 images, all cut from the Final MP4 except the committed contact sheet and poster: step pairs (f745|746, f1375|1376, f1533|1536, f2452|2456); proof window f1526–1582 every 8th frame; flash f2431, f2709 and hero f2941–3120 every 30th; the ten focal beats at mid-beat; cuts f1245–1247, f1395–1397, trust store f1640, f1690, f240; the 33-tile contact sheet; the poster. Luma per frame by FFmpeg `signalstats` on the MP4; rig-light positions recomputed from `cff.stage.camera.CameraPlan` with the maths of `blender\lighting.py`.

### Per-item result on the film

| Item | Where | Result | Evidence |
|---|---|---|---|
| A / V1-CIN-03 look | whole film | **PASS, closed** | Haze with depth, horizon glow, pool lights in identity tints, reflective floor, bloom on role colours. Wide and medium shots have material and light design. Interiors at 14–24 s remain simple grey shapes (plan Section 7; residual, not a MAJOR). |
| B hero brightness | 98–104 s | **PASS** | B-09.2 mean YAVG 51.3 (≥ 50). Topology whole from about f3031 (101 s); residual V1-CIN-02 timing kept (follow 0.45). |
| C flash | 81.0 s, 90.0–90.3 s | **PASS** | f2431 step 0.3; f2695–2712 largest 3.7. Frames show the badge as a dim plate, no flare. |
| D focal sizes | ten beats | **PASS (residual accepted)** | Six beats grew, none shrank; every subject identifiable and carried by a caption or label. |
| E F3-LEG-01 | cut at 46.5 s | **PASS** | No "Earlier" marker on f1396–1397; clean cuts at f1246 and f1396 (no blend). |
| E F3-AUD-01 / F3-PIPE-02 | MP4, metadata | **PASS** | −1.2 dBFS true peak; `dirty: false`. |
| E F3-PKI-01 | 50.9–52.7 s | **open MINOR, accepted** | See ruling L2-R3. |
| v1.1.0 fixes | contact sheet + sheets | **PASS, no regression** | Signs legible over haze (dark plates), captions on dark plates, trust store gold before docking with "Installed earlier by policy", keys named, check lists in place, no blank frame. |

### Rulings

| ID | Ruling |
|---|---|
| L2-R1 | **Haze glow near the rim light: accepted.** It is a soft, low-contrast backlight bloom (poster upper centre, f1526–1566 top, f3061–3120 behind the root). It never covers a label, caption or focal subject, has no hard dot, and is motivated by the rim light. C-08 restraint holds. |
| L2-R2 | **Luma steps: new finding L2-CIN-01, MINOR.** Cause found (was "unknown" in the plan): the camera-following rim light (`blender\lighting.py`, `rim_pos = look + 0.85·d·forward + offsets`) is placed without regard to geometry. f746 (24.83 s, step 8.0, B-04.1): the rim is 0.7 m from the AD tower's axis at z 3.2 m, inside the tower, so its light is cut in one frame (the CA 1 vault's side wall goes dark). f1376 (45.83 s, step 10.6, B-05.2, inside the flashback, not its exit): the rim leaves the Root CA complex (0.9 → 1.1 m from its axis), so its light returns in one frame. f1534–1535 (51.1 s, 4.4 / 6.7, B-06.1): the rim's haze glow comes out from behind the root tower over three frames. L1's haze and volumetric shadows amplified all three (v1.1.0: 5.6 and 4.6). **Severity MINOR, by the project's calibrated scale:** the v1 audit classed V1-CIN-06, a 6-frame white flash with a 12.2 step, as MINOR; these are single-step pops of 8.0 and 10.6 that do not hide a subject or a caption. f2454–2455 (81.8 s, 5.6 / 5.1) is the camera passing through the CA 2 doorway (its glowing violet frame leaves the picture over four frames): real motion, **no finding**. |
| L2-R3 | **F3-PKI-01 accepted as an open MINOR.** Without the label the film stays accurate (F-10): the proof is created at the server with `KEY-RDP-PRIV` (E-06.1d), travels as its own object beside the certificate and the CA 1 copy (seen f1542–1550), and is checked at the client against `CERT-RDP` (E-06.1f). Nothing on screen says a certificate alone proves possession. It is weak, not misleading; B-06.1 stays ACCURATE. |
| L2-R4 | **Focal-size residuals (10 `RESIDUAL_PX` entries) accepted for v1.2.0.** The plan's "at most 6" was a target, not a gate. All entries were raised or kept; the three beats that could not move (B-02.2, B-05.3, B-08.3) are blocked by camera and sign checks (L1-R4). No entry was lowered and no check was relaxed. |
| L2-R5 | **V1-CIN-03 closed; release as the public latest.** With 0 BLOCKER and 0 MAJOR open and V1-CIN-03 closed, v1.2.0 is a full release (plan Section 6). The charter film gate (scores ≥ 8, two clean discriminator rounds) is still not met. That is recorded, and it does not affect the release decision in lean mode. |

Scores (Chief of Staff estimate, not a discriminator score): **PKI 9, legibility 8, cinema 7** (v1.1.0: 9, 8, 5). PKI beats: 33 of 33 ACCURATE (B-06.1 weak, unlabelled proof).

### L2-CIN-01 fix for v1.3 (MINOR; Sonnet 5.5, medium; partial re-render)

1. `blender\lighting.py`, `build_lights`: after computing `rim_pos` (and `key_pos`), push it out of every actor's keep-out cylinder: for each anchor in `lo.CLIENT, RDP, WEB, AD, CA1, CA2, ROOT` with a keep-out radius `RIG_KEEP_OUT_M` (new constant in `cff\theme\look.py`; start at 3.5, the root complex's drum radius plus 0.5 m), if the horizontal distance is below the radius and `z` is below the actor's top plus 1 m, move the light radially to the radius. Apply it per frame **before** keying, so the Bezier keys stay smooth.
2. New pure-Python test `test_L2_CIN_01_rig_lights_stay_out_of_actors`: rebuild the rig positions from `CameraPlan` (as in the L2 scratch check) for every frame and assert none is inside a keep-out cylinder.
3. Re-render only the beats whose rim keys changed (expected B-04.1, B-05.2, B-06.1; delete just those frames in `renders\final\beauty`), then `tools encode`, `tools verify`, and `tools\luma.py`: no step above 4.0 at f746, f1376 or f1534–1535.

## Session V3 (2026-11-14, `claude-opus-5-5`; lean mode, no subagents, 5 of 8 images): v1.3 finishing pass, no release

- **Scope:** four items set by the owner: (1) L2-CIN-01, (2) interiors to the v1.2 look, (3) the whole topology in frame from 98.5 s with B-09.2 mean luma ≥ 50, (4) F3-PKI-01 proof of possession readable at 50.9–52.7 s. No release; Pages stays on v1.2.0. Spec hash unchanged; no amendment.
- **Commits:** 9882cec (rig keep-out), 63289f7 (interiors), ab51778 (hero), 9d11993 (proof tag), 994e7ca (tests, MP4 luma gate), 9b84da2 and fb4e1f1 (V3-CIN-01), state commits 32e222b, 0d50b4d, 3260ec4.
- **Final MP4:** SHA-256 `e5050765e7633399b04b3c3014fd811da7ccff6d3871d36216015001bfd330b6`, 70.3 MB, render commit 3260ec4, `dirty: false`. ffprobe: H.264 High level 41, bt709, 1920x1080, 3270 frames, 109.000 s; AAC LC. `python -m tools verify` VERIFY GREEN: ruff, mypy 68 files, pytest 205, traceability, palette 87/0, planned-film audits 0 hard (1 advisory, B-05.1), 16 in-Blender checks, both tiers 3270/3270, MP4 on spec, true peak −1.2 dBFS, cut steps 0.4 / 0.1, new step `MP4 luma (L2-CIN-01, hero)` PASS.

### Per item

| Item | Change | Result on the Final MP4 | Regression |
|---|---|---|---|
| 1 L2-CIN-01 | Rig positions planned in `cff\stage\rig.py`. A light inside an actor's keep-out cylinder (footprint half-diagonal + 0.5 m, up to top + 1 m) is **lifted**, with a 4 m linear ramp outside. The rim is also lifted over a solid that stands between the subject and it (not over the solid that holds the subject). | Steps f746 **0.1** (was 8.0), f1376 **0.6** (10.6), f1534 **1.4** (4.4), f1535 **2.0** (6.7). | `test_L2_CIN_01_rig_lights_stay_out_of_actors`; verify `step_mp4_luma`. |
| 2 Interiors | `blender\dressing.py`: per chassis, rack ribs and rails, two pale strips, a lamp bar, five status LEDs, a ceiling area light (3 W, `POOL_NEUTRAL_HEX`) and a back rim (1 W, `RIM_LIGHT_HEX`); per CA vault, ribs, tinted strips (`POOL_CA1/CA2_HEX`) and a ceiling light (12 W). Brushed-metal chassis material (noise roughness 0.3–0.6). Static, parented, no state colour. | Beat means B-03.1 50.9, B-03.2 63.4, B-03.3 59.3, B-03.4 65.3, B-07.2 63.4, B-04.3 63.5, B-04.4 66.9, B-08.1 53.9, B-08.2 62.0 (v1.2: 48.4, 57.8, 54.4, 60.6, 61.9, 61.0, 68.7, 51.7, 61.0). No beat rises more than 1.6x the beat before. | `test_V13_interiors_are_dressed_with_static_practicals`; in-Blender `interior_dressing`. |
| 3 Hero | `Shot` gains `lead_s`, `arrive`, `focus_pull`. Hero: the pull-back starts 0.8 s before B-09.2, reaches the pose in 27% of its move, follow 0.7, focus racks to the root in 8% (C-02 is relative to the focus distance). No cut. | Every frame from f2956 (98.5 s) to the end of B-09.2 and the B-09.3 hold has all seven actors, the user included, inside x 96–1824, y 200–1026. B-09.2 mean YAVG **56.3**; f2956–3120 mean **56.1**. B-09.2 now passes C-03 and left `C03_OPEN_BEATS`. | `test_V13_hero_holds_the_whole_topology_from_98_5_s`; verify `step_mp4_luma`. |
| 4 F3-PKI-01 | Tag `LBL-HS-RDP` "Proof: private-key signature" on `HS-RDP`, window 50.9 s to the beat end; the matched proof rests by the card until 53.0 s, then dissolves (STORYBOARD B-06.1 updated). | Legibility audit: shown 45 of 45 full frames (L1: 36). F-10 holds: the proof is made at the server with `KEY-RDP-PRIV` (E-06.1d), the key never moves, and the client checks it against `CERT-RDP`. | `test_F3_PKI_01_handshake_proof_is_labelled_and_readable`. |

### New finding found and fixed in this session

| ID | Severity | Finding | Fix |
|---|---|---|---|
| V3-CIN-01 | MINOR (fixed) | The first v1.3 render popped inside the chassis at f477 (5.0), f595 (4.3) and f600 (4.4). Dimming the emitters looked like the fix on a short test, but the second render popped at f671, f705 and f719 instead, and the same build re-rendered f671 smoothly: the interior toggled between two levels about 4.7 apart. Cause: EEVEE shadow-pool overflow from the four close-range shadowed dressing lights. | `data.use_shadow = False` on dressing lights (their spill outside a shell is under 10% of a pool light); emitters kept dim. A full 300-frame chunk f421–720 then had no step above 3.5; the final film has none above 1.8 at those six frames. All six are in the MP4 gate. |

### Rulings

| ID | Ruling |
|---|---|
| V3-R1 | **Lift instead of the ledger's radial push.** A radial push swings a light round a cylinder's axis when its path passes near it (2.4 m in one frame at f1372, a new pop), and pushing along the view direction jumps by a chord length on entry. The lift is continuous; the test bounds the extra per-frame movement at 0.5 m (measured 0.43). Per-actor radii instead of one 3.5 m radius, so the camera-side key in the server close-ups is not moved. The fix changes the rim in 1255 frames, not only B-04.1, B-05.2 and B-06.1. |
| V3-R2 | **Full beauty re-render, partial overlays.** The practicals are on screen in 3025 of 3270 frames, so the whole beauty pass changed. Signs were re-rendered only where the sign plan changed (442 frames: f1528–1598, f2744–3119; diffed against cee6245); captions (bands unchanged) and audio (event timing unchanged) were kept. |
| V3-R3 | **Remaining steps above 4.0 are not findings.** f2454–2455 (5.9 / 5.1): camera through the CA 2 doorway (L2-R2). f1254 (4.1): one frame of the designed flashback brighten-up ramp (f1252–1258); the v1.2 beauty frames step 4.1 there too. f641 (beam event, 3.5) and f1381 (flashback, below 4 on the MP4) are pre-existing. |

Images viewed: baseline sheet (v1.2 final frames), preview strips (found the white-rib bug: dressing objects glowed through `Object Info > Color`; fixed and checked in `interior_dressing`), preview contact sheet, difference sheet for V3-CIN-01, final contact sheet. Not heard: the audio (unchanged). Not run: a discriminator round (lean mode).

Next: V3 audit (Fable 5.2, High): re-audit this Final MP4 and decide whether v1.3.0 is released.
