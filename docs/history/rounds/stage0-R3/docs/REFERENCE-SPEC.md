# Reference spec

This is the frozen reference spec for Certificate-Flow-Film: the "real-data distribution" every discriminator judges against (Charter 2.1–2.2). It holds:
- the architecture statements AR-01..AR-07
- the PKI facts F-01..F-17
- the beats B-01.1..B-09.3
- the cinematic criteria C-01..C-11
- the legibility criteria L-01..L-08

`docs/GLOSSARY.md` is part of the spec. `docs/PKI-TECHNICAL-NOTES.md` gives the full technical meaning behind every beat and every shortened on-screen wording.

**Change control.** The SHA-256 of this file is recorded in `docs/GAN-LEDGER.md` when Stage 0 freezes. After that:
- any change needs a written Chief of Staff amendment in the ledger, with its reason
- the new hash is recorded
- the current stage's clean-round counter resets to zero

The generator never edits this file to make a finding go away.

**What is frozen.** The following are frozen:
- the IDs and their text
- scene order and scene durations
- beat order and beat content
- caption wording
- the criteria thresholds

Beat start/end times inside a scene and event timings are owned by `cff/story/timing.py`; `docs/STORYBOARD.md` and `docs/TRACEABILITY.md` list them. They may be retimed without amendment, provided that:
- scene durations hold
- beat order holds
- L-04 holds

## Names in use

From `cff/config/names.py`. Fallbacks are marked; placeholder text is never rendered. A name change is a names update, not a spec amendment, but every document must then be updated in the same commit.

| Variable | Value | Fallback? |
|---|---|---|
| `AD_DOMAIN_FQDN` | `1SN0S.LAB` | no |
| `AD_NETBIOS` | `1SN0S` | no |
| `DNS_SUFFIX` | `1sn0s.lab` | no |
| `DC_HOSTNAME` | `DC01` | yes |
| `CLIENT_HOSTNAME` | `CLIENT01` | yes |
| `RDP_SERVER_HOSTNAME` | `RDP01` | yes |
| `WEB_SERVER_HOSTNAME` | `WEB01` | yes |
| `WEB_SITE_DNS_NAME` | `portal.1sn0s.lab` | yes |
| `ROOT_CA_NAME` | `1SN0S Root CA` | yes |
| `ISSUING_CA1_NAME` | `1SN0S Issuing CA 1` | yes |
| `ISSUING_CA2_NAME` | `1SN0S Issuing CA 2` | yes |
| `PKI_HTTP_HOST` | `pki.1sn0s.lab` | yes |
| `RDP_TEMPLATE` | `RDPAuth` | no |
| `WEB_TEMPLATE` | `WebServer-TLS` | no |

Derived (lower-case hostname + `.` + DNS suffix): `RDP_SERVER_FQDN` = `rdp01.1sn0s.lab`, `WEB_SERVER_FQDN` = `web01.1sn0s.lab`, `DC_FQDN` = `dc01.1sn0s.lab`, `CLIENT_FQDN` = `client01.1sn0s.lab`.

The `.lab` suffix and its status in the IANA root zone are covered in `docs/PKI-TECHNICAL-NOTES.md`, section "Lab names and the .lab suffix".

## Severities

- **BLOCKER**: wrong PKI; any violation involving a private key or the Root CA; a blank or broken frame; an unreadable required caption; a shot judged DIAGRAM in Stage 4 or later.
- **MAJOR**: misleading PKI; weak film quality; readability problems; broken continuity.
- **MINOR**: polish.

A beat verdict of **WRONG** is a BLOCKER. A verdict of **MISLEADING** is at least MAJOR. **ACCURATE** means a knowledgeable ADCS engineer would find nothing to correct.

## Architecture

### AR-01 Root CA
`1SN0S Root CA` is an offline, standalone, non-domain-joined Root CA. Its certificate is self-signed. It is the **trust anchor**. It has no live network connection at any time in the film. On screen: a sealed gold vault on its own plinth, with no cables or network channels.

### AR-02 What the Root CA signs
The Root CA signs only:
- the issuing CA certificates, in an offline ceremony during setup (request and certificate carried on removable media)
- its own CRL, published periodically

It never signs end-entity certificates. It never receives an end-entity request.

