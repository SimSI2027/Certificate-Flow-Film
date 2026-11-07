"""Repository sync check (Charter 4 and 12): clean tree and local HEAD == origin/main."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SyncResult:
    local_head: str
    remote_head: str
    clean: bool

    @property
    def ok(self) -> bool:
        return self.clean and bool(self.local_head) and self.local_head == self.remote_head


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def check(remote: str = "origin", branch: str = "main") -> SyncResult:
    local = _git("rev-parse", "HEAD")
    listing = _git("ls-remote", remote, f"refs/heads/{branch}")
    remote_head = listing.split()[0] if listing else ""
    clean = _git("status", "--porcelain") == ""
    return SyncResult(local, remote_head, clean)
