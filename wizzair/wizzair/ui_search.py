from __future__ import annotations

import re
from datetime import date

from playwright.async_api import Page

from wizzair.config import WALLETS_URL
from wizzair.models import Destination, MultipassFlight
from wizzair.multipass import ORIGIN_QUERIES, dismiss_modals
from wizzair.urls import multipass_wallets_url, wizzair_booking_url

NO_RESULTS_SNIPPET = "niestety, nie znaleziono żadnych wyników"
FLIGHT_CODE_RE = re.compile(r"\bW6\d+\b")


async def search_route_ui(
    page: Page,
    *,
    origin: str,
    destination: Destination,
    departure_date: str,
) -> list[MultipassFlight]:
    origin_code = origin.upper()
    dest_code = destination.code.upper()
    origin_query, origin_pick = ORIGIN_QUERIES.get(origin_code, (origin_code[:3], origin_code))
    dest_query = _destination_query(destination.label)
    dest_pick = _pick_label(destination.label)

    await page.goto(WALLETS_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(1000)
    await dismiss_modals(page)

    await _select_autocomplete(page, field="origin", query=origin_query, pick=origin_pick)
    await _select_autocomplete(page, field="destination", query=dest_query, pick=dest_pick)

    if not await _select_departure_date(page, departure_date):
        return []

    search_button = page.locator("button.SearchCombo-submit")
    if not await search_button.is_enabled():
        return []

    await search_button.click()
    try:
        await page.wait_for_url("**/availability/**", timeout=15000)
    except Exception:
        await page.wait_for_timeout(3000)

    await page.wait_for_function(
        """() => {
            const text = document.body.innerText;
            if (text.toLowerCase().includes('niestety, nie znaleziono żadnych wyników')) {
                return true;
            }
            return /W6\\d+/.test(text) && /WYBIERZ/i.test(text);
        }""",
        timeout=20000,
    )
    await page.wait_for_timeout(500)

    body_text = await page.evaluate("() => document.body.innerText")
    if NO_RESULTS_SNIPPET in body_text.lower():
        return []

    raw_cards: list[str] = await page.evaluate(
        """() => {
            const cards = [...document.querySelectorAll('[class*="SearchResult"]')];
            const fromCards = cards
                .map((card) => (card.innerText || '').trim())
                .filter((text) => /WYBIERZ/i.test(text) && /W6\\d+/.test(text))
                .filter((text) => text.length > 80 && text.length < 1200);
            if (fromCards.length > 0) return fromCards;

            const body = document.body.innerText || '';
            if (!/WYBIERZ/i.test(body) || !/W6\\d+/.test(body)) return [];

            const chunks = body.split(/(?=\\bW6\\d+\\b)/).filter((chunk) => /WYBIERZ/i.test(chunk));
            return chunks.map((chunk) => chunk.trim()).filter((chunk) => /\\d{1,2}:\\d{2}/.test(chunk));
        }"""
    )

    flights: list[MultipassFlight] = []
    seen: set[str] = set()
    multipass_url = page.url if "availability" in page.url else multipass_wallets_url()
    wizzair_url = wizzair_booking_url(
        origin=origin_code,
        destination=dest_code,
        departure_date=departure_date,
    )
    for card_text in raw_cards:
        parsed = _parse_card_text(
            card_text,
            origin=origin_code,
            destination=dest_code,
            departure_date=departure_date,
            destination_label=destination.label,
            multipass_url=multipass_url,
            wizzair_url=wizzair_url,
        )
        if parsed is None:
            continue
        key = f"{parsed.flight_code}|{parsed.departure_date}|{parsed.departure_time}"
        if key in seen:
            continue
        seen.add(key)
        flights.append(parsed)

    return flights


async def _select_autocomplete(page: Page, *, field: str, query: str, pick: str) -> None:
    field_input = page.locator(f'input[id^="autocomplete-{field}"]').first
    await field_input.click()
    await field_input.fill("")
    await field_input.type(query, delay=30)
    await page.wait_for_timeout(900)
    await page.locator("ul.autocomplete-result-list:visible li").filter(has_text=pick).first.click()
    await page.wait_for_timeout(400)


async def _select_departure_date(page: Page, departure_date: str) -> bool:
    target = date.fromisoformat(departure_date)
    departure_input = page.locator("#Odloty").first
    await departure_input.click()
    await page.wait_for_timeout(600)

    for _ in range(8):
        cell = page.locator(f'td.cell[title="{departure_date}"]:not(.disabled)')
        if await cell.count() > 0:
            await cell.first.click()
            await page.wait_for_timeout(400)
            return True
        await page.locator(".Datepicker-btn-icon-right").first.click()
        await page.wait_for_timeout(300)

    return False


def _destination_query(label: str) -> str:
    name = _pick_label(label)
    return name[:4] if len(name) >= 4 else name


def _pick_label(label: str) -> str:
    return label.split("(")[0].strip()


def _parse_card_text(
    text: str,
    *,
    origin: str,
    destination: str,
    departure_date: str,
    destination_label: str,
    multipass_url: str,
    wizzair_url: str,
) -> MultipassFlight | None:
    code_match = FLIGHT_CODE_RE.search(text)
    if not code_match:
        return None

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    times = [line for line in lines if re.fullmatch(r"\d{1,2}:\d{2}", line)]
    if len(times) < 2:
        return None

    duration = next((line for line in lines if re.fullmatch(r"\d+h \d+m", line)), "")
    origin_name = next(
        (
            line
            for line in lines
            if line not in times
            and "UTC" not in line
            and "W6" not in line
            and "zł" not in line.lower()
            and "WYBIERZ" not in line.upper()
        ),
        origin,
    )
    destination_name = destination_label.split("(")[0].strip()
    price_match = re.search(r"zł\s*([\d.,]+)", text, re.IGNORECASE)
    price = float(price_match.group(1).replace(",", ".")) if price_match else 0.0
    currency = "PLN" if price_match else ""

    return MultipassFlight(
        origin=origin,
        origin_name=origin_name,
        destination=destination,
        destination_name=destination_name,
        departure_date=departure_date,
        departure_time=times[0],
        arrival_time=times[1],
        flight_code=code_match.group(0),
        duration=duration,
        price=price,
        currency=currency,
        stops="",
        multipass_url=multipass_url,
        wizzair_url=wizzair_url,
    )
