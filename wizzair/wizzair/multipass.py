from __future__ import annotations

import string

from playwright.async_api import BrowserContext, Page

from wizzair.config import WALLETS_URL, Settings
from wizzair.models import Destination

ORIGIN_QUERIES = {
    "KRK": ("Krak", "Kraków"),
    "KTW": ("Katow", "Katowice"),
    "WAW": ("Warsz", "Warszawa"),
    "GDN": ("Gda", "Gdańsk"),
    "WRO": ("Wroc", "Wrocław"),
    "POZ": ("Pozn", "Poznań"),
}


async def login(context: BrowserContext, settings: Settings) -> Page:
    page = await context.new_page()
    await page.goto(WALLETS_URL, wait_until="domcontentloaded", timeout=int(settings.http_timeout * 1000))

    if "openid-connect/auth" in page.url:
        await page.fill("#username", settings.email)
        await page.fill("#password", settings.password)
        await page.click("#kc-login")
        await page.wait_for_url("**/wallets**", timeout=int(settings.http_timeout * 1000))

    await page.wait_for_timeout(1500)
    await dismiss_modals(page)
    return page


async def dismiss_modals(page: Page) -> None:
    for selector in (".CvoModal button", ".CvoModal .cvo-button"):
        button = page.locator(selector).first
        if await button.count() > 0:
            try:
                await button.click(timeout=1500)
            except Exception:
                pass
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)


async def extract_pass_id(page: Page, settings: Settings) -> str:
    if settings.pass_id:
        return settings.pass_id

    pass_id = await page.evaluate(
        """() => {
            if (window.DD_RUM && typeof window.DD_RUM.getUser === 'function') {
                const user = window.DD_RUM.getUser();
                if (user && user.pass_id) return user.pass_id;
            }
            return null;
        }"""
    )
    if pass_id:
        return pass_id

    html = await page.content()
    from wizzair.api import extract_pass_id as parse_pass_id

    parsed = parse_pass_id(html)
    if parsed:
        return parsed
    raise RuntimeError("Could not determine Wizz Multipass pass_id from the wallets page.")


async def discover_destinations(page: Page, origin: str) -> list[Destination]:
    query, pick = ORIGIN_QUERIES.get(origin.upper(), (origin[:3], origin))
    await page.goto(WALLETS_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(1200)
    await dismiss_modals(page)

    origin_input = page.locator('input[id^="autocomplete-origin"]').first
    await origin_input.click()
    await origin_input.fill("")
    await origin_input.type(query, delay=30)
    await page.wait_for_timeout(1000)
    await page.locator("ul.autocomplete-result-list:visible li").filter(has_text=pick).first.click()
    await page.wait_for_timeout(500)

    destinations: set[str] = set()
    for letter in string.ascii_lowercase:
        dest_input = page.locator('input[id^="autocomplete-destination"]').first
        await dest_input.click()
        await dest_input.fill("")
        await dest_input.type(letter, delay=20)
        await page.wait_for_timeout(500)
        for label in await page.locator("ul.autocomplete-result-list:visible li").all_inner_texts():
            label = label.strip()
            if not label:
                continue
            destinations.add(label)

    parsed: list[Destination] = []
    for label in sorted(destinations):
        code = _extract_iata(label)
        if code:
            parsed.append(Destination(code=code, label=label))
    return parsed


def _extract_iata(label: str) -> str | None:
    if "(" not in label or ")" not in label:
        return None
    return label.rsplit("(", 1)[-1].rstrip(")").strip().upper()
