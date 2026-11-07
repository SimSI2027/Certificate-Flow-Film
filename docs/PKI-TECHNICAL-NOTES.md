# PKI technical notes

This document gives the full technical meaning of every beat, including the complete explanation behind any shortened on-screen wording. It is a frozen file (with `docs/REFERENCE-SPEC.md` and `docs/GLOSSARY.md`). IDs refer to the reference spec. Model IDs (`CERT-RDP`, `E-04.3a`, …) refer to `cff/story/model.py`, as dumped in the round packets.

## Lab names and the .lab suffix

The lab uses the AD domain `1SN0S.LAB` (NetBIOS `1SN0S`) and the DNS suffix `1sn0s.lab`. DNS names are case-insensitive (RFC 4343), so SAN dNSNames appear in lower case, as they normally do in certificates.

**Status of `.lab` in the DNS root zone (checked 2026-11-06).** Three sources were checked:
- The IANA TLD list `https://data.iana.org/TLD/tlds-alpha-by-domain.txt` (version 2026110600, "Last Updated Fri Nov 6 07:07:01 2026 UTC") does not list `LAB`.
- The root zone file `https://www.internic.net/domain/root.zone` (SOA serial 2026110602) contains no delegation for `lab.`.
- The IANA Root Zone Database page `https://www.iana.org/domains/root/db/lab.html` returns HTTP 404.

So at the time of writing, `.lab` is **not delegated** in the public DNS root.

**Collision risk.** A private suffix that is not delegated today can be delegated publicly later. If that happened:
- lab queries that leak to public DNS could resolve to someone else's hosts
- names in internal certificates could then also exist publicly

Public CAs do not issue certificates for internal names, so the lab's names come only from its own PKI.

**`.internal`.** ICANN has permanently reserved `.internal` for private use. ICANN Board resolution 2024.07.29.06, of 29 July 2024, "reserves .INTERNAL from delegation in the DNS root zone permanently to provide for its use in private-use applications". A new deployment might choose it.

**Decision.** The lab keeps `1SN0S.LAB` / `1sn0s.lab` unchanged, as the charter requires. This note records the risk.

## Architecture in one page

| Component | Role | Model |
|---|---|---|
| `1SN0S Root CA` | Offline, standalone, non-domain-joined. Self-signed certificate. Trust anchor. Signs only issuing CA certificates (offline ceremony) and its own CRL. | `ROOT_CA`, `CERT-ROOT`, `CRL-ROOT` (AR-01, AR-02) |
| `1SN0S Issuing CA 1` | Enterprise subordinate CA. Its certificate is signed by the root (CA=true). Publishes `RDPAuth` only. | `ISSUING_CA1`, `CERT-CA1`, `CRL-CA1` (AR-03, AR-04) |
| `1SN0S Issuing CA 2` | Enterprise subordinate CA. Its certificate is signed by the root (CA=true). Publishes `WebServer-TLS` only. | `ISSUING_CA2`, `CERT-CA2`, `CRL-CA2` (AR-03, AR-04) |
| AD `1SN0S.LAB` on `DC01` | Authenticates requesters (Kerberos). Stores templates, permissions and Enrollment Services objects. Distributes the root to Trusted Root stores. | `AD` (AR-05) |
| `pki.1sn0s.lab` | HTTP publication point for AIA (issuer certificates) and CDP (CRLs). | `PKI_HTTP`, `SVC-AIA`, `SVC-CDP` (AR-06) |
| Online Responder | Not deployed. Shown only as "OCSP if deployed". | `SVC-OCSP` (AR-07) |
| `rdp01.1sn0s.lab` | RDP server (`RDP01`). Owns its key pair and RDP certificate. | `RDP_SERVER`, `KP-RDP`, `CERT-RDP` |
| `WEB01` serving `portal.1sn0s.lab` | Web server. Owns its key pair and TLS certificate. | `WEB_SERVER`, `KP-WEB`, `CERT-WEB` |
| `CLIENT01` | The user's domain-joined laptop. Relying party for both connections. | `CLIENT`, `TS-CLIENT-ROOT` |

**Certificates in the story.**

