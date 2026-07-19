from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Route:
    origin: str
    destination: str
    origin_name: str
    destination_name: str

    @property
    def id(self) -> str:
        return f"{self.origin}-{self.destination}"


@dataclass
class FlightOffer:
    origin: str
    destination: str
    departure_date: str
    return_date: str
    departure_time: str
    arrival_time: str
    flight_number: str
    price: float
    currency: str
    bundle: str
    url: str = ""


@dataclass
class SearchDiagnostic:
    route_id: str
    origin: str
    destination: str
    departure_date: str
    return_date: str
    offers_found: int
    error: str = ""


@dataclass
class SearchResult:
    offers: list[FlightOffer] = field(default_factory=list)
    diagnostics: list[SearchDiagnostic] = field(default_factory=list)
