# Wizz Air

Standalone CLI that searches Wizz Air flights and surfaces the cheapest fares across configured routes.

This is a **separate project** from [travel-agent](https://github.com/krzysztofras666/travel-agent). It lives in the `wizzair/` subdirectory of that repo and can be split into its own repository later.

## Quick start

```bash
cd wizzair
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
.venv/bin/python -m wizzair list-routes
.venv/bin/python -m wizzair search --from WAW --to BCN --depart 2026-08-01
```

## Commands

```bash
python -m wizzair list-routes
python -m wizzair list-routes --origin WAW
python -m wizzair search --from WAW --to BCN --depart 2026-08-01
python -m wizzair search --from KRK --to LTN --depart 2026-08-01 --return 2026-08-08 --json
python -m wizzair scan --origin WAW --depart 2026-08-01
python -m wizzair scan --route WAW-BCN --route WAW-FCO --depart 2026-08-01
python -m wizzair booking-url --from WAW --to BCN --depart 2026-08-01
```

## How it works

Wizz Air protects its booking API with bot detection. This tool uses Playwright (headless Chromium) to open the official booking page and capture the internal `Api/search/search` response, then parses outbound and return flight fares.

## Configuration

Environment variables (`.env` supported):

| Variable | Default | Purpose |
| --- | --- | --- |
| `WIZZAIR_API_VERSION` | auto | Pin API version if auto-discovery fails |
| `WIZZAIR_HTTP_TIMEOUT` | `30` | Page load timeout (seconds) |
| `WIZZAIR_SEARCH_CONCURRENCY` | `3` | Max parallel route scans |
| `WIZZAIR_DEFAULT_ORIGIN` | `WAW` | Default origin airport |
| `WIZZAIR_LOCALE` | `en-gb` | Booking page locale |
| `WIZZAIR_WDC` | `true` | Include Wizz Discount Club fares |

## Project layout

```
wizzair/
├── wizzair/           # Python package
│   ├── api.py         # URL builders and response parsing
│   ├── search.py      # Playwright-based flight search
│   ├── routes.py      # Configured origin/destination pairs
│   └── __main__.py    # CLI entry point
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Notes

- Flight search depends on Wizz Air's website and may fail when captchas or rate limits appear.
- Configured routes focus on popular Wizz Air departures from Polish airports (WAW, KRK, GDN, WRO, KTW, POZ).
- Add more routes in `wizzair/routes.py` as needed.