### AR-03 Issuing CAs
`1SN0S Issuing CA 1` and `1SN0S Issuing CA 2` are enterprise subordinate (intermediate) issuing CAs:
- their CA certificates are signed by the Root CA
- their certificates carry Basic Constraints CA=true
- they are online and domain-joined
- they are **not** trust anchors

### AR-04 Template publication
- `RDPAuth` is published only on Issuing CA 1.
- `WebServer-TLS` is published only on Issuing CA 2.
- The Root CA publishes no templates: a standalone CA does not use templates.

### AR-05 Active Directory
Active Directory `1SN0S.LAB` (domain controller `DC01`):
- authenticates requesters (Kerberos, computer accounts)
- stores the certificate templates and their permissions
- stores the Enrollment Services objects, which list which CA publishes which template
- distributes the root certificate to domain members' Trusted Root Certification Authorities store (by AD publication or Group Policy)

AD does not receive, sign or forward certificate requests.

### AR-06 AIA and CDP
AIA and CDP are HTTP locations on `pki.1sn0s.lab`, embedded as extensions in the certificates the CAs issue:
- AIA gives the location of the issuer's certificate.
- CDP gives the location of the issuer's CRL.

The root certificate itself carries neither. Publication points are passive file locations, never trust sources.

### AR-07 OCSP
OCSP appears only as "if an Online Responder is deployed". No Online Responder is deployed in this lab.

## PKI facts

The film must never contradict these.

### F-01 Who initiates and who presents
The user initiates RDP from `CLIENT01`. The **RDP server** (`rdp01.1sn0s.lab`) owns and presents the RDP certificate. The client never owns, requests or presents the server's certificate.

### F-02 The problem
Out of the box, RDP uses a **self-signed** certificate the client cannot verify. That is the problem being solved. The self-signed certificate *is* signed (by its own key); what it lacks is an issuer the client already trusts.

### F-03 Keys stay home
- Each server generates its key pair locally.
- **Private keys never leave their owner.**
- CA private keys never leave their CA's protected key storage.
- No private key is ever shown inside a request, a certificate, a channel, a beam or any moving object.

### F-04 The request
A certificate request (PKCS #10, inside CMC for ADCS enrollment):
- contains the public key and request information
- is **signed with the requester's private key** (proof of possession)
- never contains the private key

### F-05 Policy trigger and CA discovery
For RDP, enrollment is triggered by policy: Group Policy's RDP server authentication certificate template setting names `RDPAuth`. Before sending, the enrollment client **discovers eligible CAs from AD**. It never sends to a CA that does not publish the template, and it never picks a CA arbitrarily.

### F-06 CA checks before signing
Before signing, the issuing CA:
1. **authenticates the requester**
2. confirms the **template is published on this CA**
3. confirms **Enroll permission** (on the template, plus Request Certificates on the CA)
4. confirms the **request satisfies the template's policy** (this includes verifying the request's proof-of-possession signature)

Arriving at a CA is never sufficient.

### F-07 Subject and identity
- `RDPAuth` **builds the subject and SAN from AD**: the computer object's DNS name.
- `WebServer-TLS` is based on the Web Server template, so the **subject is supplied in the request**. Because of that, Enroll permission is restricted to authorized web-server accounts.

### F-08 Extended Key Usage
- `RDPAuth` uses the **Remote Desktop Authentication EKU (1.3.6.1.4.1.311.54.1.2)**.
- RDP also accepts Server Authentication (1.3.6.1.5.5.7.3.1). Both are documented.
- `WebServer-TLS` uses **Server Authentication (1.3.6.1.5.5.7.3.1)**.

### F-09 Installation
The issued certificate goes into the computer's Personal store (`LocalMachine\My`), associated with the existing private key, which never moves. (Docs only: the Remote Desktop service needs read access to that private key.)

### F-10 Presentation and proof of possession
During the TLS handshake the server:
- sends its certificate, normally together with the issuing CA certificate (the root is not needed)
- **proves possession of the private key** by signing as part of the handshake

A certificate alone proves nothing.

### F-11 Chain building
The client builds the chain upward to a root that is **already present** in its Trusted Root store.
- If the intermediate certificate is missing, **AIA may fetch it. AIA never creates trust.**
- Building a chain does not prove identity.

### F-12 Validation checks
Validation is a set of distinct checks:
- the chain terminates at a trusted root
- each signature verifies with its issuer's public key
- each certificate is within its validity period
- Basic Constraints are correct (the issuing CA certificate has CA=true; the end-entity certificate is not a CA)
- unknown critical extensions cause rejection
- **the name matches the SAN dNSName** (identity — a separate check)
- the **EKU** permits the purpose
- **revocation** is acceptable

