# Certificate-Flow-Film

A 100–120 s, 1920x1080, 30 FPS film (Approach B) that explains an Active Directory Certificate Services PKI flow as one continuous shot through a stylized 3D world. It is built with scripted Blender (`bpy`), rendered headless, and checked by a staged production pipeline and a GAN-style adversarial review loop.

> **Status: under construction (Session 1 of 9 done: environment and repository).** The full README (all sections listed in `docs\BUILD-CHARTER.md`, Section 13) is written in Session 8. See `docs\PROJECT-STATE.md` for current status.

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
- Demo (GitHub Pages): not yet published
- Release: not yet published
- Related: [Certificate-Flow-Lab](https://github.com/SimSI2027/Certificate-Flow-Lab) ([Pages](https://simsi2027.github.io/Certificate-Flow-Lab/)). Approach A (`Certificate-Flow-Animation`) was not found under SimSI2027 (HTTP 404), so it is not linked.
