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
python -m wizzair login --headed
python -m wizzair send --dry-run
```

## Komendy

```bash
python -m wizzair run
python -m wizzair send                 # poranny pełny mail + snapshot
python -m wizzair send-delta           # popołudniowy mail tylko ze zmianami
python -m wizzair send --dry-run
python -m wizzair send-delta --dry-run
python -m wizzair preview-email --out logs/last_email.html
python -m wizzair preview-delta --out logs/last_delta_email.html
```

## Harmonogram e-maili (macOS launchd)

| Godzina | Co robi |
| --- | --- |
| **08:00** | Pełny HTML z wszystkimi lotami i linkami |
| **13:00** | Tylko zmiany względem porannego maila (+ nowe, − zniknięte) |

Domyślni odbiorcy:
- `katarzyna.dyngosz@gmail.com`
- `andalath@gmail.com`

### Jednorazowa konfiguracja Gmail

```bash
cd ~/gmail-agent
source .venv/bin/activate
pip install -r requirements.txt
python -m gmail_agent auth --account andalath@gmail.com
```

### Wyślij ręcznie

```bash
cd ~/travel-agent/wizzair
source .venv/bin/activate
python -m wizzair send --dry-run          # poranny podgląd
python -m wizzair send                    # poranny mail
python -m wizzair send-delta --dry-run    # popołudniowy podgląd zmian
python -m wizzair send-delta              # popołudniowy mail (tylko jeśli są zmiany)
```

### Zaplanuj codziennie 08:00 i 13:00

```bash
cd ~/travel-agent/wizzair
chmod +x scripts/*.sh
./scripts/install_wizzair_schedule.sh
./scripts/run_wizzair_morning.sh --dry-run
./scripts/run_wizzair_afternoon.sh --dry-run
```

Logi:
- `logs/wizzair_morning.log`
- `logs/wizzair_afternoon.log`
- `logs/last_email.html`
- `logs/last_delta_email.html`
- `logs/snapshots/YYYY-MM-DD-morning.json`

## Jak działa

1. Loguje się na Multipass i skanuje loty z **KRK** i **KTW** (dziś + 3 dni)
2. O **08:00** wysyła pełny HTML z linkami przy każdej ofercie:
   - **Rezerwuj w Multipass**
   - **Zobacz na wizzair.com**
3. Zapisuje snapshot poranny do `logs/snapshots/`
4. O **13:00** skanuje ponownie i wysyła mail **tylko ze zmianami**:
   - nowe loty od rana
   - loty, które zniknęły
5. Jeśli o 13:00 nie ma zmian — mail nie jest wysyłany

## Konfiguracja (`.env`)

| Zmienna | Domyślnie | Opis |
| --- | --- | --- |
| `WIZZAIR_EMAIL` | — | Login Multipass |
| `WIZZAIR_PASSWORD` | — | Hasło Multipass |
| `WIZZAIR_EMAIL_FROM` | `andalath@gmail.com` | Nadawca |
| `WIZZAIR_EMAIL_TO` | katarzyna + andalath | Odbiorcy |
| `GMAIL_TOKEN_DIR` | `~/.config/gmail-agent` | Token OAuth |
