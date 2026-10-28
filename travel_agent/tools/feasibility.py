"""Deterministic Feasibility & Constraint Validator (PRD FR-09 & Section 13.2).

Enforces hard constraints in code:
- Daily active duration & energy limits based on travel pace.
- Realistic travel and transfer buffers between activities.
- Budget compliance checks.
- Overload flags and constructive adjustment recommendations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PACE_HOURS_LIMIT = {
    "relaxed": 6.0,
    "moderate": 8.5,
    "intense": 11.0,
}


async def validate_itinerary_feasibility(
    days: List[Dict[str, Any]],
    travel_pace: str = "moderate",
    target_budget: Optional[float] = None,
    total_cost: Optional[float] = None,
    currency: str = "INR",
) -> Dict[str, Any]:
    """Validate schedule feasibility, daily active hours, and budget constraints in deterministic code.

    Args:
        days: List of day plans with day_number and activities (each with duration_minutes, activity_name)
        travel_pace: 'relaxed', 'moderate', or 'intense'
        target_budget: Optional user budget cap
        total_cost: Calculated total trip expense
        currency: 'INR'

    Returns:
        Feasibility audit with is_feasible bool, score (0-100), warnings, and recommendations.
    """
    pace = travel_pace.lower() if travel_pace.lower() in PACE_HOURS_LIMIT else "moderate"
    max_daily_hours = PACE_HOURS_LIMIT[pace]
    curr_symbol = "₹" if currency.upper() == "INR" else f"{currency.upper()} "

    warnings: List[str] = []
    recommendations: List[str] = []
    passed_checks: List[str] = []
    day_summaries: List[Dict[str, Any]] = []

    total_activity_count = 0

    for day in days:
        day_num = day.get("day_number", 1)
        activities = day.get("activities", [])
        total_activity_count += len(activities)

        active_minutes = sum(int(a.get("duration_minutes", 120)) for a in activities)
        # Add 30 mins estimated transfer buffer between activities if > 1 activity
        transfer_minutes = max(0, len(activities) - 1) * 35
        total_day_minutes = active_minutes + transfer_minutes
        total_day_hours = round(total_day_minutes / 60.0, 1)

        day_status = "feasible"
        if total_day_hours > max_daily_hours:
            day_status = "overloaded"
            diff = round(total_day_hours - max_daily_hours, 1)
            warnings.append(
                f"Day {day_num} has {total_day_hours}h of planned activities and transit, exceeding the {pace} limit ({max_daily_hours}h) by {diff}h."
            )
            recommendations.append(
                f"On Day {day_num}, consider moving 1 activity to a later day or adding a rest break."
            )
        elif len(activities) > 4:
            warnings.append(
                f"Day {day_num} has {len(activities)} separate stops; transfer fatigue may occur."
            )

        day_summaries.append({
            "day_number": day_num,
            "activity_count": len(activities),
            "active_hours": round(active_minutes / 60.0, 1),
            "transit_buffer_hours": round(transfer_minutes / 60.0, 1),
            "total_day_hours": total_day_hours,
            "status": day_status,
        })

    if not warnings:
        passed_checks.append(f"Daily pace conforms to {pace} schedule limits (<= {max_daily_hours}h/day).")

    # Budget constraint check
    if target_budget and total_cost:
        if total_cost > target_budget:
            overage = round(total_cost - target_budget, 2)
            warnings.append(
                f"Budget constraint violated: Total cost ({curr_symbol}{total_cost:,.2f}) exceeds target ({curr_symbol}{target_budget:,.2f}) by {curr_symbol}{overage:,.2f}."
            )
            recommendations.append(
                f"Run budget optimization to reduce discretionary accommodation or activity expenses."
            )
        else:
            savings = round(target_budget - total_cost, 2)
            passed_checks.append(
                f"Budget compliant: Total cost ({curr_symbol}{total_cost:,.2f}) is within target ({curr_symbol}{target_budget:,.2f}) with {curr_symbol}{savings:,.2f} headroom."
            )

    # Feasibility Score calculation
    penalty = len(warnings) * 15
    feasibility_score = max(20, min(100, 100 - penalty))
    is_feasible = len(warnings) == 0 or (len(warnings) <= 1 and feasibility_score >= 70)

    return {
        "status": "success",
        "is_feasible": is_feasible,
        "feasibility_score": feasibility_score,
        "travel_pace": pace,
        "max_allowed_daily_hours": max_daily_hours,
        "warnings": warnings,
        "passed_checks": passed_checks,
        "recommendations": recommendations,
        "day_summaries": day_summaries,
    }
