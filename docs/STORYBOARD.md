# Storyboard

One continuous camera through a stylized 3D world, 109 s at 30 fps (frames 1–3270). The only cut is the motivated flashback in S5 (C-02). Beat content and caption wording follow `docs/REFERENCE-SPEC.md`. Times and frames come from `cff/story/timing.py`; a test checks that every heading below matches the model. Focal subjects are the model's `focal` IDs. The PKI meaning of every beat is in `docs/PKI-TECHNICAL-NOTES.md`.

## World blocking

These coordinates are non-binding. They are metres, with Z up. The topology must be kept exactly; distances may be tuned in the animatic.

| Element | Position | Notes |
|---|---|---|
| User and laptop `CLIENT01` | (-12, -8, 0) | Night-lit desk; the user is an adult office worker seated within reach of the keyboard (V4). The laptop lid carries the `CLIENT01` plate. Above the laptop sits the Trusted Root cradle that holds the gold root card from the start. |
| Floor light-channels | client → `RDP01`; client → `WEB01` | Network channels: floor conduits, amber while pending and green once validated. No channel goes near the root dais. |
| `rdp01.malawi.lab` rack | (0, 0, 0) | The chassis has a hinged front panel for the key cutaway, and an outbound port on the side that faces the AD node. |
| `WEB01` rack (serves `portal.malawi.lab`) | (9, 2, 0) | Same chassis family; a different plate. |
| AD node `MALAWI.LAB` (`DC01`) | (4, 6, 0) | A steel-blue directory column with Enrollment Services rings. It stands beside both servers' outbound ports, off the request routes. |
| Issuing CA 1 vault (cyan) | (-3, 14, 0) | An antechamber cradle for checks, a sealed key module, a signing press, and a crown that displays its CA certificate. |
| Issuing CA 2 vault (violet) | (11, 14, 0) | Same vault family, in violet. |
| Root vault (gold) | (4, 24, 6) | A sealed vault on a tall plinth on a raised dais, with open space all around. No conduits or cables touch it; only trust links reach it. |
| `pki.malawi.lab` kiosk (AIA/CDP) | (-8, 4, 0) | A small publication kiosk near the client side. |

**Camera rig.** One camera on a dolly/crane path, with a look-at target and an animated focus target. Lenses are 24–50 mm, with restrained f-stops (f/2–f/5.6). Moves are eased, and the moving subject (capsule, card, pulse or trust link) leads the camera on travel beats.

## S1 — The connection begins

### B-01.1 — User opens RDP (0–3 s, frames 1–90)
- **Shot:** a close three-quarter view of the user at a night-lit desk. The laptop glow lights the face area; behind, the room falls off into navy dark with the faint floor grid. The user types `rdp01.malawi.lab` and opens the connection.
- **Lens:** 50 mm, f/2.8
- **Camera move:** a slow push-in (about 0.3 m) with a slight arc to the right
- **Focal subject:** the user (`USER`)
- **Caption:** *Secure RDP connection* (`CAP-S1`)
- **Must-read text:** `CLIENT01`

### B-01.2 — Connection pulse (3–7 s, frames 91–210)
- **Shot:** an amber pulse leaves the laptop and drops into the floor light-channel. It runs toward the distant rack, which grows out of the haze.
- **Lens:** 35 mm, f/4
- **Camera move:** the camera drops to floor height and tracks alongside and behind the pulse, accelerating, then easing as the rack approaches. The pulse leads.
- **Focal subject:** the amber pulse on the RDP channel (`CH-RDP`)
- **Caption:** none (`CAP-S1` fades out at 5.3 s)

## S2 — An identity the client can't verify

### B-02.1 — Listener lights (7–9 s, frames 211–270)
- **Shot:** arrival at the rack front. The `rdp01.malawi.lab` host plate catches a rim light, and the RDP listener port lights amber.
- **Lens:** 35 mm, f/2.8
- **Camera move:** the dolly decelerates and rises into a low three-quarter view of the listener
- **Focal subject:** the RDP server (`RDP_SERVER`)
- **Caption:** *The RDP server needs a trusted identity* (`CAP-S2`)
- **Must-read text:** `rdp01.malawi.lab`

