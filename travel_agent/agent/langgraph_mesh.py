"""LangGraph Multi-Agent Mesh Specification and Demonstration Engine.

Represents the multi-agent state graph architecture:
- Supervisor / Intent Router
- Flight Specialist
- Hotel Specialist
- Local Transit & App Advisor
- Itinerary Planner
- Budget Intelligence & Auditor
- Feasibility & Pacing Validator
- Payment & Checkout Agent

Provides topology, dynamic agent management (enable/disable, model, temperature),
and step-by-step demonstration / simulation execution.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentNodeConfig(BaseModel):
    id: str
    name: str
    role: str
    icon: str
    color: str
    badge: str
    model: str = "gemini-2.5-flash"
    temperature: float = 0.2
    enabled: bool = True
    max_retries: int = 2
    tools: List[str] = Field(default_factory=list)
    description: str
    system_role: str
    calls_count: int = 0
    avg_latency_ms: int = 350
    status: str = "idle"  # idle, active, completed, disabled


class GraphEdge(BaseModel):
    from_node: str
    to_node: str
    label: str = ""
    edge_type: str = "direct"  # direct, conditional, fan_out, fan_in


class LangGraphTopology(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    state_channels: List[Dict[str, str]]


# Default Agent Mesh Registry
DEFAULT_AGENTS: Dict[str, AgentNodeConfig] = {
    "supervisor": AgentNodeConfig(
        id="supervisor",
        name="Supervisor & Intent Router",
        role="Meta-Cognitive Controller",
        icon="🧠",
        color="#8ab4f8",
        badge="Router",
        model="gemini-2.5-flash",
        temperature=0.1,
        enabled=True,
        tools=["get_current_datetime", "list_user_trips", "get_saved_trip"],
        description="Deconstructs user travel queries into structured subtasks, delegating to specialized domain workers and synchronizing global state.",
        system_role="Master orchestrator. Dispatches flight, hotel, itinerary, and budget goals based on user intent and location context.",
        calls_count=42,
        avg_latency_ms=280,
    ),
    "flight_specialist": AgentNodeConfig(
        id="flight_specialist",
        name="Flight & Aviation Specialist",
        role="Airfare & Round-Trip Engine",
        icon="✈️",
        color="#4285f4",
        badge="Partner Deep Links",
        model="gemini-2.5-flash",
        temperature=0.1,
        enabled=True,
        tools=["search_flights", "book_flight"],
        description="Queries live carrier inventory via Aviasales, generates verified round-trip deep links (e.g. DEL-GOI), and returns localized ₹ fares.",
        system_role="Searches outbound and return flights, matches user dates and traveler counts, and constructs valid deep-link URLs.",
        calls_count=29,
        avg_latency_ms=410,
    ),
    "hotel_specialist": AgentNodeConfig(
        id="hotel_specialist",
        name="Hotel & Accommodation Specialist",
        role="Lodging & Stays Engine",
        icon="🏨",
        color="#34a853",
        badge="Verified Stays",
        model="gemini-2.5-flash",
        temperature=0.2,
        enabled=True,
        tools=["search_hotels"],
        description="Finds verified hotels and resorts via Hotellook / Booking partners, evaluates star ratings, neighborhood proximity, and night rates.",
        system_role="Searches accommodations matching budget tier and destination coordinates with partner booking verification.",
        calls_count=27,
        avg_latency_ms=390,
    ),
    "local_guide_specialist": AgentNodeConfig(
        id="local_guide_specialist",
        name="Local Transit & App Advisor",
        role="Ground Transport & On-Site Guide",
        icon="🧭",
        color="#fbbc04",
        badge="Ground Ops",
        model="gemini-2.5-flash",
        temperature=0.2,
        enabled=True,
        tools=["get_destination_local_guide"],
        description="Advises on ground transportation realities: GoaMiles vs scooter rentals (warning of taxi unions), Rapido/Uber in metros, Grab in SE Asia, and local food delivery (Zomato/Swiggy/Blinkit).",
        system_role="Delivers hyper-local ground transit intelligence, rental costs, app availability, and local taxi union alerts.",
        calls_count=35,
        avg_latency_ms=210,
    ),
    "itinerary_builder": AgentNodeConfig(
        id="itinerary_builder",
        name="Itinerary Planner & Chrono Engine",
        role="Day-by-Day Scheduler",
        icon="📅",
        color="#a142f4",
        badge="Timeline Builder",
        model="gemini-2.5-flash",
        temperature=0.4,
        enabled=True,
        tools=["build_day_by_day_itinerary", "save_planned_trip"],
        description="Constructs chronological day cards with Morning, Afternoon, and Evening activities, estimating durations, locations, and costs.",
        system_role="Creates structured day-by-day itineraries and writes complete trip models to SQLite persistence.",
        calls_count=38,
        avg_latency_ms=490,
    ),
    "feasibility_validator": AgentNodeConfig(
        id="feasibility_validator",
        name="Feasibility & Pacing Validator",
        role="Safety & Fatigue Inspector",
        icon="⚡",
        color="#ea4335",
        badge="Rule Engine",
        model="gemini-2.5-flash",
        temperature=0.0,
        enabled=True,
        tools=["validate_itinerary_feasibility", "get_forecast"],
        description="Performs heuristic checks for activity density, geographic transit delays, weather compatibility, and traveler exhaustion risks.",
        system_role="Audits day plans to ensure realistic travel times between attractions and validates weather forecasts.",
        calls_count=22,
        avg_latency_ms=190,
    ),
    "budget_auditor": AgentNodeConfig(
        id="budget_auditor",
        name="Budget Intelligence & Auditor",
        role="Deterministic Math Engine",
        icon="💰",
        color="#00c853",
        badge="Zero Hallucination",
        model="gemini-2.5-flash",
        temperature=0.0,
        enabled=True,
        tools=["calculate_trip_budget", "estimate_standard_budget"],
        description="Executes deterministic Python arithmetic to compute total trip costs (flights + lodging + activities + contingency) with per-traveler split.",
        system_role="Eliminates LLM math errors by calculating exact expense sums, budget caps, and variance reports in ₹ INR.",
        calls_count=40,
        avg_latency_ms=160,
    ),
    "payment_agent": AgentNodeConfig(
        id="payment_agent",
        name="Payment & Checkout Agent",
        role="Secure Partner & Stripe Gateway",
        icon="💳",
        color="#ff6d00",
        badge="PCI-DSS Compliant",
        model="gemini-2.5-flash",
        temperature=0.0,
        enabled=True,
        tools=["create_payment_session", "get_payment_status"],
        description="Generates compliant Stripe Checkout sessions for deposits or tours and redirects to verified partner airlines/hotels.",
        system_role="Manages Stripe checkout sessions, verifies webhook signatures, and records payment states.",
        calls_count=12,
        avg_latency_ms=310,
    ),
}

# Graph Edges Definition
GRAPH_EDGES: List[GraphEdge] = [
    GraphEdge(from_node="__start__", to_node="supervisor", label="User Request", edge_type="direct"),
    GraphEdge(from_node="supervisor", to_node="flight_specialist", label="Fan-out: Flights", edge_type="fan_out"),
    GraphEdge(from_node="supervisor", to_node="hotel_specialist", label="Fan-out: Lodging", edge_type="fan_out"),
    GraphEdge(from_node="supervisor", to_node="local_guide_specialist", label="Fan-out: Ground Transit", edge_type="fan_out"),
    GraphEdge(from_node="flight_specialist", to_node="itinerary_builder", label="Flight Sync", edge_type="fan_in"),
    GraphEdge(from_node="hotel_specialist", to_node="itinerary_builder", label="Stay Sync", edge_type="fan_in"),
    GraphEdge(from_node="local_guide_specialist", to_node="itinerary_builder", label="Ground Transit Sync", edge_type="fan_in"),
    GraphEdge(from_node="itinerary_builder", to_node="feasibility_validator", label="Pacing Check", edge_type="direct"),
    GraphEdge(from_node="feasibility_validator", to_node="budget_auditor", label="Pass Pacing -> Math", edge_type="direct"),
    GraphEdge(from_node="budget_auditor", to_node="payment_agent", label="If Booking Req.", edge_type="conditional"),
    GraphEdge(from_node="budget_auditor", to_node="supervisor", label="Budget Approved", edge_type="direct"),
    GraphEdge(from_node="payment_agent", to_node="supervisor", label="Session Ready", edge_type="direct"),
    GraphEdge(from_node="supervisor", to_node="__end__", label="Response Stream", edge_type="direct"),
]

STATE_CHANNELS = [
    {"channel": "messages", "type": "List[BaseMessage]", "description": "Conversation history with role annotations"},
    {"channel": "trip_context", "type": "Dict[str, Any]", "description": "Origin, destination, dates, traveler count, currency"},
    {"channel": "flight_offers", "type": "List[FlightOffer]", "description": "Outbound and return flight pairing results"},
    {"channel": "hotel_offers", "type": "List[HotelOffer]", "description": "Verified lodging candidates and nightly rates"},
    {"channel": "local_guide_info", "type": "Dict[str, Any]", "description": "Ground cab apps, rental rates, and delivery services"},
    {"channel": "itinerary_days", "type": "List[DaySchedule]", "description": "Structured day-by-day activities and locations"},
    {"channel": "budget_breakdown", "type": "BudgetSummary", "description": "Deterministic line items, totals, and per-person split"},
    {"channel": "feasibility_report", "type": "FeasibilityResult", "description": "Pacing rating, warnings, and weather assessment"},
]


class AgentMeshManager:
    """In-memory manager for the agent mesh configuration and demo engine."""

    def __init__(self):
        self._agents: Dict[str, AgentNodeConfig] = {k: v.model_copy() for k, v in DEFAULT_AGENTS.items()}

    def get_agents(self) -> List[Dict[str, Any]]:
        return [agent.model_dump() for agent in self._agents.values()]

    def get_agent(self, agent_id: str) -> Optional[AgentNodeConfig]:
        return self._agents.get(agent_id)

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        if "enabled" in updates:
            agent.enabled = bool(updates["enabled"])
            agent.status = "idle" if agent.enabled else "disabled"
        if "model" in updates and updates["model"]:
            agent.model = str(updates["model"])
        if "temperature" in updates:
            agent.temperature = max(0.0, min(1.0, float(updates["temperature"])))
        if "max_retries" in updates:
            agent.max_retries = max(1, int(updates["max_retries"]))
        return agent.model_dump()

    def get_topology(self) -> Dict[str, Any]:
        nodes = []
        # Add Start node
        nodes.append({
            "id": "__start__",
            "name": "User Query Start",
            "role": "Entrypoint",
            "icon": "🚀",
            "color": "#9aa0a6",
            "badge": "Input",
            "status": "active",
            "tools": [],
            "description": "User intent ingested via HTTP/WebSocket streaming endpoint."
        })
        for agent in self._agents.values():
            nodes.append(agent.model_dump())
        # Add End node
        nodes.append({
            "id": "__end__",
            "name": "User Response / Delivery",
            "role": "Output Stream",
            "icon": "✨",
            "color": "#e8eaed",
            "badge": "Output",
            "status": "idle",
            "tools": [],
            "description": "Rendered day timeline, Aviasales booking buttons, budget tables, and local app advisory."
        })

        edges = [edge.model_dump() for edge in GRAPH_EDGES]
        return {
            "nodes": nodes,
            "edges": edges,
            "state_channels": STATE_CHANNELS,
            "total_agents": len(self._agents),
            "active_agents": sum(1 for a in self._agents.values() if a.enabled),
        }

    def get_demo_scenarios(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "goa_4day",
                "title": "🏖️ 4-Day Goa Beach & Heritage (Delhi Departure)",
                "description": "Round-trip flights (DEL ⇄ GOI), scooter rental & GoaMiles advisory, 4-day timeline, and ₹24,500 deterministic budget.",
                "destination": "Goa",
                "origin": "DEL",
                "days": 4,
                "travelers": 2,
                "currency": "INR",
            },
            {
                "id": "dubai_luxury",
                "title": "🏙️ 5-Day Dubai International Luxury & Desert",
                "description": "Round-trip flight booking, 5-star hotel options, Careem app guidance, and AED/₹ currency conversion.",
                "destination": "Dubai",
                "origin": "BOM",
                "days": 5,
                "travelers": 2,
                "currency": "INR",
            },
            {
                "id": "manali_mountains",
                "title": "⛰️ 3-Day Manali Scenic Mountain Retreat",
                "description": "Weather checks, mountain driving feasibility check, local taxi union rates, and cozy stays under ₹18,000.",
                "destination": "Manali",
                "origin": "DEL",
                "days": 3,
                "travelers": 2,
                "currency": "INR",
            },
        ]

    def build_simulation_trace(self, scenario_id: str = "goa_4day") -> List[Dict[str, Any]]:
        """Constructs a rich step-by-step trace showing the LangGraph state machine execution."""
        if scenario_id == "manali_mountains":
            return [
                {
                    "step": 1,
                    "agent_id": "supervisor",
                    "action": "Intake & Intent Decomposition",
                    "detail": "Identified destination 'Manali', 3 days, from Delhi. Dispatched weather verification and route feasibility.",
                    "state_update": {"destination": "Manali", "duration": 3, "travelers": 2},
                    "node_status": {"supervisor": "active"},
                    "active_edge": {"from": "__start__", "to": "supervisor"},
                },
                {
                    "step": 2,
                    "agent_id": "feasibility_validator",
                    "action": "Weather & Mountain Road Feasibility",
                    "detail": "Tool `get_forecast('Manali')`: 12°C clear. Evaluated Delhi-Manali 12hr transit time. Flagged overnight Volvo bus or Bhuntar flight.",
                    "state_update": {"weather": "12°C Sunny", "feasibility": "Valid with overnight transit"},
                    "node_status": {"feasibility_validator": "active"},
                    "active_edge": {"from": "supervisor", "to": "feasibility_validator"},
                },
                {
                    "step": 3,
                    "agent_id": "local_guide_specialist",
                    "action": "Himachal Ground Transit Advisory",
                    "detail": "Tool `get_destination_local_guide('Manali')`: Taxi Union fixed rates for Rohtang/Solang. Auto-rickshaws in town. Food: Zomato limited.",
                    "state_update": {"local_guide": "Manali Taxi Union rates apply; 4x4 recommended for Solang"},
                    "node_status": {"local_guide_specialist": "active"},
                    "active_edge": {"from": "supervisor", "to": "local_guide_specialist"},
                },
                {
                    "step": 4,
                    "agent_id": "hotel_specialist",
                    "action": "Mountain Stays Selection",
                    "detail": "Tool `search_hotels('Manali', min_rating=4.2)`: Found 3 boutique river cottages (₹3,200/night).",
                    "state_update": {"lodging": "River View Cottages (₹6,400 for 2 nights)"},
                    "node_status": {"hotel_specialist": "active"},
                    "active_edge": {"from": "supervisor", "to": "hotel_specialist"},
                },
                {
                    "step": 5,
                    "agent_id": "itinerary_builder",
                    "action": "3-Day Mountain Itinerary Assembly",
                    "detail": "Tool `build_day_by_day_itinerary`: Day 1 Old Manali & Hadimba; Day 2 Solang Valley; Day 3 Naggar Castle & cafes.",
                    "state_update": {"itinerary_days_count": 3},
                    "node_status": {"itinerary_builder": "active"},
                    "active_edge": {"from": "hotel_specialist", "to": "itinerary_builder"},
                },
                {
                    "step": 6,
                    "agent_id": "budget_auditor",
                    "action": "Deterministic Budget Calculation",
                    "detail": "Tool `calculate_trip_budget`: Transit ₹4,800 + Hotels ₹6,400 + Activities ₹3,500 + Contingency ₹1,500 = ₹16,200 total (₹8,100/person).",
                    "state_update": {"total_cost": 16200, "per_person": 8100, "status": "Within Target"},
                    "node_status": {"budget_auditor": "active"},
                    "active_edge": {"from": "itinerary_builder", "to": "budget_auditor"},
                },
                {
                    "step": 7,
                    "agent_id": "supervisor",
                    "action": "Synthesize & Deliver Final Package",
                    "detail": "Synthesizes timeline cards, hotel booking links, Taxi Union guidelines, and cost breakdown.",
                    "state_update": {"complete": True},
                    "node_status": {"supervisor": "completed", "__end__": "active"},
                    "active_edge": {"from": "supervisor", "to": "__end__"},
                },
            ]

        # Default: goa_4day
        return [
            {
                "step": 1,
                "agent_id": "supervisor",
                "action": "Intent Analysis & Task Graph Decomposition",
                "detail": "User requested '4-Day Goa trip from Delhi for 2 travelers'. Supervisor creates tasks: Flight Search (DEL ⇄ GOI), Hotel Matching, Local Cab Guide, Day Scheduling, and Budgeting.",
                "state_update": {"origin": "DEL", "destination": "GOI", "pax": 2, "days": 4},
                "node_status": {"supervisor": "active"},
                "active_edge": {"from": "__start__", "to": "supervisor"},
            },
            {
                "step": 2,
                "agent_id": "flight_specialist",
                "action": "Live Round-Trip Flight Search",
                "detail": "Tool `search_flights(origin='DEL', destination='GOI', departure_date='2026-11-20', return_date='2026-11-24', passengers=2)`. Generated round-trip Aviasales slug DEL2011GOI24112. Best pairing: IndiGo 6E-205 / Air India AI-850 at ₹11,200 for 2 travelers.",
                "state_update": {"flights_found": 3, "best_fare": "₹11,200 (Round-trip, 2 pax)"},
                "node_status": {"flight_specialist": "active"},
                "active_edge": {"from": "supervisor", "to": "flight_specialist"},
            },
            {
                "step": 3,
                "agent_id": "hotel_specialist",
                "action": "Verified Stays & Resort Discovery",
                "detail": "Tool `search_hotels(city='Goa', check_in='2026-11-20', check_out='2026-11-24')`. Found Candolim Beach Resort (₹4,200/night, 4.4★) and Baga Boutique Inn (₹2,800/night, 4.2★).",
                "state_update": {"hotels_found": 4, "selected_hotel": "Candolim Beach Resort (₹12,600 / 3 nights)"},
                "node_status": {"hotel_specialist": "active"},
                "active_edge": {"from": "supervisor", "to": "hotel_specialist"},
            },
            {
                "step": 4,
                "agent_id": "local_guide_specialist",
                "action": "Goa Ground Transit & Taxi Union Intelligence",
                "detail": "Tool `get_destination_local_guide('Goa')`. Extracted crucial local rules: Uber/Ola face severe taxi union restrictions. Recommendation: Rent Honda Activa scooter (₹350-₹500/day) or use GoaMiles government app. Food apps: Zomato & Swiggy active in North Goa.",
                "state_update": {"local_transit": "Scooter rental (₹400/day) + GoaMiles app for airport pickup"},
                "node_status": {"local_guide_specialist": "active"},
                "active_edge": {"from": "supervisor", "to": "local_guide_specialist"},
            },
            {
                "step": 5,
                "agent_id": "itinerary_builder",
                "action": "Day-by-Day Timeline Creation",
                "detail": "Tool `build_day_by_day_itinerary`. Generated 4 days: Day 1 North Beach Chill & Curlies Sunset; Day 2 Aguada Fort & Watersports; Day 3 Old Goa Churches & Fontainhas Latin Quarter; Day 4 Anjuna Flea Market & Return flight.",
                "state_update": {"itinerary_days": 4, "activities_count": 12},
                "node_status": {"itinerary_builder": "active"},
                "active_edge": {"from": "flight_specialist", "to": "itinerary_builder"},
            },
            {
                "step": 6,
                "agent_id": "feasibility_validator",
                "action": "Pacing & Geographic Proximity Validation",
                "detail": "Tool `validate_itinerary_feasibility`. Analyzed transit times: Day 2 North Goa (15 mins between stops); Day 3 South/Central (45 mins drive). Pacing: Moderate (Well balanced, no travel burnout detected).",
                "state_update": {"feasibility": "Validated 100% realistic pacing"},
                "node_status": {"feasibility_validator": "active"},
                "active_edge": {"from": "itinerary_builder", "to": "feasibility_validator"},
            },
            {
                "step": 7,
                "agent_id": "budget_auditor",
                "action": "Deterministic Budget Arithmetic (Zero LLM Math Error)",
                "detail": "Tool `calculate_trip_budget`. Exact items: Flights ₹11,200 + Lodging ₹12,600 + Scooter rental ₹1,600 + Meals & Activities ₹8,000 + Contingency (10%) ₹3,340 = Total ₹36,740 (₹18,370 per person).",
                "state_update": {"total_cost": 36740, "per_person": 18370, "contingency": 3340},
                "node_status": {"budget_auditor": "active"},
                "active_edge": {"from": "feasibility_validator", "to": "budget_auditor"},
            },
            {
                "step": 8,
                "agent_id": "supervisor",
                "action": "Final Response Synthesis & UI Broadcast",
                "detail": "Synchronized all state channels: renders timeline in Itinerary Tab, flight cards with Aviasales links in Flights Tab, deterministic breakdown in Budget Tab, and delivers structured advice in Chat.",
                "state_update": {"pipeline_status": "Complete", "execution_time_ms": 1420},
                "node_status": {"supervisor": "completed", "__end__": "active"},
                "active_edge": {"from": "supervisor", "to": "__end__"},
            },
        ]


# Singleton instance
mesh_manager = AgentMeshManager()
