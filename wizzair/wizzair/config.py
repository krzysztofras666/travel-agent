from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class Settings:
    api_version: str | None
    http_timeout: float
    search_concurrency: int
    default_origin: str
    locale: str
    user_agent: str
    wdc: bool


def get_settings() -> Settings:
    return Settings(
        api_version=os.getenv("WIZZAIR_API_VERSION") or None,
        http_timeout=float(os.getenv("WIZZAIR_HTTP_TIMEOUT", "30")),
        search_concurrency=int(os.getenv("WIZZAIR_SEARCH_CONCURRENCY", "3")),
        default_origin=os.getenv("WIZZAIR_DEFAULT_ORIGIN", "WAW"),
        locale=os.getenv("WIZZAIR_LOCALE", "en-gb"),
        user_agent=os.getenv("WIZZAIR_USER_AGENT", DEFAULT_USER_AGENT),
        wdc=os.getenv("WIZZAIR_WDC", "true").lower() in {"1", "true", "yes"},
    )