### B-02.2 — Self-signed, unverified (9–12 s, frames 271–360)
- **Shot:** a pale card rises at the listener. Its faint seal loops back on itself (self-signed), with no issuer seal and the label "Self-signed". The card slides along the amber channel to the laptop. Over the laptop, an "Unverified" tag lights, and the card hovers there, not accepted. The channel stays amber. The user does not accept: the card fades, and the amber pulse dies out of the channel as this attempt closes.
- **Lens:** 35 mm, f/2.8
- **Camera move:** the camera pans and trucks back along the channel so the laptop sits in the midground, with a rack focus from the card to the "Unverified" tag
- **Focal subject:** the self-signed certificate (`CERT-RDP-SELF`)
- **Caption:** none (`CAP-S2` continues to 12.8 s)
- **Must-read text:** "Self-signed", "Unverified"

### B-02.3 — Template from policy (12–14 s, frames 361–420)
- **Shot:** the channel is dark; no connection is pending. On the server's own policy refresh, an `RDPAuth` template badge drops from the AD node's direction and lands with a small settle on the RDP server's top plate.
- **Lens:** 35 mm, f/4
- **Camera move:** a crane up, tilting down as the badge lands, ending over the server
- **Focal subject:** the `RDPAuth` badge (`TPL-RDPAUTH`)
- **Caption:** none
- **Must-read text:** `RDPAuth`

## S3 — Keys born locally, request sealed

### B-03.1 — Key pair forms (14–16 s, frames 421–480)
- **Shot:** the chassis front panel swings open to a cutaway interior. Two key shapes condense from light inside: the private key, with its lock motif, and the public key, with an open, notched form.
- **Lens:** 50 mm, f/2.8
- **Camera move:** a slow push-in through the opened panel
- **Focal subject:** the new key pair (`KP-RDP`)
- **Caption:** *The private key stays on the server* (`CAP-S3a`)
- **Must-read text:** `Private key`, `Public key` (tags on the two key shapes; V1-PKI-03)

### B-03.2 — Private key anchored (16–18.5 s, frames 481–555)
- **Shot:** the private key settles into the key container. The lid closes, the lock turns and anchor clamps engage the container to the chassis frame.
- **Lens:** 50 mm, f/2
- **Camera move:** a slide left with a slight arc, holding the container centre-frame
- **Focal subject:** the private key (`KEY-RDP-PRIV`)
- **Caption:** none (`CAP-S3a` continues)

### B-03.3 — Request assembled (18.5–21 s, frames 556–630)
- **Shot:** a glass capsule opens beside the container. The public key and request-information tiles float in. The locked container stays in the soft foreground, still holding the private key.
- **Lens:** 50 mm, f/2.8
- **Camera move:** a rack focus from the container (foreground) to the capsule (midground) with a slow truck right
- **Focal subject:** the request capsule (`REQ-RDP`)
- **Caption:** *The request is signed, not the key sent* (`CAP-S3b`)

### B-03.4 — Proof of possession (21–24 s, frames 631–720)
- **Shot:** a white beam of light rises from the container to the capsule and a seal ring closes around it. The container never opens and the key never moves.
- **Lens:** 50 mm, f/2.8
- **Camera move:** a gentle pull-back, revealing container and capsule together
- **Focal subject:** the request capsule (`REQ-RDP`)
- **Caption:** none (`CAP-S3b` continues to 24.0 s)

## S4 — Finding the right CA, then evaluation

### B-04.1 — Who publishes the template? (24–27 s, frames 721–810)
- **Shot:** the sealed capsule moves to the server's outbound port and waits there in the foreground. The steel-blue AD node `MALAWI.LAB` stands behind it in the same frame. A small steel-blue query pulse, separate from the capsule, runs from the port to the AD node and back. Two Enrollment Services rings appear on the node. Only the ring for Issuing CA 1 lights, and a cyan route lights in the floor from the port toward Issuing CA 1. The capsule has not moved off the server.
- **Lens:** 35 mm, f/4
- **Camera move:** a pull-out from the chassis and a boom up over the server's shoulder, framing port and AD node
- **Focal subject:** the AD node (`AD`)
- **Caption:** none
- **Must-read text:** `MALAWI.LAB`, `RDPAuth`

