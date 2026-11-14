# Certificate-Flow-Film

A 100–120 s, 1920x1080, 30 FPS film (Approach B) that explains an Active Directory Certificate Services PKI flow as one continuous camera move, with a single flashback, through a stylized 3D world. It is built with scripted Blender (`bpy`), rendered headless, and checked by automated hard checks; an adversarial review loop judged the story spec and the first animatic round only.

> **Status: v1.0.0 pre-release, under audit (`docs\AUDIT-v1.md`).** Fixes are being applied toward v1.1.0; see `CHANGELOG.md`. The automated checks in `python -m tools verify` are the quality gate.

## The film

109 s, 1920x1080, 30 FPS, H.264 + AAC, captions only (no narration), synthesised sound cues. It shows two certificates issued under one root: an RDP server (`RDPAuth` template, Issuing CA 1) and a web server (`WebServer-TLS` template, Issuing CA 2), both chaining to the single trusted Root CA. The private key never leaves its owner; the request is signed, not the key sent.

Outputs (`output\`; the Final MP4 is a release asset, not committed): `Certificate-Flow-Film-Final.mp4`, `-Preview.mp4` (720p), `-Poster.png`, `-Contact-Sheet.png`, `captions.vtt`, `transcript.md`, `render-metadata.json`, `audio\loudness.json` (-16.0 LUFS).

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
- Release: https://github.com/SimSI2027/Certificate-Flow-Film/releases/tag/v1.0.0
- Related: [Certificate-Flow-Lab](https://github.com/SimSI2027/Certificate-Flow-Lab) ([Pages](https://simsi2027.github.io/Certificate-Flow-Lab/)). Approach A (`Certificate-Flow-Animation`) was not found under SimSI2027 (HTTP 404), so it is not linked.