The connection becomes trusted only after all of them pass.

### F-13 Revocation per link
Revocation is checked for each link:
- the end-entity certificate against the issuing CA's CRL (via its CDP)
- the issuing CA certificate against the Root's CRL (via its CDP)
- the root itself is not revocation-checked

CDP/CRL is the ADCS default; OCSP is optional.

### F-14 Different templates, different CAs
Different templates can be issued by different eligible issuing CAs.

### F-15 One root
Both issuing paths terminate at the same Root CA.

### F-16 Kerberos scope (docs, not on screen)
A domain-joined client connecting by FQDN with NLA can authenticate the server through Kerberos. It may then show no warning even for a self-signed certificate. The film depicts **certificate-based server authentication**, for example where Kerberos server authentication is unavailable or policy requires a trusted certificate.

### F-17 Terminology
- "end-entity certificate", never "sub certificate"
- "subordinate/intermediate issuing CA"
- "trust anchor" is used for the root only

## Beats

Scene durations are frozen (total 109 s). Each beat's caption wording is frozen. "Accuracy constraint" lines are part of the beat.

### S1 — The connection begins (7 s)

#### B-01.1 User opens RDP
A night-lit desk. The stylized low-poly user at `CLIENT01` opens an RDP connection to `rdp01.1sn0s.lab`.
- Accuracy constraint: the user connects by the server's FQDN, which is the name later matched against the SAN.
- Caption: *Secure RDP connection*

#### B-01.2 Connection pulse
An amber connection pulse travels along a floor light-channel toward a distant rack; the camera follows it. Amber means pending: nothing is trusted yet.

### S2 — An identity the client can't verify (7 s)

#### B-02.1 Listener lights
Arrival at `rdp01.1sn0s.lab`; the RDP listener lights up.
- Caption: *The RDP server needs a trusted identity*

#### B-02.2 Self-signed, unverified
A pale self-signed card appears at the listener. It carries only its own self-seal and no issuer seal. The client side shows it as unverified. The connection stays amber; nothing has been accepted. The attempt then ends: the user does not accept, and the amber pulse dies out of the channel.
- Accuracy constraint: the card is not shown as unsigned. It is shown as signed only by itself.
- Accuracy constraint: one connection attempt presents one server certificate. This unverified attempt is closed; the trusted connection in S6 is a new attempt.

#### B-02.3 Template from policy
An `RDPAuth` template badge drops in from policy (from the AD node, where Group Policy lives) onto the RDP server.
- Accuracy constraint: enrollment is driven by Group Policy processing on the server. The client's connection does not cause it, and no client connection is pending while the server enrolls (S3–S4).

### S3 — Keys born locally, request sealed (10 s)

#### B-03.1 Key pair forms
A key pair forms inside the RDP server chassis.
- Caption: *The private key stays on the server*

#### B-03.2 Private key anchored
The private key settles into a locked key container and is visibly anchored. It has a distinct shape with a lock motif.

#### B-03.3 Request assembled
The public key and the request information enter a glass request capsule. The private key stays in its container.
- Caption: *The request is signed, not the key sent*

#### B-03.4 Proof of possession
A beam from the private key **seals** the capsule (proof of possession). The key does not move. The beam is light emitted from the container; no key-shaped object travels.

### S4 — Finding the right CA, then evaluation (14 s)

#### B-04.1 Who publishes RDPAuth?
The capsule pauses at the server's outbound port, framed with the AD node (`1SN0S.LAB`). A lookup for "who publishes RDPAuth?" lights a route to Issuing CA 1 only.
- Accuracy constraint: the request has not been submitted and is not sent to AD. The capsule is held at the RDP server's outbound port, framed together with the AD node. The lookup is a separate steel-blue query pulse that travels to AD and back. The answer comes from the Enrollment Services objects. The capsule never enters the AD node, and AD neither receives, signs nor forwards the request.

#### B-04.2 Into Issuing CA 1
The capsule travels into the Issuing CA 1 vault (cyan), along the lit route only.

#### B-04.3 Four checks
Four checks resolve with staggered ticks:
1. Requester authenticated
2. Template published on this CA
3. Enroll permission granted
4. Request meets template policy

