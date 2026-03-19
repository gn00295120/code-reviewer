"""TDD tests for the World Model Sandbox module.

Tests cover:
  - Pydantic schemas (validation)
  - MuJoCo mock service (load, step, reset, render, get_state)
  - Physics pipeline (WorldModelState, run_physics_step mock)
  - API endpoints via FastAPI TestClient with mocked DB + Celery
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Schema tests (no DB, no network)
# ---------------------------------------------------------------------------


class TestWorldModelSchemas:
    """RED → GREEN for Pydantic schema validation."""

    def test_world_model_create_requires_name(self):
        from pydantic import ValidationError
        from app.schemas.world_model import WorldModelCreate

        with pytest.raises(ValidationError):
            WorldModelCreate()  # name is required

    def test_world_model_create_defaults(self):
        from app.schemas.world_model import WorldModelCreate

        obj = WorldModelCreate(name="test-model")
        assert obj.model_type == "custom"
        assert obj.agent_config == {}
        assert obj.description is None
        assert obj.mujoco_xml is None

    def test_world_model_create_full(self):
        from app.schemas.world_model import WorldModelCreate

        obj = WorldModelCreate(
            name="Crazyflie",
            description="UAV sandbox",
            model_type="crazyflie",
            mujoco_xml="<mujoco/>",
            agent_config={"model": "gpt-4", "temperature": 0.2},
        )
        assert obj.name == "Crazyflie"
        assert obj.model_type == "crazyflie"
        assert obj.agent_config["temperature"] == 0.2

    def test_world_model_create_name_max_length(self):
        from pydantic import ValidationError
        from app.schemas.world_model import WorldModelCreate

        with pytest.raises(ValidationError):
            WorldModelCreate(name="x" * 257)  # exceeds max_length=256

    def test_step_action_defaults_empty_action(self):
        from app.schemas.world_model import StepAction

        s = StepAction()
        assert s.action == {}

    def test_step_action_with_ctrl(self):
        from app.schemas.world_model import StepAction

        s = StepAction(action={"ctrl": [0.1, -0.2, 0.3]})
        assert s.action["ctrl"] == [0.1, -0.2, 0.3]

    def test_world_model_response_from_attributes(self):
        from app.schemas.world_model import WorldModelResponse
        from datetime import datetime

        mock_wm = MagicMock()
        mock_wm.id = uuid.uuid4()
        mock_wm.name = "Test"
        mock_wm.description = None
        mock_wm.model_type = "ur5"
        mock_wm.status = "idle"
        mock_wm.total_steps = 0
        mock_wm.total_cost_usd = Decimal("0.000000")
        mock_wm.current_state = {}
        mock_wm.agent_config = {}
        mock_wm.created_at = datetime.utcnow()
        mock_wm.updated_at = datetime.utcnow()

        resp = WorldModelResponse.model_validate(mock_wm)
        assert resp.name == "Test"
        assert resp.status == "idle"

    def test_physics_event_response_from_attributes(self):
        from app.schemas.world_model import PhysicsEventResponse
        from datetime import datetime

        mock_event = MagicMock()
        mock_event.id = uuid.uuid4()
        mock_event.model_id = uuid.uuid4()
        mock_event.step = 5
        mock_event.action = {"ctrl": [0.0]}
        mock_event.observation = {"qpos": [0.0]}
        mock_event.reward = -0.01
        mock_event.agent_reasoning = "stable"
        mock_event.tokens_used = 120
        mock_event.cost_usd = Decimal("0.000050")
        mock_event.timestamp = datetime.utcnow()

        resp = PhysicsEventResponse.model_validate(mock_event)
        assert resp.step == 5
        assert resp.reward == -0.01


# ---------------------------------------------------------------------------
# MuJoCo service tests (mock backend)
# ---------------------------------------------------------------------------


class TestMuJoCoServiceMock:
    """Tests for mujoco_service when MuJoCo is not installed (mock path)."""

    def test_load_model_returns_model_data(self):
        from app.services.mujoco_service import load_model, ModelData

        md = load_model(None)
        assert isinstance(md, ModelData)

    def test_load_model_with_xml_counts_joints(self):
        # Force the mock path so this test runs without a real MuJoCo model/XML.
        import app.services.mujoco_service as _svc
        from app.services.mujoco_service import _load_mock

        xml = "<mujoco><joint/><joint/><joint/></mujoco>"
        md = _load_mock(xml)
        assert md.info.n_joints == 3

    def test_get_state_returns_dict_with_qpos(self):
        from app.services.mujoco_service import load_model, get_state

        md = load_model(None)
        state = get_state(md)
        assert "qpos" in state
        assert "qvel" in state
        assert "time" in state

    def test_step_advances_step_count(self):
        from app.services.mujoco_service import load_model, step, get_state

        md = load_model(None)
        before = get_state(md)
        action = {"ctrl": [0.5] * md.info.n_actuators}
        step(md, action)
        after = get_state(md)
        assert after["step"] == before["step"] + 1

    def test_step_returns_observation(self):
        from app.services.mujoco_service import load_model, step

        md = load_model(None)
        obs = step(md, {"ctrl": [0.0] * md.info.n_actuators})
        assert isinstance(obs, dict)
        assert "qpos" in obs

    def test_reset_zeroes_state(self):
        from app.services.mujoco_service import load_model, step, reset

        md = load_model(None)
        # advance a few steps
        for _ in range(5):
            step(md, {"ctrl": [1.0] * md.info.n_actuators})

        obs = reset(md)
        assert obs["step"] == 0
        assert all(v == 0.0 for v in obs["qpos"])

    def test_get_render_data_returns_bodies(self):
        from app.services.mujoco_service import load_model, get_render_data

        md = load_model(None)
        render = get_render_data(md)
        assert "bodies" in render
        assert isinstance(render["bodies"], list)
        assert len(render["bodies"]) > 0

    def test_render_data_has_position_field(self):
        from app.services.mujoco_service import load_model, get_render_data

        md = load_model(None)
        render = get_render_data(md)
        for body in render["bodies"]:
            assert "position" in body
            assert "name" in body

    def test_model_info_to_dict(self):
        from app.services.mujoco_service import load_model

        md = load_model(None)
        d = md.info.to_dict()
        assert "n_joints" in d
        assert "n_actuators" in d
        assert "joint_names" in d
        assert "actuator_names" in d
        assert "timestep" in d

    def test_step_clamp_ctrl_handled(self):
        """Service should not raise when ctrl length mismatches n_actuators."""
        from app.services.mujoco_service import load_model, step

        md = load_model(None)
        # provide fewer ctrl values than actuators
        obs = step(md, {"ctrl": []})
        assert "qpos" in obs


# ---------------------------------------------------------------------------
# Physics pipeline state tests
# ---------------------------------------------------------------------------


class TestPhysicsPipelineState:
    """Verify WorldModelState structure and run_physics_step with mocked LLM."""

    def test_world_model_state_is_typed_dict(self):
        from agents.physics_pipeline import WorldModelState

        state: WorldModelState = {
            "model_id": "abc",
            "n_actuators": 3,
            "agent_config": {},
            "observation": {"qpos": [0.0, 0.0, 0.0]},
            "action": {},
            "reasoning": "",
            "reward": 0.0,
            "tokens_used": 0,
            "step_cost_usd": 0.0,
            "total_cost": 0.0,
            "step_count": 0,
            "error": None,
        }
        assert state["model_id"] == "abc"
        assert state["n_actuators"] == 3

    @patch("agents.nodes.physics_agent.call_llm")
    def test_run_physics_step_returns_action(self, mock_call_llm):
        """run_physics_step should return action/reasoning/reward/cost keys."""
        import asyncio
        from app.services.litellm_service import LLMResponse
        from agents.physics_pipeline import run_physics_step

        mock_response = LLMResponse(
            content='{"reasoning": "stable", "ctrl": [0.1, 0.0, -0.1]}',
            prompt_tokens=50,
            completion_tokens=30,
            total_tokens=80,
            cost_usd=0.0005,
            model="test-model",
        )

        # asyncio.coroutine was removed in Python 3.11; use a plain async def instead.
        async def fake_call(*args, **kwargs):
            return mock_response

        mock_call_llm.side_effect = fake_call

        result = run_physics_step(
            model_id="test-model-id",
            observation={"qpos": [0.0, 0.0, 0.0], "qvel": [0.0, 0.0, 0.0], "time": 0.0, "step": 0},
            n_actuators=3,
            agent_config={},
            step_count=0,
            total_cost=0.0,
        )

        assert "action" in result
        assert "reasoning" in result
        assert "reward" in result
        assert "tokens_used" in result
        assert "step_cost_usd" in result
        assert "total_cost" in result

    def test_observe_node_passthrough(self):
        from agents.physics_pipeline import observe_node

        obs = {"qpos": [1.0, 2.0], "qvel": [0.1, 0.2], "time": 0.01, "step": 5}
        state = {
            "observation": obs,
            "n_actuators": 2,
            "step_count": 5,
            "total_cost": 0.0,
        }
        result = observe_node(state)
        assert result["observation"] == obs

    def test_observe_node_fallback_when_empty(self):
        from agents.physics_pipeline import observe_node

        state = {
            "observation": {},
            "n_actuators": 4,
            "step_count": 0,
            "total_cost": 0.0,
        }
        result = observe_node(state)
        assert len(result["observation"]["qpos"]) == 4

    def test_act_node_produces_reward(self):
        from agents.physics_pipeline import act_node

        state = {
            "observation": {"qpos": [0.0], "qvel": [5.0], "time": 0.1, "step": 1},
            "action": {"ctrl": [0.5]},
            "n_actuators": 1,
            "step_count": 1,
            "total_cost": 0.0,
        }
        result = act_node(state)
        assert "reward" in result
        assert isinstance(result["reward"], float)
        assert result["reward"] <= 0.0  # penalty-based reward is always <= 0

    def test_act_node_increments_step_count(self):
        from agents.physics_pipeline import act_node

        state = {
            "observation": {},
            "action": {"ctrl": []},
            "n_actuators": 0,
            "step_count": 7,
            "total_cost": 0.0,
        }
        result = act_node(state)
        assert result["step_count"] == 8


# ---------------------------------------------------------------------------
# API endpoint tests (mocked DB and Celery)
# ---------------------------------------------------------------------------


class TestWorldModelAPI:
    """Integration-style tests for /api/world-models endpoints.

    DB interactions are mocked so these run without a real Postgres instance.
    FastAPI's dependency_overrides mechanism is used so the override is
    respected when the app resolves Depends(get_db) at request time.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fake_wm(self, **kwargs):
        """Build a fake WorldModel ORM-like object."""
        wm = MagicMock()
        wm.id = uuid.uuid4()
        wm.name = kwargs.get("name", "Test")
        wm.description = kwargs.get("description")
        wm.model_type = kwargs.get("model_type", "custom")
        wm.status = kwargs.get("status", "idle")
        wm.total_steps = 0
        wm.total_cost_usd = Decimal("0.000000")
        wm.current_state = {}
        wm.agent_config = kwargs.get("agent_config", {})
        wm.mujoco_xml = kwargs.get("mujoco_xml")
        from datetime import datetime
        wm.created_at = datetime.utcnow()
        wm.updated_at = datetime.utcnow()
        wm.events = []
        return wm

    def _make_mock_session(self, execute_result=None):
        """Return a mock async session whose execute() returns execute_result."""
        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.add = MagicMock()
        if execute_result is not None:
            mock_session.execute = AsyncMock(return_value=execute_result)
        return mock_session

    def _client_with_db(self, mock_session):
        """Return (app, TestClient) with get_db overridden to yield mock_session."""
        from app.main import app
        from app.core.database import get_db

        async def _override():
            try:
                yield mock_session
                await mock_session.commit()
            except Exception:
                await mock_session.rollback()
                raise

        app.dependency_overrides[get_db] = _override
        try:
            client = TestClient(app)
            return app, client
        finally:
            app.dependency_overrides.pop(get_db, None)

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_create_world_model_returns_201(self):
        from app.main import app
        from app.core.database import get_db
        from datetime import datetime

        mock_session = self._make_mock_session()

        # Capture the ORM object passed to session.add() so we can populate
        # the server-assigned fields (id, timestamps) that flush would normally set.
        added_objects = []

        def _capture_add(obj):
            added_objects.append(obj)

        mock_session.add = _capture_add

        async def _fake_flush():
            for obj in added_objects:
                # Always set — Column descriptors are truthy even when no value
                obj.id = uuid.uuid4()
                obj.total_steps = 0
                obj.total_cost_usd = Decimal("0.000000")
                obj.created_at = datetime.utcnow()
                obj.updated_at = datetime.utcnow()
                obj.status = getattr(obj, "_status_value", None) or "idle"

        mock_session.flush = _fake_flush

        async def _override():
            try:
                yield mock_session
                await mock_session.commit()
            except Exception:
                await mock_session.rollback()
                raise

        app.dependency_overrides[get_db] = _override
        try:
            with TestClient(app) as client:
                resp = client.post(
                    "/api/world-models",
                    json={"name": "UAV Lab", "model_type": "crazyflie"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 201

    def test_list_world_models_endpoint_exists(self):
        from app.main import app
        from app.core.database import get_db

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session = self._make_mock_session()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.scalar = AsyncMock(return_value=0)

        async def _override():
            try:
                yield mock_session
                await mock_session.commit()
            except Exception:
                await mock_session.rollback()
                raise

        app.dependency_overrides[get_db] = _override
        try:
            with TestClient(app) as client:
                resp = client.get("/api/world-models")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code != 404

    def test_get_world_model_not_found_returns_404(self):
        from app.main import app
        from app.core.database import get_db

        nonexistent_id = "00000000-0000-0000-0000-000000000099"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session = self._make_mock_session(execute_result=mock_result)

        async def _override():
            try:
                yield mock_session
                await mock_session.commit()
            except Exception:
                await mock_session.rollback()
                raise

        app.dependency_overrides[get_db] = _override
        try:
            with TestClient(app) as client:
                resp = client.get(f"/api/world-models/{nonexistent_id}")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 404

    def test_delete_world_model_not_found_returns_404(self):
        from app.main import app
        from app.core.database import get_db

        nonexistent_id = "00000000-0000-0000-0000-000000000099"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session = self._make_mock_session(execute_result=mock_result)

        async def _override():
            try:
                yield mock_session
                await mock_session.commit()
            except Exception:
                await mock_session.rollback()
                raise

        app.dependency_overrides[get_db] = _override
        try:
            with TestClient(app) as client:
                resp = client.delete(f"/api/world-models/{nonexistent_id}")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 404

    def test_pause_non_running_returns_409(self):
        from app.main import app
        from app.core.database import get_db

        model_id = str(uuid.uuid4())
        idle_wm = self._fake_wm(status="idle")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = idle_wm
        mock_session = self._make_mock_session(execute_result=mock_result)

        async def _override():
            try:
                yield mock_session
                await mock_session.commit()
            except Exception:
                await mock_session.rollback()
                raise

        app.dependency_overrides[get_db] = _override
        try:
            with TestClient(app) as client:
                resp = client.post(f"/api/world-models/{model_id}/pause")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 409

    def test_start_already_running_returns_409(self):
        from app.main import app
        from app.core.database import get_db

        model_id = str(uuid.uuid4())
        running_wm = self._fake_wm(status="running")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = running_wm
        mock_session = self._make_mock_session(execute_result=mock_result)

        async def _override():
            try:
                yield mock_session
                await mock_session.commit()
            except Exception:
                await mock_session.rollback()
                raise

        app.dependency_overrides[get_db] = _override
        try:
            with TestClient(app) as client:
                resp = client.post(f"/api/world-models/{model_id}/start")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Alembic migration sanity check
# ---------------------------------------------------------------------------


class TestAlembicMigration:
    """Verify migration file structure without running against a real DB."""

    def test_migration_file_exists(self):
        import os
        path = "/Users/longweiwang/github/code-reviewer/backend/alembic/versions/002_world_models.py"
        assert os.path.exists(path)

    def test_migration_has_correct_revision(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "migration_002",
            "/Users/longweiwang/github/code-reviewer/backend/alembic/versions/002_world_models.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.revision == "002"
        assert mod.down_revision == "001"

    def test_migration_has_upgrade_and_downgrade(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "migration_002",
            "/Users/longweiwang/github/code-reviewer/backend/alembic/versions/002_world_models.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert callable(mod.upgrade)
        assert callable(mod.downgrade)
