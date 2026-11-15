# Enhancement plan for v1.4 (plan only, nothing built)

Written by the V5 audit session (2026-11-14). The v1.3.0 film is accurate and released; this list is about making it nicer to watch without touching any PKI fact. Findings named `V5A-…` and `V5B-…` are in `docs\AUDIT-V5.md`.

## Rules that apply to every item

- **The frozen spec stays as it is.** No caption wording, beat order or beat content changes. Anything that would need a spec amendment is marked.
- **PKI guard rails.** The root does nothing in the present tense: its seal never animates, and its key module and press stay dark outside the flashback (B-05.1, B-08.3). No private key moves. Nothing may look like traffic to or from the root.
- **Three layers.** The film is composited from beauty, signs and captions. A captions-only change re-renders in minutes. A signs change takes about 17 minutes for the full layer. A beauty change needs a partial re-render with `python -m tools rerender-range` (a full beauty pass is about 1 hour on the RTX 4090).
- **Any change makes a new MP4.** That means a new encode, `python -m tools verify`, a short audit and a v1.4.0 release.
- **"Share of a window"** is a rough share of one 5-hour Claude Pro usage window for the build session. GPU render time is wall-clock time, not usage, but the session has to wait and poll.

## Ranked list

| Rank | Item | Payoff | Risk | Model, effort | Share of a window |
|---|---|---|---|---|---|
| 1 | Seals stamp, chain links lock | high | medium | Opus 5.5, High | 45% |
| 2 | Stronger title card | high | low | Sonnet 5.5, medium | 15% |
| 3 | Screen UI on the laptop and session window | medium to high | low to medium | Sonnet 5.5, High | 30% |
| 4 | Tighter hero shot | medium to high | medium | Opus 5.5, High | 35% |
| 5 | Depth-of-field moments | medium | low to medium | Sonnet 5.5, medium | 20% |
| 6 | Tags re-anchored near their subject | medium | low to medium | Sonnet 5.5, High | 20% |
| 7 | Root card marks on the back of the trust store | medium | low | Sonnet 5.5, medium | 15% |
| 8 | Interior key light in the CA enclosures | medium | medium | Sonnet 5.5, High | 25% |
| 9 | Twinkle on the trust paths | medium | medium to high | Opus 5.5, High | 35% |
| 10 | Seal contrast and matching cage emblem | low to medium | low, but a full beauty render | Sonnet 5.5, medium | 15% plus the render |

## The items

### 1. Seals stamp, chain links lock

- **Change.**
  - In `cff\stage\choreography.py`, at B-04.4 (33–36 s) and B-08.2 (85.5–90 s): the issuer seal on `CERT-RDP` and `CERT-WEB` lands on the frame the press head touches. It scales from 1.6 to 1.0 with a named overshoot preset and gives one short flash in the issuer's colour. The ribbon tails unroll over the next 8 frames.
  - At B-05.3 (46.5–50 s) and B-08.3 (90–93 s): the links of `TL-CA1` and `TL-CA2` appear one at a time, two frames apart, starting at the CA certificate. When the last link is in place, one soft pulse runs along the chain and each link brightens as it passes.
  - In `cff\audio\cues.py`: a low thud for each stamp and a short click train for each chain, from the existing synth.
- **Visual payoff.** The two signing moments and the two "same root" moments become events. These are the beats the audit called correct but plain.
- **Risk.**
  - Accuracy: the pulse must start at the CA certificate, and the root cage, seal, module and press must not react. The root self-seal and the self-signed RDP card never animate. An in-Blender check should assert both.
  - Checks: C-06 (Bezier presets, pop limit), C-07 (the seal stays part of one card object), the `silhouettes` check, the luma step gate.
  - Render: beauty for B-04.4, B-05.3, B-08.2 and B-08.3, about 420 frames; audio and encode.
- **Build.** Opus 5.5, High. About 45% of a window.

### 2. Stronger title card

