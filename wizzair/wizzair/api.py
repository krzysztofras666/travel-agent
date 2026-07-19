from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from wizzair.config import Settings
from wizzair.models import FlightOffer

API_VERSION_RE = re.compile(r"be\.wizzair\.com/([\d.]+)/Api")


def booking_url(
    settings: Settings,
    *,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
) -> str:
    ret = return_date or "null"
    return (
        f"https://www.wizzair.com/{settings.locale}/booking/select-flight/"
        f"{origin.upper()}/{destination.upper()}/{departure_date}/{ret}/"
        f"{adults}/{children}/{infants}/null"
    )


def extract_api_version(text: str) -> str | None:
    match = API_VERSION_RE.search(text)
    if match:
        return match.group(1)
    return None


def build_search_payload(
    *,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None,
    adults: int,
    children: int,
    infants: int,
    wdc: bool,
) -> dict[str, Any]:
    flight_list = [
        {
            "departureStation": origin.upper(),
            "arrivalStation": destination.upper(),
            "departureDate": departure_date,
        }
    ]
    if return_date:
        flight_list.append(
            {
                "departureStation": destination.upper(),
                "arrivalStation": origin.upper(),
                "departureDate": return_date,
            }
        )

    return {
        "isFlightChange": False,
        "flightList": flight_list,
        "adultCount": adults,
        "childCount": children,
        "infantCount": infants,
        "wdc": wdc,
    }


def parse_search_response(
    data: dict[str, Any],
    *,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None,
    booking_page_url: str,
) -> list[FlightOffer]:
    offers: list[FlightOffer] = []
    outbound = _parse_leg(
        flights=data.get("outboundFlights") or [],
        origin=origin,
        destination=destination,
        leg_date=departure_date,
        return_date=return_date or "",
        booking_page_url=booking_page_url,
    )
    offers.extend(outbound)

    if return_date:
        inbound = _parse_leg(
            flights=data.get("returnFlights") or [],
            origin=destination,
            destination=origin,
            leg_date=return_date,
            return_date=return_date,
            booking_page_url=booking_page_url,
        )
        offers.extend(inbound)

    return offers


def _parse_leg(
    *,
    flights: list[dict[str, Any]],
    origin: str,
    destination: str,
    leg_date: str,
    return_date: str,
    booking_page_url: str,
) -> list[FlightOffer]:
    offers: list[FlightOffer] = []
    for flight in flights:
        fare = _cheapest_fare(flight.get("fares") or [])
        if fare is None:
            continue

        offers.append(
            FlightOffer(
                origin=flight.get("departureStation", origin).upper(),
                destination=flight.get("arrivalStation", destination).upper(),
                departure_date=leg_date,
                return_date=return_date,
                departure_time=_format_time(flight.get("departureDateTime", "")),
                arrival_time=_format_time(flight.get("arrivalDateTime", "")),
                flight_number=_format_flight_number(flight),
                price=fare["price"],
                currency=fare["currency"],
                bundle=fare["bundle"],
                url=booking_page_url,
            )
        )
    return offers


def _cheapest_fare(fares: list[dict[str, Any]]) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for fare in fares:
        price_info = fare.get("discountedPrice") or fare.get("basePrice")
        if not price_info:
            continue
        amount = price_info.get("amount")
        if amount is None:
            continue
        currency = price_info.get("currencyCode", "")
        bundle = str(fare.get("bundle", "basic")).lower()
        candidate = {
            "price": float(amount),
            "currency": currency,
            "bundle": bundle,
        }
        if best is None or candidate["price"] < best["price"]:
            best = candidate
    return best


def _format_time(value: str) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value).strftime("%H:%M")
    except ValueError:
        return value


def _format_flight_number(flight: dict[str, Any]) -> str:
    carrier = flight.get("carrierCode", "W6")
    number = flight.get("flightNumber", "")
    if number:
        return f"{carrier}{number}"
    return str(number)
