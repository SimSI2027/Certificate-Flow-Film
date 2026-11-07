# Toolchain (verified 2026-11-06, Session 1)

Machine-specific paths live in the gitignored `config\toolchain.local.json`; tools read them from there.

| Item | Result |
|---|---|
| OS / shell | Windows 11 Enterprise 10.0.29698, PowerShell (Git Bash also present) |
| Project dir | `E:\ClaudeCode\Projects\Certificate-Flow-Film` (was empty except the two charter files) |
| Git | 2.51.1.windows.1 |
| GitHub CLI | 2.103.3, authenticated as **SimSI2027** (keyring; scopes gist, read:org, repo, workflow) |
| FFmpeg / FFprobe | 9.0.2-essentials_build-www.gyan.dev; encoders `libx264` and `aac` present (also `aac_mf`) |
| Python | 3.12.10 (`py -3.12`); also 3.11 and 3.14 installed. Project venv `.venv` = 3.12.10 |
| Dev tools (`requirements-dev.txt`) | pytest 9.2.0, ruff 0.17.4, mypy 2.4.1 |
| Disk | E: 1.0 TB free of 1.9 TB. A full-length pass is about 3,300 PNG frames, so a few GB per tier; ample |
| GPU | NVIDIA GeForce RTX 4090 (24 GB), driver 621.14 (also AMD Radeon iGPU, unused) |
| Claude Code dirs | project `.claude\agents\` created (3 discriminators); no project skills dir; user skills in `%USERPROFILE%\.claude\skills` |
| Blender | **5.2.3 LTS** (build 2026-10-22), installed via `winget install -e --id BlenderFoundation.Blender --version 5.2.3` |
| Blender path | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` |

Blender 5.2.3 was the version winget offered for `BlenderFoundation.Blender`, so no alternative package ID was needed. Pin: **5.2.3**.

Blender invocation (always): `"<blender.exe>" -b [file.blend] --factory-startup --python-exit-code 1 -P <script.py> -- <args>`

## Headless GPU probe (`scripts\gpu_probe.py`)

Renders a lit cube, sphere and floor at 960x540 and measures the frame. Not blank means std dev >= 0.01 and >= 16 unique levels.

| Engine | Result |
|---|---|
| EEVEE | Render engine enum on 5.2.3 is `["BLENDER_EEVEE"]`. Headless render OK in about 13 s. mean 0.663, std 0.214, 2,670 unique levels. **Not blank.** Frame inspected visually. |
| Cycles (fallback check) | OPTIX on RTX 4090, seed 1, denoising on. mean 0.684, std 0.211, 6,159 unique levels. Not blank. |

**Decision: EEVEE** is the primary engine (`BLENDER_EEVEE`, detected from the enum, never hard-coded). Cycles/OPTIX with fixed seed and denoising is the verified fallback if EEVEE later fails headless.
Probe output is in the gitignored `renders\probe\`.

## Notes
- `Material.use_nodes` emits a deprecation warning in 5.2 (removal in 6.0). Avoid it in production code, where possible.
- Blender prints a harmless `TBBmalloc ... ucrtbase.dll` line at start-up.
- FFmpeg and FFprobe resolve to `C:\Program Files (x86)\FFMPEG\bin` (the single install on PATH). Tooling reads the path from `toolchain.local.json`.
