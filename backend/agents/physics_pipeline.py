"""LangGraph physics pipeline: observe → reason → act → loop.

This graph drives a single simulation step.  The Celery task calls
``run_physics_step`` in a loop for the full simulation.

Graph structure:
    [observe] → [reason] → [act] → END

State (WorldModelState) carries everything needed to persist results after
each step.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph

from agents.nodes.physics_agent import physics_agent_node
from app.services import mujoco_service


# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------


class WorldModelState(TypedDict):
    """Shared state across physics pipeline nodes."""

    # Simulation identity
    model_id: str
    n_actuators: int
    agent_config: dict[str, Any]

    # Per-step data
    observation: dict[str, Any]
    action: dict[str, Any]
    reasoning: str
    reward: float

    # Cost tracking (accumulated via reducer so parallel nodes add correctly)
    tokens_used: Annotated[int, operator.add]
    step_cost_usd: Annotated[float, operator.add]
    total_cost: float

    # Control
    step_count: int
    error: str | None


# ---------------------------------------------------------------------------
# Node: observe
# ---------------------------------------------------------------------------


def observe_node(state: WorldModelState) -> dict[str, Any]:
    """Collect current observation from the MuJoCo service handle.

    In the pipeline the actual ModelData handle is created outside (in the
    Celery task) and the observation is injected into state before invoking
    the graph.  This node is therefore a pass-through that validates the
    observation field exists.
    """
    observation = state.get("observation", {})
    if not observation:
        # Fallback: return a zeroed observation (should not happen in normal flow)
        n_joints = state.get("n_actuators", 1)
        observation = {
            "qpos": [0.0] * n_joints,
            "qvel": [0.0] * n_joints,
            "time": 0.0,
            "step": state.get("step_count", 0),
        }
    return {"observation": observation}


# ---------------------------------------------------------------------------
# Node: act
# ---------------------------------------------------------------------------


def act_node(state: WorldModelState) -> dict[str, Any]:
    """Apply the chosen action and compute the reward signal.

    The actual physics step is executed by the Celery task (which holds the
    ModelData handle).  This node computes a simple reward heuristic so the
    graph result carries a meaningful scalar.
    """
    action = state.get("action", {"ctrl": [0.0] * state.get("n_actuators", 1)})
    obs = state.get("observation", {})

    # Reward heuristic: penalise high velocities and large control effort.
    qvel = obs.get("qvel", [])
    ctrl = action.get("ctrl", [])
    velocity_penalty = sum(v ** 2 for v in qvel)
    effort_penalty = sum(u ** 2 for u in ctrl)
    reward = float(-0.01 * velocity_penalty - 0.001 * effort_penalty)

    return {
        "action": action,
        "reward": reward,
        "step_count": state.get("step_count", 0) + 1,
    }


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def _build_physics_graph():
    graph = StateGraph(WorldModelState)

    graph.add_node("observe", observe_node)
    graph.add_node("reason", physics_agent_node)
    graph.add_node("act", act_node)

    graph.set_entry_point("observe")
    graph.add_edge("observe", "reason")
    graph.add_edge("reason", "act")
    graph.add_edge("act", END)

    return graph.compile()


# Singleton compiled graph
physics_graph = _build_physics_graph()


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------


def run_physics_step(
    model_id: str,
    observation: dict[str, Any],
    n_actuators: int,
    agent_config: dict[str, Any],
    step_count: int,
    total_cost: float,
) -> dict[str, Any]:
    """Execute one observe-reason-act cycle and return the result dict.

    Returns a dict with keys:
        action, reasoning, reward, tokens_used, step_cost_usd, total_cost
    """
    initial_state: WorldModelState = {
        "model_id": model_id,
        "n_actuators": n_actuators,
        "agent_config": agent_config,
        "observation": observation,
        "action": {},
        "reasoning": "",
        "reward": 0.0,
        "tokens_used": 0,
        "step_cost_usd": 0.0,
        "total_cost": total_cost,
        "step_count": step_count,
        "error": None,
    }

    result = physics_graph.invoke(initial_state)

    return {
        "action": result.get("action", {}),
        "reasoning": result.get("reasoning", ""),
        "reward": result.get("reward", 0.0),
        "tokens_used": result.get("tokens_used", 0),
        "step_cost_usd": result.get("step_cost_usd", 0.0),
        "total_cost": result.get("total_cost", total_cost),
    }
