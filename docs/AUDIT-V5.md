# V5 audit (full audit of the v1.3.0 film)

Date: 2026-11-14. Auditor: Chief of Staff, `claude-fable-5-2`, High, lean mode (no subagents, 13 of 14 images).
Film: `Certificate-Flow-Film-Final.mp4`, SHA-256 `ce4cf1fb12fa71d35237463506069c5f80c06b2c6ff15722dc69be43646f15d9`, render commit `2666bad`.
Judged against `docs\REFERENCE-SPEC.md` (SHA-256 `90d698fc…6fe8`). Times are `(frame − 1) / 30`.

## Result

**Gate: PASS. 0 BLOCKER, 0 MAJOR, 10 MINOR. 33 of 33 PKI beats ACCURATE. Released as v1.3.0.**

| Area | Score |
|---|---|
| a) PKI accuracy | 9 |
| b) Icons and representations | 8.5 |
| c) Realism and consistency | 8 |
| d) Presentation | 7.5 |
| e) Legibility | 8.5 |

The session gate was "no BLOCKER, no MAJOR". Presentation is half a point under the charter's score gate of 8; the reasons are the MINOR findings V5A-CIN-01 to V5A-CIN-04 below, and `docs\ENHANCEMENTS-v1.4.md` addresses them.

## Pre-flight

- `python -m tools verify`: VERIFY GREEN. ruff clean; mypy --strict 76 files; pytest 232 passed; traceability current; palette 87 pairs, 0 failing; planned-film audits 0 hard findings (1 advisory); in-Blender checks 20 of 20; both tiers 3270/3270 frames, 0 blank; final MP4 on spec, true peak −1.2 dBFS; cut steps 0.5 / 0.1; MP4 luma gate PASS (B-09.2 mean 58.8).
- ffprobe: H.264 High, level 4.1, 1920x1080, yuv420p, bt709 (space, transfer, primaries), 30 fps, 3270 frames, 109.000 s; AAC LC, 48 kHz, stereo.
- SHA-256 of the Final MP4 matches the value recorded in PROJECT-STATE.
- Full-film luma scan (`tools\luma.py`): film mean 57.4; steps over 4.0 outside the cuts: f2454 6.4 and f2455 5.5 only; steps between 3.0 and 4.0: f1254, f1258, f2430, f2453, f2709. Cut frames f1246 1.6 and f1396 15.3 (the cut out of the brighter flashback, by design).

## a) PKI accuracy: 9

Every beat is ACCURATE against F-01..F-17. Evidence frames are the ones viewed.

