# Glossary

Part of the frozen reference spec (`docs/REFERENCE-SPEC.md`). On-screen wording and every document use these terms (L-08). Lab names are the values in use from `cff/config/names.py`.

## Terms not to use

| Do not use | Use instead | Why |
|---|---|---|
| "sub certificate", "child certificate" | **end-entity certificate** (or "server certificate" for a specific one) | Never used: "sub" suggests a subordinate CA, and end-entity certificates cannot issue certificates. |
| "leaf CA" | **subordinate (intermediate) issuing CA** | Never used: a CA is never a leaf. |
| "root of trust" | **trust anchor** (for the Root CA only) | Never used: only the root's certificate is trusted directly, and the glossary term is "trust anchor". |
| "trusted" for an issuing CA or AIA by itself | "chains to the trusted root" | An issuing CA is trusted only through the chain to the trust anchor. |
| "sending the key", "the key travels" | "the request is signed", "proof of possession" | Private keys never move (F-03). |
| "AD signs" or "AD forwards the request" | "the enrollment client asks AD which CA publishes the template" | AD is consulted; it never handles the request (AR-05). |

## PKI and ADCS terms

### Active Directory Certificate Services (ADCS)
The Windows Server role that runs certification authorities and integrates them with Active Directory: templates, enrollment and publication.

### Active Directory (AD)
The directory service of the domain `1SN0S.LAB` (NetBIOS `1SN0S`), hosted on the domain controller `DC01`. In this story it authenticates requesters with Kerberos and stores the certificate templates, their permissions and the Enrollment Services objects. It also distributes the root certificate to domain members.

### Certification authority (CA)
A service that signs certificates and CRLs with its private key.

### Root CA
The CA at the top of the hierarchy: `1SN0S Root CA`. Its certificate is self-signed. In this lab it is offline, standalone and not domain-joined, and it signs only the issuing CA certificates and its own CRL.

### Trust anchor
A certificate a relying party trusts directly, because it was deliberately placed in that party's trusted root store. Here, only the Root CA's certificate. Being self-signed does not make a certificate a trust anchor; being installed as trusted does.

### Subordinate (intermediate) issuing CA
A CA whose own certificate is signed by another CA (here, by the root), with Basic Constraints CA=true. `1SN0S Issuing CA 1` and `1SN0S Issuing CA 2` are enterprise subordinate issuing CAs. They are not trust anchors. On screen: "Issuing CA 1", "Issuing CA 2".

### Standalone CA
A CA that does not use AD or certificate templates. Requests are typically held pending until an administrator issues them. The offline root is a standalone CA.

### Enterprise CA
A domain-joined CA that uses certificate templates and AD for authentication, permissions and publication. Both issuing CAs are enterprise CAs.

### End-entity certificate
A certificate issued to a subject that is not a CA (a server, user or device). It cannot be used to issue other certificates. The RDP and TLS server certificates are end-entity certificates.

### Self-signed certificate
A certificate signed with the private key that matches its own public key. Both the root certificate and RDP's out-of-the-box certificate are self-signed. The difference is that the root was deliberately installed as a trust anchor, while RDP's self-signed certificate was not, so the client cannot verify it.

### Certificate template
An AD object that defines what an enterprise CA will issue: EKU, subject rules, key requirements, validity and permissions. `RDPAuth` and `WebServer-TLS` are templates.

### Template publication
Configuring an enterprise CA to issue a given template. Publication is recorded in that CA's Enrollment Services object in AD. A CA issues only templates published on it.

### Enrollment Services object
The AD object (in the Configuration partition, under Public Key Services) that represents one enterprise CA and lists the templates it publishes. Enrollment clients read these objects to find eligible CAs.

### Enrollment
Requesting and receiving a certificate: generate a key pair, build and sign a request, submit it to an eligible CA, and install the issued certificate.

### Enrollment policy
The information an enrollment client retrieves (here, from AD) that tells it which templates it may request and which CAs offer them.

### Enroll permission
The template permission that allows a security principal to request certificates based on that template. It is separate from Read and Autoenroll.

### Request Certificates permission
The CA permission that allows a principal to submit requests to that CA.

### Certificate request (PKCS #10, CMC)
The message a requester sends to a CA:
- **PKCS #10** is the certification request format: the subject public key, request attributes and a signature by the requester's private key.
- **CMC** (Certificate Management over CMS) is the wrapper ADCS enrollment clients commonly use around PKCS #10.

A request never contains the private key.

### Proof of possession
Evidence that the requester holds the private key matching the public key in the request: the request is signed with that private key. In TLS, the server proves possession by signing handshake data.

### Key pair
A private key and its matching public key, generated together on the owner's machine.

### Private key
The secret half of a key pair. It never leaves its owner (F-03). On screen it has a distinct shape with a lock motif, and stays in its key container.

### Public key
The shareable half of a key pair. It goes into the request and then into the certificate.

### Key container
The protected storage that holds a private key:
- on a server, a machine key container of a key storage provider (KSP)
- on a CA, its protected key storage, either a hardware security module (HSM) or the CA's KSP