- Caption: *Issuing CA 1 verifies, then signs*

#### B-04.4 CA signs
The request capsule is consumed at the press: the request ends its life inside Issuing CA 1 and never reappears. Issuing CA 1's own key stays in a sealed module and drives a signing press, which stamps a certificate card. The card shows:
- the SAN `rdp01.1sn0s.lab`
- the Remote Desktop Authentication EKU
- a validity bar
- small AIA/CDP ports

#### B-04.5 Certificate installed
The card returns and locks into the server **beside** the existing private key, forming one identity. The key has not moved. A translucent copy of Issuing CA 1's certificate arrives with it (the enrollment response chain) and settles into the server's intermediate store. The original stays on the CA's crown.

### S5 — The hierarchy and the trust anchor (12 s)

#### B-05.1 The trust anchor
The camera cranes up to a sealed gold vault on its own plinth, **with no cables**: `1SN0S Root CA`. Its self-signed seal, a ring that closes on itself, is revealed by a sweep of light as an existing property.
- Accuracy constraint: the root is offline and performs no signing in the present-tense part of the film. The seal does not animate closed. The root's key module does not glow and its press does not move outside the flashback.

#### B-05.2 Offline ceremony (flashback)
A desaturated flashback of setup, clearly marked as earlier. Issuing CA 1's own CA-certificate request is carried to the root on removable media. From it, the root issues and signs Issuing CA 1's CA certificate offline, and the certificate is carried back.
- Caption: *The Root CA signs the issuing CA certificate*
- Accuracy constraint: this is a subordinate-CA request, sealed by Issuing CA 1's own key. It is not an end-entity request. The flashback is the only cut in the film (C-02).
- Accuracy constraint: the CA request has its own visible identity. It carries a cyan CA=true band and a must-read tag, "Issuing CA 1's own CA request", and it is shown being sealed by Issuing CA 1's own key module. The RDP request was consumed in B-04.4 and never appears in the flashback.

#### B-05.3 Issuer link
Back in the present, a gold-to-cyan link joins Issuing CA 1's certificate to the root. No end-entity request ever travels to the root.
- Caption: *The Root CA is the trust anchor*
- Accuracy constraint: the link is a trust (issuer) relationship, not a network cable. The root stays cable-free.

### S6 — Presentation and validation (20 s)

#### B-06.1 Presentation
A new connection attempt: a fresh amber pulse runs from the client to the server. In this new handshake, the server presents its certificate together with Issuing CA 1's certificate. A key pulse inside the closed key container shows proof of possession; the key does not move. No key material travels. The cards and a handshake proof (a signature impression, a shape distinct from every key) travel to the client. The intermediate card is the server's own copy from B-04.5. On arrival, the client matches the impression against the server certificate's public key (proof verified), and the impression dissolves.

#### B-06.2 Chain builds
On the laptop side the cards dock upward: server certificate → Issuing CA 1 → a gold root **already** in the Trusted Root store. The root is shown with a brief "installed earlier by policy" memory shimmer.
- Caption: *The client validates the whole chain*

#### B-06.3 AIA is not trust
A small AIA indicator shows the "missing intermediate? fetch it" possibility. It is clearly not a trust source. Nothing is fetched here, because the intermediate was presented.

#### B-06.4 Validation checks
Staggered checks:
1. Chain ends at a trusted root
2. Signatures verify
3. Currently valid
4. Name matches `rdp01.1sn0s.lab`
5. EKU permits RDP
6. Revocation OK

Checks 1–5 resolve here. Check 6 appears as pending and resolves in B-06.5.

#### B-06.5 Revocation per link
During check 6, two amber CRL fetches come from the CDP, one for each link:
- Issuing CA 1's CRL, for the server certificate
- the Root CA's CRL, for Issuing CA 1's certificate

A small "OCSP if deployed" tag appears. There is no fetch for the root.

#### B-06.6 Trusted session
The new connection's channel turns from amber to green and the session window opens.
- Caption: *Trusted RDP connection established*

### S7 — A second workload (12 s)

#### B-07.1 Web server
The camera glides to `WEB01` (serving `portal.1sn0s.lab`), which has a `WebServer-TLS` badge.

#### B-07.2 Local key, sealed request
A local key pair forms. The private key is locked and anchored, and the request is sealed by proof of possession.