| Beat | Time | Seen on the film | Verdict |
|---|---|---|---|
| B-01.1 | 1.5 s (f45) | Seated user at `CLIENT01`; sign "Connect to rdp01.malawi.lab" (the FQDN later matched to the SAN). Gold trust store already above the laptop. | ACCURATE |
| B-01.2 | 5.0 s (f150) | Amber pulse runs along the floor channel. | ACCURATE |
| B-02.1 | 8.3 s (f250) | Listener lights amber on the `rdp01.malawi.lab` rack. | ACCURATE |
| B-02.2 | 9.5 s (f285), 11.2 s (f338) | Pale card with a seal that closes on itself, no ribbon, no CA badge; "Self-signed"; "Unverified" at the client; channel stays amber; card gone by f356, channel dark at 13.3 s. | ACCURATE |
| B-02.3 | 13.3 s (f400) | `RDPAuth` badge lands on the server; no connection pending. | ACCURATE |
| B-03.1 | 15.5 s (f465) | Key pair inside the chassis: padlocked "Private key", open "Public key". | ACCURATE |
| B-03.2 | 17.6 s (f530) | Private key in the locked container. | ACCURATE |
| B-03.3 | 20.3 s (f610) | Request capsule with the public key; private key stays in its container. | ACCURATE |
| B-03.4 | 23.0 s (f690) | Capsule sealed, signature tag on it; no key-shaped object moved. | ACCURATE |
| B-04.1 | 25.6 s (f770) | Capsule held at the server's port; AD node (`MALAWI.LAB`, `DC01`) with its rings; route lit to Issuing CA 1 only. | ACCURATE |
| B-04.2 | 28.3 s (f850) | Capsule enters Issuing CA 1 on the cyan route. | ACCURATE |
| B-04.3 | 32.0 s (f960) | Four checks in F-06 order, each with its own tick. | ACCURATE |
| B-04.4 | 34.6 s (f1040) | Press stamps the card: `rdp01.malawi.lab`, "Remote Desktop Authentication", validity bar, AIA/CDP ports, cyan issuer seal. | ACCURATE |
| B-04.5 | 37.6 s (f1130) | Card locks beside the key container; translucent copy of CA 1's certificate (CA badge, gold seal) arrives with it. | ACCURATE |
| B-05.1 | 38.6–41.5 s (f1160–1245) | Crane up to the gold cage on its plinth, alone on the dais; the light sweep reveals the existing self-seal. | ACCURATE |
| B-05.2 | 41.5–46.5 s (f1246–1395) | Desaturated; "Earlier: offline signing ceremony"; capsule tagged "Issuing CA 1's own CA request" carried to the root; CA certificate (CA badge) carried back. | ACCURATE |
| B-05.3 | 48.6 s (f1460), 49.3 s (f1480) | Gold-to-cyan chain link from CA 1's certificate to the root. No request goes to the root. | ACCURATE |
| B-06.1 | 52.0 s (f1560), 52.5 s (f1575) | New amber pulse; server certificate, CA 1's certificate copy and the proof banner ("Proof: private-key signature") travel to the client. | ACCURATE |
| B-06.2 | 54.6–56.6 s (f1640–1700) | Cards dock upward under the gold trust store; "Installed earlier by policy". See ruling V5B-OBS-01. | ACCURATE |
| B-06.3 | 58.1 s (f1745) | AIA indicator; "Missing intermediate? AIA can fetch it", "Fetching never creates trust". | ACCURATE |
| B-06.4 | 63.3 s (f1900) | Checks 1–5 green in the frozen order; "Revocation OK" pending amber. | ACCURATE |
| B-06.5 | 65.3 s (f1960), 66.3 s (f1990) | Two CRLs from `pki.malawi.lab` dock beside their own cards; "OCSP if deployed"; no fetch for the root. | ACCURATE |
| B-06.6 | 68.0 s (f2040) | Channel green, session window open. | ACCURATE |
| B-07.1 | 71.6 s (f2150) | `WEB01`, `portal.malawi.lab`, `WebServer-TLS`. | ACCURATE |
| B-07.2 | 75.0 s (f2250) | Local key pair, private key in its container, sealed request. | ACCURATE |
| B-07.3 | 77.2 s (f2318), 78.3 s (f2350) | CA 1 grey, "WebServer-TLS not published here"; CA 2 violet with four eligibility tags; query pulse at the AD node. | ACCURATE |
| B-07.4 | 81.0 s (f2430) | Capsule travels only to Issuing CA 2. | ACCURATE |
| B-08.1 | 84.3 s (f2530) | Four checks plus "Name supplied in request — enrollment restricted". | ACCURATE |
| B-08.2 | 87.5 s (f2625), 89.6 s (f2690) | Violet card stamped (`portal.malawi.lab`, "Server Authentication"), locked beside the key with CA 2's certificate copy. | ACCURATE |
| B-08.3 | 92.0 s (f2760), 92.3 s (f2770) | CA 2's certificate chained to the same root; the root's module and press stay dark. | ACCURATE |
| B-09.1 | 95.0–97.5 s (f2850–2925) | Chain `portal.malawi.lab` → CA 2 → root; CRL fetches at f2860–2878, ticks from f2880; channel then green. | ACCURATE |
| B-09.2 | 99.0–103.6 s (f2970–3110) | Whole topology: root on top, both CAs, both servers, the user; cyan and violet paths meet in gold at the root. | ACCURATE |
| B-09.3 | 104.5–108.3 s (f3135–3250) | Title, then fade to black. | ACCURATE |

**Root CA offline and air-gapped: confirmed.** At 38.6–41.5 s, 46.5 s, 72.4 s, 92.3 s and 99–104 s the cage stands alone on its plinth and dais. No floor channel and no cable reaches it; only the chain-link trust links do. The in-Blender check `root_no_cables` passes (200 cables, the nearest 5.2 m from the root complex).

