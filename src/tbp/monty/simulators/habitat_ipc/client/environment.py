# Copyright 2025 Thousand Brains Project
# Copyright 2022-2024 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
from __future__ import annotations

import multiprocessing
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Sequence

import quaternion

from tbp.monty.frameworks.actions.actions import Action
from tbp.monty.frameworks.environments.environment import (
    ObjectID,
    QuaternionWXYZ,
    SemanticID,
    SimulatedObjectEnvironment,
    VectorXYZ,
)
from tbp.monty.frameworks.models.abstract_monty_classes import Observations
from tbp.monty.frameworks.models.motor_system_state import ProprioceptiveState
from tbp.monty.simulators.habitat_ipc.server.server import HabitatServer
from tbp.monty.simulators.habitat_ipc.transport import ShmRpcTransport
from .client import HabitatClient

if TYPE_CHECKING:
    pass

__all__ = [
    "HabitatEnvironment",
]


class HabitatEnvironment(SimulatedObjectEnvironment):
    """habitat-sim environment compatible with Monty.

    Attributes:
        agents: List of :class:`AgentConfig` to place in the scene.
        objects: Optional list of :class:`ObjectConfig` to place in the scene.
        scene_id: Scene to use or None for empty environment.
        seed: Simulator seed to use
        data_path: Path to the dataset.
    """

    # def __init__(
    #     self,
    #     config_name: str,
    # ):
    #     super().__init__()
    #     self._habitat_server = HabitatServer(QueueBasedTransport())
    #     server_process = multiprocessing.Process(target=self._habitat_server.start)
    #     server_process.start()
    #
    #     self._habitat_client = HabitatClient(self._habitat_server.transport)
    #     self._habitat_client.init(config_name)

    def __init__(
        self,
        agents: dict,
        objects: list[dict] | None  = None,
        scene_id: str | None = None,
        seed: int = 42,
        data_path: str | Path | None = None,
    ):
        super().__init__()

        transport = ShmRpcTransport()

        self._habitat_server = HabitatServer(transport)
        ctx = multiprocessing.get_context("spawn")
        self._server_process = ctx.Process(target=self._habitat_server.start, daemon=True)
        self._server_process.start()

        sleep(10)

        self._habitat_client = HabitatClient(transport)

        _data_path = str(data_path) if data_path else None
        self._habitat_client.init(agents, objects, scene_id, seed, _data_path)
        self.action_space_type = self._extract_action_space_type(agents)

    def __del__(self):
        self._server_process.terminate()

    def add_object(
        self,
        name: str,
        position: VectorXYZ = (0.0, 0.0, 0.0),
        rotation: QuaternionWXYZ = (1.0, 0.0, 0.0, 0.0),
        scale: VectorXYZ = (1.0, 1.0, 1.0),
        semantic_id: SemanticID | None = None,
        primary_target_object: ObjectID | None = None,
    ) -> ObjectID:

        _rotation = rotation
        if isinstance(rotation, quaternion.quaternion):
            _rotation = (rotation.w, rotation.x, rotation.y, rotation.z)

        return self._habitat_client.add_object(
            name,
            position,
            _rotation,
            scale,
            semantic_id,
            primary_target_object,
        ).object_id

    def step(self, actions: Sequence[Action]) -> tuple[Observations, ProprioceptiveState]:
        return self._habitat_client.step(actions)

    def remove_all_objects(self) -> None:
        return self._habitat_client.remove_all_objects()

    def reset(self) -> tuple[Observations, ProprioceptiveState]:
        return self._habitat_client.reset()

    def close(self) -> None:
        self._habitat_client.close()

    @staticmethod
    def _extract_action_space_type(agents):
        """Extract action_space_type from agents config (dict or dataclass)."""
        import dataclasses

        if dataclasses.is_dataclass(agents):
            agents = dataclasses.asdict(agents)

        return agents.get("agent_args", {}).get("action_space_type")
