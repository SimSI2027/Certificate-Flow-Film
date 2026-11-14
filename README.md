# Certificate-Flow-Film

A 100–120 s, 1920x1080, 30 FPS film (Approach B) that explains an Active Directory Certificate Services PKI flow as one continuous camera move, with a single flashback, through a stylized 3D world. It is built with scripted Blender (`bpy`), rendered headless, and checked by automated hard checks; an adversarial review loop judged the story spec and the first animatic round only.

> **Status: v1.2.0 is the current release (the newest audited version).** It adds the v1.2 look pass (`docs\LOOK-PLAN-v1.2.md`: materials, haze, pool lights, bloom, a brighter closing wide shot) to the audited v1.1.0 content, and passed a targeted re-audit on the rendered film (session L2, `docs\GAN-LEDGER.md`). It is accurate and legible; the remaining limitations are listed below and in `CHANGELOG.md`. The automated checks in `python -m tools verify` are the quality gate.

## The film

109 s, 1920x1080, 30 FPS, H.264 + AAC, captions only (no narration), synthesised sound cues. It shows two certificates issued under one root: an RDP server (`RDPAuth` template, Issuing CA 1) and a web server (`WebServer-TLS` template, Issuing CA 2), both chaining to the single trusted Root CA. The private key never leaves its owner; the request is signed, not the key sent.

Outputs (`output\`; the Final MP4 is a release asset, not committed): `Certificate-Flow-Film-Final.mp4`, `-Preview.mp4` (720p), `-Poster.png`, `-Contact-Sheet.png`, `captions.vtt`, `transcript.md`, `render-metadata.json`, `audio\loudness.json` (-15.9 LUFS).

## Known limitations (v1.2.0)

- **Shapes are still simple.** The look pass gave the wide shots haze, light and colour, but the props have no bevels or textures, and the server interior (14–24 s) still reads mostly grey. Cinema estimate 7 of 10; the charter's film gate (8 or more) is not met.
- **Two lighting pops (L2-CIN-01).** The camera-following rim light passes through the AD tower at 24.8 s and out of the Root CA complex at 45.8 s, so the picture's mean luma steps by 8.0 and 10.6 in one frame. A softer glow rise at 51.1 s has the same cause.
- **Small focal subjects.** In 10 beats the focal object is below its size target (39–103 px on its longer side; six of them grew in v1.2).
- **Hero shot (98–104 s).** Bright enough now (mean luma 51.3, target 50), but the whole topology is in frame only from about 101 s.
- **Handshake proof.** The proof of possession is shown as its own object, sent beside the certificates, but it has no label.
- **Audio and review.** Nobody has reviewed the sound by ear. No adversarial discriminator round judged this film; it was checked by `python -m tools verify` and by a Chief of Staff re-audit on the rendered film.

Details and measured values: `docs\GAN-LEDGER.md` ("Session L1" and "Session L2").

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

See `LICENSE` for the summary.

## Names in use

Fixed: AD domain `1SN0S.LAB`, NetBIOS `1SN0S`, DNS suffix `1sn0s.lab`, templates `RDPAuth` and `WebServer-TLS`.
Fallbacks currently in use (owner may replace them later): `DC01`, `CLIENT01`, `RDP01`, `WEB01`, `portal.1sn0s.lab`, `1SN0S Root CA`, `1SN0S Issuing CA 1`, `1SN0S Issuing CA 2`, `pki.1sn0s.lab`.

## Links

- Repository: https://github.com/SimSI2027/Certificate-Flow-Film
- Demo (GitHub Pages): https://simsi2027.github.io/Certificate-Flow-Film/
- Latest release, v1.2.0 (current): https://github.com/SimSI2027/Certificate-Flow-Film/releases/tag/v1.2.0 (v1.1.0 and v1.0.0 are superseded)
- Related: [Certificate-Flow-Lab](https://github.com/SimSI2027/Certificate-Flow-Lab) ([Pages](https://simsi2027.github.io/Certificate-Flow-Lab/)). Approach A (`Certificate-Flow-Animation`) was not found under SimSI2027 (HTTP 404), so it is not linked.
