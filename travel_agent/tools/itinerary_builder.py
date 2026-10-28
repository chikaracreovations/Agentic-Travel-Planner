"""Structured Day-by-Day Itinerary Builder tool (PRD Section 6 & FR-04).

Builds and persists day-wise schedules with activity cards, time slots,
durations, locations, and cost estimates.
Directly communicates structured itinerary plans to the frontend Itinerary & Timeline tab.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..storage.db import save_trip
from ..storage.models import ActivityItem, DayPlan, TripRecord

logger = logging.getLogger(__name__)


async def build_day_by_day_itinerary(
    destination: str,
    duration_days: int,
    days: List[Dict[str, Any]],
    trip_title: Optional[str] = None,
    origin: str = "DEL",
    traveler_count: int = 1,
    budget: Optional[float] = None,
    currency: str = "INR",
) -> Dict[str, Any]:
    """Construct, validate, and store a day-by-day travel itinerary with activity cards.

    Args:
        destination: Target city or region (e.g. 'Goa', 'Manali', 'Kerala', 'Dubai')
        duration_days: Total number of days
        days: List of day dictionaries, each containing:
              - day_number: int (1, 2, 3...)
              - title: str (e.g. 'Arrival & North Goa Beaches')
              - date: Optional[str] (YYYY-MM-DD)
              - activities: List of activity dicts:
                  - time_slot: '09:00 AM' or 'Morning' / 'Afternoon' / 'Evening'
                  - activity_name: Name of attraction or activity
                  - location: Specific beach, fort, temple, or neighborhood
                  - duration_minutes: Duration in minutes (e.g. 90, 120, 180)
                  - estimated_cost: Numeric cost in specified currency
                  - category: 'Sightseeing' / 'Adventure' / 'Dining' / 'Relaxation'
                  - notes: Practical tips (e.g. 'Best sunset views from cliff')
        trip_title: Optional title for the trip (e.g. '4-Day Goa Beach & Culture Tour')
        origin: Departure hub (default 'DEL')
        traveler_count: Number of travelers
        budget: Target or estimated budget
        currency: 'INR'

    Returns:
        Structured itinerary object consumed by the frontend Itinerary & Timeline tab.
    """
    import json

    days_count = max(1, int(duration_days))
    title = trip_title or f"{days_count}-Day {destination.title()} Itinerary"

    if isinstance(days, str):
        try:
            days = json.loads(days)
        except Exception:
            days = [days]

    parsed_days: List[DayPlan] = []
    total_activities = 0
    total_itinerary_cost = 0.0

    for d in days:
        if isinstance(d, str):
            try:
                d = json.loads(d)
            except Exception:
                d = {
                    "day_number": len(parsed_days) + 1,
                    "title": d,
                    "activities": [{"time_slot": "All Day", "activity_name": d, "location": destination.title(), "estimated_cost": 0.0}]
                }
        if not isinstance(d, dict):
            continue

        day_num = int(d.get("day_number", len(parsed_days) + 1))
        day_title = d.get("title", f"Day {day_num}: Exploring {destination.title()}")
        acts_raw = d.get("activities", [])
        if isinstance(acts_raw, str):
            try:
                acts_raw = json.loads(acts_raw)
            except Exception:
                acts_raw = [{"time_slot": "All Day", "activity_name": acts_raw, "location": destination.title(), "estimated_cost": 0.0}]
        
        parsed_activities: List[ActivityItem] = []
        for a in acts_raw:
            if isinstance(a, str):
                try:
                    a = json.loads(a)
                except Exception:
                    a = {"time_slot": "Morning", "activity_name": a, "location": destination.title(), "estimated_cost": 0.0}
            if not isinstance(a, dict):
                continue

            cost = float(a.get("estimated_cost", 0.0))
            total_itinerary_cost += cost
            total_activities += 1
            
            parsed_activities.append(ActivityItem(
                time_slot=a.get("time_slot", "Morning"),
                activity_name=a.get("activity_name", "Sightseeing"),
                location=a.get("location", destination.title()),
                duration_minutes=int(a.get("duration_minutes", 120)),
                estimated_cost=cost,
                currency=currency.upper(),
                is_verified=bool(a.get("is_verified", False)),
                source=a.get("category", "Sightseeing"),
                notes=a.get("notes"),
            ))

        parsed_days.append(DayPlan(
            day_number=day_num,
            date=d.get("date"),
            title=day_title,
            activities=parsed_activities,
            day_notes=d.get("day_notes"),
        ))

    # Persist directly into SQLite so it appears in Saved Trips & workspace
    record = TripRecord(
        title=title,
        origin=origin.upper(),
        destination=destination.title(),
        duration_days=days_count,
        traveler_count=max(1, int(traveler_count)),
        budget=budget,
        currency=currency.upper(),
        itinerary_days=parsed_days,
    )
    saved = save_trip(record)

    return {
        "status": "success",
        "trip_id": saved.id,
        "trip_title": title,
        "destination": destination.title(),
        "duration_days": days_count,
        "traveler_count": traveler_count,
        "currency": currency.upper(),
        "total_activities": total_activities,
        "itinerary_days": [dp.model_dump() for dp in parsed_days],
        "message": f"Successfully created {days_count}-day itinerary for {destination.title()} with {total_activities} scheduled activities.",
    }
