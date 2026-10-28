"""SQLite database storage for Trips, Itineraries, and Budgets (PRD FR-10 & Section 12)."""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import DayPlan, TripRecord

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "travel_planner.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables for Trips and Itineraries."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT,
                duration_days INTEGER DEFAULT 1,
                traveler_count INTEGER DEFAULT 1,
                budget REAL,
                currency TEXT DEFAULT 'INR',
                status TEXT DEFAULT 'planned',
                itinerary_json TEXT,
                budget_json TEXT,
                bookings_json TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        conn.commit()


# Ensure tables exist
init_db()


def save_trip(trip: TripRecord) -> TripRecord:
    """Insert or update a trip record."""
    trip.updated_at = time.time()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trips (
                id, title, origin, destination, start_date, end_date,
                duration_days, traveler_count, budget, currency, status,
                itinerary_json, budget_json, bookings_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                origin=excluded.origin,
                destination=excluded.destination,
                start_date=excluded.start_date,
                end_date=excluded.end_date,
                duration_days=excluded.duration_days,
                traveler_count=excluded.traveler_count,
                budget=excluded.budget,
                currency=excluded.currency,
                status=excluded.status,
                itinerary_json=excluded.itinerary_json,
                budget_json=excluded.budget_json,
                bookings_json=excluded.bookings_json,
                updated_at=excluded.updated_at
        """, (
            trip.id,
            trip.title,
            trip.origin,
            trip.destination,
            trip.start_date,
            trip.end_date,
            trip.duration_days,
            trip.traveler_count,
            trip.budget,
            trip.currency,
            trip.status,
            json.dumps([day.model_dump() for day in trip.itinerary_days]),
            json.dumps(trip.budget_breakdown) if trip.budget_breakdown else None,
            json.dumps(trip.booking_references),
            trip.created_at,
            trip.updated_at,
        ))
        conn.commit()
    return trip


def list_trips(limit: int = 50) -> List[Dict[str, Any]]:
    """List recent trips without full nested itinerary bloat."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, origin, destination, start_date, end_date,
                   duration_days, traveler_count, budget, currency, status,
                   created_at, updated_at
            FROM trips
            ORDER BY updated_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_trip(trip_id: str) -> Optional[TripRecord]:
    """Retrieve full trip by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        row_dict = dict(row)
        itinerary_days: List[DayPlan] = []
        if row_dict.get("itinerary_json"):
            try:
                days_data = json.loads(row_dict["itinerary_json"])
                itinerary_days = [DayPlan(**d) for d in days_data]
            except Exception as e:
                logger.error("Failed to parse itinerary_json: %s", e)

        budget_breakdown = None
        if row_dict.get("budget_json"):
            try:
                budget_breakdown = json.loads(row_dict["budget_json"])
            except Exception as e:
                logger.error("Failed to parse budget_json: %s", e)

        bookings = []
        if row_dict.get("bookings_json"):
            try:
                bookings = json.loads(row_dict["bookings_json"])
            except Exception as e:
                logger.error("Failed to parse bookings_json: %s", e)

        return TripRecord(
            id=row_dict["id"],
            title=row_dict["title"],
            origin=row_dict["origin"],
            destination=row_dict["destination"],
            start_date=row_dict.get("start_date"),
            end_date=row_dict.get("end_date"),
            duration_days=row_dict.get("duration_days", 1),
            traveler_count=row_dict.get("traveler_count", 1),
            budget=row_dict.get("budget"),
            currency=row_dict.get("currency", "INR"),
            status=row_dict.get("status", "planned"),
            itinerary_days=itinerary_days,
            budget_breakdown=budget_breakdown,
            booking_references=bookings,
            created_at=row_dict.get("created_at", time.time()),
            updated_at=row_dict.get("updated_at", time.time()),
        )


def delete_trip(trip_id: str) -> bool:
    """Delete a trip by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        conn.commit()
        return cursor.rowcount > 0