#### B-07.3 Eligibility
The AD lookup shows both CAs:
- Issuing CA 1 dims to muted grey ("WebServer-TLS not published here").
- Issuing CA 2 illuminates in violet. Its existing CA certificate is already on its crown, dimmed.
- Eligibility tags: template published, enrollment policy, permissions, CA available.

The same accuracy constraint as B-04.1 applies: the lookup is a query to AD, and the request is not sent to AD.
- Caption: *Different templates can use different issuing CAs*

#### B-07.4 Only to Issuing CA 2
The capsule travels **only** to Issuing CA 2.

### S8 — Issuing CA 2 signs (11 s)

#### B-08.1 Compressed checks
Faster, compressed versions of the same four checks, including the note "name supplied in request — enrollment restricted".

#### B-08.2 TLS certificate
The web request capsule is consumed at the press. Issuing CA 2's key-driven press stamps the TLS certificate (SAN `portal.1sn0s.lab`, Server Authentication EKU). It returns and locks beside the web server's private key, with a translucent copy of Issuing CA 2's certificate for the server's intermediate store.
- Caption: *Issuing CA 2 signs the TLS certificate*

#### B-08.3 Same root
Issuing CA 2's own certificate is revealed, linked in gold to the **same** root.
- Accuracy constraint: the certificate already existed (it is on the crown, dimmed, from B-07.3). It was issued in an offline ceremony like B-05.2, which is not shown. The link reveals an existing issuer relationship. The root does nothing: its key module and press stay dark here and in B-09.2.

### S9 — Full picture and close (16 s)

#### B-09.1 Browser validation
A quick browser validation (about 5 s):
- `portal.1sn0s.lab` → Issuing CA 2 → Root
- the server presents its chain and proves possession, and the client verifies the proof
- compressed ticks: name, EKU, validity, revocation (with one CRL fetch per non-root link)
- the channel turns green

The chain-to-root and signature checks are conveyed by the docking and are listed in the notes.

#### B-09.2 Hero topology
A wide hero shot of the complete topology:
- the Root on top
- Issuing CA 1 and Issuing CA 2 below it
- the RDP server under CA 1 and the web server under CA 2
- the user consuming both services
- two trust paths (cyan and violet) rising and converging in gold at the single root

The trust paths are trust links, not network cables; the root stays cable-free.
- Caption: *Different issuing paths. One trusted root.*

#### B-09.3 Close
Title card: *Certificate Flow — From request to trust*. A gentle settle and fade, with a clean end.

## Cinematic criteria

Each criterion has a requirement, a measurement and a pass threshold. "Beat hold" means a beat's frames excluding its first and last 0.5 s. World units are metres. Thresholds apply at every render tier, unless one is stated as 1080p (scale pixel values linearly at other tiers).

### C-01 No diagram grammar
- **Requirement.** No arrows or connector-diagram grammar. Relationships are shown by motion, docking, light and the camera.
- **Measurement.** Two parts:
  - A scene audit of every object.
  - The cinema-discriminator's per-shot verdict.
- **Threshold.**
  - 0 arrowhead meshes, curves or glyphs (→ ⇒ ▶).
  - Every line-like object is a network channel (floor conduit) or a trust link from the shape vocabulary, and grows or flows when introduced.
  - 0 static straight connectors drawn between nodes.
  - 0 shots judged DIAGRAM for C-01.

### C-02 One continuous camera
- **Requirement.** One continuous camera. No hard cuts, except the motivated flashback in S5.
- **Measurement.** One camera object. Per-frame camera transform deltas.
- **Threshold.**
  - Exactly 1 camera.
  - Per-frame translation ≤ 4% of the camera-to-focus distance.
  - Per-frame rotation ≤ 2°.
  - Focal-length change ≤ 0.5 mm per frame.
  - No frame-to-frame change in speed greater than 25% of that move's peak speed.
  - Exactly 2 cuts in the film, at the start of B-05.2 (into the flashback) and the start of B-05.3 (out of it). A cut is a translation above 10% of the focus distance, or a rotation above 5°, between consecutive frames.

### C-03 One focal subject
- **Requirement.** Every shot has one clear focal subject, established with depth of field, light and composition.
- **Measurement.** The model's declared focal subject per beat (`focal`), projected bounds, and the focus distance.
- **Threshold.**
  - During each beat hold, the focal subject's projected bounding-box centre lies inside x, y ∈ [0.15, 0.85] of the frame on ≥ 90% of frames.
  - |focus distance − focal-subject distance| ≤ 10% of the subject distance on ≥ 90% of frames.
  - The discriminator names the same subject.

