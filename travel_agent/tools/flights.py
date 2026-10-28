import asyncio
import logging
import random
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field

from ..config import Config

logger = logging.getLogger(__name__)

AMADEUS_TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_FLIGHTS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"
AVIASALES_BASE = "https://www.aviasales.com/search"

AIRLINE_MAP = {
    # Leading Indian Domestic & International Airlines
    "6E": "IndiGo",
    "AI": "Air India",
    "UK": "Vistara",
    "QP": "Akasa Air",
    "SG": "SpiceJet",
    "IX": "Air India Express",
    # Global & Middle Eastern Carriers connecting India
    "EK": "Emirates",
    "QR": "Qatar Airways",
    "EY": "Etihad Airways",
    "SQ": "Singapore Airlines",
    "FZ": "flydubai",
    "TG": "Thai Airways",
    "BA": "British Airways",
    "LH": "Lufthansa",
    "AF": "Air France",
    "DL": "Delta Air Lines",
    "UA": "United Airlines",
    "AA": "American Airlines",
    "AZ": "ITA Airways",
    "VS": "Virgin Atlantic",
}


class FlightSearchArgs(BaseModel):
    origin: str = Field(..., description="Three-letter airport code (e.g., DEL).")
    destination: str = Field(..., description="Three-letter airport code (e.g., GOI).")
    date: str = Field(..., description="Departure date of travel (YYYY-MM-DD).")
    return_date: Optional[str] = Field(None, description="Optional return date of travel (YYYY-MM-DD) for round-trip flights.")
    passengers: int = Field(1, ge=1, le=9, description="Number of adult passengers (default 1).")


class BookFlightArgs(BaseModel):
    origin: str = Field(..., description="Three-letter airport code (e.g., DEL).")
    destination: str = Field(..., description="Three-letter airport code (e.g., GOI).")
    date: str = Field(..., description="Departure date of travel (YYYY-MM-DD).")
    passenger_name: str = Field(..., description="Full name of the passenger.")
    return_date: Optional[str] = Field(None, description="Optional return date of travel (YYYY-MM-DD) for round-trip.")
    passengers: int = Field(1, ge=1, le=9, description="Number of adult passengers (default 1).")


