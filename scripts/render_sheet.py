"""Render one middle frame per beat (beauty, signs, captions) at a tier and tile them into a contact sheet.

Usage: .venv\\Scripts\\python.exe scripts\\render_sheet.py <tier>

The frames land in the tier's normal frame folders, so a later full render skips them (use_overwrite=False).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cff.story import model  # noqa: E402
from tools import frames, pipeline  # noqa: E402


def main(tier: str) -> int:
    middles = [frames.sample_frames(beat.id)[1] for beat in model.MODEL.beats]
    sign_wanted = set(frames.sign_frames())
    caption_wanted = set(frames.caption_frames())
    for layer, wanted in (
        ("beauty", middles),
        ("signs", [f for f in middles if f in sign_wanted]),
        ("captions", [f for f in middles if f in caption_wanted]),
    ):
        code = pipeline.render_frame_list(tier, layer, wanted, pipeline.BLEND, tier)
        if code != 0:
            return code
    print(f"wrote {pipeline.contact_sheet(tier)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "final"))
