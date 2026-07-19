from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

WALLETS_URL = "https://multipass.wizzair.com/pl/w6/subscriptions/spa/private-page/wallets"


@dataclass(frozen=True)
class Settings:
    email: str
    password: str
    pass_id: str | None
    origins: tuple[str, ...]
    days_ahead: int
    http_timeout: float
    search_concurrency: int
    locale: str
    user_agent: str
    headless: bool


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip().upper() for part in value.split(",") if part.strip())


def get_settings() -> Settings:
    email = os.getenv("WIZZAIR_EMAIL", "")
    password = os.getenv("WIZZAIR_PASSWORD", "")
    if not email or not password:
        raise RuntimeError(
            "WIZZAIR_EMAIL and WIZZAIR_PASSWORD are required. Set them in wizzair/.env"
        )

    return Settings(
        email=email,
        password=password,
        pass_id=os.getenv("WIZZAIR_PASS_ID") or None,
        origins=_split_csv(os.getenv("WIZZAIR_ORIGINS", "KRK,KTW")),
        days_ahead=int(os.getenv("WIZZAIR_DAYS", "4")),
        http_timeout=float(os.getenv("WIZZAIR_HTTP_TIMEOUT", "60")),
        search_concurrency=int(os.getenv("WIZZAIR_SEARCH_CONCURRENCY", "4")),
        locale=os.getenv("WIZZAIR_LOCALE", "pl"),
        user_agent=os.getenv("WIZZAIR_USER_AGENT", DEFAULT_USER_AGENT),
        headless=os.getenv("WIZZAIR_HEADLESS", "true").lower() in {"1", "true", "yes"},
    )