| Certificate | Subject / SAN | Issuer (signed with) | EKU | Basic Constraints | AIA → | CDP → |
|---|---|---|---|---|---|---|
| `CERT-ROOT` | CN=1SN0S Root CA | itself (root key) | none (unrestricted) | CA=true | — | — |
| `CERT-CA1` | CN=1SN0S Issuing CA 1 | Root CA | none (unrestricted) | CA=true | `http://pki.1sn0s.lab/pki/1SN0S-Root-CA.crt` | `http://pki.1sn0s.lab/pki/1SN0S-Root-CA.crl` |
| `CERT-CA2` | CN=1SN0S Issuing CA 2 | Root CA | none (unrestricted) | CA=true | same as CA 1 | same as CA 1 |
| `CERT-RDP` | CN=rdp01.1sn0s.lab; SAN dNSName=rdp01.1sn0s.lab | Issuing CA 1 | Remote Desktop Authentication 1.3.6.1.4.1.311.54.1.2 | not a CA | `http://pki.1sn0s.lab/pki/1SN0S-Issuing-CA-1.crt` | `http://pki.1sn0s.lab/pki/1SN0S-Issuing-CA-1.crl` |
| `CERT-WEB` | CN=portal.1sn0s.lab; SAN dNSName=portal.1sn0s.lab | Issuing CA 2 | Server Authentication 1.3.6.1.5.5.7.3.1 | not a CA | `http://pki.1sn0s.lab/pki/1SN0S-Issuing-CA-2.crt` | `http://pki.1sn0s.lab/pki/1SN0S-Issuing-CA-2.crl` |
| `CERT-RDP-SELF` | CN=rdp01.1sn0s.lab (no SAN is modelled or shown) | itself (its own separate key `KP-RDP-SELF`) | Server Authentication | not a CA | — | — |

URL file names are illustrative. ADCS also offers LDAP AIA/CDP locations by default. This lab publishes HTTP locations, which suit any client and are common practice. The offline root's CRL and certificate are copied to `pki.1sn0s.lab` by an administrator, because the root has no network connection.

**Templates.**

| Template | Published on | EKU | Subject | Who may enroll | Trigger |
|---|---|---|---|---|---|
| `RDPAuth` | Issuing CA 1 only | Remote Desktop Authentication | Built from AD: the computer object's DNS name, as subject and SAN dNSName | RDP server computer accounts (Read + Enroll) | Group Policy RDP server authentication certificate template setting |
| `WebServer-TLS` | Issuing CA 2 only | Server Authentication | Supplied in the request | Authorized web-server accounts only (restricted Enroll) | An authorized request for the web server |

`RDPAuth` is a custom template, commonly made by duplicating a computer template and setting its Application Policies to Remote Desktop Authentication. `WebServer-TLS` is a duplicate of the built-in Web Server template.

Because `WebServer-TLS` lets the requester choose the subject, restricted Enroll permission is essential. Anyone who could enroll could ask for any name. For the same reason, it must not add client-authentication or other logon-capable EKUs.

## Beats

### B-01.1
**On screen:** the user at `CLIENT01` opens RDP. Caption *Secure RDP connection*.

**Meaning:** the user starts the Remote Desktop client and connects to `rdp01.1sn0s.lab` by its FQDN (F-01). That typed name is the one the client later compares with the certificate's SAN dNSName (B-06.4, check 4), so connecting by FQDN matters.

The caption names the goal: an RDP connection whose server identity the client can verify. RDP's security layer runs the connection inside TLS. With NLA, CredSSP then authenticates the user over that TLS channel, so server authentication protects the user's credentials.

Kerberos server authentication is out of scope on screen (F-16; see "Kerberos scope" below).

### B-01.2
**On screen:** an amber pulse travels the floor channel to the server rack.

**Meaning:** a network connection is being set up (TCP 3389, then RDP and TLS negotiation). Amber means pending: nothing is verified or trusted yet. The floor channel is a network connection. It is never used for trust relationships, which are shown as trust links.

### B-02.1
**On screen:** arrival at `rdp01.1sn0s.lab`; the RDP listener lights up. Caption *The RDP server needs a trusted identity*.

**Meaning:** the Remote Desktop service on `RDP01` accepts the connection. The server, not the client, owns and presents the certificate used for server authentication (F-01). The caption states the problem: the server needs a certificate that clients can validate up to a root they already trust.

### B-02.2
**On screen:** a pale self-signed card with only its own self-seal; the client shows it as unverified; the channel stays amber. The attempt then ends and the amber pulse dies out.

**Meaning:** out of the box, the Remote Desktop service creates a self-signed certificate for the computer, with Server Authentication EKU (`CERT-RDP-SELF`, with its own key pair `KP-RDP-SELF`) (F-02).

The certificate *is* signed, by its own private key. What it lacks is an issuer the client already trusts. It is not in the client's Trusted Root store, and no CA that chains to a trusted root vouches for it. So the certificate cannot be validated through the PKI; that is what the "Unverified" tag means. Where Kerberos server authentication is unavailable (see "Kerberos scope" below), the Remote Desktop client then warns ("The identity of the remote computer cannot be verified"), depending on its server-authentication setting. In this lab's exact configuration (a domain-joined client, a domain-joined server, an FQDN and NLA), Kerberos would usually authenticate the server, and no warning would appear. The film depicts the certificate-based case. The film shows nothing being accepted.

The root certificate (B-05.1) is also self-signed. The difference is not the signature but the fact that the root was deliberately installed as a trust anchor (B-06.2).

A TLS handshake carries exactly one server Certificate message. This attempt therefore ends here, because the user does not accept the warning (model `E-02.2c`, connection closed). The trusted connection in S6 is a **new** connection attempt, with a new handshake that presents the CA-issued certificate.

