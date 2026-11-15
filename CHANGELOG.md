# Changelog

## v1.3.0 (2026-11-14, current release)

A 109 s, 1920x1080, 30 FPS film (H.264 High + AAC, captions only) that follows an ADCS certificate from request to trust. Audited on the rendered film (`docs\AUDIT-V5.md`): no blocker or major finding, 33 of 33 PKI beats accurate. Scores: PKI accuracy 9, icons 8.5, realism 8, presentation 7.5, legibility 8.5.

Final MP4 SHA-256: `ce4cf1fb12fa71d35237463506069c5f80c06b2c6ff15722dc69be43646f15d9`.

The film:
- **Story.** An RDP server shows a self-signed certificate that the client cannot verify. Group Policy names the `RDPAuth` template; the server makes its key pair locally, signs a request and finds the right CA through Active Directory. Issuing CA 1 runs four checks and signs. The client validates the whole chain to a root it already trusts, including revocation for each link, and the connection turns green. A web server then repeats the path with `WebServer-TLS` and Issuing CA 2. Both paths end at one Root CA.
- **PKI accuracy.** Private keys never leave their owners. Requests are signed, not the key sent. AD answers a lookup and never receives a request. The Root CA is offline: it signs only the issuing CA certificates, in a flashback of the setup ceremony. AIA can fetch a missing intermediate but never creates trust.
- **World.** A night-time datacenter with haze and pools of light: a seated user at a laptop, server racks with devices behind perforated doors, an HSM and CA racks inside each issuing CA enclosure, and the Root CA as an offline machine in a locked gold cage on a concrete plinth, with no network cable. Rows of racks, cable trays and a raised floor surround the stage. All hardware is modelled in code, with three CC0 textures and no vendor marks.
- **Symbols.** One symbol per concept, the same everywhere: certificate cards with a ribbon seal in the issuer's colour (cyan for Issuing CA 1, violet for Issuing CA 2, gold for the root); a shield badge on CA certificates only; a seal that closes on itself on the two self-signed certificates; a key locked in a padlock for private keys and an open key for public keys; a signature mark on each request and on the handshake proof; a list with a struck entry for each CRL; chain links for trust; ticks for validation checks.
- **Camera and sound.** One continuous camera move with two clean cuts, into and out of the flashback. 13 captions, 54 in-world labels, 88 synthesised sound cues, −15.9 LUFS, true peak −1.2 dBFS.
- **Names.** Domain `MALAWI.LAB`; `MALAWI Root CA`, `MALAWI Issuing CA 1`, `MALAWI Issuing CA 2`; hosts `rdp01.malawi.lab` and `portal.malawi.lab`.

Quality gate:
- `python -m tools verify`: pytest 232, 20 in-Blender checks (including "no cable at the root", key containment and the greyscale silhouette test for the 14 shapes), both render tiers 3270 of 3270 frames, MP4 on spec.
- A Chief of Staff audit of the rendered film, beat by beat and symbol by symbol.

Known limitations (all minor):
- "Self-signed" and "Unverified" sit about 600 px from the self-signed card at 10.4–12.1 s. The "not published here" tag takes a second to settle beside Issuing CA 1 at 76.8 s.
- The picture darkens over five frames at 81.7 s as the camera passes through Issuing CA 2's doorway (mean luma 64 to 45).
- While the chain docks (53–64 s) the client's trust store is seen from behind and hides the root card.
- The closing wide shot (99–104 s) is small in frame, and the title is a plain caption plate.
- On end-entity cards the issuer seal has the card's own colour. The emblem on the root cage has a centre disc that the card seal does not have. The session window is a blank panel. The offline machine is hard to see inside the cage, and the root's key module stands on the dais outside it.
- No adversarial discriminator round judged this film, and nobody has reviewed the sound by ear.
