"""MuJoCo physics service.

This module wraps MuJoCo Python bindings.  The real implementation requires
``mujoco>=3.1.0`` to be installed and a valid MJCF XML.  When MuJoCo is not
available (CI, dev without system libs) the module falls back to a mock service
that returns structurally identical data so the rest of the stack can operate
normally.

Switching to real MuJoCo later only requires implementing the *real* helpers
below and removing the ``_MOCK`` flag (or fixing the ImportError path).
"""

from __future__ import annotations

import math
import random
import time
from typing import Any

try:
    import mujoco  # type: ignore

    _MUJOCO_AVAILABLE = True
except ImportError:
    _MUJOCO_AVAILABLE = False


# ---------------------------------------------------------------------------
# Public data-classes
# ---------------------------------------------------------------------------


class ModelInfo:
    """Metadata extracted from a parsed MJCF model."""

    def __init__(
        self,
        n_joints: int,
        n_bodies: int,
        n_actuators: int,
        joint_names: list[str],
        body_names: list[str],
        actuator_names: list[str],
        timestep: float,
    ):
        self.n_joints = n_joints
        self.n_bodies = n_bodies
        self.n_actuators = n_actuators
        self.joint_names = joint_names
        self.body_names = body_names
        self.actuator_names = actuator_names
        self.timestep = timestep

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_joints": self.n_joints,
            "n_bodies": self.n_bodies,
            "n_actuators": self.n_actuators,
            "joint_names": self.joint_names,
            "body_names": self.body_names,
            "actuator_names": self.actuator_names,
            "timestep": self.timestep,
        }


class ModelData:
    """Runtime handle wrapping MuJoCo model + data (or mock state)."""

    def __init__(self, info: ModelInfo, _mj_model=None, _mj_data=None):
        self.info = info
        self._mj_model = _mj_model
        self._mj_data = _mj_data
        # Mock internal state
        self._qpos: list[float] = [0.0] * info.n_joints
        self._qvel: list[float] = [0.0] * info.n_joints
        self._step_count: int = 0

    # ------------------------------------------------------------------
    # Convenience helpers used by the mock path
    # ------------------------------------------------------------------

    def _advance_mock(self, ctrl: list[float]) -> None:
        """Naive Euler integration for the mock (spring-damper on each DOF)."""
        dt = self.info.timestep
        for i in range(self.info.n_joints):
            u = ctrl[i] if i < len(ctrl) else 0.0
            # simple linear spring-damper: q'' = u - 2*q - 0.5*q'
            acc = u - 2.0 * self._qpos[i] - 0.5 * self._qvel[i]
            self._qvel[i] += acc * dt
            self._qpos[i] += self._qvel[i] * dt
        self._step_count += 1


# ---------------------------------------------------------------------------
# Internal helpers — real MuJoCo path
# ---------------------------------------------------------------------------


def _load_real(xml_string: str) -> ModelData:
    model = mujoco.MjModel.from_xml_string(xml_string)
    data = mujoco.MjData(model)
    info = ModelInfo(
        n_joints=model.njnt,
        n_bodies=model.nbody,
        n_actuators=model.nu,
        joint_names=[model.joint(i).name for i in range(model.njnt)],
        body_names=[model.body(i).name for i in range(model.nbody)],
        actuator_names=[model.actuator(i).name for i in range(model.nu)],
        timestep=model.opt.timestep,
    )
    return ModelData(info, _mj_model=model, _mj_data=data)


def _step_real(model_data: ModelData, action: dict[str, Any]) -> dict[str, Any]:
    ctrl = action.get("ctrl", [0.0] * model_data.info.n_actuators)
    model_data._mj_data.ctrl[:] = ctrl[: model_data.info.n_actuators]
    mujoco.mj_step(model_data._mj_model, model_data._mj_data)
    return _get_state_real(model_data)


def _get_state_real(model_data: ModelData) -> dict[str, Any]:
    d = model_data._mj_data
    return {
        "qpos": d.qpos.tolist(),
        "qvel": d.qvel.tolist(),
        "time": float(d.time),
        "step": model_data._step_count,
    }


def _reset_real(model_data: ModelData) -> dict[str, Any]:
    mujoco.mj_resetData(model_data._mj_model, model_data._mj_data)
    model_data._step_count = 0
    return _get_state_real(model_data)


def _render_real(model_data: ModelData) -> dict[str, Any]:
    # Full rendering pipeline would use offscreen renderer; return mesh metadata.
    bodies = []
    for i in range(model_data.info.n_bodies):
        body = model_data._mj_model.body(i)
        xpos = model_data._mj_data.xpos[i].tolist()
        xmat = model_data._mj_data.xmat[i].reshape(3, 3).tolist()
        bodies.append({"name": body.name, "position": xpos, "rotation_matrix": xmat})
    return {"bodies": bodies, "backend": "mujoco"}


