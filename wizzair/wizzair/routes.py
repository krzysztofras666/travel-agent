from __future__ import annotations

from wizzair.models import Route

# Popular Wizz Air routes from Polish airports.
ROUTES: tuple[Route, ...] = (
    Route("WAW", "LTN", "Warsaw", "London Luton"),
    Route("WAW", "BCN", "Warsaw", "Barcelona"),
    Route("WAW", "FCO", "Warsaw", "Rome Fiumicino"),
    Route("WAW", "MXP", "Warsaw", "Milan Malpensa"),
    Route("WAW", "BGY", "Warsaw", "Milan Bergamo"),
    Route("WAW", "VIE", "Warsaw", "Vienna"),
    Route("WAW", "BUD", "Warsaw", "Budapest"),
    Route("WAW", "OTP", "Warsaw", "Bucharest"),
    Route("WAW", "SKG", "Warsaw", "Thessaloniki"),
    Route("WAW", "LCA", "Warsaw", "Larnaca"),
    Route("KRK", "LTN", "Krakow", "London Luton"),
    Route("KRK", "BCN", "Krakow", "Barcelona"),
    Route("KRK", "BGY", "Krakow", "Milan Bergamo"),
    Route("KRK", "STN", "Krakow", "London Stansted"),
    Route("KRK", "EIN", "Krakow", "Eindhoven"),
    Route("GDN", "LTN", "Gdansk", "London Luton"),
    Route("GDN", "BGY", "Gdansk", "Milan Bergamo"),
    Route("GDN", "CPH", "Gdansk", "Copenhagen"),
    Route("GDN", "OSL", "Gdansk", "Oslo"),
    Route("WRO", "LTN", "Wroclaw", "London Luton"),
    Route("WRO", "BGY", "Wroclaw", "Milan Bergamo"),
    Route("WRO", "EIN", "Wroclaw", "Eindhoven"),
    Route("KTW", "LTN", "Katowice", "London Luton"),
    Route("KTW", "BGY", "Katowice", "Milan Bergamo"),
    Route("KTW", "STN", "Katowice", "London Stansted"),
    Route("POZ", "LTN", "Poznan", "London Luton"),
    Route("POZ", "STN", "Poznan", "London Stansted"),
    Route("POZ", "BGY", "Poznan", "Milan Bergamo"),
)

ROUTES_BY_ID = {route.id: route for route in ROUTES}


def get_routes(
    *,
    origin: str | None = None,
    route_ids: list[str] | None = None,
) -> list[Route]:
    if route_ids:
        unknown = [route_id for route_id in route_ids if route_id not in ROUTES_BY_ID]
        if unknown:
            raise ValueError(f"Unknown route id(s): {', '.join(unknown)}")
        return [ROUTES_BY_ID[route_id] for route_id in route_ids]

    if origin:
        origin = origin.upper()
        return [route for route in ROUTES if route.origin == origin]
    return list(ROUTES)
