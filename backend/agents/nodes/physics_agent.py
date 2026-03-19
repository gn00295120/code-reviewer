"""LangGraph node: physics agent.

Receives an observation (IMU, camera, force feedback) and calls the LLM to
reason about the next action (joint torques / velocities).  Returns the action
command and tracks token cost.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.core.config import get_settings
from app.services.litellm_service import call_llm

settings = get_settings()

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

PHYSICS_AGENT_SYSTEM_PROMPT = """You are a physics-based robot controller.
You receive sensor observations from a simulated robot (joint positions,
velocities, IMU data, force/torque readings) and must output the next control
action.

Your response MUST be valid JSON with this exact structure:
{
  "reasoning": "<brief explanation of your decision>",
  "ctrl": [<float>, ...]   // one value per actuator, typically in [-1, 1]
}

Guidelines:
- Use smooth, incremental control signals to avoid instability.
- Prefer small corrections rather than large sudden moves.
- If the robot appears to be in a stable state, output near-zero ctrl values.
- Base your reasoning on the physics state, not on assumptions.
"""

# ---------------------------------------------------------------------------
# Helper: build observation prompt
# ---------------------------------------------------------------------------


def _format_observation(observation: dict[str, Any], n_actuators: int) -> str:
    lines = ["Current observation:"]
    if "qpos" in observation:
        lines.append(f"  joint positions (qpos): {observation['qpos']}")
    if "qvel" in observation:
        lines.append(f"  joint velocities (qvel): {observation['qvel']}")
    if "imu_acc" in observation:
        lines.append(f"  IMU acceleration: {observation['imu_acc']}")
    if "imu_gyro" in observation:
        lines.append(f"  IMU gyroscope: {observation['imu_gyro']}")
    if "force_torque" in observation:
        lines.append(f"  force/torque sensor: {observation['force_torque']}")
    if "contact_forces" in observation:
        lines.append(f"  contact forces: {observation['contact_forces']}")
    lines.append(f"  simulation time: {observation.get('time', 0):.4f}s")
    lines.append(f"  simulation step: {observation.get('step', 0)}")
    lines.append(f"\nExpected ctrl length: {n_actuators}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LangGraph node function
# ---------------------------------------------------------------------------


def physics_agent_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node: observe → reason → act.

    Expected state keys:
        observation   (dict)  – sensor data from MuJoCo service
        n_actuators   (int)   – number of actuators in the model
        agent_config  (dict)  – optional overrides (model, temperature)
        step_count    (int)   – current simulation step
        total_cost    (float) – accumulated cost so far

    Returns updates for:
        action        (dict)  – {"ctrl": [...]}
        reasoning     (str)   – LLM chain-of-thought
        tokens_used   (int)   – tokens for this step
        step_cost_usd (float) – cost for this step
        total_cost    (float) – cumulative cost
    """
    observation: dict[str, Any] = state.get("observation", {})
    n_actuators: int = state.get("n_actuators", 1)
    agent_config: dict[str, Any] = state.get("agent_config", {})

    model = agent_config.get("model", settings.default_model)
    temperature = float(agent_config.get("temperature", 0.0))
    max_tokens = int(agent_config.get("max_tokens", 512))

    messages = [
        {"role": "system", "content": PHYSICS_AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _format_observation(observation, n_actuators),
        },
    ]

    # Run async call_llm in synchronous Celery context
    loop = asyncio.new_event_loop()
    try:
        llm_response = loop.run_until_complete(
            call_llm(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        )
    finally:
        loop.close()

    # Parse LLM output
    try:
        parsed = json.loads(llm_response.content)
        reasoning: str = parsed.get("reasoning", "")
        ctrl: list[float] = parsed.get("ctrl", [0.0] * n_actuators)
        # Clamp ctrl to [-1, 1] and ensure correct length
        ctrl = [max(-1.0, min(1.0, float(v))) for v in ctrl]
        while len(ctrl) < n_actuators:
            ctrl.append(0.0)
        ctrl = ctrl[:n_actuators]
    except (json.JSONDecodeError, ValueError):
        reasoning = llm_response.content
        ctrl = [0.0] * n_actuators

    action = {"ctrl": ctrl}
    prev_cost: float = float(state.get("total_cost", 0.0))

    return {
        "action": action,
        "reasoning": reasoning,
        "tokens_used": llm_response.total_tokens,
        "step_cost_usd": llm_response.cost_usd,
        "total_cost": prev_cost + llm_response.cost_usd,
    }
