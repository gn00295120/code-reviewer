"""Celery task: run the physics simulation loop.

Flow:
    1. Load WorldModel from DB (sync SQLAlchemy).
    2. Initialise MuJoCo model via mujoco_service.
    3. For each step:
       a. Get observation from MuJoCo.
       b. Run physics_pipeline (LangGraph: observe → reason → act).
       c. Apply action back to MuJoCo.
       d. Persist PhysicsEvent to DB.
       e. Publish WebSocket event via Redis.
    4. Update WorldModel.status / total_steps / total_cost_usd.
"""

from __future__ import annotations

import json
import uuid as uuid_mod
from datetime import datetime
from decimal import Decimal

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.config import get_settings
from app.core.models import PhysicsEvent, WorldModel
from app.services import mujoco_service
from agents.physics_pipeline import run_physics_step

settings = get_settings()

# Sync engine for Celery
_sync_engine = create_engine(settings.database_url_sync)
_redis_client = redis.from_url(settings.redis_url, decode_responses=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _publish(model_id: str, event: str, data: dict) -> None:
    payload = json.dumps({
        "room": f"world_model:{model_id}",
        "event": event,
        "data": data,
    })
    _redis_client.publish("ws:events", payload)


def _get_model(db: Session, model_id: str) -> WorldModel | None:
    return db.query(WorldModel).filter(
        WorldModel.id == uuid_mod.UUID(model_id)
    ).first()


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, name="simulation.run", max_retries=1)
def run_simulation_task(
    self,
    model_id: str,
    max_steps: int = 100,
) -> dict:
    """Run the full simulation loop for *max_steps* steps."""
    with Session(_sync_engine) as db:
        wm = _get_model(db, model_id)
        if not wm:
            return {"error": "WorldModel not found"}

        if wm.status not in ("idle", "paused"):
            return {"error": f"Cannot start from status={wm.status}"}

        # Load MuJoCo model
        model_data = mujoco_service.load_model(wm.mujoco_xml)
        n_actuators = model_data.info.n_actuators

        # Mark as running
        wm.status = "running"
        db.commit()

        _publish(model_id, "simulation:started", {
            "model_id": model_id,
            "max_steps": max_steps,
            "n_actuators": n_actuators,
            "model_info": model_data.info.to_dict(),
        })

        total_cost: float = float(wm.total_cost_usd or 0)
        completed_steps = int(wm.total_steps or 0)

        try:
            for _ in range(max_steps):
                # Re-check status from DB (allows pause/cancel from API)
                db.refresh(wm)
                if wm.status != "running":
                    break

                step_index = completed_steps

                # 1. Get observation
                observation = mujoco_service.get_state(model_data)

                # 2. Run LangGraph pipeline (observe → reason → act)
                step_result = run_physics_step(
                    model_id=model_id,
                    observation=observation,
                    n_actuators=n_actuators,
                    agent_config=wm.agent_config or {},
                    step_count=step_index,
                    total_cost=total_cost,
                )

                action = step_result["action"]
                reasoning = step_result["reasoning"]
                reward = step_result["reward"]
                tokens_used = step_result["tokens_used"]
                step_cost = step_result["step_cost_usd"]
                total_cost = step_result["total_cost"]

                # 3. Apply action → advance physics
                new_observation = mujoco_service.step(model_data, action)

                # 4. Persist event
                event = PhysicsEvent(
                    model_id=wm.id,
                    step=step_index,
                    action=action,
                    observation=new_observation,
                    reward=reward,
                    agent_reasoning=reasoning,
                    tokens_used=tokens_used,
                    cost_usd=Decimal(str(round(step_cost, 6))),
                    timestamp=datetime.utcnow(),
                )
                db.add(event)

                completed_steps += 1
                wm.total_steps = completed_steps
                wm.total_cost_usd = Decimal(str(round(total_cost, 6)))
                wm.current_state = new_observation
                db.commit()

                # 5. Publish WS event
                _publish(model_id, "simulation:step", {
                    "step": step_index,
                    "observation": new_observation,
                    "action": action,
                    "reward": reward,
                    "reasoning": reasoning,
                    "cost_usd": step_cost,
                    "total_cost_usd": total_cost,
                })

            # Finalise
            db.refresh(wm)
            if wm.status == "running":
                wm.status = "completed"
            db.commit()

            _publish(model_id, "simulation:completed", {
                "model_id": model_id,
                "total_steps": completed_steps,
                "total_cost_usd": total_cost,
                "final_status": wm.status,
            })

            return {
                "status": wm.status,
                "total_steps": completed_steps,
                "total_cost_usd": total_cost,
            }

        except Exception as exc:
            db.refresh(wm)
            wm.status = "error"
            db.commit()

            _publish(model_id, "simulation:error", {
                "model_id": model_id,
                "error": str(exc),
            })

            raise self.retry(exc=exc, countdown=10, max_retries=0)


@celery_app.task(name="simulation.step_once")
def step_once_task(model_id: str, action: dict | None = None) -> dict:
    """Execute a single manual step with an optional explicit action dict."""
    with Session(_sync_engine) as db:
        wm = _get_model(db, model_id)
        if not wm:
            return {"error": "WorldModel not found"}

        if wm.status not in ("idle", "paused", "running"):
            return {"error": f"Cannot step from status={wm.status}"}

        model_data = mujoco_service.load_model(wm.mujoco_xml)

        # Restore state from DB if available
        if wm.current_state:
            # For the mock service the state is self-contained; for real MuJoCo
            # we would set qpos/qvel here.  Leave as-is for now.
            pass

        observation = mujoco_service.get_state(model_data)
        step_index = int(wm.total_steps or 0)
        total_cost = float(wm.total_cost_usd or 0)

        if action is None:
            # Let the agent decide
            step_result = run_physics_step(
                model_id=model_id,
                observation=observation,
                n_actuators=model_data.info.n_actuators,
                agent_config=wm.agent_config or {},
                step_count=step_index,
                total_cost=total_cost,
            )
            action = step_result["action"]
            reasoning = step_result["reasoning"]
            reward = step_result["reward"]
            tokens_used = step_result["tokens_used"]
            step_cost = step_result["step_cost_usd"]
            total_cost = step_result["total_cost"]
        else:
            reasoning = "manual"
            reward = 0.0
            tokens_used = 0
            step_cost = 0.0

        new_observation = mujoco_service.step(model_data, action)

        event = PhysicsEvent(
            model_id=wm.id,
            step=step_index,
            action=action,
            observation=new_observation,
            reward=reward,
            agent_reasoning=reasoning,
            tokens_used=tokens_used,
            cost_usd=Decimal(str(round(step_cost, 6))),
            timestamp=datetime.utcnow(),
        )
        db.add(event)

        wm.total_steps = step_index + 1
        wm.total_cost_usd = Decimal(str(round(total_cost, 6)))
        wm.current_state = new_observation
        db.commit()

        _publish(model_id, "simulation:step", {
            "step": step_index,
            "observation": new_observation,
            "action": action,
            "reward": reward,
            "reasoning": reasoning,
            "cost_usd": step_cost,
        })

        return {
            "step": step_index,
            "observation": new_observation,
            "action": action,
            "reward": reward,
            "reasoning": reasoning,
            "tokens_used": tokens_used,
            "cost_usd": step_cost,
        }