### B-04.2 — Into Issuing CA 1 (27–29 s, frames 811–870)
- **Shot:** the capsule launches along the cyan route, which runs clear of the AD node, and glides into the Issuing CA 1 vault antechamber. The nameplate reads `MALAWI Issuing CA 1`.
- **Lens:** 35 mm, f/4
- **Camera move:** a chase dolly; the capsule leads, and the camera eases in as the vault door frames it
- **Focal subject:** the request capsule (`REQ-RDP`)
- **Caption:** none
- **Must-read text:** `MALAWI Issuing CA 1`

### B-04.3 — Four checks (29–33 s, frames 871–990)
- **Shot:** the capsule rests on the evaluation cradle. Four check slots on a curved rail resolve one after another with cyan ticks: *Requester authenticated*, *Template published on this CA*, *Enroll permission granted*, *Request meets template policy*.
- **Lens:** 35 mm, f/2.8
- **Camera move:** a slow 20° orbit around the cradle
- **Focal subject:** Issuing CA 1's evaluation cradle (`ISSUING_CA1`)
- **Caption:** *Issuing CA 1 verifies, then signs* (`CAP-S4`)
- **Must-read text:** the four check labels, `MALAWI Issuing CA 1`

### B-04.4 — CA signs (33–36 s, frames 991–1080)
- **Shot:** the request capsule dissolves into the press's intake and is gone for good. Deeper in the vault, Issuing CA 1's key glows inside a sealed module that stays shut. Its light drives a signing press through a linkage. The press stamps a certificate card, which shows the SAN `rdp01.malawi.lab`, "Remote Desktop Authentication", a validity bar and two small AIA/CDP ports.
- **Lens:** 50 mm, f/2.8
- **Camera move:** a push-in to the press at the stamp, then a tilt to read the card's fields
- **Focal subject:** the RDP certificate (`CERT-RDP`)
- **Caption:** none (`CAP-S4` continues to 35.3 s)
- **Must-read text:** `rdp01.malawi.lab`, "Remote Desktop Authentication"

### B-04.5 — Certificate installed (36–38 s, frames 1081–1140)
- **Shot:** the card returns along the cyan route to `rdp01.malawi.lab` and locks into the chassis beside the key container. The two glow together as one identity. A translucent copy of Issuing CA 1's certificate travels with it (the response chain) and settles into the server's intermediate slot. The original stays on the CA's crown.
- **Lens:** 35 mm, f/2.8
- **Camera move:** an eased return chase, settling on a chassis close-up
- **Focal subject:** the RDP certificate (`CERT-RDP`)
- **Caption:** none

## S5 — The hierarchy and the trust anchor

### B-05.1 — The trust anchor (38–41.5 s, frames 1141–1245)
- **Shot:** rising from the CA hall, a sealed gold vault appears on its own tall plinth, with open air and no cables around it. A slow sweep of light reveals its existing self-signed seal, a ring that closes on itself. The ring does not animate, and the root's key module and press stay dark and still. The nameplate reads `MALAWI Root CA`.
- **Lens:** 28 mm, f/4
- **Camera move:** a crane up about 6 m with a tilt up, easing to a hover
- **Focal subject:** the Root CA vault (`ROOT_CA`)
- **Caption:** none
- **Must-read text:** `MALAWI Root CA`

