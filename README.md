# Certificate-Flow-Film

A 109 s, 1920x1080, 30 FPS film (Approach B) that explains an Active Directory Certificate Services PKI flow as one continuous camera move, with a single flashback, through a 3D datacenter. It is built with scripted Blender (`bpy`), rendered headless, and checked by automated hard checks; an adversarial review loop judged the story spec and the first animatic round only.

> **Status: v1.3.0 is the current release.** It passed a full audit on the rendered film (`docs\AUDIT-V5.md`): no blocker or major finding, and all 33 PKI beats accurate. Scores: PKI accuracy 9, icons 8.5, realism 8, presentation 7.5, legibility 8.5. The remaining polish items are listed below. The automated checks in `python -m tools verify` are the quality gate.

## The film

109 s, 1920x1080, 30 FPS, H.264 + AAC, captions only (no narration), synthesised sound cues. It shows two certificates issued under one root: an RDP server (`RDPAuth` template, Issuing CA 1) and a web server (`WebServer-TLS` template, Issuing CA 2), both chaining to the single trusted Root CA. The private key never leaves its owner; the request is signed, not the key sent.

- **World.** A night-time datacenter: a seated user at a laptop, server racks, an HSM in each issuing CA enclosure, and an offline, air-gapped Root CA in a locked gold cage on its own plinth, with no network cable.
- **Symbols.** One symbol per PKI concept, the same everywhere: a certificate card with a ribbon seal in its issuer's colour, a shield badge on CA certificates, a seal that closes on itself on self-signed certificates, a key locked in a padlock for a private key, an open key for a public key, a signature mark on requests and on the handshake proof, a list with a struck entry for a CRL, and chain links for trust. Legend: `qa\v5b\icon-legend.png`.

Outputs (`output\`; the Final MP4 is a release asset, not committed): `Certificate-Flow-Film-Final.mp4`, `-Preview.mp4` (720p), `-Poster.png`, `-Contact-Sheet.png`, `captions.vtt`, `transcript.md`, `render-metadata.json`, `audio\loudness.json` (-15.9 LUFS).

## Known limitations

All are minor (polish); none affects accuracy. Times and details: `docs\AUDIT-V5.md`.

- **Two tags sit far from their subject.** "Self-signed" and "Unverified" are about 600 px from the self-signed card at 10.4–12.1 s; the "not published here" tag takes a second to settle beside Issuing CA 1 at 76.8 s.
- **One visible light change.** The picture darkens over five frames at 81.7 s as the camera passes through Issuing CA 2's doorway.
- **Trust store seen from behind.** While the chain docks (53–64 s) the client's gold trust store hides the root card; the sign "Installed earlier by policy" carries the point.
- **Hero and title.** The closing wide shot (99–104 s) shows the whole topology, but small in frame; the title is a plain caption plate.
- **Small details.** On end-entity cards the issuer seal has the card's own colour; the session window is a blank panel; the offline machine is hard to see inside the root cage.
- **Review.** No adversarial discriminator round judged this film; it was checked by `python -m tools verify` and by a Chief of Staff audit on the rendered film. Nobody has reviewed the sound by ear.

Planned polish: `docs\ENHANCEMENTS-v1.4.md`.

## Rebuild

```
.venv\Scripts\python.exe -m tools verify          # ruff, mypy, pytest, audits, in-Blender checks
.venv\Scripts\python.exe -m tools render --tier final   # background, resumable, ~1 h on an RTX 4090
.venv\Scripts\python.exe -m tools audio
.venv\Scripts\python.exe -m tools encode
.venv\Scripts\python.exe scripts\build_site.py
```

Requires Blender 5.2.x LTS, FFmpeg and Python 3.12 (paths in `config\toolchain.local.json`, see `docs\TOOLCHAIN.md`). Pipeline details: `docs\PIPELINE.md`.

## Licensing split

- **Code** (`cff\`, `blender\`, `tools\`, `tests\`, `scripts\`): GPL-3.0-or-later. Blender scripts import `bpy`, which is GPL, so the whole code base uses a GPL-compatible licence. Text: `LICENSES\GPL-3.0-or-later.txt`.
- **Rendered film, images and documentation**: CC BY 4.0. Text: `LICENSES\CC-BY-4.0.txt`.
- **Bundled font**: Inter (SIL OFL 1.1), `assets\fonts\`, with its licence in `assets\fonts\OFL.txt`.
- **User character** (`assets\character.blend`; the build loads it locally and never downloads anything): every piece is CC0 1.0 (text: `LICENSES\CC0-1.0.txt`). Sources, SHA-256 hashes and the CC0 statement quoted from each source file are in `assets\character.manifest.json`.
  - MakeHuman base mesh (`base.obj`) and default rig skin weights (`weights.default.json`), as shipped in MPFB 2.0.18. Both are CC0. The skeleton definition (`rig.default.json`) carries no licence field of its own.
  - From the MakeHuman system asset pack (CC0, released September 2020): eyes `low-poly`, eyebrows `eyebrow001`, hair `short02`, clothes `male_casualsuit01`, shoes `shoes02`, with their textures (downscaled and packed).
- **Hardware textures** (`assets\textures\`): three CC0 1.0 PBR materials from ambientCG (text: `LICENSES\CC0-1.0.txt`): `Metal009` (brushed steel), `SheetMetal001` (perforated sheet) and `Concrete034` (concrete), 1K JPG maps only. Created using Metal009, SheetMetal001 and Concrete034 from ambientCG.com, licensed under the Creative Commons CC0 1.0 Universal License. Pages, download hashes and per-file SHA-256 are in `assets\textures\textures.manifest.json`. Every hardware model is procedural `bpy` code; no brand marks or logos.
  - Generated with the MPFB add-on 2.0.18 (extensions.blender.org, GPL-3.0-or-later). MPFB is only the generator: none of its code is in the asset or the repository. Regenerate with `python -m tools character`, which fetches the pinned files and checks their SHA-256.

See `LICENSE` for the summary.

## Names in use

Fixed: AD domain `MALAWI.LAB`, NetBIOS `MALAWI`, DNS suffix `malawi.lab`, templates `RDPAuth` and `WebServer-TLS`.
Fallbacks currently in use (owner may replace them later): `DC01`, `CLIENT01`, `RDP01`, `WEB01`, `portal.malawi.lab`, `MALAWI Root CA`, `MALAWI Issuing CA 1`, `MALAWI Issuing CA 2`, `pki.malawi.lab`.

## Links

- Repository: https://github.com/SimSI2027/Certificate-Flow-Film
- Demo (GitHub Pages): https://simsi2027.github.io/Certificate-Flow-Film/
- Latest release, v1.3.0: https://github.com/SimSI2027/Certificate-Flow-Film/releases/tag/v1.3.0
- Related: [Certificate-Flow-Lab](https://github.com/SimSI2027/Certificate-Flow-Lab) ([Pages](https://simsi2027.github.io/Certificate-Flow-Lab/)). Approach A (`Certificate-Flow-Animation`) was not found under SimSI2027 (HTTP 404), so it is not linked.
