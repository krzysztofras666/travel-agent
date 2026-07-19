from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, timedelta

from wizzair.api import booking_url
from wizzair.config import get_settings
from wizzair.models import Route, SearchResult
from wizzair.render import print_json, print_search_result
from wizzair.routes import ROUTES, get_routes
from wizzair.search import scan_routes, search_route


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wizzair",
        description="Search Wizz Air flights and surface the cheapest fares.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_routes = sub.add_parser("list-routes", help="Show configured routes")
    list_routes.add_argument("--origin", help="Filter by origin airport IATA code")
    list_routes.set_defaults(func=cmd_list_routes)

    search = sub.add_parser("search", help="Search a single route")
    search.add_argument("--from", dest="origin", required=True, help="Origin IATA code")
    search.add_argument("--to", dest="destination", required=True, help="Destination IATA code")
    search.add_argument(
        "--depart",
        dest="departure_date",
        default=_default_departure_date(),
        help="Departure date (YYYY-MM-DD)",
    )
    search.add_argument("--return", dest="return_date", help="Return date (YYYY-MM-DD)")
    search.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    search.add_argument("--no-diagnostics", action="store_true")
    search.set_defaults(func=cmd_search)

    scan = sub.add_parser("scan", help="Scan configured routes for cheap flights")
    scan.add_argument("--origin", help="Limit to routes from this airport")
    scan.add_argument("--route", action="append", dest="routes", help="Limit to route id(s)")
    scan.add_argument(
        "--depart",
        dest="departure_date",
        default=_default_departure_date(),
        help="Departure date (YYYY-MM-DD)",
    )
    scan.add_argument("--return", dest="return_date", help="Return date (YYYY-MM-DD)")
    scan.add_argument(
        "--max-per-route",
        type=int,
        default=1,
        help="Keep N cheapest offers per route",
    )
    scan.add_argument("--json", action="store_true")
    scan.add_argument("--no-diagnostics", action="store_true")
    scan.set_defaults(func=cmd_scan)

    url = sub.add_parser("booking-url", help="Print the Wizz Air booking URL for a route")
    url.add_argument("--from", dest="origin", required=True)
    url.add_argument("--to", dest="destination", required=True)
    url.add_argument("--depart", dest="departure_date", default=_default_departure_date())
    url.add_argument("--return", dest="return_date")
    url.set_defaults(func=cmd_booking_url)

    return parser


def _default_departure_date() -> str:
    return (date.today() + timedelta(days=14)).isoformat()


def cmd_list_routes(args: argparse.Namespace) -> int:
    routes = get_routes(origin=args.origin)
    for route in routes:
        print(f"{route.id:12} {route.origin_name} ({route.origin}) → {route.destination_name} ({route.destination})")
    print(f"\n{len(routes)} route(s)")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    settings = get_settings()
    route = _route_from_args(args.origin, args.destination)
    offers, diagnostic = asyncio.run(
        search_route(
            settings,
            route,
            departure_date=args.departure_date,
            return_date=args.return_date,
        )
    )
    search_result = SearchResult(offers=offers, diagnostics=[diagnostic])
    if args.json:
        print_json(search_result)
    else:
        print_search_result(search_result, show_diagnostics=not args.no_diagnostics)
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    settings = get_settings()
    result = asyncio.run(
        scan_routes(
            settings,
            departure_date=args.departure_date,
            return_date=args.return_date,
            origin=args.origin,
            route_ids=args.routes,
            max_per_route=args.max_per_route,
        )
    )
    if args.json:
        print_json(result)
    else:
        print_search_result(result, show_diagnostics=not args.no_diagnostics)
    return 0


def cmd_booking_url(args: argparse.Namespace) -> int:
    settings = get_settings()
    print(
        booking_url(
            settings,
            origin=args.origin,
            destination=args.destination,
            departure_date=args.departure_date,
            return_date=args.return_date,
        )
    )
    return 0


def _route_from_args(origin: str, destination: str) -> Route:
    origin = origin.upper()
    destination = destination.upper()
    for route in ROUTES:
        if route.origin == origin and route.destination == destination:
            return route
    return Route(origin, destination, origin, destination)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