### C-04 Depth layers
- **Requirement.** Foreground, midground and background layers with parallax.
- **Measurement.** Visible-object depths per beat; screen motion during camera moves.
- **Threshold.**
  - In ≥ 90% of beats, at least 1 visible object lies nearer than 0.7× the focal distance, and at least 1 lies farther than 1.5× it. B-09.3's fade is exempt.
  - During every camera move longer than 1 s, the screen-space speed of the nearest layer is ≥ 1.5× that of the farthest layer.

### C-05 Motivated lighting
- **Requirement.** Motivated key and rim lighting. No flat, ambient-only lighting.
- **Measurement.** A light audit per scene; luminance samples on the focal subject.
- **Threshold.**
  - Each scene has ≥ 1 key light and ≥ 1 rim or back light (≥ 120° from the camera direction around the subject).
  - World and ambient contribution ≤ 20% of key-light illuminance at the focal subject.
  - The focal subject's lit-side : shadow-side luminance ratio is between 2:1 and 8:1.

### C-06 Eased motion
- **Requirement.** Eased motion with no pops or jitter. Exits are slightly faster than entrances.
- **Measurement.** An F-curve audit, plus per-frame screen displacement of visible objects.
- **Threshold.**
  - 100% of keyframes are Bézier with a named easing preset; LINEAR only on whitelisted constant-speed channels.
  - 0 NaN or Inf values; keys strictly ordered.
  - Each entrance animates ≥ 2 of location, scale and emission; 0 opacity-only entrances.
  - Exit duration is 0.6–0.9× the matching entrance duration.
  - No visible object moves more than 5% of the frame width between consecutive frames, except whitelisted fast effects (pulses, fetches).
  - Staggered ticks in one check list are evenly spaced within ±1 frame.
  - Idle micro-motion amplitude ≤ 2% of object size.

### C-07 Object continuity
- **Requirement.** Object continuity across scenes.
- **Measurement.** Object identity and positions at scene boundaries.
- **Threshold.**
  - Each persistent subject (request capsules, certificate cards, keys, key containers, vaults, nodes) is one object for its whole life.
  - 0 appearances or disappearances without an entrance or exit animation.
  - At every scene boundary, no persistent object jumps more than the C-06 pop threshold.
  - The moving capsule or trust link leads the camera on travel beats.

### C-08 Restraint
- **Requirement.** Restraint in glow, haze and particles.
- **Measurement.** Image statistics per frame; a particle audit.
- **Threshold.**
  - ≤ 1.5% of pixels clipped (all channels ≥ 0.98) per frame.
  - Haze raises mean background luminance by ≤ 0.06 compared with the same frame without haze.
  - Particle effects only where whitelisted, with ≤ 1 active at a time.
  - Film grain amplitude ≤ 2% of the signal.

### C-09 Not a template or slide
- **Requirement.** Never template-like or slide-like.
- **Measurement.** A camera audit, a layout audit and the discriminator verdict.
- **Threshold.**
  - The beauty camera is always perspective, with focal length 24–50 mm.
  - No frame shows ≥ 3 same-size flat cards arranged in a regular grid within 10° of facing the camera.
  - The camera is never exactly frontal (both yaw and pitch relative to the focal subject < 2°) for more than 2 s.
  - 0 shots judged DIAGRAM for C-09.

### C-10 Colour language
- **Requirement.** Consistent colour language (Charter Section 8):
  - Root: warm gold
  - Issuing CA 1: cyan
  - Issuing CA 2: violet
  - requests: bright neutral white
  - validated paths: green
  - pending connection: amber
  - revocation checks: restrained amber
  - ineligible routes: muted grey
  - AD node: steel blue
- **Measurement.** A material audit against the palette tokens, plus rendered samples.
- **Threshold.**
  - 100% of role-coloured objects use their role token.
  - Green appears only after the corresponding validation completes.
  - Amber appears only on pending connections and revocation fetches.
  - Grey appears only on ineligible routes and CAs.
  - Rendered role samples stay within CIEDE2000 ΔE ≤ 10 of the palette test frame.

