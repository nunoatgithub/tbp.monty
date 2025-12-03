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
from typing import TYPE_CHECKING, Sequence

from tbp.monty.frameworks.actions.actions import Action
from tbp.monty.frameworks.environments.embodied_environment import (
    EmbodiedEnvironment,
    ObjectID,
    QuaternionWXYZ,
    SemanticID,
    VectorXYZ,
)
from tbp.monty.frameworks.models.abstract_monty_classes import Observations
from tbp.monty.simulators.habitat_ipc.server.server import HabitatServer
from tbp.monty.simulators.habitat_ipc.transport import QueueBasedTransport
from .client import HabitatClient

if TYPE_CHECKING:
    pass

__all__ = [
    "HabitatEnvironment",
]


class HabitatEnvironment(EmbodiedEnvironment):
    """habitat-sim environment compatible with Monty.

    Attributes:
        agents: List of :class:`AgentConfig` to place in the scene.
        objects: Optional list of :class:`ObjectConfig` to place in the scene.
        scene_id: Scene to use or None for empty environment.
        seed: Simulator seed to use
        data_path: Path to the dataset.
    """

    def __init__(
        self,
        config_name: str,
    ):
        super().__init__()
        self._habitat_server = HabitatServer(QueueBasedTransport())
        server_process = multiprocessing.Process(target=self._habitat_server.start)
        server_process.start()

        self._habitat_client = HabitatClient(self._habitat_server.transport)
        self._habitat_client.init(config_name)

    def add_object(
        self,
        name: str,
        position: VectorXYZ = (0.0, 0.0, 0.0),
        rotation: QuaternionWXYZ = (1.0, 0.0, 0.0, 0.0),
        scale: VectorXYZ = (1.0, 1.0, 1.0),
        semantic_id: SemanticID | None = None,
        primary_target_object: ObjectID | None = None,
    ) -> ObjectID:
        return self._habitat_client.add_object(
            name,
            position,
            rotation,
            scale,
            semantic_id,
            primary_target_object,
        ).object_id

    def step(self, actions: Sequence[Action]) -> Observations:
        return self._habitat_client.apply_actions(actions)

    def remove_all_objects(self) -> None:
        return self._habitat_client.remove_all_objects()

    def reset(self) -> Observations:
        return self._habitat_client.reset()

    def close(self) -> None:
        self._habitat_client.close()

    def get_state(self):
        return self._habitat_client.states