# ---------------------------------------------------------------------------
# Internal helpers — mock path
# ---------------------------------------------------------------------------


def _make_mock_info(xml_string: str | None) -> ModelInfo:
    """Produce a plausible ModelInfo without parsing the XML."""
    # Heuristic: count <joint> tags when xml is provided.
    n_joints = 6
    if xml_string:
        n_joints = max(1, xml_string.count("<joint"))

    joint_names = [f"joint_{i}" for i in range(n_joints)]
    body_names = ["world"] + [f"link_{i}" for i in range(n_joints)]
    actuator_names = [f"actuator_{i}" for i in range(n_joints)]

    return ModelInfo(
        n_joints=n_joints,
        n_bodies=len(body_names),
        n_actuators=n_joints,
        joint_names=joint_names,
        body_names=body_names,
        actuator_names=actuator_names,
        timestep=0.002,
    )


def _load_mock(xml_string: str | None) -> ModelData:
    info = _make_mock_info(xml_string)
    return ModelData(info)


def _step_mock(model_data: ModelData, action: dict[str, Any]) -> dict[str, Any]:
    ctrl = action.get("ctrl", [0.0] * model_data.info.n_joints)
    model_data._advance_mock(ctrl)
    state = _get_state_mock(model_data)
    # Simulate sensor noise
    for i in range(len(state["imu_acc"])):
        state["imu_acc"][i] += random.gauss(0, 0.01)
    return state


def _get_state_mock(model_data: ModelData) -> dict[str, Any]:
    t = model_data._step_count * model_data.info.timestep
    return {
        "qpos": list(model_data._qpos),
        "qvel": list(model_data._qvel),
        "time": t,
        "step": model_data._step_count,
        "imu_acc": [
            math.sin(t) * 0.1,
            math.cos(t) * 0.1,
            9.81 + random.gauss(0, 0.005),
        ],
        "imu_gyro": [random.gauss(0, 0.001) for _ in range(3)],
        "force_torque": [random.gauss(0, 0.1) for _ in range(6)],
        "contact_forces": [],
    }


def _reset_mock(model_data: ModelData) -> dict[str, Any]:
    model_data._qpos = [0.0] * model_data.info.n_joints
    model_data._qvel = [0.0] * model_data.info.n_joints
    model_data._step_count = 0
    return _get_state_mock(model_data)


def _render_mock(model_data: ModelData) -> dict[str, Any]:
    """Return synthetic geometry data compatible with a Three.js scene."""
    bodies = []
    for i, name in enumerate(model_data.info.body_names):
        angle = 2 * math.pi * i / max(len(model_data.info.body_names), 1)
        radius = 0.5 * i
        bodies.append(
            {
                "name": name,
                "position": [
                    radius * math.cos(angle + model_data._qpos[min(i, len(model_data._qpos) - 1)]),
                    0.0,
                    radius * math.sin(angle + model_data._qpos[min(i, len(model_data._qpos) - 1)]),
                ],
                "rotation_euler": [model_data._qpos[min(i, len(model_data._qpos) - 1)], 0.0, 0.0],
                "geometry": "box",
                "size": [0.05, 0.3, 0.05],
                "color": "#4a9eff",
            }
        )
    return {
        "bodies": bodies,
        "backend": "mock",
        "timestamp": time.time(),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_model(xml_string: str | None) -> ModelData:
    """Parse an MJCF XML string and return a ModelData handle.

    When ``xml_string`` is None a default 6-DOF robot arm model is used.
    """
    if _MUJOCO_AVAILABLE and xml_string:
        return _load_real(xml_string)
    return _load_mock(xml_string)


def step(model_data: ModelData, action: dict[str, Any]) -> dict[str, Any]:
    """Execute one physics step and return the new observation dict."""
    if _MUJOCO_AVAILABLE and model_data._mj_model is not None:
        return _step_real(model_data, action)
    return _step_mock(model_data, action)


def get_state(model_data: ModelData) -> dict[str, Any]:
    """Return the current state without advancing the simulation."""
    if _MUJOCO_AVAILABLE and model_data._mj_model is not None:
        return _get_state_real(model_data)
    return _get_state_mock(model_data)


def reset(model_data: ModelData) -> dict[str, Any]:
    """Reset simulation to its initial state and return the reset observation."""
    if _MUJOCO_AVAILABLE and model_data._mj_model is not None:
        return _reset_real(model_data)
    return _reset_mock(model_data)


def get_render_data(model_data: ModelData) -> dict[str, Any]:
    """Return 3-D geometry data suitable for Three.js rendering."""
    if _MUJOCO_AVAILABLE and model_data._mj_model is not None:
        return _render_real(model_data)
    return _render_mock(model_data)
