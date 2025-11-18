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

from typing import Sequence

import numpy as np
import habitat_sim

from tbp.monty.frameworks.actions.actions import Action
from tbp.monty.frameworks.agents import AgentID
from tbp.monty.frameworks.environments.embodied_environment import (
    ObjectID,
    ObjectInfo,
    QuaternionWXYZ,
    SemanticID,
    VectorXYZ,
)
from tbp.monty.simulators.habitat import simulator as _habitat_simulator
from tbp.monty.simulators.habitat_proxy.actuator import HabitatActuator

__all__ = [
    "PRIMITIVE_OBJECT_TYPES",
    "HabitatSim",
]

PRIMITIVE_OBJECT_TYPES: dict[str, int] = {}


class HabitatSim(HabitatActuator):
    def initialize_agent(self, agent_id: AgentID, agent_state) -> None:
        pass

    def remove_all_objects(self) -> None:
        pass

    def add_object(
        self,
        name: str,
        position: VectorXYZ = (0.0, 0.0, 0.0),
        rotation: QuaternionWXYZ = (1.0, 0.0, 0.0, 0.0),
        scale: VectorXYZ = (1.0, 1.0, 1.0),
        semantic_id: SemanticID | None = None,
        primary_target_object: ObjectID | None = None,
    ) -> ObjectInfo:
        return None

    def _bounding_corners(self, object_id: ObjectID):
        return None

    def non_conflicting_vector(self) -> np.ndarray:
        return None  # type: ignore[return-value]

    def check_viewpoint_collision(
        self,
        primary_obj_bb,
        new_obj_bb,
        overlap_threshold=0.75,
    ) -> bool:
        return False

    def find_non_colliding_positions(
        self,
        new_object,
        start_position,
        start_orientation,
        primary_obj_bb,
        max_distance=1,
        step_size=0.00005,
    ):
        return None

    @property
    def num_objects(self):
        return 0

    @property
    def action_space(self) -> set[str]:
        return set()

    def get_agent(self, agent_id: AgentID) -> habitat_sim.Agent:
        return None

    def apply_actions(self, actions: Sequence[Action]) -> dict[str, dict]:
        return {}

    @property
    def observations(self) -> dict:
        return {}

    def process_observations(self, obs) -> dict:
        return {}

    @property
    def states(self) -> dict:
        return {}

    def reset(self):
        return {}

    def close(self) -> None:
        pass