### Key storage provider (KSP)
The Windows cryptographic provider that creates, stores and uses keys without exposing them.

### Subject
The identity a certificate names, for example `CN=rdp01.1sn0s.lab`.

### Subject Alternative Name (SAN)
A certificate extension that lists the subject's names. Clients match the name they connected to against the SAN dNSName entries.

### dNSName
The SAN entry type that holds a DNS host name, for example `rdp01.1sn0s.lab` or `portal.1sn0s.lab`. DNS names are case-insensitive (RFC 4343) and shown in lower case.

### Extended Key Usage (EKU)
A certificate extension listing the purposes a certificate may be used for. The two here:
- **Remote Desktop Authentication**: `1.3.6.1.4.1.311.54.1.2`
- **Server Authentication**: `1.3.6.1.5.5.7.3.1`

### Basic Constraints
A certificate extension stating whether the subject is a CA (CA=true) and, optionally, a path-length limit. Issuing CA certificates have CA=true. End-entity certificates are not CAs (CA=false, or the extension is absent).

### Critical extension
An extension marked critical must be understood by the relying party. A certificate with an unrecognized critical extension is rejected.

### Validity period
The notBefore–notAfter interval in which a certificate may be used. On screen: the validity bar.

### Authority Information Access (AIA)
A certificate extension that says where to download the issuer's certificate (here, over HTTP from `pki.1sn0s.lab`). It helps build a chain when an intermediate certificate is missing. It never creates trust.

### CRL Distribution Point (CDP)
A certificate extension that says where to download the CRL of the CA that issued that certificate (here, over HTTP from `pki.1sn0s.lab`).

### Certificate Revocation List (CRL)
A list, signed by a CA, of the serial numbers of certificates that CA has revoked before expiry. The CRL has its own validity (thisUpdate/nextUpdate). ADCS CAs may also publish delta CRLs.

### Online Certificate Status Protocol (OCSP)
A protocol for asking an Online Responder about one certificate's status. It is optional in ADCS. On screen only as "OCSP if deployed"; none is deployed here.

### Revocation
Declaring a certificate invalid before its expiry. A revocation check consults the issuer's CRL (or OCSP) for each non-root certificate in the chain.

### Chain building
Assembling the path from the end-entity certificate up through issuer certificates to a trusted root. It uses the certificates presented, the local stores and, if needed, AIA. Building a chain does not prove identity.

### Path validation
Checking a built chain:
- it ends at a trusted root
- each signature verifies with the issuer's public key
- validity periods
- Basic Constraints
- critical extensions
- name match
- EKU
- revocation

### Trusted Root Certification Authorities store
The local certificate store whose certificates are trust anchors. On domain members, AD publication or Group Policy places the root here ahead of time.

### Intermediate Certification Authorities store
The local store that caches CA certificates that are not trust anchors.

### Personal store (LocalMachine\My)
The computer's certificate store for its own certificates. Each certificate is associated with a private key in a key container.

### Issuance
A CA signing a certificate with its private key after its checks pass.

### Offline root ceremony
The controlled procedure in which an administrator carries a subordinate CA's request to the offline root on removable media. The root signs the request, and the certificate (with the root certificate and CRL) is carried back. The root never joins the network.

### Removable media
The transport used for the offline root ceremony (for example, a USB drive). It is not a network connection.

## Protocols and Windows terms

### Remote Desktop Protocol (RDP)
The protocol the user's client uses to open a remote session on `rdp01.1sn0s.lab`. Here it is protected by TLS, with the server authenticated by its certificate.

### TLS handshake
The start of a TLS connection, in which the server sends its certificate chain and proves possession of its private key. The client validates the chain and the name.

### Network Level Authentication (NLA)
RDP's mode in which the user authenticates (through CredSSP over TLS) before a session is created.

### Kerberos
The domain's authentication protocol. Here it authenticates requesters to the CAs. Kerberos can also authenticate an RDP server in some cases; that is out of scope on screen (F-16).

### Group Policy
AD-delivered configuration. Here it does two things:
- names `RDPAuth` as the RDP server authentication certificate template
- distributes the root certificate (as an alternative to AD publication)

### Fully qualified domain name (FQDN)
A complete DNS name, for example `rdp01.1sn0s.lab`.

## Film shapes

| Shape | Represents |
|---|---|
| Request capsule (glass) | A signed certificate request: public key plus request information |
| Certificate card | A certificate; its seal shows who signed it |
| Key container | Protected key storage on its owner |
| Template badge | A certificate template |
| CA vault | An issuing CA, with its key in a sealed module |
| Root vault (cable-free plinth) | The offline Root CA |
| Trust link | An "issued by" relationship between certificates; not a network cable |
| Network channel (floor conduit) | A network connection; amber = pending, green = validated |
| Validation tick | One distinct check |
| CRL scroll fetch | Downloading a CRL from a CDP |
| AIA indicator | Where a missing issuer certificate could be fetched; never a trust source |
