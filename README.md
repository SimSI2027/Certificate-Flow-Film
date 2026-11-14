# Certificate-Flow-Film

A 100–120 s, 1920x1080, 30 FPS film (Approach B) that explains an Active Directory Certificate Services PKI flow as one continuous camera move, with a single flashback, through a stylized 3D world. It is built with scripted Blender (`bpy`), rendered headless, and checked by automated hard checks; an adversarial review loop judged the story spec and the first animatic round only.

> **Status: v1.1.0 pre-release.** It carries the fixes from the v1 audit (`docs\AUDIT-v1.md`) and passed a targeted re-audit on the rendered film. It is accurate and legible, but it is not yet the finished film: see "Known limitations" below and `CHANGELOG.md`. The automated checks in `python -m tools verify` are the quality gate. The look pass planned for v1.2 is in `docs\LOOK-PLAN-v1.2.md`.

## The film

109 s, 1920x1080, 30 FPS, H.264 + AAC, captions only (no narration), synthesised sound cues. It shows two certificates issued under one root: an RDP server (`RDPAuth` template, Issuing CA 1) and a web server (`WebServer-TLS` template, Issuing CA 2), both chaining to the single trusted Root CA. The private key never leaves its owner; the request is signed, not the key sent.

Outputs (`output\`; the Final MP4 is a release asset, not committed): `Certificate-Flow-Film-Final.mp4`, `-Preview.mp4` (720p), `-Poster.png`, `-Contact-Sheet.png`, `captions.vtt`, `transcript.md`, `render-metadata.json`, `audio\loudness.json` (-15.9 LUFS).

## Known limitations (v1.1.0)

- **Look (V1-CIN-03, open MAJOR).** The film still looks like a stylised grey-box: flat grey props, little material or light design, an empty dark upper frame. The charter's film gate (cinema score of 8 or more, no open MAJOR) is not met.
- **Hero shot (98–104 s).** The whole topology, with the user, is in frame only from about 102 s, and the shot is the darkest of the film (mean luma 38.4 against a target of 50).
- **Small focal subjects.** In 10 beats the focal object is below its size target (39–99 px on its longer side).
- **Brightness bump at 90.2 s.** A passing highlight steps the picture's mean luma by 7.7 in one frame; three smaller steps are at 24.8, 45.8 and 81.0 s.
- **Flashback marker.** "Earlier: offline signing ceremony" fades out over the first three frames after the cut back to the present (46.5 s).
- **Audio.** The AAC track peaks at −0.6 dBFS true peak (the WAV mix is at −1.2 dBFS). Nobody has reviewed the sound by ear.
- **Review.** No adversarial discriminator round judged this film; it was checked by `python -m tools verify` and by a Chief of Staff re-audit of 56 frames.

Details and measured values: `docs\AUDIT-v1.md` ("F3 targeted re-audit, third run") and `docs\GAN-LEDGER.md` ("Session F3").

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
- Latest pre-release, v1.1.0: https://github.com/SimSI2027/Certificate-Flow-Film/releases/tag/v1.1.0 (v1.0.0 is superseded)
- Related: [Certificate-Flow-Lab](https://github.com/SimSI2027/Certificate-Flow-Lab) ([Pages](https://simsi2027.github.io/Certificate-Flow-Lab/)). Approach A (`Certificate-Flow-Animation`) was not found under SimSI2027 (HTTP 404), so it is not linked.
