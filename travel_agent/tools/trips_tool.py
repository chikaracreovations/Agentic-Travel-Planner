"""LLM-facing tools for saving and retrieving planned trips (PRD FR-10)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..storage.db import get_trip, list_trips, save_trip
from ..storage.models import ActivityItem, DayPlan, TripRecord

logger = logging.getLogger(__name__)


async def save_planned_trip(
    title: str,
    origin: str,
    destination: str,
    duration_days: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    traveler_count: int = 1,
    budget: Optional[float] = None,
    currency: str = "INR",
    days: Optional[List[Dict[str, Any]]] = None,
    budget_breakdown: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Save an approved or planned trip itinerary and budget to database persistence.

    Args:
        title: Trip title (e.g. 'Goa Beach & Culture Getaway')
        origin: Departure city/airport (e.g. 'DEL' or 'New Delhi')
        destination: Destination city (e.g. 'Goa')
        duration_days: Length of trip in days
        start_date: Optional starting date YYYY-MM-DD
        end_date: Optional ending date YYYY-MM-DD
        traveler_count: Number of travelers
        budget: Total budget limit or target
        currency: 'INR'
        days: List of day plans with day_number, title, activities
        budget_breakdown: Optional budget breakdown dictionary
    """
    itinerary_days: List[DayPlan] = []
    if days:
        for d in days:
            acts = []
            for a in d.get("activities", []):
                acts.append(ActivityItem(
                    time_slot=a.get("time_slot", "Morning"),
                    activity_name=a.get("activity_name", "Sightseeing"),
                    location=a.get("location", destination),
                    duration_minutes=int(a.get("duration_minutes", 120)),
                    estimated_cost=float(a.get("estimated_cost", 0.0)),
                    currency=currency,
                    is_verified=bool(a.get("is_verified", False)),
                    source=a.get("source", "Itinerary"),
                ))
            itinerary_days.append(DayPlan(
                day_number=int(d.get("day_number", len(itinerary_days) + 1)),
                title=d.get("title", f"Day {len(itinerary_days) + 1}"),
                activities=acts,
                day_notes=d.get("day_notes"),
            ))

    record = TripRecord(
        title=title,
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        duration_days=max(1, int(duration_days)),
        traveler_count=max(1, int(traveler_count)),
        budget=budget,
        currency=currency.upper(),
        itinerary_days=itinerary_days,
        budget_breakdown=budget_breakdown,
    )

    saved = save_trip(record)
    return {
        "status": "success",
        "trip_id": saved.id,
        "title": saved.title,
        "message": f"Trip '{saved.title}' successfully saved with ID {saved.id}.",
    }


async def get_saved_trip(trip_id: str) -> Dict[str, Any]:
    """Retrieve a previously saved trip itinerary by its ID."""
    trip = get_trip(trip_id)
    if not trip:
        return {"status": "error", "message": f"Trip with ID {trip_id} not found."}
    return {
        "status": "success",
        "trip": trip.model_dump(),
    }


async def list_user_trips() -> Dict[str, Any]:
    """List all saved user trips."""
    trips = list_trips()
    return {
        "status": "success",
        "count": len(trips),
        "trips": trips,
    }