**The earlier lab name `1SN0S`:**
- Film: absent. Every label, caption and plate seen reads `MALAWI` or `malawi.lab`; `test_V4_REN_01` guards the model, captions, labels and site text.
- README: absent.
- Site: absent after the v1.3.0 rebuild (the v1.2.0 page, poster and preview carried it until this release).
- It remains only in process history: `docs\history\AUDIT-v1.md`, the frozen calibration packets in `qa\calibration\` and git history.

## b) Icons and representations: 8.5

Checked against `qa\v5b\icon-legend.png`.

| Symbol | Where checked | Accurate | Consistent | Readable at 1080p |
|---|---|---|---|---|
| End-entity certificate (document, key emblem, ribbon seal, no CA badge) | 34.6 s (218 px wide), 56.3 s, 87.5 s, 96.6 s | yes | yes | yes |
| CA certificate (CA badge above the top-left corner) | 37.6 s, 45.6 s, 56.3 s, 89.6 s | yes | yes; never on an end-entity card | yes |
| Root self-signed seal (ring that closes on itself, gold card with CA badge) | 11.2 s, 66.3 s, 68.0 s | yes | yes on the card; see V5A-ICO-02 for the cage | yes |
| RDP self-signed certificate (pale card, self-seal, no ribbon, no badge) | 9.5 s (126 px), 11.2 s (79 px) | yes | yes | yes at the listener, small at the client |
| Issuer-coloured seals (cyan from CA 1, violet from CA 2, gold from the root) | 34.6 s, 37.6 s, 87.5 s, 89.6 s | yes | yes | yes; see V5A-ICO-01 |
| Private key (key locked in a padlock) and public key (open key) | 15.5 s, 75.0 s | yes | yes | yes, and both are labelled |
| Request with a signature mark | 23.3 s, 32.0 s, 84.3 s | yes | yes | yes |
| Handshake proof with a signature mark (swallowtail banner) | 52.5 s (164 px) | yes | yes | yes, labelled |
| CRL (hanging list, one entry struck) | 66.3 s | yes | yes | yes (each about 50 x 85 px) |
| Chain links (trust links) | 49.3 s, 72.4 s, 92.3 s | yes | yes | yes |
| Validation ticks | 32.0 s, 63.6 s, 84.6 s, 97.5 s | yes | yes | yes |

Nothing is misleading. No private key appears on a card, in a request or in motion. The key emblem on a card is always the open (public) key.

## c) Realism and consistency: 8

- The character, laptop and desk (1.5 s, 68.0 s) are in scale and sit together; the hands reach the keyboard.
- Racks with devices behind perforated doors (8.3 s, 71.6 s), the HSM with keypad and display (32.0 s), the gold cage on a concrete plinth (41.3 s) and the datacenter rows (55.0 s) read as one world: dark steel with identity-coloured light. No vendor marks.
- The abstract story objects (cards, capsules, keys) glow against the hardware and never blend into it.
- Weaker points: rack interiors are close to black; the key container and the presses are plain blocks next to the detailed racks; the session window is a blank panel (V5A-CIN-04); the offline tower is hard to make out inside the cage (V5A-REAL-01).

## d) Presentation: 7.5

- **Focal subject.** Clear in every beat viewed. Small in a few: the self-signed card at the client (79 px, 11.2 s), the web chain (84 px wide, 96.6 s), the hero topology (V5A-CIN-02).
- **Lighting continuity.** One visible change in the whole film, at 81.7 s (ruling below). No flicker.
- **Camera.** One continuous move; transit frames carry motion blur (69.6 s, 88.3 s), which reads as speed.
- **The two cuts.** f1245/1246 (41.5 s) and f1395/1396 (46.5 s) are clean single frames with no double exposure; the desaturation and the marker make the flashback clear.
- **Pacing.** 33 beats in 109 s. Dense but followable, because the web path (70–98 s) repeats the RDP path at double speed.
- **Hero and title.** The hero holds the whole topology from 99 s with every node labelled; it is correct but small in frame. The title is a caption plate laid over the hero (V5A-CIN-03).
- **Entertaining?** It holds attention as an explainer: the reveal of the root (38.6–41.5 s), the stamp (34.6 s) and the green channel (68.0 s) are the payoffs. It has little flourish; the stamps, links and ticks appear without much animation of their own.

## e) Legibility: 8.5

- L-01..L-08 hard checks pass in `tools verify`. All 54 signs use a 52 px plate; captions are single and clear of the focal subject; 13 caption cues hold 2.5 s or longer.
- Dense lists read cleanly at 1080p: 63.6 s (six checks), 78.3 s (eligibility), 84.6 s (CA 2 checks and note), 97.5 s (web checks).
- Two tags sit far from what they name (V5A-LEG-01, V5A-LEG-02).

## Rulings on the open items

- **V5B-CIN-03 (steps 6.4 and 5.5 at f2454/2455, 81.77–81.80 s): accepted, stays MINOR, no fix needed for release.** Frames f2440–2500 were viewed. The camera passes through CA 2's lit doorway: the violet door frame and the lit floor outside leave the picture, and mean luma falls from 64.0 (f2450) to 44.7 (f2456) and then stays flat. It is a one-way change over five frames with no rebound, so it reads as entering a darker room, not as a lighting fault. B-08.1 is the darkest story beat (mean 45.3); an interior key light is in the enhancement plan.
- **V5B-OBS-01 (the gold cradle hides the root card at B-06.2, 53–64 s): accepted, MINOR. The viewer still understands that the root is already trusted.** Reasons:
  1. The gold store is on screen from the first frame and never animates in.
  2. The root card is seen in it from the front at 11.2 s, at 52.0 s (1.5 s before the docking) and again at 66–70 s.
  3. The sign "Installed earlier by policy" is on the store while the chain docks.
  4. The first check line reads "Chain ends at a trusted root".

  The weakness: for 11 s the top of the chain is a plain gold slab, and the sign does not say what was installed. Printing the root card's marks on the cradle's back is in the enhancement plan.

## Findings (all MINOR)

| ID | Time | Finding |
|---|---|---|
| V5A-LEG-01 | 10.4–12.1 s (f313–363) | "Self-signed" and "Unverified" sit about 600 px to the right of the self-signed card and the client, over empty floor. Readable, and no other object is wrongly labelled, but the link to the card is weak. |
| V5A-LEG-02 | 76.8–77.8 s (f2304–2335) | "MALAWI Issuing CA 1" and "WebServer-TLS not published here" sit up to 530 px from CA 1's enclosure before they settle beside it. |
| V5A-ICO-01 | 34.6 s (f1040), 87.5 s (f2625) | On end-entity cards the issuer seal has the same colour as the card body, so it reads by its outline only. |
| V5A-ICO-02 | 41.3 s (f1240) vs 68.0 s (f2040) | The emblem on the root cage is a ring with a centre disc; the self-seal on the cards has no disc. |
| V5A-PKI-01 | 39.6 s (f1190), 92.3 s (f2770) | The root's key module, press and reader stand on the open dais outside the locked cage. This matches the spec (they are dark and still outside the flashback), but an engineer may ask why the HSM is not inside the cage. |
| V5A-REAL-01 | 41.3 s (f1240) | The offline tower inside the cage is dark and partly behind the seal, so the cage reads as "cage and seal" more than "a machine in a cage". |
| V5A-CIN-01 | 81.7 s (f2451–2456) | Same frames as V5B-CIN-03 (ruled above). |
| V5A-CIN-02 | 99–104 s (f2970–3110) | The hero topology fills only about the middle 40% of the frame width; the root cage is about 110 px wide. |
| V5A-CIN-03 | 104.5–108.2 s (f3135–3250) | The title is a caption plate across the middle of the topology, with no design of its own. |
| V5A-CIN-04 | 67–70 s (f2040) | The session window is a blank pale panel. |

Also noted, no finding: the returning CA certificate passes behind the fading caption for about three frames at 46.0 s (f1380) as it rises to the crown; the validity bar and AIA/CDP ports on end-entity cards are too small to tell from text lines at viewing size.

## Images used (13 of 14)

`qa\v5b\icon-legend.png`; four 3x3 beat sheets (36 frames); two native-resolution icon sheets (18 crops); the CA 2 doorway strip (f2440–2500); the hero and title sheet (f2941–3250); the cuts and root reveal sheet; the hardware sheet; the label sheet; one 2x2 half-resolution sheet for V5A-LEG-01/02. The sheets were scratch files and are not kept.
