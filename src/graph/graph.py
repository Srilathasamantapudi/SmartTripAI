"""Wires the agents together into the LangGraph workflow."""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from src.agents.final_agent import final_agent
from src.agents.flight_agent import flight_agent
from src.agents.hotel_agent import hotel_agent
from src.agents.itinerary_agent import itinerary_agent
from src.agents.weather_agent import weather_agent
from src.clients.checkpointer import get_checkpointer
<<<<<<< HEAD
from src.config import settings
=======
>>>>>>> 6139a41007e8ebd425a8fc868f356828dfc9dfcf
from src.config.session import require, resolve_database_url
from src.graph.state import TravelState


def build_graph() -> StateGraph:
    """Build the uncompiled graph. Useful for tests and for visualisation."""

    graph = StateGraph(TravelState)

    graph.add_node("flight_agent", flight_agent)
    graph.add_node("hotel_agent", hotel_agent)
    graph.add_node("weather_agent", weather_agent)
    graph.add_node("itinerary_agent", itinerary_agent)
    graph.add_node("final_agent", final_agent)

    graph.add_edge(START, "flight_agent")
    graph.add_edge("flight_agent", "hotel_agent")
    graph.add_edge("hotel_agent", "weather_agent")
    graph.add_edge("weather_agent", "itinerary_agent")
    graph.add_edge("itinerary_agent", "final_agent")
    graph.add_edge("final_agent", END)

    return graph


@lru_cache(maxsize=4)
def _compiled_graph(database_url: str):
    return build_graph().compile(checkpointer=get_checkpointer(database_url))


def get_travel_graph():
    """
    Compile the graph against whichever database the current session
    resolves to. One compiled graph is cached per distinct URL.
    """

    require("DATABASE_URL")

<<<<<<< HEAD
    url = resolve_database_url()
    try:
        return _compiled_graph(url)
    except Exception as error:
        # Fall back to server .env DATABASE_URL if session URL fails (e.g. bad credentials in cookie)
        env_url = settings.normalize_database_url(settings.DATABASE_URL) if settings.DATABASE_URL else None
        if env_url and env_url != url:
            try:
                return _compiled_graph(env_url)
            except Exception:
                pass
        raise error
=======
    return _compiled_graph(resolve_database_url())
>>>>>>> 6139a41007e8ebd425a8fc868f356828dfc9dfcf
