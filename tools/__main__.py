"""Project CLI: ``python -m tools <command>``.

Commands: env, calibrate, verify, build, render, captions, packet, contact, palette, motion, traceability, model-dump,
spec-hash, sync-check. Blender is always called as
``"<blender.exe>" -b [file.blend] --factory-startup --python-exit-code 1 -P <script.py> -- <args>``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cff.story.export import model_dump
from tools import packet, pipeline, sync, traceability, verify


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
    if args.stage == "stage0":
        print(f"built {packet.build_stage0(args.round)}")
        return 0
    if args.stage == "stage1":
        print(f"built {packet.build_stage1(args.round, args.tier)}")
        return 0
    print(f"packet {args.stage}: unknown stage (stage0 or stage1)")
    return 2


def _cmd_spec_hash(_: argparse.Namespace) -> int:
    print(packet.sha256(packet.SPEC))
    return 0


def _cmd_sync_check(_: argparse.Namespace) -> int:
    result = sync.check()
    print(f"local HEAD : {result.local_head}")
    print(f"origin/main: {result.remote_head or '(missing)'}")
    print(f"clean tree : {result.clean}")
    print("SYNC OK" if result.ok else "SYNC FAILED")
    return 0 if result.ok else 1


def _cmd_env(args: argparse.Namespace) -> int:
    info = pipeline.env_report()
    print(json.dumps(info, indent=2) if args.json else "\n".join(f"{k}: {v}" for k, v in info.items()))
    return 0 if info["ok"] else 1


def _cmd_verify(args: argparse.Namespace) -> int:
    return verify.run(repo=args.repo, skip_blender=args.skip_blender)


def _cmd_build(args: argparse.Namespace) -> int:
    return pipeline.build(args.tier)


def _cmd_render(args: argparse.Namespace) -> int:
    return pipeline.render_all(args.tier, args.scene, args.first, args.last, args.rebuild)


def _cmd_captions(_: argparse.Namespace) -> int:
    for path in pipeline.write_captions():
        print(f"wrote {path}")
    return 0


def _cmd_contact(args: argparse.Namespace) -> int:
    print(f"wrote {pipeline.contact_sheet(args.tier)}")
    return 0


def _cmd_palette(_: argparse.Namespace) -> int:
    lines, bad = pipeline.palette_report()
    print("\n".join(lines))
    print(f"{bad} failing pair(s)")
    return 1 if bad else 0


def _cmd_motion(_: argparse.Namespace) -> int:
    lines, bad = pipeline.motion_report()
    print("\n".join(lines))
    return 1 if bad else 0


def _cmd_legibility(_: argparse.Namespace) -> int:
    from tools import legibility_audit  # noqa: PLC0415  (builds the sign plan: only this command pays for it)

    return legibility_audit.main()


def _cmd_focal(_: argparse.Namespace) -> int:
    from tools import focal_audit  # noqa: PLC0415

    return focal_audit.main()


def _cmd_look_test(_: argparse.Namespace) -> int:
    from tools import look_test  # noqa: PLC0415

    return look_test.main()


def _cmd_calibrate(args: argparse.Namespace) -> int:
    from tools import calibrate  # noqa: PLC0415  (imported only by this command, so no other command can reach a fault)

    faults = calibrate.FAULTS if args.fault == "all" else (args.fault,)
    worst = 0
    for fault in faults:
        worst = max(worst, calibrate.run(fault, make_packet=args.packet, skip_checks=args.skip_checks))
    return worst


def _cmd_audio(_: argparse.Namespace) -> int:
    from tools import film  # noqa: PLC0415

    print(json.dumps(film.build_audio(), indent=2))
    return 0


def _cmd_encode(args: argparse.Namespace) -> int:
    from tools import film  # noqa: PLC0415

    film.encode(args.tier)
    print(f"wrote {film.FINAL_MP4}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("calibrate", help="build a deliberately broken animatic (Charter 2.8), run the hard checks on it, optionally build a blind packet")
    p.add_argument("fault", choices=["private_key_leak", "root_issues_leaf", "flowchart", "caption_clip", "all"])
    p.add_argument("--packet", action="store_true", help="also render the packet frames and build qa/calibration/stage1-K<n>")
    p.add_argument("--skip-checks", action="store_true", help="skip the in-Blender checks (packet only)")
    p.set_defaults(func=_cmd_calibrate)

    p = sub.add_parser("env", help="print the toolchain (Blender, FFmpeg, Python) and check it against the pin")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_env)

    p = sub.add_parser("verify", help="run every hard discriminator (pytest, ruff, mypy, audits, Blender scene checks, frame checks)")
    p.add_argument("--repo", action="store_true", help="also check a clean tree and local HEAD == origin/main")
    p.add_argument("--skip-blender", action="store_true", help="skip the in-Blender scene checks (pure-Python steps only)")
    p.set_defaults(func=_cmd_verify)

    p = sub.add_parser("build", help="build the .blend from the story model (renders/film.blend)")
    p.add_argument("--tier", default="animatic", choices=["animatic", "preview", "final"])
    p.set_defaults(func=_cmd_build)

    p = sub.add_parser("render", help="render frames in resumable 300-frame chunks (skips frames already on disk)")
    p.add_argument("--tier", default="animatic", choices=["animatic", "preview", "final"])
    p.add_argument("--scene", default="all", choices=["all", "BEAUTY", "SIGNS", "CAPTIONS"])
    p.add_argument("--first", type=int)
    p.add_argument("--last", type=int)
    p.add_argument("--rebuild", action="store_true", help="rebuild the .blend first")
    p.set_defaults(func=_cmd_render)

    p = sub.add_parser("contact", help="contact sheet with one tile per beat")
    p.add_argument("--tier", default="animatic")
    p.set_defaults(func=_cmd_contact)

    for name, func, text in (
        ("captions", _cmd_captions, "write output/captions.vtt and output/transcript.md from cff/story/captions.py"),
        ("palette", _cmd_palette, "L-07 palette check (CIEDE2000, with colour-vision simulation)"),
        ("motion", _cmd_motion, "planned-film audits: camera, focal subject, keys, easing, glow"),
        ("legibility", _cmd_legibility, "planned-film legibility audit: must-read sign holds (L-06), captions clear of the focal subject (L-05)"),
        ("focal", _cmd_focal, "focal-subject size per beat (V1-CIN-01): median projected longer side over the beat hold"),
        ("look-test", _cmd_look_test, "stills-and-strips gate of the v1.2 look plan: renders into renders/look-test and measures luma (build --tier final first)"),
    ):
        sub.add_parser(name, help=text).set_defaults(func=func)

    p = sub.add_parser("audio", help="synthesise the cue mix and loudness-normalise it (output/audio/mix.wav)")
    p.set_defaults(func=_cmd_audio)

    p = sub.add_parser("encode", help="overlay signs and captions, mux audio, write Final/Preview MP4, poster, contact sheet, metadata")
    p.add_argument("--tier", default="final", choices=["preview", "final"])
    p.set_defaults(func=_cmd_encode)

    p = sub.add_parser("traceability", help="generate docs/TRACEABILITY.md")
    p.add_argument("--check", action="store_true", help="fail if stale or any ID is uncovered")
    p.set_defaults(func=_cmd_traceability)

    p = sub.add_parser("model-dump", help="print or write the model dump JSON")
    p.add_argument("--out")
    p.set_defaults(func=_cmd_model_dump)

    p = sub.add_parser("packet", help="build a round packet (stage0 or stage1)")
    p.add_argument("stage")
    p.add_argument("--round", type=int)
    p.add_argument("--tier", default="animatic")
    p.set_defaults(func=_cmd_packet)

    p = sub.add_parser("spec-hash", help="print the SHA-256 of docs/REFERENCE-SPEC.md")
    p.set_defaults(func=_cmd_spec_hash)

    p = sub.add_parser("sync-check", help="verify a clean tree and local HEAD == origin/main")
    p.set_defaults(func=_cmd_sync_check)

    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
