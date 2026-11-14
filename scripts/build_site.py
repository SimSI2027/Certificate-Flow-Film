"""Build the static GitHub Pages site in site\\ from the delivered outputs (poster, preview video, captions, transcript).

Usage: .venv\\Scripts\\python.exe scripts\\build_site.py [release_url]

Relative paths only. The poster, the preview and captions.vtt are copied next to index.html.
"""

from __future__ import annotations

import html
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cff.story import captions as story_captions  # noqa: E402
from cff.story import model  # noqa: E402
from tools import pipeline  # noqa: E402

OUTPUT = ROOT / "output"
SITE = ROOT / "site"
REPO = "https://github.com/SimSI2027/Certificate-Flow-Film"
LAB = "https://github.com/SimSI2027/Certificate-Flow-Lab"
LAB_PAGES = "https://simsi2027.github.io/Certificate-Flow-Lab/"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Certificate Flow Film</title>
<meta name="description" content="A 109-second film that follows an ADCS certificate from request to trust: RDP and TLS paths, one trusted root.">
<style>
:root {{ --bg:#0d1420; --fg:#e8edf5; --muted:#9db0c8; --accent:#5ec4e8; --card:#16202f; }}
@media (prefers-color-scheme: light) {{ :root {{ --bg:#f4f7fb; --fg:#101826; --muted:#44546b; --accent:#0a6f99; --card:#ffffff; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ max-width:60rem; margin:0 auto; padding:1.5rem 16px 4rem; }}
h1 {{ font-size:2rem; margin:.4rem 0; }} h2 {{ margin-top:2.4rem; font-size:1.35rem; }}
a {{ color:var(--accent); }} a:focus-visible, summary:focus-visible, video:focus-visible {{ outline:3px solid var(--accent); outline-offset:3px; }}
video {{ width:100%; height:auto; border-radius:8px; background:#000; }}
.card {{ background:var(--card); border-radius:8px; padding:1rem 1.25rem; margin:1rem 0; }}
.path {{ font-family:ui-monospace,Consolas,monospace; }}
.muted {{ color:var(--muted); }}
li {{ margin:.2rem 0; }}
</style>
</head>
<body>
<main>
<header>
<h1>Certificate Flow Film</h1>
<p class="muted">One continuous camera move, with a single flashback, through a stylised 3D world: how a certificate is requested, issued and trusted in an Active Directory Certificate Services PKI. 109 seconds, 1920&times;1080, 30 FPS, no narration.</p>
</header>

<section aria-labelledby="watch">
<h2 id="watch">Watch</h2>
<video controls preload="metadata" poster="poster.png" aria-describedby="watch-note">
<source src="preview.mp4" type="video/mp4">
<track kind="captions" src="captions.vtt" srclang="en" label="English captions (same text as on screen)">
Your browser cannot play this video. <a href="{release}">Download the full MP4</a>.
</video>
<p id="watch-note" class="muted">This is the 720p preview with captions. <a href="{release}">Full 1080p MP4 (release asset)</a>.</p>
</section>

<section aria-labelledby="what">
<h2 id="what">What the film shows</h2>
<div class="card">
<p><strong>RDP path.</strong> The RDP server is issued a certificate from the <span class="path">RDPAuth</span> template by <span class="path">1SN0S Issuing CA 1</span>, whose CA certificate was signed offline by the <span class="path">1SN0S Root CA</span>. The client validates the whole chain up to the root it already trusts.</p>
<p><strong>TLS path.</strong> The web server is issued a certificate from the <span class="path">WebServer-TLS</span> template by <span class="path">1SN0S Issuing CA 2</span>, signed by the same root.</p>
<p><strong>One trusted root.</strong> Different templates can use different issuing CAs, but trust always anchors at the single Root CA. The private key never leaves the machine that generated it: the request is signed with it, and the request carries only the public key.</p>
</div>
</section>

<section aria-labelledby="how">
<h2 id="how">How it was made</h2>
<p>Everything is generated from one story model in Python: scripted Blender (<span class="path">bpy</span>) builds the scene and animation, EEVEE renders PNG sequences, and FFmpeg composites captions and sound-effect audio and encodes the film. A suite of automated checks (story consistency, PKI facts, motion limits, legibility, text contrast, frame sanity) acts as the discriminator against the generator; an adversarial review loop judged the story spec and the first animatic round only, and the film is gated on those automated checks.</p>
</section>

<section aria-labelledby="tr">
<h2 id="tr">Transcript</h2>
<details>
<summary>Captions, scene by scene</summary>
{transcript}
</details>
</section>

<section aria-labelledby="links">
<h2 id="links">Links</h2>
<ul>
<li><a href="{repo}">Repository</a></li>
<li><a href="{repo}/blob/main/docs/PKI-TECHNICAL-NOTES.md">PKI technical notes</a></li>
<li><a href="{repo}/blob/main/docs/STORYBOARD.md">Storyboard</a></li>
<li><a href="{release}">v1.0.0 pre-release, under audit (Final MP4)</a></li>
<li>Related: <a href="{lab}">Certificate-Flow-Lab</a> (<a href="{lab_pages}">demo</a>)</li>
</ul>
</section>
<footer class="muted"><p>Film, images and documentation: CC BY 4.0. Code: GPL-3.0-or-later.</p></footer>
</main>
</body>
</html>
"""


def transcript_html() -> str:
    titles = {s.id: s.title for s in model.MODEL.scenes}
    by_scene: dict[str, list[story_captions.Caption]] = {}
    for cap in story_captions.captions_in_order():
        by_scene.setdefault(cap.scene, []).append(cap)
    parts: list[str] = []
    for scene_id, caps in by_scene.items():
        parts.append(f"<h3>{html.escape(titles.get(scene_id, scene_id))}</h3><ul>")
        parts += [f"<li><span class=\"muted\">{pipeline.vtt_time(c.hold_start_s)[3:8]}</span> &mdash; {html.escape(c.text)}</li>" for c in caps]
        parts.append("</ul>")
    return "\n".join(parts)


def main(release_url: str) -> int:
    SITE.mkdir(exist_ok=True)
    shutil.copyfile(OUTPUT / "Certificate-Flow-Film-Poster.png", SITE / "poster.png")
    shutil.copyfile(OUTPUT / "Certificate-Flow-Film-Preview.mp4", SITE / "preview.mp4")
    pipeline.write_captions()
    shutil.copyfile(OUTPUT / "captions.vtt", SITE / "captions.vtt")
    page = PAGE.format(release=release_url, transcript=transcript_html(), repo=REPO, lab=LAB, lab_pages=LAB_PAGES)
    (SITE / "index.html").write_text(page, encoding="utf-8", newline="\n")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print(f"wrote {SITE / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else f"{REPO}/releases/tag/v1.0.0"))
