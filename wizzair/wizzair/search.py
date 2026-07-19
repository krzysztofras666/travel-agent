from __future__ import annotations

import asyncio
import json
from typing import Any

from playwright.async_api import async_playwright

from wizzair.api import booking_url, extract_api_version, parse_search_response
from wizzair.config import Settings
from wizzair.models import FlightOffer, Route, SearchDiagnostic, SearchResult
from wizzair.routes import get_routes


async def search_route(
    settings: Settings,
    route: Route,
    *,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
) -> tuple[list[FlightOffer], SearchDiagnostic]:
    page_url = booking_url(
        settings,
        origin=route.origin,
        destination=route.destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=adults,
        children=children,
        infants=infants,
    )

    try:
        offers = await _search_via_browser(
            settings,
            page_url=page_url,
            origin=route.origin,
            destination=route.destination,
            departure_date=departure_date,
            return_date=return_date,
        )
        return offers, SearchDiagnostic(
            route_id=route.id,
            origin=route.origin,
            destination=route.destination,
            departure_date=departure_date,
            return_date=return_date or "",
            offers_found=len(offers),
        )
    except Exception as exc:  # noqa: BLE001
        return [], SearchDiagnostic(
            route_id=route.id,
            origin=route.origin,
            destination=route.destination,
            departure_date=departure_date,
            return_date=return_date or "",
            offers_found=0,
            error=str(exc),
        )


async def scan_routes(
    settings: Settings,
    *,
    departure_date: str,
    return_date: str | None = None,
    origin: str | None = None,
    route_ids: list[str] | None = None,
    max_per_route: int = 1,
) -> SearchResult:
    routes = get_routes(origin=origin, route_ids=route_ids)
    semaphore = asyncio.Semaphore(settings.search_concurrency)

    async def run_route(route: Route) -> tuple[list[FlightOffer], SearchDiagnostic]:
        async with semaphore:
            return await search_route(
                settings,
                route,
                departure_date=departure_date,
                return_date=return_date,
            )

    pairs = await asyncio.gather(*(run_route(route) for route in routes))

    all_offers: list[FlightOffer] = []
    diagnostics: list[SearchDiagnostic] = []
    for offers, diag in pairs:
        diagnostics.append(diag)
        if max_per_route > 0:
            all_offers.extend(sorted(offers, key=lambda offer: offer.price)[:max_per_route])
        else:
            all_offers.extend(offers)

    all_offers.sort(key=lambda offer: (offer.price, offer.departure_date, offer.origin))
    return SearchResult(offers=all_offers, diagnostics=diagnostics)


async def _search_via_browser(
    settings: Settings,
    *,
    page_url: str,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None,
) -> list[FlightOffer]:
    captured: list[dict[str, Any]] = []
    api_version = settings.api_version

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=settings.user_agent)
        page = await context.new_page()

        async def handle_response(response) -> None:
            nonlocal api_version
            url = response.url
            if "be.wizzair.com" in url and "/Api/search/search" in url:
                if not api_version:
                    discovered = extract_api_version(url)
                    if discovered:
                        api_version = discovered
                if response.status != 200:
                    return
                try:
                    captured.append(await response.json())
                except Exception:
                    return

        page.on("response", handle_response)
        await page.goto(page_url, wait_until="domcontentloaded", timeout=int(settings.http_timeout * 1000))

        for _ in range(30):
            if captured:
                break
            await page.wait_for_timeout(1000)

        if not captured:
            html = await page.content()
            if "captcha" in html.lower():
                raise RuntimeError("Wizz Air returned a captcha challenge. Try again later.")
            raise RuntimeError("No flight search response captured from Wizz Air.")

        await browser.close()

    offers: list[FlightOffer] = []
    for payload in captured:
        offers.extend(
            parse_search_response(
                payload,
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                booking_page_url=page_url,
            )
        )
    return offers


def dump_search_payload(
    settings: Settings,
    *,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
) -> str:
    from wizzair.api import build_search_payload

    payload = build_search_payload(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=1,
        children=0,
        infants=0,
        wdc=settings.wdc,
    )
    return json.dumps(payload, indent=2)
