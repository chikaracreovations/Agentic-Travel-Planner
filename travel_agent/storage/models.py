"""Data models for Trip Persistence & Management (PRD Section 12).

Defines Trips, Itineraries, Activities, and Budget Snapshots.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActivityItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    time_slot: str = Field(..., description="e.g. '09:00 AM - 11:30 AM' or 'Morning'")
    activity_name: str
    location: str
    duration_minutes: int = 120
    estimated_cost: float = 0.0
    currency: str = "INR"
    is_verified: bool = False
    source: str = "Planned"
    notes: Optional[str] = None


class DayPlan(BaseModel):
    day_number: int
    date: Optional[str] = None
    title: str = Field(..., description="e.g. 'Arrival & Beach Exploration'")
    activities: List[ActivityItem] = Field(default_factory=list)
    day_notes: Optional[str] = None


class TripRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"trip_{str(uuid.uuid4())[:8]}")
    title: str
    origin: str
    destination: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: int = 1
    traveler_count: int = 1
    budget: Optional[float] = None
    currency: str = "INR"
    status: str = "planned"  # 'planned', 'booked', 'archived'
    itinerary_days: List[DayPlan] = Field(default_factory=list)
    budget_breakdown: Optional[Dict[str, Any]] = None
    booking_references: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
