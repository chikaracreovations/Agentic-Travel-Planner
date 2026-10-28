"""Deterministic Budget Intelligence Engine (PRD Section 7 & FR-05, FR-07..14).

Guarantees 100% mathematical accuracy without relying on LLM arithmetic.
Provides itemized breakdown, verified vs estimated cost tracking,
per-person group allocation, and budget overrun detection with savings suggestions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "transportation",
    "accommodation",
    "food",
    "local_travel",
    "activities",
    "additional_costs",
    "contingency",
}

# Standard daily benchmarks for India travel (INR per person per day)
DAILY_BENCHMARKS_INR = {
    "budget": {
        "accommodation": 800.0,
        "food": 600.0,
        "local_travel": 350.0,
        "activities": 400.0,
        "contingency_rate": 0.08,
    },
    "moderate": {
        "accommodation": 2500.0,
        "food": 1400.0,
        "local_travel": 900.0,
        "activities": 1000.0,
        "contingency_rate": 0.10,
    },
    "luxury": {
        "accommodation": 7500.0,
        "food": 3500.0,
        "local_travel": 2500.0,
        "activities": 2500.0,
        "contingency_rate": 0.12,
    },
}


class ExpenseItem(BaseModel):
    category: str = Field(..., description="Category: transportation, accommodation, food, local_travel, activities, additional_costs, contingency")
    description: str = Field(..., description="Item description (e.g., 'IndiGo DEL->GOI return flight')")
    amount: float = Field(..., ge=0, description="Cost in specified currency")
    is_verified: bool = Field(False, description="True if verified via live API or confirmed booking; False if estimate")
    source: Optional[str] = Field(None, description="Source or provider (e.g., 'Amadeus', 'Hotellook', 'Estimate')")


async def calculate_trip_budget(
    items: List[Dict[str, Any]],
    traveler_count: int = 1,
    target_budget: Optional[float] = None,
    currency: str = "INR",
    include_contingency_percent: float = 0.0,
) -> Dict[str, Any]:
    """Deterministically calculate total trip expenses, per-person allocation, and overrun status.

    Args:
        items: List of expense dictionaries, each with:
               - category: 'transportation', 'accommodation', 'food', 'local_travel', 'activities', 'additional_costs', 'contingency'
               - description: description string
               - amount: numeric price
               - is_verified: bool (optional, default False)
               - source: source name (optional)
        traveler_count: Number of travelers (default 1)
        target_budget: Optional user budget limit to check against for overruns
        currency: 3-letter currency code (default 'INR')
        include_contingency_percent: Optional percentage (e.g. 5.0 or 10.0) to auto-add as contingency if not explicitly in items.

    Returns:
        Structured budget report with category breakdown, total cost, cost per person,
        verified vs estimated split, overrun alerts, and markdown table.
    """
    try:
        count = max(1, int(traveler_count or 1))
    except (ValueError, TypeError):
        count = 1

    try:
        contingency_pct = float(include_contingency_percent or 0.0)
    except (ValueError, TypeError):
        contingency_pct = 0.0

    target_b: Optional[float] = None
    if target_budget is not None and str(target_budget).strip():
        try:
            target_b = float(target_budget)
        except (ValueError, TypeError):
            target_b = None

    curr_symbol = "₹" if currency.upper() == "INR" else f"{currency.upper()} "

    category_totals: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}
    category_items: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in VALID_CATEGORIES}
    
    import json

    verified_total = 0.0
    estimated_total = 0.0

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            items = []

    parsed_items: List[ExpenseItem] = []
    for raw in items:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = {"category": "activities", "description": raw, "amount": 0.0}
        if not isinstance(raw, dict):
            continue

        try:
            cat = str(raw.get("category", "activities")).strip().lower()
            if cat not in VALID_CATEGORIES:
                cat = "activities"
            
            amount = float(raw.get("amount", 0.0))
            is_verified = bool(raw.get("is_verified", False))
            desc = str(raw.get("description", "Unnamed expense"))
            src = raw.get("source") or ("Live API" if is_verified else "Estimate")
            
            item = ExpenseItem(
                category=cat,
                description=desc,
                amount=amount,
                is_verified=is_verified,
                source=src,
            )
            parsed_items.append(item)
            category_totals[cat] += amount
            category_items[cat].append({
                "description": desc,
                "amount": amount,
                "is_verified": is_verified,
                "source": src,
            })

            if is_verified:
                verified_total += amount
            else:
                estimated_total += amount
        except (ValueError, TypeError) as e:
            logger.warning("Skipping invalid budget item %s: %s", raw, e)

    # Optional auto-contingency if no contingency items provided
    if category_totals["contingency"] == 0.0 and contingency_pct > 0:
        base_subtotal = sum(category_totals.values())
        auto_contingency = round(base_subtotal * (contingency_pct / 100.0), 2)
        category_totals["contingency"] = auto_contingency
        estimated_total += auto_contingency
        category_items["contingency"].append({
            "description": f"Contingency Reserve ({contingency_pct}%)",
            "amount": auto_contingency,
            "is_verified": False,
            "source": "Calculated reserve",
        })

    total_cost = round(sum(category_totals.values()), 2)
    cost_per_person = round(total_cost / count, 2)

    # Overrun detection
    is_over_budget = False
    overrun_amount = 0.0
    budget_utilization_pct = 0.0
    savings_suggestions: List[str] = []

    if target_b is not None and target_b > 0:
        budget_utilization_pct = round((total_cost / target_b) * 100, 1)
        if total_cost > target_b:
            is_over_budget = True
            overrun_amount = round(total_cost - target_b, 2)
            # Generate deterministic savings recommendations
            if category_totals["accommodation"] > 0.35 * total_cost:
                savings_suggestions.append(
                    f"Accommodation represents {round((category_totals['accommodation']/total_cost)*100)}% of expenses. Consider a verified boutique stay or homestay to save ~{curr_symbol}{round(category_totals['accommodation'] * 0.25):,}."
                )
            if category_totals["transportation"] > 0.40 * total_cost:
                savings_suggestions.append(
                    f"Transportation is high ({curr_symbol}{round(category_totals['transportation']):,}). Consider off-peak flight timings or express train routes."
                )
            if category_totals["contingency"] > 0:
                savings_suggestions.append(
                    f"You have {curr_symbol}{round(category_totals['contingency']):,} in contingency reserve that can absorb unexpected spikes."
                )

    # Human-readable markdown summary
    md_lines = [
        f"### Itemized Trip Budget ({currency.upper()})",
        "",
        "| Category | Estimated / Verified Cost | Status |",
        "| :--- | :--- | :--- |",
    ]
    for cat in ["transportation", "accommodation", "food", "local_travel", "activities", "additional_costs", "contingency"]:
        amt = category_totals[cat]
        if amt > 0:
            status_badge = "Verified" if any(i["is_verified"] for i in category_items[cat]) else "Estimate"
            md_lines.append(f"| **{cat.replace('_', ' ').title()}** | {curr_symbol}{amt:,.2f} | {status_badge} |")

    md_lines.extend([
        f"| **Total Trip Cost** | **{curr_symbol}{total_cost:,.2f}** | |",
        f"| **Cost Per Person ({count} traveler{'s' if count > 1 else ''})** | **{curr_symbol}{cost_per_person:,.2f}** | |",
    ])

    if target_b:
        md_lines.append(f"| Target Budget | {curr_symbol}{target_b:,.2f} | {'⚠️ OVER BUDGET by ' + curr_symbol + f'{overrun_amount:,.2f}' if is_over_budget else '✅ Within Budget'} |")

    return {
        "status": "success",
        "currency": currency.upper(),
        "total_cost": total_cost,
        "cost_per_person": cost_per_person,
        "traveler_count": count,
        "category_breakdown": {k: round(v, 2) for k, v in category_totals.items() if v > 0},
        "itemized_items": category_items,
        "verification_audit": {
            "verified_total": round(verified_total, 2),
            "estimated_total": round(estimated_total, 2),
            "verified_ratio_pct": round((verified_total / total_cost * 100), 1) if total_cost > 0 else 0.0,
        },
        "budget_evaluation": {
            "target_budget": target_b,
            "is_over_budget": is_over_budget,
            "overrun_amount": overrun_amount,
            "utilization_pct": budget_utilization_pct,
            "savings_suggestions": savings_suggestions,
        },
        "markdown_table": "\n".join(md_lines),
    }


async def estimate_standard_budget(
    destination: str,
    duration_days: int,
    traveler_count: int = 1,
    travel_style: str = "moderate",
    currency: str = "INR",
) -> Dict[str, Any]:
    """Generate baseline deterministic daily expense benchmarks for Indian or global travel.

    Args:
        destination: Destination city or state
        duration_days: Number of days of the trip
        traveler_count: Number of people traveling
        travel_style: 'budget', 'moderate', or 'luxury'
        currency: Default 'INR'

    Returns:
        Structured baseline estimate ready to be customized or verified.
    """
    style = travel_style.lower() if travel_style.lower() in DAILY_BENCHMARKS_INR else "moderate"
    benchmarks = DAILY_BENCHMARKS_INR[style]
    days = max(1, int(duration_days))
    travelers = max(1, int(traveler_count))

    # Accommodation is typically shared per 2 travelers
    rooms = (travelers + 1) // 2
    accom_total = benchmarks["accommodation"] * days * rooms
    food_total = benchmarks["food"] * days * travelers
    local_transport_total = benchmarks["local_travel"] * days * travelers
    activities_total = benchmarks["activities"] * days * travelers

    base_subtotal = accom_total + food_total + local_transport_total + activities_total
    contingency = round(base_subtotal * benchmarks["contingency_rate"], 2)

    items = [
        {"category": "accommodation", "description": f"{days} nights stay ({style} style, {rooms} room{'s' if rooms > 1 else ''})", "amount": accom_total, "is_verified": False},
        {"category": "food", "description": f"Daily meals & refreshments ({travelers} travelers)", "amount": food_total, "is_verified": False},
        {"category": "local_travel", "description": "Local cabs, autos, or metro", "amount": local_transport_total, "is_verified": False},
        {"category": "activities", "description": "Entry tickets, sightseeing, experiences", "amount": activities_total, "is_verified": False},
        {"category": "contingency", "description": f"Contingency buffer ({int(benchmarks['contingency_rate']*100)}%)", "amount": contingency, "is_verified": False},
    ]

    return await calculate_trip_budget(
        items=items,
        traveler_count=travelers,
        currency=currency,
    )
