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

## Komendy

```bash
python -m wizzair run
python -m wizzair send
python -m wizzair send --dry-run
python -m wizzair preview-email --out logs/last_email.html
```

## Codzienny e-mail o 08:00 (macOS launchd)

Domyślni odbiorcy:
- `katarzyna.dyngosz@gmail.com`
- `andalath@gmail.com`

### Jednorazowa konfiguracja Gmail

```bash
cd ~/gmail-agent
source .venv/bin/activate
python -m gmail_agent auth --account andalath@gmail.com
```

### Wyślij raz ręcznie

```bash
cd ~/travel-agent/wizzair
source .venv/bin/activate
python -m wizzair send --dry-run
python -m wizzair send
python -m wizzair preview-email --out logs/last_email.html
```

### Zaplanuj codziennie o 08:00

```bash
cd ~/travel-agent/wizzair
chmod +x scripts/*.sh
./scripts/install_wizzair_schedule.sh
./scripts/run_wizzair_daily.sh --dry-run
launchctl kickstart gui/$(id -u)/com.wizzair.daily
```

Logi: `logs/wizzair_run.log`, `logs/last_email.html`

## Jak działa

1. Otwiera stronę wallets Multipass i loguje się kontem z `.env`
2. Dla lotnisk **KRK** i **KTW** pobiera listę destynacji
3. Sprawdza loty od **dziś** przez **3 najbliższe dni**
4. Lot jest uznawany za dostępny tylko gdy w UI widać kartę z numerem lotu i przyciskiem **WYBIERZ**
5. Wysyła ładny HTML e-mail z linkami **Rezerwuj w Multipass** i **Zobacz na wizzair.com** przy każdej pozycji

## Konfiguracja (`.env`)

| Zmienna | Domyślnie | Opis |
| --- | --- | --- |
| `WIZZAIR_EMAIL` | — | Login Multipass (wymagany) |
| `WIZZAIR_PASSWORD` | — | Hasło Multipass (wymagane) |
| `WIZZAIR_EMAIL_FROM` | `andalath@gmail.com` | Nadawca digestu |
| `WIZZAIR_EMAIL_TO` | katarzyna + andalath | Odbiorcy (po przecinku) |
| `GMAIL_TOKEN_DIR` | `~/.config/gmail-agent` | Token OAuth z gmail-agent |
| `WIZZAIR_ORIGINS` | `KRK,KTW` | Lotniska wylotu |
| `WIZZAIR_DAYS` | `4` | Dziś + 3 kolejne dni |
| `WIZZAIR_HEADLESS` | `true` | Headless Chromium |

**Nie commituj pliku `.env` z hasłem.**

## Struktura

```
wizzair/
├── wizzair/
│   ├── ui_search.py     # skanowanie przez UI Multipass
│   ├── render_html.py   # HTML e-mail
│   ├── email.py         # wysyłka Gmail
│   └── __main__.py
├── scripts/             # launchd (macOS)
└── .env.example
```
