# Stage 1 round packet: animatic (grey-box, 960x540)

Judge the animatic as film, not as a diagram, against the frozen spec (REFERENCE-SPEC criteria C-01..C-11,
L-01..L-08, facts F-01..F-17, architecture AR-01..AR-07).

Contents:
- `frames/`: composited animatic frames (3D beauty pass + caption layer). Three per beat (`B-xx.y_a/b/c`: just after
  entry, middle, just before exit) and the frames on both sides of each cut (`T-cut-*`).
- `strips/`: one motion strip per beat (6 frames from first to last, left to right, top to bottom).
- `shots.json`: per beat, the model's focal subject and the camera lens, f-stop and focus distance at the middle frame.
- `model-dump.json`: the story data (events, certificates, labels, captions with timings).
- `docs/`: the frozen spec, glossary, PKI notes and the storyboard.
- `schema.json`: the required report format. `regressions.json`: previously accepted findings to re-check.
- `manifest.json`: every file with its SHA-256, the frame list and the spec hash.

For each beat give a PKI verdict (ACCURATE, MISLEADING or WRONG) citing frame file names; report findings with
severities as defined in `schema.json`. Grey-box geometry is expected at this stage: judge composition, motion,
legibility, colour language and accuracy, not surface finish.

Judging protocol (every reviewer):
- Open every file in `frames/` and `strips/`, and list each one in `files_read`. Never judge a beat from a sample.
- Track persistent objects across beats, not frame by frame in isolation. In particular, follow every private key
  (each server's key and each CA's module key) from the moment it forms to the end of the film, and every request
  capsule from its creation to the place it is consumed. Once stored, a private key must stay inside its own locked
  container or sealed module; a key outside it, beside or attached to a capsule, travelling with anything, or an
  emptied container, is a key violation even when the shape is small or partly hidden.
