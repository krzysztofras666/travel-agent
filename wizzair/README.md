# Wizz Air Multipass

CLI, który loguje się do [Wizz Multipass](https://multipass.wizzair.com) i wyszukuje dostępne loty **All You Can Fly** z wybranych lotnisk.

## Szybki start

```bash
cd wizzair
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
cp .env.example .env          # uzupełnij WIZZAIR_EMAIL i WIZZAIR_PASSWORD
python -m wizzair run
```

## Jak działa

1. Otwiera `https://multipass.wizzair.com/pl/w6/subscriptions/spa/private-page/wallets`
2. Loguje się kontem z `.env`
3. Dla lotnisk **KRK** i **KTW** pobiera listę destynacji z formularza wyszukiwania
4. Sprawdza loty od **dziś** przez **3 najbliższe dni** (łącznie 4 dni)
5. Dla każdej kombinacji origin / destynacja / data woła wewnętrzne API dostępności
6. Gdy API zwraca `error.availability` — traktuje to jako brak lotu i przechodzi dalej
7. Wyświetla wszystkie znalezione loty

## Komendy

```bash
python -m wizzair run
python -m wizzair run --json
python -m wizzair run --diagnostics
python -m wizzair run --headed
```

## Konfiguracja (`.env`)

| Zmienna | Domyślnie | Opis |
| --- | --- | --- |
| `WIZZAIR_EMAIL` | — | E-mail do logowania (wymagany) |
| `WIZZAIR_PASSWORD` | — | Hasło (wymagane) |
| `WIZZAIR_PASS_ID` | auto | ID karnetu Multipass (wykrywane po logowaniu) |
| `WIZZAIR_ORIGINS` | `KRK,KTW` | Lotniska wylotu (kody IATA, po przecinku) |
| `WIZZAIR_DAYS` | `4` | Liczba dni do sprawdzenia (dziś + N-1) |
| `WIZZAIR_SEARCH_CONCURRENCY` | `4` | Równoległe zapytania API |
| `WIZZAIR_HEADLESS` | `true` | Headless Chromium |

**Nie commituj pliku `.env` z hasłem.**

## Struktura

```
wizzair/
├── wizzair/
│   ├── multipass.py   # logowanie i odkrywanie destynacji
│   ├── scanner.py     # skanowanie dostępności
│   ├── api.py         # parsowanie odpowiedzi API
│   └── __main__.py    # CLI
├── requirements.txt
└── .env.example
```
