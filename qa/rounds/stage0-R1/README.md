# Stage 0 round packet: written specification

This packet is for judging the written specification. No frames exist at Stage 0, so
there are no images or motion strips. Judge the text and the model dump instead.

Contents:
- `docs/REFERENCE-SPEC.md`, `docs/GLOSSARY.md`, `docs/PKI-TECHNICAL-NOTES.md` (the frozen-file candidates)
- `docs/STORYBOARD.md` (what each beat will show on screen)
- `model-dump.json` (the story data the film is generated from: actors, keys, certificates,
  templates, CAs, CRLs, requests, discoveries, chains, labels, events and captions with timings)
- `schema.json` (the required report format)
- `regressions.json` (previously accepted findings to re-check; may be empty)
- `manifest.json` (file list with SHA-256, beat list, spec hash)

For every beat B-xx, give a verdict ACCURATE, MISLEADING or WRONG against facts F-01..F-17
and architecture AR-01..AR-07, citing the document sections and model-dump entries
(event, certificate or label IDs) in the `frames` field in place of frame files.
Report findings with severities as defined in `schema.json` and in REFERENCE-SPEC.
