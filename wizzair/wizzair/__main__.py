from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import replace

from wizzair.config import get_settings
from wizzair.render import print_json, print_scan_result
from wizzair.scanner import scan_multipass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wizzair",
        description=(
            "Loguje się do Wizz Multipass i wyszukuje dostępne loty "
            "All You Can Fly z wybranych lotnisk."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser(
        "run",
        help="Zaloguj się i przeskanuj dostępne loty (domyślnie KRK/KTW, dziś + 3 dni)",
    )
    run.add_argument("--json", action="store_true", help="Wydrukuj JSON")
    run.add_argument("--diagnostics", action="store_true", help="Pokaż diagnostykę")
    run.add_argument("--headed", action="store_true", help="Uruchom przeglądarkę z UI")
    run.set_defaults(func=cmd_run)

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    settings = get_settings()
    if args.headed:
        settings = replace(settings, headless=False)

    result = asyncio.run(scan_multipass(settings))
    if args.json:
        print_json(result)
    else:
        print_scan_result(result, show_diagnostics=args.diagnostics)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
