# LOOK PLAN v1.2 — from accurate to watchable

Written 2026-11-14 by the Chief of Staff (session F3, `claude-fable-5-2`), after v1.1.0 was released as a pre-release.
Goal of v1.2: the film should be visually entertaining, not only accurate. v1.1.0 scores PKI 9, legibility 8, cinema 5 (my estimate). The target for v1.2 is cinema 7 with no loss in the other two.

This plan is written so that the executing model needs no design judgement. Every value below is either measured on a prototype or comes with a fixed tuning rule. Where a rule says "stop", stop and record the value reached; do not improvise.

## 1. What the prototype showed

I built a final-tier `.blend` from commit `a036067` into the scratch folder and applied the look changes of Item A with a scratch script (no project file was changed; the script's working parts are in Appendix B). I rendered stills at the final tier and measured them with FFmpeg `signalstats` (beauty pass only, 8-bit video range, as in AUDIT-v1 Appendix A.4).

| Frame | What | v1.1.0 YAVG | Prototype YAVG | v1.1.0 SATAVG | Prototype SATAVG |
|---|---|---|---|---|---|
| f457 | server interior, keys | 48.9 | 49.8 | 5.8 | 8.4 |
| f1204 | root reveal | 44.0 | 64.7 | — | — |
| f1700 | chain at the client | 48.8 | 46.8 | 10.0 | 13.8 |
| f2058 | trusted session | 52.9 | 58.7 | 10.2 | 15.7 |
| f3100 | hero | 36.7 | 57.4 | 8.0 | 16.3 |
| B-09.2, mean of f2950, f2980, f3010, f3040, f3070, f3100, f3118 | hero beat | **37.8** | **53.1** | | |

- The hero beat passes the brightness target (53.1 against 50) without any hero-only trick. The same seven frames of v1.1.0 give 37.8, and the whole beat on the MP4 gives 38.4, so the seven-frame mean is a fair stand-in for the beat mean.
- Hero shadows stay dark (10th-percentile luma 33) and highlights rise (90th percentile from 51 to 88): the picture gains contrast and colour; it is not just lifted.
- Render time per final frame rose from about 0.70 s to about 0.85 s on the RTX 4090. A full beauty pass is about 50 minutes.
- Two viewed sheets confirmed the look: blue haze with depth, a soft gold glow around the root, pool lights over each actor, glowing channels. They also showed two defects of the first try, both fixed by the values in Item A: a white specular hot-spot on the floor (fixed by light specular 0.2 and floor roughness 0.4), and a hard bright dot where the rim light sits in the haze (fixed by a rim light radius of 4 m).
- Two things were tried and rejected. Do not repeat them:
  - Turning off the haze contribution of the key and rim lights removes the dot, but the hero mean falls to 34–39.
  - Neutral metallic 0.8 with floor roughness 0.3 darkens interiors (f457 from 48.9 to 34.8) and causes the hot-spot.
- **Not tested: motion.** I rendered stills only. Whether the haze flickers, and how the soft backlight glow drifts as the camera moves, is checked in the stills-and-strips gate (Section 5) before the full render.

## 2. Rules for the executing sessions

1. Read only this file, `docs\PROJECT-STATE.md`, and the files named in the item being worked on. Do not re-read the spec documents.
2. Do the items in the order of Section 4. Commit after each item with `python -m tools verify --skip-blender` green; run the full `python -m tools verify` after Items A and E.
3. All new numbers are named constants in a new module `cff\theme\look.py`. All new colours are tokens in `cff\theme\palette.py`. `tests\test_blender_static.py` fails on a literal colour in `blender\`.
4. Test renders never go into `renders\final\`. The final render skips frames that are already on disk, so a stale test frame would ship. Test frames go to `renders\look-test\`.
5. **Render budget: one full final-tier render.** Test renders are limited to 150 final-tier frames in total per attempt (about 2 minutes), and at most three attempts.
6. **Image budget: 6 images** in the execution session (Section 6 lists them).
7. Anti-gaming rules of `CLAUDE.md` apply: no beat, caption or check is cut, shrunk or moved out of frame to pass a number. No test is deleted. A threshold is relaxed only where this plan says so, and the value is recorded in the ledger.
8. `docs\REFERENCE-SPEC.md` does not change. Rulings needed by this plan are in Section 8.

## 3. The items

### Item A. Materials and lighting pass (V1-CIN-03) — replaces the grey-box look

One art direction, applied through parameters only: a night-time machine hall. Dark glossy floor, blue haze that gives depth, a pool of light over each actor in its own identity colour, soft back light, stronger bloom on the role colours.

**A1. Constants.** New file `cff\theme\look.py`:

```python
"""Look constants for the v1.2 materials and lighting pass (docs/LOOK-PLAN-v1.2.md). Colours live in cff.theme.palette."""

from __future__ import annotations

from cff.stage import layout as lo
from cff.stage.layout import Vec3

# Haze: a thin world volume. Only tiers with ``volumetrics`` get it.
HAZE_DENSITY = 0.004
HAZE_DENSITY_MIN, HAZE_DENSITY_MAX, HAZE_DENSITY_STEP = 0.0025, 0.006, 0.0005
HAZE_ANISOTROPY = 0.4
VOLUME_START_M, VOLUME_END_M = 0.5, 150.0
VOLUME_TILE_SIZE = "4"
VOLUME_SAMPLES = 96
VOLUME_SAMPLE_DISTRIBUTION = 0.8
VOLUME_RAY_DEPTH = 8

# Horizon glow: seen by the camera only, so the ambient light on the stage does not change (C-05).
HORIZON_STRENGTH = 1.2
HORIZON_POWER = 6.0

# Key and rim: softer shadows, weaker floor highlights, a soft glow in the haze instead of a hard dot.
KEY_RADIUS_M = 1.5
RIM_RADIUS_M = 4.0
KEY_SPECULAR = 0.2
RIM_SPECULAR = 0.2

# Pool lights: one static spot above each actor. They never animate.
POOL_HEIGHT_M = 12.0
POOL_OFFSET_Y_M = -1.5
POOL_CONE_DEG = 50.0
POOL_BLEND = 0.7
POOL_RADIUS_M = 0.5
POOL_WATTS = 4000.0
POOL_SPECULAR = 0.3
POOLS: tuple[tuple[str, Vec3, str, float], ...] = (  # name, actor anchor, palette token name, relative power
    ("client", lo.CLIENT, "POOL_NEUTRAL_HEX", 1.0),
    ("rdp", lo.RDP, "POOL_NEUTRAL_HEX", 1.0),
    ("web", lo.WEB, "POOL_NEUTRAL_HEX", 1.0),
    ("ad", lo.AD, "RIM_LIGHT_HEX", 0.8),
    ("ca1", lo.CA1, "POOL_CA1_HEX", 1.6),
    ("ca2", lo.CA2, "POOL_CA2_HEX", 1.6),
    ("root", lo.ROOT, "POOL_ROOT_HEX", 3.0),
)

# Materials.
NEUTRAL_METALLIC = 0.35
NEUTRAL_ROUGHNESS = 0.45
ROLE_ROUGHNESS = 0.4
BACKDROP_METALLIC = 0.6
BACKDROP_ROUGHNESS = 0.5
FLOOR_ROUGHNESS = 0.4

# Compositor bloom (final and preview tiers).
BLOOM_THRESHOLD = 0.8
BLOOM_STRENGTH = 0.6
```

`cff\theme\palette.py`, after `RIM_LIGHT_HEX`: add `HAZE_HEX = "#9CC4FF"`, `HORIZON_HEX = "#2B5C9E"`, `POOL_NEUTRAL_HEX = "#CFE0FF"`, `POOL_CA1_HEX = "#8CEBFF"`, `POOL_CA2_HEX = "#C4B1FF"`, `POOL_ROOT_HEX = "#FFE08A"`.
No pool is green or amber: those colours are states (C-10). The three tinted pools are pale tints of their owner's identity colour.

**A2. World** (`blender\world.py`, `build_world`; give it the tier: `build_world(scene, tier)` and pass `tier` from `blender\build_scene.py`).
- Horizon glow, all tiers. Node graph exactly as in Appendix B, `horizon()`: `Light Path > Is Camera Ray` chooses between the existing navy background (for lighting) and navy plus a glow of `HORIZON_HEX` whose strength is `HORIZON_STRENGTH * (1 - |z|) ** HORIZON_POWER` (z from `Texture Coordinate > Generated`).
- Haze, only if `tier.volumetrics`: a `ShaderNodeVolumeScatter` (colour `HAZE_HEX`, density `HAZE_DENSITY`, anisotropy `HAZE_ANISOTROPY`) into the world output's `Volume` socket.

**A3. Render settings** (`blender\render_settings.py`, `apply_tier`, only when `tier.volumetrics and not transparent`): set on `scene.eevee`, each guarded by `hasattr`: `volumetric_start`, `volumetric_end`, `volumetric_tile_size`, `volumetric_samples`, `volumetric_sample_distribution`, `volumetric_ray_depth` from the constants, and `use_volumetric_shadows = True`. All seven attributes exist in Blender 5.2.3 (checked in the prototype).

**A4. Lights** (`blender\lighting.py`).
- In `_spot`, replace `data.shadow_soft_size = 0.3` by a parameter: `KEY_RADIUS_M` for the key, `RIM_RADIUS_M` for the rim. Set `data.specular_factor` to `KEY_SPECULAR` / `RIM_SPECULAR`. Leave `volume_factor` at its default of 1.0. Do not change `KEY_LIGHT_POWER_W` or `RIM_LIGHT_POWER_W`.
- New function `build_pools(collection)`, called from `build_lights`: for each row of `look.POOLS` create a `SPOT` light named `LIGHT-pool-<name>` at `(x, y + POOL_OFFSET_Y_M, POOL_HEIGHT_M)`, rotation zero (a spot points down by default), `energy = POOL_WATTS * relative`, `spot_size = radians(POOL_CONE_DEG)`, `spot_blend = POOL_BLEND`, `shadow_soft_size = POOL_RADIUS_M`, `specular_factor = POOL_SPECULAR`, colour `linear(getattr(palette, token))`. Tag each like the other lights (`PROP_KIND: "light"`). No keyframes.

**A5. Materials** (`blender\materials.py`).
- `stage_material`: roughness `look.NEUTRAL_ROUGHNESS` and `Metallic = look.NEUTRAL_METALLIC` when `role is ColourRole.NEUTRAL and not glow_only`; otherwise roughness `look.ROLE_ROUGHNESS`, metallic 0. Remove `SOLID_ROUGHNESS` from this function (the trust-link material keeps it).
- `backdrop_material`: metallic `look.BACKDROP_METALLIC`, roughness `look.BACKDROP_ROUGHNESS`.
- `floor_material`: roughness `look.FLOOR_ROUGHNESS` (was 0.8).

**A6. Bloom** (`blender\compositor.py`): `BLOOM_THRESHOLD` and `BLOOM_STRENGTH` come from `cff.theme.look` (0.8 and 0.6; were 1.0 and 0.35). `BLOOM_SIZE` stays 6.

**A7. Tests** (new file `tests\test_look_v12.py`; static, no Blender needed, in the style of `tests\test_blender_static.py`):
- `test_LOOK_A_haze_only_on_volumetric_tiers`: the source of `build_world` contains `tier.volumetrics`; the animatic tier has `volumetrics=False`.
- `test_LOOK_A_pools_never_use_state_colours`: no pool token is within 25 dE2000 of `ColourRole.VALIDATED`, `PENDING` or `REVOCATION` (use `cff.theme.colour`).
- `test_LOOK_A_pools_are_static`: the source of `build_pools` contains no `.key(` call.
- `test_LOOK_A_ambient_unchanged`: `palette.WORLD_STRENGTH`, `KEY_LIGHT_POWER_W` and `RIM_LIGHT_POWER_W` still equal 0.02, 900.0 and 1050.0.
- One in-Blender check in `blender\checks\scene_checks.py`: every `LIGHT-pool-*` object has no animation data, and there are exactly `len(look.POOLS)` of them.

**Expected visual result.** Wide shots show the actors as lit islands in blue haze, each under its own cone of light; the upper frame is a blue gradient instead of black; channels and trust links glow against a dark, slightly reflective floor; the root sits in a gold glow. Interiors (the server at 14–24 s, the CA vaults at 29–36 s and 82–90 s) change least: they stay simple shapes, with softer shadows and slightly more colour.

**Measurable checks (stills gate, Section 5).** Beauty pass, final tier:
- B-09.2 seven-frame mean YAVG between 50 and 62 (prototype 53.1).
- f3100: 10th-percentile luma (`YLOW`) at most 40 (prototype 33) and `SATAVG` at least 12 (prototype 16.3).
- f457 at least 45; f2058 at most 70; f943 between 55 and 75 (v1.1.0: 63.8). No still above 75.
- Tuning rule, hero mean only: below 50, raise `HAZE_DENSITY` by `HAZE_DENSITY_STEP` (maximum 0.006); above 62, lower it by one step (minimum 0.0025). At most three attempts. Change nothing else.

### Item B. Hero shot brightness (target: mean YAVG of at least 50)

- **Exact change:** none beyond Item A. The hero was dark because the frame was mostly unlit floor and black sky; haze, the horizon and seven pool lights fill it. Leave the F2 hero glow (`GLOW_PEAK` on the channels and trust paths) in place.
- **Second change, the hero arrives too late.** The whole topology is in frame only for the last 2 s of the 6 s beat; f2970 (99.0 s) is an almost empty floor under the film's key caption. In `cff\theme\shots.py`, shot `hero`: try `follow` 0.3, then 0.2, then 0.1 (it is 0.45). For each value run `python -m pytest tests\test_audit_v1.py tests\test_camera.py -q` and count the B-09.2 frames on which all seven actors are fully in frame (the measure inside `test_V1_CIN_02_hero_holds_the_whole_topology`). Keep the value with the highest count among those where every camera test passes. Then raise `HERO_ARRIVED_FRAMES` in `tests\test_audit_v1.py` to the achieved count, rounded down to a multiple of 15. If no value beats 0.45, keep 0.45 and record that.
- **Expected visual result:** the closing wide shot reads as the pay-off: the lit topology, both green channels and the gold root, visible earlier and for longer.
- **Measurable check:** on the final MP4, B-09.2 mean `YAVG` ≥ 50 (Appendix A, `luma.py`; v1.1.0: 38.4). `HERO_ARRIVED_FRAMES` ≥ 60 and not lower than before.

### Item C. The white flash at 90 s (V1-CIN-06 residual)

- **Cause (measured in F3):** the template badge `TPL-WEBTLS` lies on top of the web server and glows at level 0.8. The camera flies over it at 1.8–2.9 m: at f2425–2436 (81.0 s, step 6.4) and at f2700–2709 (90.0–90.3 s, step 7.7). At f2708 the badge is 513 px wide at the bottom of the frame; at f2709 it leaves the frame and the mean luma drops from 55.7 to 48.0. Bloom makes it worse. The camera path was already searched in F2 (`bulge` 4.8); do not search it again.
- **Exact change** (`cff\stage\choreography.py` and `cff\theme\palette.py`):
  1. `palette.py`: add `BADGE_REST_GLOW = 0.25` beside `GLOW_SOFT`.
  2. In `choreography.py`, in the block for B-07.4: `b = self.beat("B-07.4")`, then `self.glow_to("TPL-WEBTLS", b, b + 30, hex_glow(palette.TEXT_HEX, palette.BADGE_REST_GLOW))`. The badge has done its job by then (it is read in B-07.1 and B-07.3).
  3. Do not touch `TPL-RDPAUTH` (level 0.4) unless the check below fails at f746.
- **Expected visual result:** the badge stays visible as a grey plate on the server but no longer flares when the camera passes over it.
- **Measurable check:** render f2420–2440 and f2695–2715 at the final tier into `renders\look-test\` (42 frames). No frame-to-frame `YAVG` step above 4.0 in either range. If a step is still above 4.0, set `BADGE_REST_GLOW` to 0.15 and repeat once. Then stop and record the value. New test `test_LOOK_C_web_badge_rests_before_the_flyovers`: the glow track of `TPL-WEBTLS` is at `BADGE_REST_GLOW` from f2416 to the last frame. On the final MP4: no step above 4.0 at f2431 or in f2695–2712. The steps at f746 (5.6) and f1376 (4.6) are measured again and recorded; they have no known cause and are not part of this item.

### Item D. The 10 beats with focal-size residuals (V1-CIN-01)

- **Why F2 stopped:** it was allowed to change only `dist`, and each further step failed a camera audit. The lens was not tried. A longer lens enlarges the subject without moving the camera, so the camera path, its speed and its clearances do not change. The charter allows 24–50 mm.
- **Exact change** (`cff\theme\shots.py`, one beat at a time, in this order):

  | Beat | Shot | Lens now | Lens target | Size now | Expected size |
  |---|---|---|---|---|---|
  | B-04.2 | `capsule-chase` | 35 | 50 | 65 | 93 (target 90) |
  | B-07.4 | `web-capsule-chase` | 35 | 50 | 64 | 92 (target 90) |
  | B-01.2 | `pulse-chase` | 35 | 42 | 78 | 94 (target 90) |
  | B-08.3 | `same-root` | 28 | 34 | 69 | 84 (target 80) |
  | B-02.3 | `badge-drop` | 35 | 50 | 96 | 137 |
  | B-06.1 | `present-follow` | 40 | 50 | 63 | 79 |
  | B-02.2 | `card-slide` | 42 | 50 | 99 | 118 |
  | B-05.2 | `flashback-glide` | 35 | 50 | 55 | 78 |
  | B-05.3 | `issuer-link` | 28 | 40 | 39 | 55 |
  | B-06.3 | `aia-push` | 50 | 50 | 53 | 80, by size (below) |

  1. For each beat raise `lens` in steps of 4 mm up to the target (the last step may be smaller). `flashback-glide` and `issuer-link` have a `start=Pose(...)`: leave the start pose's lens as it is.
  2. After each step run `python -m tools focal` and `python -m tools verify --skip-blender`. If anything fails (camera audits, the sign tests, `tools legibility`), undo that step and stop for that beat.
  3. For B-05.3 and B-08.3 also require, on at least 90% of the hold frames, that both `ROOT_CA` and the CA certificate (`CERT-CA1`, `CERT-CA2`) are fully inside the frame (`caption_layout.objects_rect`, as in Appendix A.1 of AUDIT-v1). If not, undo the step and stop.
  4. B-06.3: in `cff\stage\objects.py` multiply the `size` of `AIA-RDP` by 1.5 on every axis (the same treatment `HS-RDP` and the CRL scrolls got in v1.1.0).
  5. In `tools\focal_audit.py` set each `RESIDUAL_PX` entry to the size reached, rounded down to 5 px; delete the entry of any beat that now meets its target. Never lower an entry.
- **Expected visual result:** the request capsule, the pulse, the badge and the certificates fill more of the frame in their own beats; backgrounds go softer because a longer lens has less depth of field.
- **Measurable check:** `python -m tools focal` reports 0 beats under target with the raised values; at least the first four beats of the table meet their full target; `test_V1_CIN_01_focal_subject_size` passes; `len(RESIDUAL_PX)` is at most 6.
- **Stop rule for usage:** this item costs the most (up to about 25 verify runs). Do it last. If the session is past 70% of its usage, do only the first four rows.

### Item E. Four small fixes from the F3 re-audit (they ride along with the same render)

| ID | Exact change | Check |
|---|---|---|
| F3-LEG-01 | `cff\stage\labels.py`: `LBL-FLASHBACK` window `Window("B-05.2", 0.1, 4.7)` (was 4.9). | New test `test_F3_LEG_01_flashback_marker_ends_at_the_cut`: `plan_signs()["LBL-FLASHBACK"]` has no frame after f1395; `test_V1_PKI_02` still passes (at least 125 full frames). |
| F3-PKI-01 | `cff\story\model.py`: `Label("LBL-HS-RDP", LabelKind.TAG, "Proof of possession", "HS-RDP", ("B-06.1",))`. `cff\stage\labels.py`: `Placement("LBL-HS-RDP", "HS-RDP", (0.0, -0.12, 0.34), CAP_TAG, window=Window("B-06.1", 0.9, 2.7))` (the proof dissolves at 2.5 s). Add the line to B-06.1 in `docs\STORYBOARD.md`; run `python -m tools traceability`. | `python -m tools legibility` lists `LBL-HS-RDP` as OK (at least 45 full frames). If it cannot reach 45, remove the label again and record that. No tag for the web proof: its window is 1.2 s, too short to read. |
| F3-AUD-01 | `tools\film.py`: `TARGET_TP = -2.0`. `tools\verify.py`, step "final MP4": run `ebur128=peak=true` on the MP4 and fail if the true peak is above −1.0 dBFS. | `python -m tools verify` prints the MP4 true peak; it is at most −1.0 dBFS. |
| F3-PIPE-02 | `tools\film.py`, `write_metadata`: add `"dirty": bool(git status --porcelain output)`. `tools\verify.py`: the "final MP4" step fails if `render-metadata.json` says `dirty: true`. Commit before the final render. | `render-metadata.json` has `"dirty": false` and its `commit` is the commit that holds every Item A–E change. |

### Item F (optional, last). Film grain at encode

- `cff\theme\render.py` already has `grain=True` for the final tier, but nothing uses it. In `tools\film.py`, `encode`: when `render.tier(tier).grain`, start the graph with `[0:v]noise=alls=3:allf=t:all_seed=5201,format=rgba[b]` instead of `[0:v]format=rgba[b]`. The seed is fixed, so the encode stays deterministic. Text overlays are added after the grain and stay clean.
- **Expected visual result:** a fine, steady grain that hides banding in the haze gradients.
- **Measurable check:** Final MP4 at most 120 MB (v1.1.0: 55 MB); the cut-frame and luma-step checks still pass. If the file is larger, use `alls=2`; if still larger, drop the item.

## 4. Order: visual impact per unit of usage

| Rank | Item | Visual impact | Usage | Why this rank |
|---|---|---|---|---|
| 1 | A. Materials and lighting (and with it B, hero brightness) | very high: every wide shot, the hero and the poster | low: six files, values already measured | the grey-box look is the only open MAJOR |
| 2 | C. 90 s flash | high for 0.3 s; the film's most visible glitch | very low: two lines and a test | removes two luma steps at once |
| 3 | E. Four small fixes | low to medium | very low | they need the same re-render anyway |
| 4 | B, second change. Hero arrives earlier | medium: 4 s of near-empty frame | low: pytest only, three tries | |
| 5 | D. Focal sizes by lens | medium, spread over 10 beats | highest: up to 25 verify runs | do last; stop rule |
| 6 | F. Grain | low | very low | optional |

Work order: A, C, E, B (second change), D, F. Then the stills gate, the one final render, the encode.

## 5. Test on one scene first? Yes: a stills-and-strips gate before the full render

Do not test on one scene; test on 12 stills from six scenes and three short strips. It costs about 2 minutes of GPU and no tokens while it runs.

1. `python -m tools build --tier final`.
2. Add a command `python -m tools look-test` (new file `tools\look_test.py`, registered in `tools\__main__.py`). It renders the beauty pass at the final tier into `renders\look-test\beauty` with `pipeline.render_frame_list("final", "beauty", frames, pipeline.BLEND, "look-test")` and prints the checks of Items A and C:
   - stills: f457, f943, f1204, f1700, f2058, f2950, f2980, f3010, f3040, f3070, f3100, f3118;
   - strips: f2420–2440, f2695–2715 (Item C) and f1600–1623 (haze stability during the chain-docking move);
   - output: `YAVG`, `YLOW`, `SATAVG` per still; the seven-frame hero mean; the largest frame-to-frame step in each strip; PASS or FAIL per check.
   It must delete `renders\look-test\` first, because existing frames are skipped.
3. Pass criteria: every check of Items A and C, and no step above 4.0 in f1600–1623 (v1.1.0: none there).
4. View two images only: one 4x3 sheet of the 12 stills, and one strip of 8 frames, f3040–3110 every 10th. Look for exactly four things: a white blob on the floor; a hard bright dot in the sky; a subject that is hidden by haze; noise or banding. If any is present, stop and write it in PROJECT-STATE with the frame number. Do not tune by eye.
5. Only when the gate passes: delete `renders\final\beauty`, `renders\final\signs` and `renders\final\captions`, then `python -m tools render --tier final --rebuild` in the background, `python -m tools audio`, `python -m tools encode`, `python scripts\build_site.py`, `python -m tools verify`.

## 6. Models, effort and budget (Claude Pro)

| Session | Model, effort | Does | Images | Renders |
|---|---|---|---|---|
| L1 | **Sonnet 5.5, high** | Items A, C, E, B (second change), D, F; the stills gate; the one final render; encode; verify | at most 6: stills sheet, hero strip, one spare for a retry, final contact sheet, flash strip f2700–2710, poster | test: at most 150 final frames per attempt, three attempts; full: one |
| L2 | **Opus 5.5, medium** (or Fable 5.2) | a targeted re-audit like F3 (per-item PASS or FAIL on the film), then release v1.2.0 | at most 8 | none |

- Why Sonnet for L1: every value is given, every decision is a rule, and the tests do the judging. The work is transcription and measurement. If the stills gate fails three times, stop; do not switch models mid-session. Record the numbers and hand over to L2 for a ruling.
- Why a stronger model for L2: judging the look on frames is the one step that needs visual judgement, and `CLAUDE.md` forbids approving a first attempt without review.
- No subagents in either session. If L1 runs short of usage: Items A, C and E plus the gate and the render are the minimum that is worth a release. D and F can wait for v1.3.
- Whether v1.2.0 is a full release or again a pre-release is decided in L2: full only if V1-CIN-03 is judged closed (cinema estimate of 7 or more) and no new MAJOR is found.

## 7. What this plan does not fix

- **Shapes stay simple.** There are no bevels, textures or set dressing. The actor meshes are unit shapes scaled per object, so a bevel modifier would stretch; fixing that means rebuilding the mesh builders in `blender\actors\`. If L2 still judges the interiors (14–24 s, 29–36 s, 82–90 s) as grey-box, that is the next piece of work, and it needs a model with design judgement.
- The luma steps at f746 and f1376 (causes unknown).
- The session window (188 px against 220) and the two check lists that overlap a protected object on 42 and 21 frames.
- Audio has never been reviewed by ear.

## 8. Chief of Staff rulings for this plan

- **Lens is now a permitted lever for focal size** (Item D). AUDIT-v1 forbade it only to keep the F2 loop mechanical; the charter's lens range of 24–50 mm still holds.
- **Pool lights do not contradict "the root is dark".** The spec's rule is that the root's key module and press never operate in the present. The root's pool light is on from frame 1, never animates, and lights the whole complex equally; the glow channels of the module and the press are untouched, and the existing "root performs no operation" checks still run.
- **Haze and horizon are set dressing**, with no story role. No REFERENCE-SPEC change, no amendment; the spec hash stays `7cf45afa…6d23`.
- Record these rulings, the stills-gate numbers and every stop-rule value in `docs\GAN-LEDGER.md` under "Session L1".

## Appendix A. Luma measurement on an MP4 or on frames (port of the F3 scratch script; put it in `tools\luma.py`)

```python
# ffmpeg -i <mp4> -an -vf signalstats,metadata=print:file=stats.txt -f null -
yavg: dict[int, float] = {}
frame = 0
for line in open(stats, encoding="utf-8"):
    m = re.match(r"frame:(\d+)", line)
    if m:
        frame = int(m.group(1)) + 1            # 1-based film frame
        continue
    m = re.match(r"lavfi\.signalstats\.YAVG=([\d.]+)", line)
    if m:
        yavg[frame] = float(m.group(1))
for beat, (s, e) in timing.beat_windows().items():
    f0, f1 = timing.frame_range(s, e)
    print(beat, sum(yavg[f] for f in range(f0, f1 + 1)) / (f1 - f0 + 1))
cuts = {1246, 1247, 1396, 1397}
steps = [(f, abs(yavg[f] - yavg[f - 1])) for f in sorted(yavg) if f - 1 in yavg and f not in cuts and abs(yavg[f] - yavg[f - 1]) > 4.0]
```

For a PNG still use `-vf scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,signalstats,metadata=print:file=-` and read `YAVG`, `YLOW` and `SATAVG`.
v1.1.0 reference values: film mean 50.3; B-09.2 38.4; steps f746 5.6, f1376 4.6, f2431 6.4, f2709 7.7.

## Appendix B. Prototype code that produced the numbers in Section 1

These functions ran inside Blender 5.2.3 on a final-tier build. They show the exact node graph and properties; move them into the project files named in Item A and replace the literals by the constants of A1.

```python
def horizon(scene):                                   # -> blender/world.py
    nt = scene.world.node_tree
    background = nt.nodes["Background"]
    output = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    absz = nt.nodes.new("ShaderNodeMath"); absz.operation = "ABSOLUTE"
    nt.links.new(sep.outputs["Z"], absz.inputs[0])
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.use_clamp = True
    inv.inputs[0].default_value = 1.0
    nt.links.new(absz.outputs["Value"], inv.inputs[1])
    power = nt.nodes.new("ShaderNodeMath"); power.operation = "POWER"
    power.inputs[1].default_value = 6.0               # HORIZON_POWER
    nt.links.new(inv.outputs["Value"], power.inputs[0])
    glow = nt.nodes.new("ShaderNodeBackground")
    glow.inputs["Color"].default_value = linear4("#2B5C9E")   # palette.HORIZON_HEX
    scale = nt.nodes.new("ShaderNodeMath"); scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = 1.2               # HORIZON_STRENGTH
    nt.links.new(power.outputs["Value"], scale.inputs[0])
    nt.links.new(scale.outputs["Value"], glow.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(background.outputs["Background"], add.inputs[0])
    nt.links.new(glow.outputs["Background"], add.inputs[1])
    path = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(background.outputs["Background"], mix.inputs[1])   # lighting still sees the plain navy world
    nt.links.new(add.outputs["Shader"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], output.inputs["Surface"])


def haze(scene):                                      # -> blender/world.py and blender/render_settings.py
    nt = scene.world.node_tree
    output = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    scatter = nt.nodes.new("ShaderNodeVolumeScatter")
    scatter.inputs["Color"].default_value = linear4("#9CC4FF")
    scatter.inputs["Density"].default_value = 0.004
    scatter.inputs["Anisotropy"].default_value = 0.4
    nt.links.new(scatter.outputs["Volume"], output.inputs["Volume"])
    for name, value in (("volumetric_start", 0.5), ("volumetric_end", 150.0), ("volumetric_tile_size", "4"), ("volumetric_samples", 96),
                        ("volumetric_sample_distribution", 0.8), ("volumetric_ray_depth", 8), ("use_volumetric_shadows", True)):
        setattr(scene.eevee, name, value)


def pools(rig):                                       # -> blender/lighting.py, build_pools
    for name, pos, hex_colour, rel in POOLS:
        data = bpy.data.lights.new(f"LIGHT-pool-{name}", "SPOT")
        data.color = linear(hex_colour)
        data.energy = 4000.0 * rel
        data.spot_size = math.radians(50.0)
        data.spot_blend = 0.7
        data.shadow_soft_size = 0.5
        data.specular_factor = 0.3
        ob = bpy.data.objects.new(data.name, data)
        ob.location = (pos[0], pos[1] - 1.5, 12.0)
        rig.objects.link(ob)


def key_and_rim():                                    # -> blender/lighting.py, _spot
    for name, radius in (("LIGHT-key", 1.5), ("LIGHT-rim", 4.0)):
        light = bpy.data.objects[name].data
        light.specular_factor = 0.2
        light.volume_factor = 1.0
        light.shadow_soft_size = radius


def materials():                                      # -> blender/materials.py
    for mat in bpy.data.materials:
        bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if mat.node_tree else None
        if bsdf is None:
            continue
        if mat.name == "MAT-floor":
            bsdf.inputs["Roughness"].default_value = 0.4
        elif mat.name == "MAT-neutral":
            bsdf.inputs["Metallic"].default_value = 0.35
            bsdf.inputs["Roughness"].default_value = 0.45
        elif mat.name == "MAT-backdrop":
            bsdf.inputs["Metallic"].default_value = 0.6
            bsdf.inputs["Roughness"].default_value = 0.5
        elif mat.name.startswith("MAT-") and not mat.name.startswith(("MAT-caption", "MAT-sign", "MAT-trust")):
            bsdf.inputs["Roughness"].default_value = 0.4


def bloom(scene):                                     # -> blender/compositor.py
    glare = next(n for n in scene.compositing_node_group.nodes if n.bl_idname == "CompositorNodeGlare")
    glare.inputs["Strength"].default_value = 0.6
    glare.inputs["Threshold"].default_value = 0.8
```

Prototype runs, seven-frame hero mean (beauty only): v1.1.0 37.8; materials only 32.3; plus horizon 41.0; plus pools 43.5; plus haze 54.2 (with the hot-spot and the dot); plus bloom 55.9; with the final light settings of Item A **53.1**.
