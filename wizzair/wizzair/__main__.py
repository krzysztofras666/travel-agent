from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import replace
from pathlib import Path

from wizzair.config import get_settings
from wizzair.email import send_digest
from wizzair.render import print_json, print_scan_result
from wizzair.scanner import login_and_save_session, scan_multipass


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

    send = sub.add_parser("send", help="Przeskanuj loty i wyślij digest e-mailem")
    send.add_argument("--dry-run", action="store_true", help="Wygeneruj HTML bez wysyłki")
    send.add_argument("--from", dest="sender", help="Nadawca")
    send.add_argument("--to", action="append", dest="recipients", help="Odbiorca")
    send.add_argument("--headed", action="store_true")
    send.set_defaults(func=cmd_send)

    preview = sub.add_parser("preview-email", help="Zapisz HTML digest na dysk")
    preview.add_argument("--out", default="logs/last_email.html", help="Ścieżka wyjściowa")
    preview.add_argument("--headed", action="store_true")
    preview.set_defaults(func=cmd_preview)

    auth = sub.add_parser("login", help="Zaloguj się i zapisz sesję przeglądarki (przydatne na Macu)")
    auth.add_argument("--headed", action="store_true", help="Pokaż okno przeglądarki")
    auth.set_defaults(func=cmd_login)

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    settings = _with_headed(get_settings(), args)
    result = asyncio.run(scan_multipass(settings))
    if args.json:
        print_json(result)
    else:
        print_scan_result(result, show_diagnostics=args.diagnostics)
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    settings = _with_headed(get_settings(), args)
    result = asyncio.run(scan_multipass(settings))
    recipients = _normalize_recipients(args.recipients)
    to_addrs = recipients or settings.email_to
    out = send_digest(
        settings,
        result,
        sender=args.sender,
        recipients=recipients,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        print(f"Dry run — e-mail NIE wysłany. Podgląd: {out}")
    else:
        print(f"Wysłano do: {', '.join(to_addrs)}")
        print(f"Podgląd zapisany: {out}")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    settings = _with_headed(get_settings(), args)
    result = asyncio.run(scan_multipass(settings))
    from wizzair.render_html import render_html

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(result), encoding="utf-8")
    print(f"Zapisano {out}")
    return 0


def cmd_login(args: argparse.Namespace) -> int:
    settings = _with_headed(get_settings(), args)
    if not args.headed:
        settings = replace(settings, headless=False)
    session_path = asyncio.run(login_and_save_session(settings))
    print(f"Zalogowano. Sesja zapisana: {session_path}")
    print("Kolejne uruchomienia mogą używać zapisanej sesji bez ponownego logowania.")
    return 0


def _with_headed(settings, args: argparse.Namespace):
    if getattr(args, "headed", False):
        return replace(settings, headless=False)
    return settings


def _normalize_recipients(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    recipients: list[str] = []
    for value in values:
        recipients.extend(part.strip() for part in value.split(",") if part.strip())
    return recipients


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