class AmadeusTokenCache:
    """Async-safe cache for the Amadeus OAuth bearer token."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get(self, client_id: str, client_secret: str) -> str:
        async with self._lock:
            now = time.time()
            if self._token and now < self._expires_at:
                return self._token
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    AMADEUS_TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
            self._token = data["access_token"]
            # Refresh 60s before expiry to avoid thundering herd
            self._expires_at = time.time() + data.get("expires_in", 1800) - 60
            return self._token


_amadeus_token_cache = AmadeusTokenCache()


async def search_flights(
    origin: str,
    destination: str,
    date: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
) -> List[Dict[str, Any]]:
    """Search for flights between origin and destination on a specific date, with optional return date and passengers."""
    pax = max(1, min(9, int(passengers)))
    if Config.FLIGHT_API_KEY and Config.FLIGHT_API_SECRET:
        try:
            return await _search_real_flights(origin, destination, date, return_date=return_date, passengers=pax)
        except (httpx.HTTPError, KeyError, ValueError) as e:
            logger.warning("Amadeus API failed (%s -> %s on %s): %s. Using mock.", origin, destination, date, e)
    return await _search_mock_flights(origin, destination, date, return_date=return_date, passengers=pax)


async def _search_real_flights(
    origin: str,
    destination: str,
    date: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
) -> List[Dict[str, Any]]:
    token = await _amadeus_token_cache.get(Config.FLIGHT_API_KEY, Config.FLIGHT_API_SECRET)
    headers = {"Authorization": f"Bearer {token}"}
    params: Dict[str, Any] = {
        "originLocationCode": origin.upper(),
        "destinationLocationCode": destination.upper(),
        "departureDate": date,
        "adults": passengers,
        "max": 5,
    }
    if return_date:
        params["returnDate"] = return_date

    async with httpx.AsyncClient() as client:
        response = await client.get(AMADEUS_FLIGHTS_URL, headers=headers, params=params, timeout=15.0)
        response.raise_for_status()
        data = response.json()

    offers = data.get("data", [])
    results: List[Dict[str, Any]] = []
    for offer in offers:
        itineraries = offer.get("itineraries", [{}])
        outbound = itineraries[0] if itineraries else {}
        seg_out = outbound.get("segments", [{}])[0]
        price = offer.get("price", {})
        total_price = float(price.get("total", 0))

        carrier_code = seg_out.get("carrierCode", "Unknown")
        airline_name = AIRLINE_MAP.get(carrier_code, carrier_code)

        item: Dict[str, Any] = {
            "flight_id": offer.get("id"),
            "trip_type": "round_trip" if return_date else "one_way",
            "airline": f"{airline_name} ({carrier_code})",
            "airline_code": carrier_code,
            "flight_number": f"{carrier_code}{seg_out.get('number', '000')}",
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_time": seg_out.get("departure", {}).get("at"),
            "arrival_time": seg_out.get("arrival", {}).get("at"),
            "price": total_price,
            "price_per_person": round(total_price / passengers, 2),
            "passengers": passengers,
            "currency": price.get("currency", "USD"),
            "duration": outbound.get("duration", "Unknown"),
            "booking_url": _aviasales_deeplink(origin, destination, date, return_date=return_date, passengers=passengers),
        }

        if return_date and len(itineraries) > 1:
            ret_itin = itineraries[1]
            seg_ret = ret_itin.get("segments", [{}])[0]
            ret_code = seg_ret.get("carrierCode", carrier_code)
            item["return_flight"] = {
                "flight_number": f"{ret_code}{seg_ret.get('number', '000')}",
                "departure_time": seg_ret.get("departure", {}).get("at"),
                "arrival_time": seg_ret.get("arrival", {}).get("at"),
                "airline": AIRLINE_MAP.get(ret_code, ret_code),
            }

        results.append(item)

    return results


INDIAN_AIRPORTS = {
    "DEL", "BOM", "BLR", "MAA", "HYD", "CCU", "COK", "AMD", "PNQ",
    "GOI", "GOX", "JAI", "LKO", "ATQ", "TRV", "IXC", "GAU", "SXR",
    "VNS", "IXB", "IXZ", "IXL", "UDR", "IDR", "BDQ", "NAG", "PAT",
    "BBI", "IXR", "DED", "IXA", "IXJ", "RPR", "VTZ", "TRZ", "CJB"
}

INDIAN_AIRLINES = ["6E", "AI", "UK", "QP", "SG", "IX"]

CURRENCY_BY_REGION = {
    "INR": (tuple(INDIAN_AIRPORTS), 86.5),
    "GBP": (("LHR", "LGW", "MAN"), 0.8),
    "EUR": (("CDG", "FRA", "FCO", "MXP", "AMS", "MAD"), 0.92),
    "JPY": (("TYO", "HND", "NRT"), 150.0),
    "AED": (("DXB", "AUH", "SHJ"), 3.67),
    "THB": (("BKK", "DMK", "HKT"), 36.0),
    "SGD": (("SIN",), 1.35),
}


def _localize_price(origin: str, destination: str = "", user_currency: str = "") -> tuple[str, float]:
    if user_currency and user_currency.upper() == "INR":
        return "INR", 86.5
    u_origin = origin.upper()
    u_dest = destination.upper()
    if u_origin in INDIAN_AIRPORTS or u_dest in INDIAN_AIRPORTS or Config.DEFAULT_CURRENCY == "INR":
        return "INR", 86.5
    for currency, (codes, multiplier) in CURRENCY_BY_REGION.items():
        if u_origin in codes or u_dest in codes:
            return currency, multiplier
    return Config.DEFAULT_CURRENCY, 1.0


async def _search_mock_flights(
    origin: str,
    destination: str,
    date: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
) -> List[Dict[str, Any]]:
    logger.info("Mock flight search %s -> %s on %s (return: %s, pax: %d)", origin, destination, date, return_date, passengers)
    u_origin = origin.upper()
    u_dest = destination.upper()
    is_domestic_india = u_origin in INDIAN_AIRPORTS and u_dest in INDIAN_AIRPORTS
    is_india_connected = u_origin in INDIAN_AIRPORTS or u_dest in INDIAN_AIRPORTS

    currency, multiplier = _localize_price(origin, destination)

    if is_domestic_india:
        airline_pool = INDIAN_AIRLINES
    elif is_india_connected:
        airline_pool = ["AI", "6E", "UK", "QP", "EK", "QR", "EY", "SQ", "BA", "LH", "TG"]
    else:
        airline_pool = list(AIRLINE_MAP.keys())

    results: List[Dict[str, Any]] = []
    for _ in range(3):
        code = random.choice(airline_pool)
        airline_name = AIRLINE_MAP.get(code, code)
        flight_num = f"{code}{random.randint(100, 999)}"

        if is_domestic_india or currency == "INR":
            if is_domestic_india:
                base_one_way = random.randint(3499, 7999)
            elif is_india_connected:
                base_one_way = random.randint(18500, 48000)
            else:
                base_one_way = int(random.randint(350, 950) * 86.5)
        else:
            base_price = random.randint(300, 1200)
            base_one_way = int(base_price * multiplier)

        outbound_dep = f"{date}T{random.randint(6, 21):02d}:{random.choice([0, 15, 30, 45]):02d}:00"
        deeplink = _aviasales_deeplink(origin, destination, date, return_date=return_date, passengers=passengers)

        if return_date:
            ret_code = random.choice([code, random.choice(airline_pool)])
            ret_airline_name = AIRLINE_MAP.get(ret_code, ret_code)
            ret_flight_num = f"{ret_code}{random.randint(100, 999)}"
            ret_dep = f"{return_date}T{random.randint(7, 22):02d}:{random.choice([0, 15, 30, 45]):02d}:00"

            rt_per_person = int(base_one_way * 1.9)
            total_flight_price = rt_per_person * passengers

            results.append({
                "flight_id": f"{flight_num}/{ret_flight_num}",
                "trip_type": "round_trip",
                "airline": f"{airline_name}" if code == ret_code else f"{airline_name} / {ret_airline_name}",
                "airline_code": code,
                "flight_number": f"{flight_num} (Outbound), {ret_flight_num} (Return)",
                "origin": u_origin,
                "destination": u_dest,
                "departure_time": outbound_dep,
                "return_time": ret_dep,
                "price_per_person": rt_per_person,
                "passengers": passengers,
                "price": total_flight_price,
                "total_price": total_flight_price,
                "currency": currency,
                "booking_url": deeplink,
                "description": f"Round-trip {u_origin} ⇄ {u_dest} ({date} to {return_date}) for {passengers} pax",
            })
        else:
            total_flight_price = base_one_way * passengers
            results.append({
                "flight_id": flight_num,
                "trip_type": "one_way",
                "airline": f"{airline_name} ({code})",
                "airline_code": code,
                "flight_number": flight_num,
                "origin": u_origin,
                "destination": u_dest,
                "departure_time": outbound_dep,
                "price_per_person": base_one_way,
                "passengers": passengers,
                "price": total_flight_price,
                "total_price": total_flight_price,
                "currency": currency,
                "booking_url": deeplink,
                "description": f"One-way {u_origin} → {u_dest} ({date}) for {passengers} pax",
            })
    return results


def _aviasales_deeplink(
    origin: str,
    destination: str,
    date: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
) -> str:
    """Build an Aviasales search deeplink in the form ORIGIN+DDMM+DEST(+DDMM)+PAX.

    One-way: DEL2011GOI2
    Round-trip: DEL2011GOI24112
    Wrapped in Travelpayouts affiliate redirect when TRAVELPAYOUTS_MARKER is set.
    """
    dt_out = datetime.strptime(date, "%Y-%m-%d")
    pax = max(1, min(9, int(passengers)))
    if return_date:
        dt_ret = datetime.strptime(return_date, "%Y-%m-%d")
        slug = f"{origin.upper()}{dt_out.day:02d}{dt_out.month:02d}{destination.upper()}{dt_ret.day:02d}{dt_ret.month:02d}{pax}"
    else:
        slug = f"{origin.upper()}{dt_out.day:02d}{dt_out.month:02d}{destination.upper()}{pax}"
    target = f"{AVIASALES_BASE}/{slug}"

    marker = Config.TRAVELPAYOUTS_MARKER
    if not marker:
        return target
    return f"{Config.CARS_AFFILIATE_HOST}?{urlencode({'marker': marker, 'trs': 'flights', 'u': target})}"


async def book_flight(
    origin: str,
    destination: str,
    date: str,
    passenger_name: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
) -> Dict[str, Any]:
    """Generate a booking URL for the chosen flight route.

    The agent must present the booking_url to the user; the user completes
    payment + ticketing on the hosted Aviasales/airline page. Returns a
    reservation_intent reference for tracking.
    """
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"date must be YYYY-MM-DD: {e}") from e
    if dt.date() < datetime.now(timezone.utc).date():
        raise ValueError("date cannot be in the past")
    if return_date:
        try:
            dt_ret = datetime.strptime(return_date, "%Y-%m-%d")
            if dt_ret.date() < dt.date():
                raise ValueError("return_date cannot be earlier than departure date")
        except ValueError as e:
            raise ValueError(f"return_date must be YYYY-MM-DD: {e}") from e

    pax = max(1, min(9, int(passengers)))
    intent_ref = secrets.token_urlsafe(8).upper().replace("_", "").replace("-", "")[:10]
    booking_url = _aviasales_deeplink(origin, destination, date, return_date=return_date, passengers=pax)
    trip_desc = f"{origin.upper()} ⇄ {destination.upper()} ({date} to {return_date})" if return_date else f"{origin.upper()} → {destination.upper()} ({date})"

    logger.info(
        "Booking intent %s: %s (%d pax) for %s", intent_ref, trip_desc, pax, passenger_name
    )
    return {
        "status": "pending_user_action",
        "intent_reference": f"BK{intent_ref}",
        "origin": origin.upper(),
        "destination": destination.upper(),
        "date": date,
        "return_date": return_date,
        "trip_type": "round_trip" if return_date else "one_way",
        "passengers": pax,
        "passenger_name": passenger_name,
        "booking_url": booking_url,
        "note": (
            "No money has been charged. Click booking_url to complete payment "
            "and ticketing on the partner site."
        ),
    }
