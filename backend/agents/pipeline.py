"""LangGraph review pipeline: fan-out to 5 agents, fan-in to supervisor."""

from dataclasses import asdict
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from agents.state import ReviewState
from agents.nodes.fetch_diff import fetch_diff_node
from agents.nodes.review_agents import (
    logic_node,
    security_node,
    edge_case_node,
    convention_node,
    performance_node,
)
from agents.nodes.supervisor import supervisor_node

AGENT_NODES = ["logic", "security", "edge_case", "convention", "performance"]


def route_to_agents(state: ReviewState) -> list[Send]:
    """Fan-out: send state to all 5 review agents in parallel."""
    return [Send(agent, state) for agent in AGENT_NODES]


def build_review_graph():
    """Build the LangGraph review pipeline with proper fan-out/fan-in."""
    graph = StateGraph(ReviewState)

    # Add nodes
    graph.add_node("fetch_diff", fetch_diff_node)
    graph.add_node("logic", logic_node)
    graph.add_node("security", security_node)
    graph.add_node("edge_case", edge_case_node)
    graph.add_node("convention", convention_node)
    graph.add_node("performance", performance_node)
    graph.add_node("supervisor", supervisor_node)

    # Entry → fetch_diff
    graph.set_entry_point("fetch_diff")

    # Fan-out: fetch_diff → all 5 agents via conditional edges (Send API)
    graph.add_conditional_edges("fetch_diff", route_to_agents, AGENT_NODES)

    # Fan-in: all 5 agents → supervisor
    for agent in AGENT_NODES:
        graph.add_edge(agent, "supervisor")

    # Supervisor → END
    graph.add_edge("supervisor", END)

    return graph.compile()


# Compiled graph (singleton)
review_graph = build_review_graph()


def run_review_pipeline(review_id: str, pr_diff) -> dict:
    """Execute the review pipeline synchronously (for Celery)."""
    # Serialize PRDiff to dict
    if hasattr(pr_diff, "__dataclass_fields__"):
        pr_diff_dict = asdict(pr_diff)
        files = [asdict(f) for f in pr_diff.files]
    else:
        pr_diff_dict = pr_diff
        files = pr_diff.get("files", [])

    initial_state = {
        "review_id": review_id,
        "pr_diff": pr_diff_dict,
        "files": files,
        "findings": [],
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "deduplicated_findings": [],
        "summary": "",
        "severity_counts": {},
        "error": None,
    }

    result = review_graph.invoke(initial_state)

    # Use deduplicated_findings from supervisor (not the raw accumulated findings)
    return {
        "findings": result.get("deduplicated_findings", result.get("findings", [])),
        "summary": result.get("summary", ""),
        "severity_counts": result.get("severity_counts", {}),
        "total_tokens": result.get("total_tokens", 0),
        "total_cost_usd": result.get("total_cost_usd", 0.0),
    }
