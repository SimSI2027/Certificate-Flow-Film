# Pipeline (Session 3)

Everything is driven from `cff` (pure Python: story model, timing, theme, stage plan). `blender\` turns the plan into a scene.
Call everything through `python -m tools <command>` with `.venv\Scripts\python.exe`.

| Command | What it does |
|---|---|
| `env [--json]` | Toolchain paths and versions, checked against the pin in `config\toolchain.local.json` |
| `build [--tier animatic]` | Builds `renders\film.blend` (BEAUTY scene + separate CAPTIONS scene). About 2 s |
| `render [--tier animatic] [--scene all\|BEAUTY\|CAPTIONS] [--first N --last M] [--rebuild]` | Renders in resumable 300-frame chunks to `renders\<tier>\beauty` and `...\captions` (`f_####.png`). Skips frames already on disk (`use_overwrite = False`, `use_placeholder = True`). Progress: `renders\<tier>\progress.json`, log: `render-<layer>.log`. The caption layer renders only the frames on which a caption has opacity |
| `captions` | Writes `output\captions.vtt` and `output\transcript.md` from `cff\story\captions.py` |
| `contact [--tier animatic]` | One tile per beat (middle frame, captions composited) -> `output\animatic\contact-sheet.png` |
| `palette` | L-07: CIEDE2000 between the key role colours under normal, deuteranopia and protanopia (Machado 2009) |
| `motion` | Planned-film audits: camera C-02/C-09, focal subject C-03, keys and easing C-06, glow range |
| `verify [--repo] [--skip-blender]` | ruff, mypy --strict, pytest, traceability, palette, motion, the 11 in-Blender scene checks on a fresh build, blank-frame check on rendered frames; `--repo` adds clean tree and HEAD == origin/main |
| `packet stage1 [--round N] [--tier animatic]` | Round packet: composited frames (3 per beat, plus both sides of each cut), motion strips, `shots.json`, `locator.json` (measured screen bounds of keys, capsules, cards, containers and modules per packet frame, from `blender\locate.py` on the built `.blend`), `model-dump.json`, docs, `manifest.json` (SHA-256 of every file), `regressions.json`, `schema.json`. Needs a clean committed tree and every frame rendered |
| `packet stage0`, `traceability [--check]`, `model-dump`, `spec-hash`, `sync-check` | Stage 0 tools |

Every Blender call is `"<blender.exe>" -b [file.blend] --factory-startup --python-exit-code 1 -P <script.py> -- <args>`
(`tools\toolchain.py`). Run long renders in the background and read `progress.json`; never rely on one command finishing in a tool time limit.

## Blender modules
- `build_scene.py` (entry), `world.py` (navy world, grid floor, one mesh per catalogue object), `actors\` (a grey-box builder per `Kind`),
  `materials.py` (one shader: role colour, emission and opacity from `Object Info`), `signage.py` (label plates and text, billboarded to the camera),
  `camera_rig.py` (camera, look-at and focus empties, keyed from the plan), `lighting.py` (key and rim travel with the camera), `compositor.py`
  (flashback grade, soft vignette, fade to black, bloom in the preview/final tiers), `captions_scene.py` (orthographic caption layer),
  `animation.py` (slotted-action F-curves with named-easing Bezier handles), `render_frames.py`, `run_checks.py`, `checks\scene_checks.py`.
- Camera: one rig. The plan (`cff\stage\camera.py`) is Gaussian-smoothed (sigma 16 frames) so the subject leads the camera; the two cuts are the only jumps.

## Conventions
- Origins: base-anchored kinds (`cff.stage.objects.BASE_ANCHORED`) sit on their base centre; hinged and stretched kinds (panel, lid, channel, route,
  trust link, beam) at their start; everything else at its centre. Scale animates entrance and exit (`motion.HIDDEN_SCALE`).
- Glow: `object.color` is the emission tint and opacity (linear r, g, b, alpha); glow-only kinds (`materials.GLOW_ONLY_KINDS`) are dark until lit.
- Fonts: in-world labels use Blender's bundled DejaVu Sans Mono (distinct 1, I and 0); captions use the bundled Inter.
