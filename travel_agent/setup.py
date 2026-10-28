"""Shared agent-construction helpers used by cli.py and web_server.py."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from .agent.llm import LLMProvider, get_llm_provider
from .agent.orchestrator import AgentOrchestrator
from .config import Config
from .mcp.mcp_server import MCPServer
from .tools import (
    book_flight,
    build_day_by_day_itinerary,
    calculate_trip_budget,
    create_payment_session,
    estimate_standard_budget,
    get_current_datetime,
    get_destination_local_guide,
    get_forecast,
    get_payment_status,
    get_saved_trip,
    list_user_trips,
    rent_car,
    save_planned_trip,
    search_flights,
    search_hotels,
    validate_itinerary_feasibility,
)

logger = logging.getLogger(__name__)


def select_provider() -> Optional[Tuple[str, str]]:
    """Return (provider_name, api_key) from Config, preferring Config.LLM_PROVIDER."""
    candidates = {
        "anthropic": Config.ANTHROPIC_API_KEY,
        "openai": Config.OPENAI_API_KEY,
        "google": Config.GOOGLE_API_KEY,
    }
    preferred = Config.LLM_PROVIDER
    if candidates.get(preferred):
        return preferred, candidates[preferred]
    for name, key in candidates.items():
        if key:
            return name, key
    return None


def build_mcp_server() -> MCPServer:
    """A new MCPServer with all production tools registered (in-process only).

    Subprocess MCP servers (Google Maps, etc.) are wired in async at startup;
    call ``attach_external_mcp_servers`` from the app's lifespan hook.
    """
    server = MCPServer()
    for tool in (
        search_flights,
        book_flight,
        search_hotels,
        rent_car,
        get_forecast,
        calculate_trip_budget,
        estimate_standard_budget,
        validate_itinerary_feasibility,
        build_day_by_day_itinerary,
        get_destination_local_guide,
        save_planned_trip,
        get_saved_trip,
        list_user_trips,
        create_payment_session,
        get_payment_status,
        get_current_datetime,
    ):
        server.register_tool(tool)
    return server


async def attach_external_mcp_servers(server: MCPServer) -> None:
    """Spawn any optional MCP subprocesses whose keys are configured.

    Failures are logged but never raised — the in-process tools must still
    work even if a subprocess won't start (missing binary, bad key, etc.).
    """
    if Config.GOOGLE_MAPS_API_KEY:
        try:
            await server.register_mcp_subprocess(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-google-maps"],
                env={"GOOGLE_MAPS_API_KEY": Config.GOOGLE_MAPS_API_KEY},
                label="google-maps",
            )
        except Exception:
            logger.exception("Failed to start Google Maps MCP subprocess; continuing without it")
    else:
        logger.info("GOOGLE_MAPS_API_KEY not set; Google Maps MCP subprocess skipped")


def build_llm() -> Optional[LLMProvider]:
    """Construct an LLM provider from Config. Returns None if none configured."""
    selection = select_provider()
    if selection is None:
        logger.warning("No LLM API key configured")
        return None
    provider_name, api_key = selection
    try:
        llm = get_llm_provider(provider_name, api_key)
    except ImportError as e:
        logger.error("LLM provider %s not installed: %s", provider_name, e)
        return None
    logger.info("LLM provider built: %s", provider_name)
    return llm


def build_agent() -> Optional[AgentOrchestrator]:
    """Top-level: build a full AgentOrchestrator using Config. Returns None on failure."""
    llm = build_llm()
    if llm is None:
        return None
    return AgentOrchestrator(llm, build_mcp_server())
