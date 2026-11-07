"""Project CLI: ``python -m tools <command>``.

Commands implemented so far (Session 2): traceability, model-dump, packet stage0, spec-hash.
Session 3 adds env, verify, build, render, captions, contact, palette, motion and sync-check.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cff.story.export import model_dump
from tools import packet, traceability


def _cmd_traceability(args: argparse.Namespace) -> int:
    text = traceability.render()
    if args.check:
        current = traceability.OUTPUT.read_text(encoding="utf-8") if traceability.OUTPUT.exists() else ""
        if current != text:
            print("docs/TRACEABILITY.md is stale; run: python -m tools traceability")
            return 1
        missing = traceability.missing_ids(traceability.build_rows())
        if missing:
            print("\n".join(missing))
            return 1
        print("TRACEABILITY.md is current; every ID is covered")
        return 0
    path = traceability.write()
    print(f"wrote {path}")
    return 0


def _cmd_model_dump(args: argparse.Namespace) -> int:
    text = json.dumps(model_dump(), indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(text)
    return 0


def _cmd_packet(args: argparse.Namespace) -> int:
    if args.stage != "stage0":
        print(f"packet {args.stage}: not implemented yet (Session 3)")
        return 2
    folder = packet.build_stage0(args.round)
    print(f"built {folder}")
    return 0


def _cmd_spec_hash(_: argparse.Namespace) -> int:
    print(packet.sha256(packet.SPEC))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("traceability", help="generate docs/TRACEABILITY.md")
    p.add_argument("--check", action="store_true", help="fail if stale or any ID is uncovered")
    p.set_defaults(func=_cmd_traceability)
    p = sub.add_parser("model-dump", help="print or write the model dump JSON")
    p.add_argument("--out")
    p.set_defaults(func=_cmd_model_dump)
    p = sub.add_parser("packet", help="build a round packet")
    p.add_argument("stage")
    p.add_argument("--round", type=int)
    p.set_defaults(func=_cmd_packet)
    p = sub.add_parser("spec-hash", help="print the SHA-256 of docs/REFERENCE-SPEC.md")
    p.set_defaults(func=_cmd_spec_hash)
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