### B-05.2 — Offline ceremony (flashback) (41.5–46.5 s, frames 1246–1395)
- **Shot:** a cut into a desaturated, cooler flashback with a soft gate vignette, tagged "Earlier: offline signing ceremony". Inside Issuing CA 1's vault, its own key module seals a CA-request capsule. The capsule carries a cyan CA=true band and the tag "Issuing CA 1's own CA request", and is slotted into a removable-media cartridge. The cartridge is carried along a walkway (a footprint trail, never a conduit) to the root dais. The capsule is consumed at the root. From it, the root's sealed key drives its press, which issues and stamps Issuing CA 1's CA certificate (CA=true). The cartridge carries the certificate back to Issuing CA 1, which installs it in its crown.
- **Lens:** 35 mm, f/4
- **Camera move:** a gentle lateral glide following the cartridge out and back
- **Focal subject:** Issuing CA 1's CA request (`REQ-CA1`)
- **Caption:** *The Root CA signs the issuing CA certificate* (`CAP-S5a`)
- **Must-read text:** "Earlier: offline signing ceremony", "Issuing CA 1's own CA request"

### B-05.3 — Issuer link (46.5–50 s, frames 1396–1500)
- **Shot:** a cut back to the present, in full colour. From the root, a gold-to-cyan trust link grows down to Issuing CA 1's certificate on its vault crown. The root stays cable-free; the link is light, not cable.
- **Lens:** 28 mm, f/4
- **Camera move:** a tilt down and dolly back, holding the root and Issuing CA 1 together
- **Focal subject:** Issuing CA 1's certificate (`CERT-CA1`)
- **Caption:** *The Root CA is the trust anchor* (`CAP-S5b`)

## S6 — Presentation and validation

### B-06.1 — Presentation (50–53 s, frames 1501–1590)
- **Shot:** a new connection attempt. A fresh amber pulse runs from the laptop along the channel and arrives at `rdp01.malawi.lab`. The RDP certificate card and the server's translucent copy of Issuing CA 1's certificate lift from the chassis and set off back along the amber channel. Inside the closed key container, a key pulse glows, and a small handshake proof (a flat signature impression, unlike any key shape) follows the cards. At the laptop, the impression presses against the server card's public-key emblem, matches, rests by the card until the beat ends, and dissolves. The tag "Proof: private-key signature" rides with the impression from the server to the match (v1.3, F3-PKI-01).
- **Lens:** 35 mm, f/4
- **Camera move:** a long eased crane down from the hierarchy to the server, then a turn to follow the cards
- **Focal subject:** the RDP certificate (`CERT-RDP`)
- **Caption:** none
- **Must-read text:** "Proof: private-key signature"

### B-06.2 — Chain builds (53–57 s, frames 1591–1710)
- **Shot:** at the laptop, the cards dock upward in a short vertical stack: the server certificate, then Issuing CA 1 above it, then the gold root card, which was already sitting in the Trusted Root cradle above the laptop. A brief shimmer and the tag "Installed earlier by policy" mark the root card. The shimmer plays on the card in place; nothing travels from AD.
- **Lens:** 35 mm, f/2.8
- **Camera move:** the camera arrives with the cards and booms up with the docking
- **Focal subject:** the RDP chain (`CHAIN-RDP`)
- **Caption:** *The client validates the whole chain* (`CAP-S6a`)
- **Must-read text:** "Installed earlier by policy"

### B-06.3 — AIA is not trust (57–59 s, frames 1711–1770)
- **Shot:** the small AIA port on the server card glows softly, and the distant `pki.malawi.lab` kiosk is passively highlighted as the place a fetch could go. Nothing is requested, nothing answers, and nothing travels. Two small tags read "Missing intermediate? AIA can fetch it" and "Fetching never creates trust".
- **Lens:** 50 mm, f/2.8
- **Camera move:** a slight push to the card's port, with a rack focus to the tags
- **Focal subject:** the AIA indicator (`SVC-AIA`)
- **Caption:** none (`CAP-S6a` continues)
- **Must-read text:** both AIA tags

### B-06.4 — Validation checks (59–64 s, frames 1771–1920)
- **Shot:** six check slots beside the chain stack resolve one after another: *Chain ends at a trusted root*, *Signatures verify*, *Currently valid*, *Name matches rdp01.malawi.lab* and *EKU permits RDP*. The sixth slot, *Revocation OK*, appears with a pending amber ring.
- **Lens:** 35 mm, f/2.8
- **Camera move:** a slow vertical crane past the stack as the ticks resolve
- **Focal subject:** the RDP chain (`CHAIN-RDP`)
- **Caption:** none (`CAP-S6a` fades out at 63.3 s)
- **Must-read text:** the six check labels