### B-02.3
**On screen:** an `RDPAuth` template badge drops from the AD node onto the RDP server.

**Meaning:** a Group Policy setting applies to the RDP server: Computer Configuration → Administrative Templates → Windows Components → Remote Desktop Services → Remote Desktop Session Host → Security → *Server authentication certificate template*. It names the template `RDPAuth`.

The policy is stored in AD and SYSVOL on the domain controller and applied by the server during policy processing. With it, the Remote Desktop service enrolls for, and then uses, a certificate based on that template (F-05).

The badge represents the template *name* being assigned. No certificate and no key comes from AD. `RDPAuth` builds the subject from AD (F-07).

**Order of events.** Enrollment is driven by policy processing on the server, independently of any client connection, and in practice normally before users connect. The client's failed attempt in B-02.2 did not cause it. The film shows the problem first and the server-side fix second for narrative clarity. No client connection is pending while the server enrolls (S3–S4).

### B-03.1
**On screen:** a key pair forms inside the server chassis. Caption *The private key stays on the server*.

**Meaning:** enrollment starts by generating a new key pair on `RDP01`, in a machine key container of the server's key storage provider (F-03). The key pair is generated locally; no other machine ever generates or receives it.

This is a new key pair. It is not the self-signed certificate's key from B-02.2.

Before generating the key, the enrollment client reads the `RDPAuth` template definition from the AD enrollment policy. The definition covers the key algorithm and size, the key storage provider and the subject rules, so the key and request are built to the template's requirements. That read is part of the policy-driven enrollment introduced in B-02.3. It is not shown as a separate visual. The later lookup in B-04.1 is the **CA-selection** step: which CA publishes the template.

### B-03.2
**On screen:** the private key, with its lock motif, settles into a locked key container and is anchored.

**Meaning:** the private key stays in the machine key container (`KEY-RDP-PRIV` stored in `KP-RDP`). It is never exported, copied into a request, or sent over the network (F-03). Later, the issued certificate is associated with this key in place (F-09).

### B-03.3
**On screen:** the public key and request information enter a glass capsule. Caption *The request is signed, not the key sent*.

**Meaning:** the enrollment client builds a certificate request (F-04). It is PKCS #10, which ADCS enrollment commonly wraps in CMC. It contains:
- the public key
- the requested template (as a request attribute)
- request information

Because `RDPAuth` builds the subject from AD, the server does not need to supply a subject (F-07). The request never contains the private key.

The caption compresses two facts:
- the request is *signed* with the private key (proof of possession)
- the *key itself is not sent*

### B-03.4
**On screen:** a beam of light from the private key's container seals the capsule; the key does not move.

**Meaning:** the requester signs the request's content with its private key (F-04). This proves possession: whoever holds the matching private key made this request for this public key.

The CA verifies the signature with the public key inside the request (part of B-04.3 check 4). The beam is the act of signing. No key material leaves the container (F-03).

### B-04.1
**On screen:** the capsule pauses, framed against the AD node `1SN0S.LAB`. A steel-blue query asks "who publishes RDPAuth?", and a route lights to Issuing CA 1 only.

**Meaning:** before submitting, the enrollment client discovers eligible CAs from AD (F-05, AR-05). It reads the Enrollment Services objects in the Configuration partition, which list each enterprise CA and the templates it publishes. Only Issuing CA 1 publishes `RDPAuth` (AR-04), so only Issuing CA 1 is eligible (F-14).

The client does not send to a CA that does not publish the template, and it does not pick a CA arbitrarily. If several CAs published the template, the client would choose among those eligible ones.

The capsule has not been submitted. It waits at the server's outbound port while the separate query runs. AD answers a lookup; it does not receive, sign or forward the request.

### B-04.2
**On screen:** the capsule travels along the lit route into the Issuing CA 1 vault (cyan).

**Meaning:** the enrollment client submits the signed request to Issuing CA 1 (an authenticated DCOM/RPC request in ADCS enrollment). The submission is authenticated as the RDP server's computer account using Kerberos.

The capsule carries the public key and request information only (F-04). It never touches the Root CA, which no end-entity request reaches (AR-02).

### B-04.3
**On screen:** four staggered ticks:
1. *Requester authenticated*
2. *Template published on this CA*
3. *Enroll permission granted*
4. *Request meets template policy*

Caption *Issuing CA 1 verifies, then signs*.

**Meaning:** arriving at a CA is never sufficient (F-06). The enterprise CA:
1. **Authenticates the requester.** The request arrives over an authenticated connection, and the CA knows it comes from the `RDP01` computer account in `1SN0S.LAB` (Kerberos via the domain controller).
2. **Confirms the template is published on this CA.** `RDPAuth` is in Issuing CA 1's published templates.
3. **Confirms Enroll permission.** The requester has Enroll on the `RDPAuth` template, and the Request Certificates permission on the CA.
4. **Confirms the request satisfies the template's policy.** This covers:
   - the request is well formed
   - its proof-of-possession signature verifies with the enclosed public key
   - the key meets the template's algorithm and size rules
   - any issuance requirements are met

