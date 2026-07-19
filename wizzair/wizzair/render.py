from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from wizzair.models import FlightOffer, SearchDiagnostic, SearchResult


def print_search_result(result: SearchResult, *, show_diagnostics: bool = True) -> None:
    console = Console()
    table = Table(title="Wizz Air flights")
    table.add_column("Route")
    table.add_column("Date")
    table.add_column("Times")
    table.add_column("Flight")
    table.add_column("Price", justify="right")
    table.add_column("Bundle")

    for offer in result.offers:
        table.add_row(
            f"{offer.origin} → {offer.destination}",
            _format_dates(offer),
            f"{offer.departure_time} → {offer.arrival_time}".strip(" →"),
            offer.flight_number,
            _format_price(offer),
            offer.bundle,
        )

    if result.offers:
        console.print(table)
    else:
        console.print("[yellow]No flights found.[/yellow]")

    if show_diagnostics and result.diagnostics:
        diag = Table(title="Diagnostics")
        diag.add_column("Route")
        diag.add_column("Departure")
        diag.add_column("Return")
        diag.add_column("Offers", justify="right")
        diag.add_column("Error")
        for row in result.diagnostics:
            diag.add_row(
                row.route_id,
                row.departure_date,
                row.return_date or "—",
                str(row.offers_found),
                row.error,
            )
        console.print(diag)


def print_json(result: SearchResult) -> None:
    payload = {
        "offers": [_offer_to_dict(offer) for offer in result.offers],
        "diagnostics": [_diag_to_dict(row) for row in result.diagnostics],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _offer_to_dict(offer: FlightOffer) -> dict:
    return {
        "origin": offer.origin,
        "destination": offer.destination,
        "departure_date": offer.departure_date,
        "return_date": offer.return_date,
        "departure_time": offer.departure_time,
        "arrival_time": offer.arrival_time,
        "flight_number": offer.flight_number,
        "price": offer.price,
        "currency": offer.currency,
        "bundle": offer.bundle,
        "url": offer.url,
    }


def _diag_to_dict(row: SearchDiagnostic) -> dict:
    return {
        "route_id": row.route_id,
        "origin": row.origin,
        "destination": row.destination,
        "departure_date": row.departure_date,
        "return_date": row.return_date,
        "offers_found": row.offers_found,
        "error": row.error,
    }


def _format_dates(offer: FlightOffer) -> str:
    if offer.return_date:
        return f"{offer.departure_date} → {offer.return_date}"
    return offer.departure_date


def _format_price(offer: FlightOffer) -> str:
    amount = f"{offer.price:,.2f}".replace(",", " ")
    return f"{amount} {offer.currency}"