### B-06.5 — Revocation per link (64–66.4 s, frames 1921–1992)
- **Shot:** two restrained-amber CRL scrolls are fetched from the `pki.malawi.lab` kiosk. One docks against the server certificate (Issuing CA 1's CRL) and one against Issuing CA 1's certificate (the Root CA's CRL). The root card gets none. A small "OCSP if deployed" tag appears on the revocation check slot (not at the kiosk). Once both scrolls have docked, the revocation tick resolves.
- **Lens:** 28 mm, f/4
- **Camera move:** a pull-back and pan to bring the kiosk into frame, then back to the stack
- **Focal subject:** the CDP fetches (`SVC-CDP`)
- **Caption:** none
- **Must-read text:** "OCSP if deployed", "Revocation OK"

### B-06.6 — Trusted session (66.4–70 s, frames 1993–2100)
- **Shot:** the new connection's channel turns from amber to green, from the laptop to the server, and the laptop screen opens the remote session window.
- **Lens:** 35 mm, f/2.8
- **Camera move:** a low tracking glide along the green channel toward the laptop screen
- **Focal subject:** the RDP channel (`CH-RDP`)
- **Caption:** *Trusted RDP connection established* (`CAP-S6b`)

## S7 — A second workload

### B-07.1 — Web server (70–73 s, frames 2101–2190)
- **Shot:** the camera leaves the desk and glides to the second rack, `WEB01`, whose plate also shows `portal.malawi.lab`. A `WebServer-TLS` badge lights on its top plate, set by an authorized request.
- **Lens:** 35 mm, f/4
- **Camera move:** a lateral glide from the desk across the floor to the web rack, easing to a three-quarter view
- **Focal subject:** the web server (`WEB_SERVER`)
- **Caption:** none
- **Must-read text:** `WEB01`, `portal.malawi.lab`, `WebServer-TLS`

### B-07.2 — Local key, sealed request (73–76 s, frames 2191–2280)
- **Shot:** a compressed echo of S3. The panel opens, a key pair forms, the private key locks into its container, the public key and request information (with the site name) enter a capsule, and a beam from the container seals it.
- **Lens:** 50 mm, f/2.8
- **Camera move:** a push-in through the panel, then a pull-out
- **Focal subject:** the web request capsule (`REQ-WEB`)
- **Caption:** none
- **Must-read text:** `Private key`, `Public key` (tags on the two key shapes; V1-PKI-03)

### B-07.3 — Eligibility (76–79.5 s, frames 2281–2385)
- **Shot:** the capsule waits at `WEB01`'s outbound port with the AD node behind it. A steel-blue query runs to AD and back. Both CA vaults come into view:
  - Issuing CA 1 dims to muted grey, with the tag "WebServer-TLS not published here".
  - Issuing CA 2 lights violet, with eligibility tags *Template published*, *Enrollment policy*, *Permissions* and *CA available*. Its existing CA certificate sits dimmed on its crown.
  - A violet route lights toward Issuing CA 2.
- **Lens:** 28 mm, f/4
- **Camera move:** a boom up to a wider view that holds both vaults
- **Focal subject:** the AD node (`AD`)
- **Caption:** *Different templates can use different issuing CAs* (`CAP-S7`)
- **Must-read text:** `MALAWI.LAB`, `WebServer-TLS`, `MALAWI Issuing CA 2`, the ineligible tag, the four eligibility tags

### B-07.4 — Only to Issuing CA 2 (79.5–82 s, frames 2386–2460)
- **Shot:** the capsule travels the violet route, clear of AD and of Issuing CA 1, into the Issuing CA 2 vault.
- **Lens:** 35 mm, f/4
- **Camera move:** a chase dolly with the capsule leading
- **Focal subject:** the web request capsule (`REQ-WEB`)
- **Caption:** none (`CAP-S7` fades out at 80.8 s)

## S8 — Issuing CA 2 signs

### B-08.1 — Compressed checks (82–85.5 s, frames 2461–2565)
- **Shot:** Issuing CA 2's cradle. The same four checks resolve faster in violet. Beside the Enroll tick, a note reads "Name supplied in request — enrollment restricted".
- **Lens:** 35 mm, f/2.8
- **Camera move:** a short orbit, quicker than in S4
- **Focal subject:** Issuing CA 2's evaluation cradle (`ISSUING_CA2`)
- **Caption:** none
- **Must-read text:** `MALAWI Issuing CA 2`, the four check labels, the note

### B-08.2 — TLS certificate (85.5–90 s, frames 2566–2700)
- **Shot:** the web request capsule dissolves into the press's intake. Issuing CA 2's sealed key drives its press, which stamps the TLS card (SAN `portal.malawi.lab`, "Server Authentication"). The card returns along the violet route and locks into `WEB01` beside its key container, with a translucent copy of Issuing CA 2's certificate for its intermediate slot.
- **Lens:** 50 mm, f/2.8, then 35 mm for the return
- **Camera move:** a push-in at the stamp, a tilt to read the fields, then an eased return chase
- **Focal subject:** the web certificate (`CERT-WEB`)
- **Caption:** *Issuing CA 2 signs the TLS certificate* (`CAP-S8`)
- **Must-read text:** `portal.malawi.lab`, "Server Authentication"

### B-08.3 — Same root (90–93 s, frames 2701–2790)
- **Shot:** a reveal sweep brightens Issuing CA 2's existing certificate, dimmed on its crown since B-07.3, and a gold-to-violet trust link is revealed between it and the same root. This reveals an existing issuer relationship. The root's key module and press stay dark.
- **Lens:** 28 mm, f/4
- **Camera move:** a crane up to frame Issuing CA 2's crown and the root together
- **Focal subject:** Issuing CA 2's certificate (`CERT-CA2`)
- **Caption:** none

## S9 — Full picture and close

### B-09.1 — Browser validation (93–98 s, frames 2791–2940)
- **Shot:** at the laptop, a browser window opens `portal.malawi.lab`. A pulse reaches `WEB01`, which then presents the TLS card and its copy of Issuing CA 2's card, with a quick handshake-proof impression that matches the TLS card at the laptop and dissolves. The cards dock up to the same gold root in the cradle. Compressed ticks resolve: *Name matches portal.malawi.lab*, *EKU permits TLS server auth*, *Currently valid* and *Revocation OK*, with two quick restrained-amber CRL flickers, one per non-root card. The web channel turns green.
- **Lens:** 35 mm, f/2.8
- **Camera move:** a crane down from the hierarchy, arcing to the laptop
- **Focal subject:** the web chain (`CHAIN-WEB`)
- **Caption:** none
- **Must-read text:** the four compressed check labels

### B-09.2 — Hero topology (98–104 s, frames 2941–3120)
- **Shot:** a wide, high three-quarter view of the whole world:
  - the root on top
  - Issuing CA 1 and Issuing CA 2 below it
  - `rdp01.malawi.lab` under Issuing CA 1 and `WEB01` under Issuing CA 2
  - the user at the desk, with both green channels

  Cyan and violet trust paths rise from the two servers' certificates through their issuing CAs and converge in gold at the single root. The root stays cable-free, and its key module and press stay dark.
- **Lens:** 24 mm, f/5.6
- **Camera move:** a slow rising arc to the hero position
- **Focal subject:** the Root CA (`ROOT_CA`)
- **Caption:** *Different issuing paths. One trusted root.* (`CAP-S9a`)

### B-09.3 — Close (104–109 s, frames 3121–3270)
- **Shot:** the arc eases to rest with a slight drift, and the world settles and fades to black under the title card.
- **Lens:** 24 mm, f/5.6
- **Camera move:** ease to rest, then hold
- **Focal subject:** the Root CA (`ROOT_CA`)
- **Caption:** title card *Certificate Flow — From request to trust* (`TITLE-S9`), fully gone at 108.5 s; the film ends on black at 109.0 s
