"""``python -m tools character``: fetch the pinned MPFB add-on and CC0 MakeHuman assets, then generate assets/character.blend.

Run once by a developer (Session V4); the film build only reads the saved ``assets/character.blend`` and never downloads.
Downloads go to ``renders/character-src`` (gitignored), each checked against its SHA-256. MPFB is installed into
``renders/toolcache/extensions`` through ``BLENDER_USER_EXTENSIONS``, so the developer's own Blender profile is untouched.
Licences: ``LICENSES/CC0-1.0.txt`` (the MakeHuman assets) and README "Licensing split".
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from cff.stage import character
from tools import toolchain

ROOT = toolchain.ROOT
SRC = ROOT / "renders" / "character-src"
ASSETS_DIR = SRC / "mhassets"
EXTENSIONS = ROOT / "renders" / "toolcache" / "extensions"
SCRIPT = ROOT / "blender" / "make_character.py"
USER_AGENT = "certificate-flow-film-build"

MPFB_URL = "https://extensions.blender.org/download/sha256:c075b3e9b94b8e5556a5f03f4653602d02ea306de08126e8f55ed6dee28a2dad/add-on-mpfb-v2.0.18.zip"
MPFB_SHA256 = "c075b3e9b94b8e5556a5f03f4653602d02ea306de08126e8f55ed6dee28a2dad"
MPFB_VERSION = "2.0.18"
ASSET_PACK_URL = "https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip"
ASSET_PACK_SHA256 = "b542127a8e25547c7c29c19f2d1d2adb9a664c80396ecd694095dbc8028a0107"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch(url: str, expected: str, out: Path) -> Path:
    """Download ``url`` to ``out`` unless a file with the expected SHA-256 is already there; fail on a mismatch."""
    if out.exists() and sha256(out) == expected:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # pinned https URL, checked by SHA-256 below
    with urllib.request.urlopen(request, timeout=900) as response, out.open("wb") as handle:
        while block := response.read(1 << 20):
            handle.write(block)
    actual = sha256(out)
    if actual != expected:
        out.unlink()
        raise RuntimeError(f"{out.name}: SHA-256 {actual} != pinned {expected}")
    return out


def extract_parts(pack: Path) -> list[str]:
    """Extract only the asset folders the character uses (each part's folder, plus the eye material it points at)."""
    folders = {str(Path(p.source).parent.as_posix()) + "/" for p in character.PARTS if p.source}
    folders.add("eyes/materials/")
    written: list[str] = []
    with zipfile.ZipFile(pack) as archive:
        for info in archive.infolist():
            name = info.filename
            if name.endswith("/") or not any(name.startswith(f) for f in folders) or ".." in Path(name).parts:
                continue
            target = ASSETS_DIR / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
            written.append(name)
    return written


def install_mpfb(archive: Path) -> int:
    env = dict(os.environ, BLENDER_USER_EXTENSIONS=str(EXTENSIONS))
    EXTENSIONS.mkdir(parents=True, exist_ok=True)
    tools = toolchain.load()
    command = [str(tools.blender), "-b", "--factory-startup", "-c", "extension", "install-file", "-r", "user_default", str(archive)]
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


def generate() -> int:
    os.environ["BLENDER_USER_EXTENSIONS"] = str(EXTENSIONS)  # run_blender passes the environment on
    out = ROOT / character.ASSET_PATH
    return toolchain.run_blender(SCRIPT, args=["--assets", str(ASSETS_DIR), "--out", str(out)])


MANIFEST = ROOT / "assets" / "character.manifest.json"
CC0_MARK = re.compile(r"explicitly released as CC0[^\n]*")
MPFB_CC0_FILES = (  # the MakeHuman data inside the MPFB archive that ends up in the character: (path, what)
    ("data/3dobjs/base.obj", "MakeHuman base mesh"),
    ("data/rigs/standard/weights.default.json", "default rig skin weights"),
)


def _evidence(text: str) -> str:
    """The licence statement inside an asset file: the CC0 release line, or a JSON "license" field."""
    found = CC0_MARK.search(text) or re.search(r'"license"\s*:\s*"CC0[^"]*"', text)
    if found is None:
        raise RuntimeError("no CC0 statement found")
    return found.group(0).strip()


def write_manifest() -> Path:
    """Record where every piece of assets/character.blend came from and the CC0 statement each source file carries."""
    blend = ROOT / character.ASSET_PATH
    parts = []
    for part in character.PARTS:
        if part.source is None:
            continue
        text = (ASSETS_DIR / part.source).read_text(encoding="utf-8", errors="replace")
        parts.append({"object": part.name, "source": part.source, "licence": "CC0-1.0", "evidence": _evidence(text)})
    base = []
    with zipfile.ZipFile(SRC / f"mpfb-{MPFB_VERSION}.zip") as archive:
        for path, what in MPFB_CC0_FILES:
            text = archive.read(path).decode("utf-8", errors="replace")
            base.append({"object": "CHAR-body" if path.endswith(".obj") else character.RIG, "source": f"MPFB {MPFB_VERSION}: {path}", "what": what,
                         "licence": "CC0-1.0", "evidence": _evidence(text)})
    payload = {
        "asset": character.ASSET_PATH, "sha256": sha256(blend), "bytes": blend.stat().st_size,
        "generator": {"name": "MPFB", "version": MPFB_VERSION, "url": MPFB_URL, "sha256": MPFB_SHA256,
                      "licence": "GPL-3.0-or-later (the generator only; none of its code is in the asset)"},
        "asset_pack": {"name": "MakeHuman system assets (CC0)", "url": ASSET_PACK_URL, "sha256": ASSET_PACK_SHA256, "licence": "CC0-1.0"},
        "licence_text": "LICENSES/CC0-1.0.txt",
        "parts": base + parts,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    return MANIFEST


def main(manifest_only: bool = False) -> int:
    if manifest_only:
        print(f"wrote {write_manifest()}")
        return 0
    mpfb = fetch(MPFB_URL, MPFB_SHA256, SRC / f"mpfb-{MPFB_VERSION}.zip")
    pack = fetch(ASSET_PACK_URL, ASSET_PACK_SHA256, SRC / "makehuman_system_assets_cc0.zip")
    print(f"extracted {len(extract_parts(pack))} asset files")
    code = install_mpfb(mpfb)
    if code != 0:
        return code
    code = generate()
    if code == 0:
        out = ROOT / character.ASSET_PATH
        print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, SHA-256 {sha256(out)})")
        print(f"wrote {write_manifest()}")
    return code
