from __future__ import annotations

import asyncio
import json
from datetime import date, timedelta

from playwright.async_api import async_playwright

from wizzair.api import availability_api_url, build_availability_payload, parse_availability_response
from wizzair.config import Settings
from wizzair.models import Destination, MultipassFlight, ScanDiagnostic, ScanResult
from wizzair.multipass import discover_destinations, extract_pass_id, login


async def scan_multipass(settings: Settings) -> ScanResult:
    dates = _search_dates(settings.days_ahead)
    flights: list[MultipassFlight] = []
    diagnostics: list[ScanDiagnostic] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=settings.headless)
        context = await browser.new_context(
            locale=f"{settings.locale}-PL",
            user_agent=settings.user_agent,
        )
        page = await login(context, settings)
        pass_id = await extract_pass_id(page, settings)
        api_url = availability_api_url(pass_id)

        destinations_by_origin: dict[str, list[Destination]] = {}
        for origin in settings.origins:
            destinations_by_origin[origin] = await discover_destinations(page, origin)

        semaphore = asyncio.Semaphore(settings.search_concurrency)

        async def query_route(
            origin: str,
            destination: Destination,
            departure_date: str,
        ) -> tuple[list[MultipassFlight], ScanDiagnostic]:
            async with semaphore:
                payload = build_availability_payload(
                    origin=origin,
                    destination=destination.code,
                    departure_date=departure_date,
                )
                try:
                    response = await page.request.post(api_url, data=payload)
                    body = await response.text()
                    if response.status != 200:
                        if _is_no_availability(body):
                            return [], ScanDiagnostic(
                                origin=origin,
                                destination=destination.code,
                                departure_date=departure_date,
                                flights_found=0,
                            )
                        return [], ScanDiagnostic(
                            origin=origin,
                            destination=destination.code,
                            departure_date=departure_date,
                            flights_found=0,
                            error=f"HTTP {response.status}: {body[:200]}",
                        )

                    data = json.loads(body)
                    found = parse_availability_response(
                        data,
                        origin=origin,
                        destination=destination.code,
                        departure_date=departure_date,
                    )
                    return found, ScanDiagnostic(
                        origin=origin,
                        destination=destination.code,
                        departure_date=departure_date,
                        flights_found=len(found),
                    )
                except Exception as exc:  # noqa: BLE001
                    return [], ScanDiagnostic(
                        origin=origin,
                        destination=destination.code,
                        departure_date=departure_date,
                        flights_found=0,
                        error=str(exc),
                    )

        tasks = []
        for origin, destinations in destinations_by_origin.items():
            for destination in destinations:
                for departure_date in dates:
                    tasks.append(query_route(origin, destination, departure_date))

        pairs = await asyncio.gather(*tasks)
        for found, diag in pairs:
            diagnostics.append(diag)
            flights.extend(found)

        await browser.close()

    flights.sort(
        key=lambda flight: (
            flight.departure_date,
            flight.origin,
            flight.destination,
            flight.departure_time,
        )
    )
    return ScanResult(flights=flights, diagnostics=diagnostics)


def _search_dates(days_ahead: int) -> list[str]:
    start = date.today()
    return [(start + timedelta(days=offset)).isoformat() for offset in range(days_ahead)]


def _is_no_availability(body: str) -> bool:
    lowered = body.lower()
    return "error.availability" in lowered