- **Change.** In `blender\captions_scene.py` and `cff\stage\caption_layout.py`, for `TITLE-S9` only:
  - no plate;
  - "Certificate Flow" in Inter Bold and "From request to trust" in Inter Regular, on one line, so the frozen wording is unchanged;
  - the dash drawn as a short gold rule (the root's colour) that grows from the centre over 12 frames;
  - letters fade in left to right over 20 frames;
  - the title sits in the lower third, so the topology stays visible above it until the fade.
- **Visual payoff.** The last five seconds look designed. Today the title is a caption plate across the middle of the hero (V5A-CIN-03).
- **Risk.** Low. Only the captions layer changes (about 115 frames). L-01, L-02 (contrast without a plate, against the darkest and brightest frames under it), L-03, L-04 and L-05 must stay green. `captions.vtt` does not change.
- **Build.** Sonnet 5.5, medium. About 15% of a window.

### 3. Screen UI on the laptop and the session window

- **Change.** In `blender\actors\client.py` (`screen`), `blender\actors\hardware.py` (`screen_ui`) and `blender\finishes.py` (the existing `ui_layer` materials):
  - `SCREEN-RDP` (67–70 s) becomes a remote desktop: a title bar with a small green tick, a taskbar strip and two window outlines.
  - `SCREEN-WEB` (97–98 s) becomes a browser: tab strip, address bar with a closed padlock, page blocks.
  - Shapes only, from primitives; no readable text and no vendor marks. The existing signs keep carrying the names.
- **Visual payoff.** The payoff of each path shows what the user gained. Today the session window is a blank pale panel (V5A-CIN-04).
- **Risk.** Low to medium. The tick and padlock are green, so they may appear only with the screen, after validation completes (C-10). The V1-CIN-05 size test for the session window must stay green. Beauty re-render for f1993–2100 and f2925–3270, about 450 frames.
- **Build.** Sonnet 5.5, High. About 30% of a window.

### 4. Tighter hero shot

- **Change.** In `cff\theme\shots.py`, B-09.2: bring the camera in (distance about −25%, lens toward 40 mm) so the topology fills about 65% of the frame width instead of 40%, and add a slow 6° orbit that continues under the title.
- **Visual payoff.** The closing picture reads at a glance; the root cage grows from about 110 px to about 170 px (V5A-CIN-02).
- **Risk.** Medium. The hero tests (whole topology in frame from 98.5 s, mean luma 50 or more), the label holds and C-02 speed limits all constrain the move. Beauty and signs for f2941–3270.
- **Build.** Opus 5.5, High. About 35% of a window.

### 5. Depth-of-field moments

- **Change.** Depth of field is already on. In `cff\theme\shots.py`, open the aperture to f/1.8–2.0 on four close beats and add a short rack focus with the existing `focus_pull`:
  - B-03.1 (14–16 s): from the private key to the public key.
  - B-04.4 (33–36 s): from the press head to the stamped card.
  - B-06.1 (50–53 s): from the server to the proof banner as it leaves.
  - B-08.2 (85.5–90 s): from the press head to the card.
- **Visual payoff.** The rack LEDs behind the subject melt into soft points, and the eye is led to the object that matters.
- **Risk.** Low to medium. C-03 (focus within 10% of the subject distance) and the luma step gate. Signs are a separate layer and stay sharp. EEVEE bokeh can shimmer, so preview one strip per beat first. About 375 beauty frames.
- **Build.** Sonnet 5.5, medium. About 20% of a window.

### 6. Tags re-anchored near their subject

- **Change.** In `cff\stage\signs.py`, add a maximum distance (about 200 px) between a tag and its anchor for `LBL-SELF`, `LBL-UNVERIFIED` and `LBL-CA1-INELIGIBLE`, and let the solver prefer the side away from the caption band. No leader lines (C-01 forbids connector grammar).
- **Visual payoff.** "Self-signed" and "Unverified" sit by the card they describe (V5A-LEG-01, V5A-LEG-02).
- **Risk.** Low to medium. The must-read holds (45 frames) and the "no sign jump" tests must stay green. Signs layer only, about 150 frames. Add a test named `V5A_LEG_01`.
- **Build.** Sonnet 5.5, High. About 20% of a window.

### 7. Root card marks on the back of the trust store

- **Change.** In the trust store builder (`root_cradle` in `blender\actors\client.py`, object `TS-CLIENT-ROOT`), print the root card's marks (CA badge and self-seal, in ink) on the cradle's back face, the way the cards already carry their marks on both faces.
- **Visual payoff.** While the chain docks (53–64 s), its top link reads as the root certificate, not as a plain gold slab (V5B-OBS-01).
- **Risk.** Low. The store must stay gold and static from frame 1 (V1-PKI-01). Beauty for f1591–1920, about 330 frames.
- **Build.** Sonnet 5.5, medium. About 15% of a window.

### 8. Interior key light in the CA enclosures

- **Change.** In `blender\lighting.py`, one static, shadowless area light under the roof of each issuing CA enclosure, in the pale identity tint, sized to lift B-04.3 and B-08.1 from mean luma 50 and 45 to about 55.
- **Visual payoff.** The HSM, the press and the CA racks read clearly, and the darkening at the CA 2 doorway (81.7 s, V5B-CIN-03) is roughly halved.
- **Risk.** Medium. Earlier interior lights overflowed EEVEE's shadow pool (V3-CIN-01), so the light must cast no shadow. The pool-light check allows one static pool per actor; this adds a new, named class of light. About 525 beauty frames.
- **Build.** Sonnet 5.5, High. About 25% of a window.

### 9. Twinkle on the trust paths

- **Change.** In the hero only (B-09.2), small gold points along `TP-RDP`, `TP-WEB` and both trust links that brighten and fade in place, from a seeded `random.Random` baked to keyframes (no particle simulation). They are one whitelisted effect (C-08 allows one active particle effect).
- **Visual payoff.** The closing picture has life in it.
- **Risk.** Medium to high. The points must not travel: motion along a path to the root would read as network traffic to an offline machine. C-08 clipping limits and EEVEE flicker need a preview strip. Beauty for f2941–3270.
- **Build.** Opus 5.5, High. About 35% of a window.

### 10. Seal contrast and matching cage emblem

- **Change.** A new palette token for a darker tone of each issuer colour, used for the rosette on end-entity cards with an ink ring (V5A-ICO-01). Replace the centre disc of the emblem on the root cage with the same self-closing ring as on the cards (V5A-ICO-02).
- **Visual payoff.** The issuer seal reads by colour, not only by outline; one glyph means "self-signed" everywhere.
- **Risk.** Low for the change itself (palette and CVD tests, `silhouettes`). The cards are on screen in more than a third of the film, so this is only worth doing together with a full beauty render.
- **Build.** Sonnet 5.5, medium. About 15% of a window, plus the full render.

## Recommendation: the top 3

1. **Seals stamp, chain links lock (item 1).** The largest gain in "fancy", at the four moments that carry the story.
2. **Stronger title card (item 2).** The cheapest visible gain, and the ending is what viewers remember.
3. **Screen UI (item 3).** It completes the two payoffs.

Together they need two build sessions: items 2 and 3 in one Sonnet 5.5 session (about 45% of a window), item 1 in one Opus 5.5 session (about 45%). The re-rendered frame ranges do not overlap except in the closing shot, so one encode and one short audit can cover all three. Item 7 fits into the Sonnet session if usage allows.