### C-11 Greyscale-distinct shapes
- **Requirement.** A shape vocabulary that stays distinct even in greyscale. The 14 shapes are: request capsule, certificate card, public key, private key, key container, template badge, CA vault, root vault (on a cable-free plinth), trust link, network channel, validation tick, CRL scroll fetch, AIA indicator and handshake proof (a signature impression). The subordinate-CA request uses the request-capsule shape and is told apart by a CA=true band and its tag (B-05.2).
- **Measurement.** Binary silhouettes of the 14 shapes, normalised to equal bounding-box area and centred.
- **Threshold.**
  - Pairwise silhouette IoU ≤ 0.75 for every pair.
  - Private key vs public key IoU ≤ 0.6.
  - Handshake proof vs private key IoU ≤ 0.6, and handshake proof vs public key IoU ≤ 0.6.

## Legibility criteria

### L-01 Text size
- **Requirement.** Caption cap height ≥ 30 px at 1080p. In-world labels that must be read: ≥ 18 px cap height when on screen.
- **Measurement.** Projected glyph bounds of the capital letters.
- **Threshold.**
  - Captions: ≥ 30 px at 1920×1080 (≥ 15 px at 960×540).
  - Must-read labels (model `must_read_beats`): ≥ 18 px at 1080p throughout the moment they matter (L-06).

### L-02 Contrast
- **Requirement.** Contrast ≥ 4.5:1 against the sampled local background.
- **Measurement.** WCAG 2.x relative-luminance contrast between the text colour and the background, sampled in an 8 px band around the glyph bounds. The worst case is taken: the 95th-percentile background luminance for light text, or the 5th percentile for dark text. A caption plate, if used, counts as the background.
- **Threshold.** ≥ 4.5:1 for every caption and must-read label, on every sampled frame.

### L-03 Title-safe
- **Requirement.** All text inside the 90% title-safe area.
- **Measurement.** Projected text bounds.
- **Threshold.** At 1920×1080, x ∈ [96, 1824] and y ∈ [54, 1026] for every caption and in-world label that is on screen, on every frame.

### L-04 Caption duration
- **Requirement.** Each caption stays on screen for ≥ max(2.5 s, 0.35 s per word).
- **Measurement.** The full-opacity hold, excluding the fades. Words are tokens containing a letter or digit.
- **Threshold.** hold ≥ max(2.5 s, 0.35 s × words) for every caption, including the title card.

### L-05 One caption, clear of the action
- **Requirement.** One caption at a time, never covering the focal action.
- **Measurement.** Caption-layer alpha per frame; caption bounds against the focal subject's projected bounds.
- **Threshold.**
  - At most 1 caption with alpha > 0 on any frame.
  - ≥ 0.2 s fully clear between consecutive captions.
  - 0 frames where a caption's bounds intersect the focal subject's projected bounding box.

### L-06 Names readable when they matter
- **Requirement.** In-world names (hosts, templates, CAs) are readable at the moment they matter.
- **Measurement.** For each must-read label, during its `must_read_beats`.
- **Threshold.** The label is on screen for ≥ 1.5 s (or the whole beat, if shorter). During that time it:
  - meets L-01, L-02 and L-03
  - faces the camera within 35°
  - is ≥ 90% unoccluded
  - is in focus (circle of confusion ≤ 2 px at 1080p)

### L-07 Distinguishable colours
- **Requirement.** Key colours are distinguishable (CIEDE2000 ΔE ≥ 15 between role colours), including under simulated deuteranopia and protanopia.
- **Measurement.** Rendered samples of the 8 key role colours from the palette test frame, under three conditions:
  - normal vision
  - Machado et al. 2009 deuteranopia, severity 1.0
  - Machado et al. 2009 protanopia, severity 1.0

  The 8 key role colours are: root gold, CA 1 cyan, CA 2 violet, request white, validated green, pending amber, ineligible grey and AD steel blue.
- **Threshold.**
  - ΔE00 ≥ 15 for every pair, in all three conditions.
  - Revocation amber is a restrained variant of pending amber. That one pair needs only ΔE00 ≥ 5, and must also differ in shape (CRL scroll vs channel pulse).

### L-08 Terminology
- **Requirement.** Terminology matches the glossary.
- **Measurement.** A scan of every caption, label and spec document.
- **Threshold.**
  - 0 uses of the terms the glossary forbids.
  - "Trust anchor" appears only for the root.
  - Every PKI term on screen has a `docs/GLOSSARY.md` entry.
