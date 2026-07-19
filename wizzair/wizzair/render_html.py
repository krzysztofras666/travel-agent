from __future__ import annotations

from datetime import date
from html import escape
from itertools import groupby

from wizzair.models import MultipassFlight, ScanResult


def build_subject(result: ScanResult) -> str:
    today = date.today().isoformat()
    routes = {f"{flight.origin}-{flight.destination}" for flight in result.flights}
    return (
        f"Wizz Multipass — {today} "
        f"({len(routes)} tras, {len(result.flights)} lotów)"
    )


def render_html(result: ScanResult) -> str:
    subject = build_subject(result)
    today = date.today().strftime("%d.%m.%Y")
    sections = _render_sections(result.flights)
    if not sections:
        sections = (
            '<p style="margin:0;color:#5b6472;font-size:15px;line-height:1.6;">'
            "Dziś nie znaleźliśmy dostępnych lotów All You Can Fly z KRK i KTW "
            "w najbliższych dniach. Spróbuj ponownie jutro o 08:00."
            "</p>"
        )

    origins = sorted({flight.origin for flight in result.flights})
    origin_label = ", ".join(origins) if origins else "KRK, KTW"

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#f6f1f4;font-family:Arial,Helvetica,sans-serif;color:#1f2933;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f1f4;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:700px;background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 10px 30px rgba(198,0,126,0.12);">
          <tr>
            <td style="background:linear-gradient(135deg,#c6007e 0%,#7b005f 100%);padding:28px 28px 24px;color:#ffffff;">
              <div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;opacity:0.9;margin-bottom:8px;">
                Wizz Multipass · All You Can Fly
              </div>
              <h1 style="margin:0 0 8px;font-size:28px;line-height:1.2;font-weight:700;">
                Dostępne loty na dziś
              </h1>
              <p style="margin:0;font-size:15px;line-height:1.5;opacity:0.95;">
                Loty z {escape(origin_label)} · dziś i 3 najbliższe dni · {escape(today)}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 28px 8px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  {_stat_cell(str(len(result.flights)), "lotów")}
                  {_stat_cell(str(len({f"{f.origin}-{f.destination}" for f in result.flights})), "tras")}
                  {_stat_cell("08:00", "codziennie")}
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px 28px;">
              {sections}
            </td>
          </tr>
          <tr>
            <td style="padding:0 28px 28px;">
              <p style="margin:0;font-size:12px;line-height:1.6;color:#7b8794;">
                Loty pochodzą z konta Wizz Multipass. Dostępność w karnecie All You Can Fly
                może różnić się od zwykłej rezerwacji na wizzair.com.
                Kliknij „Rezerwuj w Multipass”, aby dokończyć rezerwację.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def render_plain_text(result: ScanResult) -> str:
    lines = [build_subject(result), ""]
    for flight in result.flights:
        lines.append(
            f"- {flight.departure_date} | {flight.origin} → {flight.destination} | "
            f"{flight.flight_code} | {flight.departure_time} → {flight.arrival_time} | "
            f"Multipass: {flight.multipass_url} | Wizz: {flight.wizzair_url}"
        )
    if not result.flights:
        lines.append("Brak dostępnych lotów w tym przebiegu.")
    return "\n".join(lines)


def _stat_cell(value: str, label: str) -> str:
    return (
        "<td width='33%' style='padding:8px;'>"
        "<div style='background:#fff7fb;border:1px solid #f2d2e4;border-radius:12px;padding:14px;text-align:center;'>"
        f"<div style='font-size:24px;font-weight:700;color:#c6007e;'>{escape(value)}</div>"
        f"<div style='font-size:12px;color:#5b6472;margin-top:4px;'>{escape(label)}</div>"
        "</div></td>"
    )


def _render_sections(flights: list[MultipassFlight]) -> str:
    sorted_flights = sorted(
        flights,
        key=lambda flight: (flight.departure_date, flight.origin, flight.destination),
    )
    sections: list[str] = []
    for departure_date, group in groupby(sorted_flights, key=lambda flight: flight.departure_date):
        group_flights = list(group)
        cards = "\n".join(_render_flight_card(flight) for flight in group_flights)
        sections.append(
            "<div style='margin-bottom:24px;'>"
            f"<h2 style='margin:0 0 12px;font-size:18px;color:#7b005f;'>{escape(departure_date)}</h2>"
            f"{cards}"
            "</div>"
        )
    return "\n".join(sections)


def _render_flight_card(flight: MultipassFlight) -> str:
    route = (
        f"{escape(flight.origin_name)} ({escape(flight.origin)}) → "
        f"{escape(flight.destination_name)} ({escape(flight.destination)})"
    )
    times = f"{escape(flight.departure_time)} → {escape(flight.arrival_time)}"
    duration = escape(flight.duration) if flight.duration else "—"
    price = _format_price(flight)

    return (
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' "
        "style='margin-bottom:12px;border:1px solid #f2d2e4;border-radius:14px;background:#fffbfd;'>"
        "<tr><td style='padding:16px 18px;'>"
        f"<div style='font-size:16px;font-weight:700;margin-bottom:6px;color:#12344d;'>{route}</div>"
        f"<div style='font-size:14px;color:#334155;margin-bottom:8px;'>"
        f"<strong>{escape(flight.flight_code)}</strong> · {times} · {duration}"
        "</div>"
        f"<div style='font-size:13px;color:#5b6472;margin-bottom:14px;'>{price}</div>"
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0'><tr>"
        "<td>"
        f"<a href='{escape(flight.multipass_url)}' style='display:inline-block;background:#c6007e;color:#ffffff;"
        "text-decoration:none;font-size:13px;font-weight:700;padding:10px 16px;border-radius:999px;margin-right:8px;'>"
        "Rezerwuj w Multipass →</a>"
        f"<a href='{escape(flight.wizzair_url)}' style='display:inline-block;background:#ffffff;color:#c6007e;"
        "text-decoration:none;font-size:13px;font-weight:700;padding:10px 16px;border-radius:999px;"
        "border:1px solid #e8b3d1;'>Zobacz na wizzair.com</a>"
        "</td></tr></table>"
        "</td></tr></table>"
    )


def _format_price(flight: MultipassFlight) -> str:
    if flight.price > 0 and flight.currency:
        amount = f"{flight.price:,.2f}".replace(",", " ")
        return f"Cena: {amount} {escape(flight.currency)}"
    return "All You Can Fly"
