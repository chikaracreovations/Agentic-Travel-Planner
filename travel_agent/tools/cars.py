import logging
import secrets
from datetime import datetime
from typing import Any, Dict
from urllib.parse import urlencode

from ..config import Config

logger = logging.getLogger(__name__)

RENTALCARS_BASE = "https://www.rentalcars.com/SearchResults.do"

# Indicative daily prices used to estimate totals before the user
# completes the real booking on the partner site.
PRICE_PER_DAY = {
    "compact": 40,
    "sedan": 60,
    "suv": 90,
    "luxury": 150,
}


PRICE_PER_DAY_INR = {
    "compact": 1800,  # e.g. WagonR / Swift
    "sedan": 2600,    # e.g. Dzire / Aura
    "suv": 4200,      # e.g. Ertiga / Innova Crysta
    "luxury": 8500,   # e.g. Fortuner / Mercedes
}


def _build_booking_url(location: str, start: datetime, end: datetime) -> str:
    """Build a deeplink to the RentalCars search page, wrapped in the Travelpayouts
    affiliate redirect when TRAVELPAYOUTS_MARKER is set."""
    rentalcars_params = {
        "location": location,
        "puYear": start.year,
        "puMonth": f"{start.month:02d}",
        "puDay": f"{start.day:02d}",
        "puHour": "10",
        "puMinute": "00",
        "doYear": end.year,
        "doMonth": f"{end.month:02d}",
        "doDay": f"{end.day:02d}",
        "doHour": "10",
        "doMinute": "00",
        "driversAge": "30",
    }
    target = f"{RENTALCARS_BASE}?{urlencode(rentalcars_params)}"

    marker = Config.TRAVELPAYOUTS_MARKER
    if not marker:
        return target

    return f"{Config.CARS_AFFILIATE_HOST}?{urlencode({'marker': marker, 'trs': 'cars', 'u': target})}"


def rent_car(location: str, start_date: str, end_date: str, car_type: str = "compact") -> Dict[str, Any]:
    """Search car rentals and return an estimated total + a booking URL.

    The agent should present BOTH the estimated price and the booking_url
    to the user. The user completes the actual reservation on the hosted
    RentalCars page (real booking, real inventory, real payment).

    Args:
        location: City name or airport code (e.g. "DEL", "Goa", "LHR", "Rome").
        start_date: Pickup date (YYYY-MM-DD).
        end_date: Drop-off date (YYYY-MM-DD).
        car_type: compact | sedan | suv | luxury.
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Dates must be YYYY-MM-DD: {e}") from e
    if end <= start:
        raise ValueError(f"end_date ({end_date}) must be after start_date ({start_date})")

    days = (end - start).days

    indian_locations = {
        "del", "delhi", "new delhi", "bom", "mumbai", "blr", "bangalore", "bengaluru",
        "goa", "goi", "gox", "jaipur", "jai", "udaipur", "udr", "kerala", "kochi", "cok",
        "hyderabad", "hyd", "chennai", "maa", "kolkata", "ccu", "pune", "pnq", "ahmedabad", "amd",
        "manali", "shimla", "rishikesh", "agra", "varanasi", "vns", "srinagar", "sxr", "ladakh", "leh", "ixl"
    }
    is_india = location.lower().strip() in indian_locations or Config.DEFAULT_CURRENCY == "INR"

    if is_india:
        currency = "INR"
        price_per_day = PRICE_PER_DAY_INR.get(car_type.lower(), 2600)
    else:
        currency = "USD"
        price_per_day = PRICE_PER_DAY.get(car_type.lower(), 50)

    estimated_total = price_per_day * days
    booking_url = _build_booking_url(location, start, end)

    logger.info("Car estimate: %s %s, %s days, est %s %s", car_type, location, days, currency, estimated_total)

    return {
        "status": "estimate",
        "search_reference": f"CAR{secrets.token_hex(4).upper()}",
        "car_type": car_type,
        "location": location,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "estimated_total_price": estimated_total,
        "currency": currency,
        "booking_url": booking_url,
        "note": (
            "Estimated price only. Click booking_url to see real-time inventory and "
            "complete the reservation on RentalCars."
        ),
    }
