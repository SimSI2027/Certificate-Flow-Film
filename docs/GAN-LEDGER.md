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