Because `RDPAuth` builds the subject from AD, the CA looks up the computer object and takes its DNS name for the subject and SAN (F-07). It does not use names from the request. Only after all four checks does it sign.

### B-04.4
**On screen:** the request capsule is consumed at the press. Issuing CA 1's key stays in a sealed module and drives a press that stamps the card. The card shows SAN `rdp01.1sn0s.lab`, the Remote Desktop Authentication EKU, a validity bar and small AIA/CDP ports.

The request ends its life here (model `E-04.4a`). The CA records the request and the issued certificate in its database. The request is never forwarded anywhere, and it never appears again; in particular, it is not in the S5 flashback.

**Meaning:** the CA signs the end-entity certificate (`CERT-RDP`) with Issuing CA 1's private key. That key stays in the CA's protected key storage (an HSM or the CA's KSP) and never leaves it (F-03). The press represents the signing operation; nothing from the key is stamped onto the card except the signature.

The certificate contains:
- subject CN=rdp01.1sn0s.lab and SAN dNSName=rdp01.1sn0s.lab (from AD; F-07)
- EKU Remote Desktop Authentication, 1.3.6.1.4.1.311.54.1.2 (F-08). RDP would also accept Server Authentication, 1.3.6.1.5.5.7.3.1.
- a validity period
- not-a-CA Basic Constraints
- the AIA extension (where to get Issuing CA 1's certificate)
- the CDP extension (where to get Issuing CA 1's CRL), both on `pki.1sn0s.lab` (AR-06)

### B-04.5
**On screen:** the card returns and locks in beside the private key.

**Meaning:** the CA returns the issued certificate in the enrollment response. The enrollment client installs it in `LocalMachine\My` and associates it with the private key generated in B-03.1, which never moved (F-09, F-03).

The response also carries the issuing CA's certificate as part of its chain. The server stores this copy of `CERT-CA1` in its Intermediate Certification Authorities store (model `E-04.5c`; the copy is its own object, `CERT-CA1-COPY-RDP`, so the original on Issuing CA 1's crown never moves). This copy is what the server presents in B-06.1. It is shown as a translucent card, distinct from the CA's own certificate on Issuing CA 1's crown. (On domain members, issuing CA certificates published in AD can also reach the Intermediate store.)

(Docs only, F-09: the Remote Desktop service needs read access to that private key in order to use the certificate. When the Group Policy template setting is used, the service uses the enrolled certificate for RDP's TLS.)

### B-05.1
**On screen:** the camera cranes up to a sealed gold vault on its own cable-free plinth: `1SN0S Root CA`. A sweep of light reveals its existing self-signed seal, a ring that closes on itself. The seal does not animate closed, and the root's key module and press stay dark and still.

**Meaning:** the Root CA is offline, standalone and not domain-joined (AR-01). It is never connected to the network, which is why there are no cables. Its certificate is self-signed: it signs itself.

It is the **trust anchor** (F-17). That is not because it is self-signed, but because its certificate was deliberately placed in the Trusted Root store of every domain member (B-06.2, F-11). In the present-tense film the root performs no operation; the seal shows a property of the certificate, not a live signature.

### B-05.2
**On screen:** a desaturated flashback, marked "Earlier: offline signing ceremony". Issuing CA 1's own CA request is sealed by Issuing CA 1's key module. The capsule carries a cyan CA=true band and the tag "Issuing CA 1's own CA request". It travels on removable media to the root. From it, the root issues and signs Issuing CA 1's CA certificate offline, and the certificate is carried back. Caption *The Root CA signs the issuing CA certificate*.

The band and tag make the capsule unmistakably a different request from the RDP request. The RDP request was consumed inside Issuing CA 1 in B-04.4, long after this ceremony, and never travels to the root.

**Meaning:** this happened at setup, before the film's present (AR-02):
1. When Issuing CA 1 was installed as an enterprise subordinate CA, it generated its own key pair in its protected storage. It then produced a subordinate-CA certificate request (PKCS #10), signed with its own private key (proof of possession; F-04), as a request file.
2. An administrator carried the request file to the offline root on removable media.
3. The standalone root holds such requests pending until a CA administrator issues them. The administrator issued it, and the root signed `CERT-CA1` with the root private key, which never leaves the root (F-03). The certificate has Basic Constraints CA=true.
4. The administrator carried back on removable media:
   - the issued certificate
   - the root certificate
   - the root's current CRL
5. The CA certificate was installed on Issuing CA 1. The root certificate and CRL were published to `pki.1sn0s.lab` and AD.

Issuing CA 2 was certified the same way (not shown).

The request in the flashback is a subordinate-CA request. No end-entity request ever goes to the root, and the root never joins the network. Periodically, the root is started again offline to sign a fresh CRL, which is copied out the same way.

### B-05.3
**On screen:** back in the present, a gold-to-cyan link joins Issuing CA 1's certificate to the root. Caption *The Root CA is the trust anchor*.

**Meaning:** the link shows the "issued by" relationship. `CERT-CA1` is signed by the root key, so it chains to the root (AR-03, F-15). It is a trust relationship, not a network connection: the root stays cable-free.

The caption's "trust anchor" applies only to the root (F-17). Issuing CA 1 is trusted only because its certificate chains to the trust anchor.

### B-06.1
**On screen:** a new amber connection pulse runs from the client to the server. The server presents its card with its copy of Issuing CA 1's card. A key pulse glows inside the closed key container. The cards and a handshake proof (a signature impression, a shape unlike any key) travel to the client; the key stays. At the laptop, the impression is matched against the server card's public key and dissolves: the proof is verified.

**Meaning:** this is a **new** connection attempt (model `E-06.1a`), not the unverified attempt from S2, which ended in B-02.2. In the TLS handshake inside this RDP connection, the server sends its certificate chain: `CERT-RDP` plus the issuing CA certificate `CERT-CA1`. The root is not needed, because the client must already have it (F-10).

The server then proves it holds the private key for `CERT-RDP`'s public key by signing handshake data:
- in TLS 1.3, the CertificateVerify message
- in TLS 1.2 with ECDHE, the ServerKeyExchange signature

The client verifies that signature with the certificate's public key (model `E-06.1f`, shown as the impression matching the card and dissolving). The handshake proof on screen is this signature over handshake data. It is not key material. Tick 2 in B-06.4, *Signatures verify*, refers to the certificate signatures in the chain. The handshake proof has its own verification visual here. (Legacy TLS 1.2 static-RSA key exchange proves possession by decryption instead; it is not depicted.)

A certificate alone proves nothing, because certificates are public. Possession of the matching private key is what binds the connection to the certificate. The private key never leaves the server (F-03).

### B-06.2
**On screen:** on the laptop side the cards dock upward: server certificate → Issuing CA 1 → a gold root already in the Trusted Root store, with a brief "Installed earlier by policy" shimmer. Caption *The client validates the whole chain*.

**Meaning:** `CLIENT01` builds the chain (F-11):
- `CERT-RDP` is issued by Issuing CA 1
- `CERT-CA1` is issued by the root
- the root certificate is found in `CLIENT01`'s Trusted Root Certification Authorities store

The root was put there **earlier**, by AD publication or Group Policy (AR-05). `CLIENT01` is a domain member, and roots published to AD's Certification Authorities container, or deployed by a Group Policy Public Key Policy, are placed in members' trusted root store. The shimmer recalls that earlier step. It plays only on the card already sitting in the cradle; nothing travels from AD, and nothing is added to the trust store now (model `E-06.2c`: transport none, era recall).

The caption's "validates the whole chain" previews B-06.4–B-06.5. Building the chain does not prove identity; the name check does that (F-11, F-12).

### B-06.3
**On screen:** a small AIA indicator: "Missing intermediate? AIA can fetch it" and "Fetching never creates trust".

The kiosk is only highlighted passively as the place a fetch *could* go. Nothing is requested and nothing answers.

**Meaning:** if the server had not sent `CERT-CA1`, the client could read the AIA extension in `CERT-RDP` and download Issuing CA 1's certificate from `pki.1sn0s.lab` (AR-06).

Here the intermediate was presented, so nothing is fetched. Even when AIA is used, the downloaded certificate is only a chain-building aid. The chain must still end at a root already in the Trusted Root store. AIA never creates trust (F-11).

### B-06.4
**On screen:** staggered ticks:
1. *Chain ends at a trusted root*
2. *Signatures verify*
3. *Currently valid*
4. *Name matches rdp01.1sn0s.lab*
5. *EKU permits RDP*

A sixth tick, *Revocation OK*, appears as pending.

**Meaning:** path validation is a set of distinct checks (F-12):
1. **Chain ends at a trusted root.** The path terminates at a certificate in the Trusted Root store. This step of path validation also enforces Basic Constraints: `CERT-CA1` must have CA=true, and the end-entity certificate must not be a CA. It also rejects any certificate with an unrecognized critical extension. Those two checks are part of F-12, but have no tick of their own.
2. **Signatures verify.** `CERT-RDP`'s signature verifies with Issuing CA 1's public key, and `CERT-CA1`'s with the root's public key.
3. **Currently valid.** Every certificate in the chain is within its validity period.
4. **Name matches `rdp01.1sn0s.lab`.** The name the user connected to matches a SAN dNSName in `CERT-RDP`. This is the identity check. It is separate from chain building: a valid chain for a different name would fail here.
5. **EKU permits RDP.** `CERT-RDP` carries Remote Desktop Authentication. RDP also accepts Server Authentication (F-08).
6. **Revocation OK.** Pending, resolved in B-06.5.

### B-06.5
**On screen:** two amber CRL fetches from the CDP, one per link, and a small "OCSP if deployed" tag. The revocation tick resolves.

**Meaning:** revocation is checked for each link (F-13):
- `CERT-RDP` against Issuing CA 1's CRL, downloaded from the CDP in `CERT-RDP`
- `CERT-CA1` against the Root CA's CRL, downloaded from the CDP in `CERT-CA1`

The root is not revocation-checked; nothing above it could revoke it.

Each CRL is signed by its issuer, and the client verifies that signature and the CRL's freshness (nextUpdate). Issuing CAs may also publish delta CRLs, which the client would also consult. The film shows one fetch per link. CRLs are cached, so a real client may not download them on every connection.

CDP/CRL is the ADCS default (AR-06). OCSP would be used only if an Online Responder were deployed (AR-07); none is. The "OCSP if deployed" tag therefore sits on the client's revocation check slot, not on the `pki.1sn0s.lab` kiosk, and the model gives the undeployed responder no host.

### B-06.6
**On screen:** the channel turns green; the session window opens. Caption *Trusted RDP connection established*.

**Meaning:** all checks passed on this new connection, so the client accepts the server's identity (F-12). The TLS session completes. With NLA, the user's credentials are then sent through CredSSP inside this authenticated channel, and the remote session opens. Green appears only now.

### B-07.1
**On screen:** the camera glides to `WEB01`, which serves `portal.1sn0s.lab` and carries a `WebServer-TLS` badge.

**Meaning:** a second workload. The web server needs a TLS certificate for the site name `portal.1sn0s.lab` (F-14). The `WebServer-TLS` template is chosen by an authorized request for this server: for example, an administrator using the certificate snap-in or `certreq`, under an account allowed to enroll. Templates whose subject is supplied in the request are not used for autoenrollment.

### B-07.2
**On screen:** a local key pair; the private key is locked and anchored; the request is sealed by proof of possession.

**Meaning:** the same rules as S3 (F-03, F-04). `WEB01` generates its key pair locally, and the private key stays in its key container. Here the request carries the subject `CN=portal.1sn0s.lab` and SAN dNSName `portal.1sn0s.lab`, because `WebServer-TLS` takes the subject from the request (F-07). The request is signed with the private key. The key is not sent.

### B-07.3
**On screen:** AD shows both CAs. Issuing CA 1 dims to grey ("WebServer-TLS not published here"); Issuing CA 2 lights violet. Eligibility tags: *Template published*, *Enrollment policy*, *Permissions*, *CA available*. Caption *Different templates can use different issuing CAs*.

**Meaning:** discovery again comes before sending (F-05). The enrollment client reads the enrollment policy from AD. It considers only CAs whose Enrollment Services object lists `WebServer-TLS` (AR-04), for a template on which the requester has Enroll permission. It then picks a CA that is available.

The four tags name these conditions:
- **Template published:** the template is listed on the CA.
- **Enrollment policy:** the template and CA come from the AD enrollment policy.
- **Permissions:** the requester may enroll.
- **CA available:** the CA is online and reachable.

Issuing CA 1 does not publish `WebServer-TLS`, so it is ineligible. Only Issuing CA 2 qualifies (F-14). As in B-04.1, AD answers a lookup and never handles the request.

### B-07.4
**On screen:** the capsule travels only to Issuing CA 2.

**Meaning:** the request goes only to the eligible CA (F-05). It never goes to Issuing CA 1 and never to the root.

### B-08.1
**On screen:** a compressed version of the four checks, with the note "Name supplied in request — enrollment restricted".

**Meaning:** Issuing CA 2 runs the same four checks as in B-04.3 (F-06):
1. It authenticates the requester.
2. It confirms `WebServer-TLS` is published on it.
3. It confirms Enroll permission (restricted to authorized web-server accounts), plus Request Certificates on the CA.
4. It confirms the request meets the template policy, including the proof-of-possession signature.

The note compresses F-07. This template takes the subject and SAN from the request, so the CA will issue whatever name an allowed requester asks for. That is why Enroll is restricted to authorized web-server accounts. (A CA certificate manager approval step is also possible, but is not depicted.)

### B-08.2
**On screen:** the web request capsule is consumed at the press. Issuing CA 2's key-driven press stamps the TLS card (SAN `portal.1sn0s.lab`, Server Authentication EKU). It returns and locks beside the web server's private key. Caption *Issuing CA 2 signs the TLS certificate*.

**Meaning:** Issuing CA 2 signs `CERT-WEB` with its own private key, which stays in its protected storage (F-03). The certificate has:
- subject and SAN `portal.1sn0s.lab`
- EKU Server Authentication, 1.3.6.1.5.5.7.3.1 (F-08)
- not-a-CA Basic Constraints
- AIA and CDP pointing to Issuing CA 2's certificate and CRL on `pki.1sn0s.lab`

It is installed in `WEB01`'s `LocalMachine\My` with the existing private key (F-09), and bound to the site's HTTPS listener. As in B-04.5, the response chain gives `WEB01` its own copy of `CERT-CA2` for its Intermediate store (model `E-08.2e`, object `CERT-CA2-COPY-WEB`). That copy is what it presents in B-09.1.

### B-08.3
**On screen:** Issuing CA 2's own certificate is revealed, linked in gold to the same root.

**Meaning:** `CERT-CA2` was signed by the same Root CA at setup, in an offline ceremony like B-05.2 (not shown). It already existed before Issuing CA 2 signed anything, and it sits dimmed on Issuing CA 2's crown from B-07.3. B-08.3 is a reveal sweep of that existing certificate and its issuer relationship. The root does nothing now: its key module and press stay dark here and in B-09.2. Both issuing paths therefore terminate at one root (F-15, AR-03). The link is a trust relationship; the root stays cable-free.

### B-09.1
**On screen:** a quick browser validation: `portal.1sn0s.lab` → Issuing CA 2 → Root. Compressed ticks for name, EKU, validity and revocation (with one CRL fetch per non-root link). The channel turns green.

**Meaning:** the same validation as S6, faster (F-10–F-13):
- The browser on `CLIENT01` connects to `https://portal.1sn0s.lab`.
- After the connection arrives, the web server sends `CERT-WEB` and its copy of `CERT-CA2`, and proves possession of its private key in the handshake. The client verifies the proof (model `E-09.1q`).
- The client builds the chain to the same pre-installed root.
- Chain-to-root and signature checks are conveyed by the docking, without ticks of their own. Basic Constraints and critical extensions are checked as in B-06.4.
- The ticks show the name (`portal.1sn0s.lab` matches the SAN dNSName), EKU (Server Authentication) and validity.
- Revocation is checked per link: `CERT-WEB` against Issuing CA 2's CRL, and `CERT-CA2` against the Root's CRL. The root itself is not checked. The revocation tick resolves only after both CRLs have arrived.

**Browser caveat (docs only).** Browser revocation behaviour depends on the browser and on policy:
- Chromium-based browsers do not perform online CRL/OCSP checks by default. Enterprise policy can require them for locally installed anchors (`RequireOnlineRevocationChecksForLocalAnchors`).
- Firefox does not use CDP CRLs.

The film depicts a client configured to check CDP/CRL for each link, consistent with F-13. The Remote Desktop client in S6 uses the Windows certificate chain engine, which checks revocation.

### B-09.2
**On screen:** the hero topology: the root on top, both issuing CAs, the RDP server under CA 1, the web server under CA 2, and the user using both. Cyan and violet trust paths rise and converge in gold at the single root. Caption *Different issuing paths. One trusted root.*

**Meaning:** two templates, two eligible issuing CAs, two end-entity certificates (F-14), and one trust anchor (F-15, F-17). The paths are trust links ("issued by"), not network cables. The offline root has no network connection in the hero shot either.

### B-09.3
**On screen:** the title card *Certificate Flow — From request to trust*; a gentle settle and fade.

**Meaning:** the close. The subtitle summarises the film's arc: a locally generated key, a signed request, CA checks and issuance, and validation up to a trust anchor the client already holds (F-15).

## Kerberos scope (F-16)

A domain-joined client that connects by FQDN to a domain-joined RDP server, with NLA, can authenticate the server through Kerberos as part of CredSSP. In that case the Remote Desktop client may show no warning even when the server uses its self-signed certificate.

**This lab's configuration is that case.** `CLIENT01` and `RDP01` are both domain-joined, the user connects by FQDN, and NLA is in use. Kerberos would therefore usually satisfy server authentication here.

The film deliberately depicts **certificate-based server authentication**: the server identity proven and validated through the PKI. In practice, certificate-based server authentication is what applies whenever Kerberos server authentication is unavailable. Examples:
- connecting by IP address, or by a name that has no matching service principal name (for example a DNS alias)
- connecting from a client that is not domain-joined
- the domain controller being unreachable

The charter's F-16 also mentions the case where "policy requires a trusted certificate". These notes do not tie that case to any single named Windows setting. It stands for an organisation's requirement that RDP servers present PKI-validated certificates whether or not Kerberos is available, and it is not depicted as a specific configuration.

On screen, the "Unverified" tag in B-02.2 means that the self-signed certificate cannot be validated through the PKI. It does not claim that every client would warn. Nothing on screen claims that Kerberos is absent or irrelevant; the scope is stated here.

## Shortened on-screen wording

| On screen | Full meaning |
|---|---|
| *Secure RDP connection* | An RDP connection whose TLS server identity the client can verify through the PKI. |
| *The RDP server needs a trusted identity* | It needs a certificate issued by a CA that chains to a root the client already trusts. |
| *The private key stays on the server* | The private key is generated and kept in the server's key container; it is never exported or sent. |
| *The request is signed, not the key sent* | The request carries the public key and is signed with the private key (proof of possession); the private key is not in it. |
| *Issuing CA 1 verifies, then signs* | The CA authenticates the requester and checks publication, Enroll and Request Certificates permissions and template policy. Only then does it sign with its own key. |
| *The Root CA signs the issuing CA certificate* | At setup, the offline root signed Issuing CA 1's CA certificate in an offline ceremony. It signs only CA certificates and its own CRL. |
| *The Root CA is the trust anchor* | Only the root's certificate is trusted directly, because it is in every member's Trusted Root store; everything else chains to it. |
| *The client validates the whole chain* | Path validation: chain to the trusted root, signatures, validity, Basic Constraints and critical extensions, name match, EKU, and revocation of each non-root link. |
| *Trusted RDP connection established* | All checks passed and the server proved possession of its key, so the TLS channel is authenticated and the session opens. |
| *Different templates can use different issuing CAs* | Each template is published on specific CAs; clients send only to an eligible CA that publishes the template. |
| *Issuing CA 2 signs the TLS certificate* | Issuing CA 2 issues the `WebServer-TLS` end-entity certificate after the same four checks. |
| *Different issuing paths. One trusted root.* | Both issuing CAs chain to the same Root CA, the single trust anchor. |
| *Requester authenticated* | The CA knows, through AD and Kerberos, which account submitted the request. |
| *Template published on this CA* | The template is listed in this CA's published templates (its Enrollment Services object). |
| *Enroll permission granted* | Enroll on the template and Request Certificates on the CA. |
| *Request meets template policy* | The request is well formed, its proof-of-possession signature verifies, and its key and contents satisfy the template. |
| *Chain ends at a trusted root* | Path validation to a certificate in the Trusted Root store, including Basic Constraints and critical-extension handling. |
| *Signatures verify* | Each certificate's signature verifies with its issuer's public key. |
| *Currently valid* | Each certificate is within its validity period. |
| *Name matches …* | The name the client connected to matches a SAN dNSName (identity check). |
| *EKU permits RDP* / *EKU permits TLS server auth* | The end-entity certificate's EKU allows the purpose: Remote Desktop Authentication or Server Authentication for RDP, and Server Authentication for TLS. |
| *Revocation OK* | Each non-root certificate was checked against its issuer's CRL (via CDP); none is revoked. |
| *Installed earlier by policy* | AD publication or Group Policy put the root into the Trusted Root store before this connection. |
| *Missing intermediate? AIA can fetch it* / *Fetching never creates trust* | AIA locates the issuer's certificate for chain building only. |
| *OCSP if deployed* | An Online Responder could answer status queries instead of CRLs; none is deployed here. |
| *WebServer-TLS not published here* | Issuing CA 1's Enrollment Services object does not list that template, so it is ineligible. |
| *Name supplied in request — enrollment restricted* | The requester chooses the subject/SAN, so only authorized web-server accounts have Enroll. |
| *Earlier: offline signing ceremony* | A flashback to setup: the subordinate-CA request was carried to the offline root on removable media. |
| *Issuing CA 1's own CA request* | The subordinate-CA certificate request generated by Issuing CA 1 at setup, signed with Issuing CA 1's own key. It is not an end-entity request. |

## Fact index

Where each fact is depicted (generated detail is in `docs/TRACEABILITY.md`):
- F-01: B-01.1, B-01.2, B-02.1, B-02.2, B-06.1, B-06.6
- F-02: B-02.2
- F-03: B-03.1, B-03.2, B-03.4, B-04.4, B-04.5, B-05.2, B-06.1, B-07.2, B-08.2
- F-04: B-03.3, B-03.4, B-04.2, B-05.2, B-07.2
- F-05: B-02.3, B-04.1, B-04.2, B-07.3, B-07.4
- F-06: B-04.3, B-08.1
- F-07: B-02.3, B-04.3, B-04.4, B-07.1, B-08.1
- F-08: B-04.4, B-06.4, B-08.2
- F-09: B-04.5, B-08.2
- F-10: B-06.1, B-09.1
- F-11: B-05.1, B-06.2, B-06.3, B-09.1
- F-12: B-06.4, B-06.6, B-09.1
- F-13: B-06.5, B-09.1
- F-14: B-04.1, B-07.1, B-07.3, B-07.4, B-09.2
- F-15: B-05.3, B-08.3, B-09.2, B-09.3
- F-16: docs only (Kerberos scope)
- F-17: B-05.1, B-05.3, B-09.2
- AR-01: B-05.1. AR-02: B-05.2. AR-03: B-05.3, B-08.3. AR-04: B-04.1, B-07.3. AR-05: B-04.1, B-04.3, B-06.2, B-07.3. AR-06: B-04.4, B-06.3, B-06.5. AR-07: B-06.5.
