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
from tbp.monty.frameworks.actions.actions import (
    LookDown,
    LookUp,
    MoveForward,
    MoveTangentially,
    OrientHorizontal,
    OrientVertical,
    SetAgentPitch,
    SetAgentPose,
    SetSensorPitch,
    SetSensorPose,
    SetSensorRotation,
    SetYaw,
    TurnLeft,
    TurnRight,
)
from habitat_sim import Agent, ActuationSpec
from tbp.monty.simulators.habitat import simulator as _habitat_simulator
from tbp.monty.simulators.habitat_proxy.actuator import HabitatActuator

__all__ = [
    "PRIMITIVE_OBJECT_TYPES",
    "HabitatSim",
]

# Direct assignment of constants from habitat
PRIMITIVE_OBJECT_TYPES: dict[str, int] = _habitat_simulator.PRIMITIVE_OBJECT_TYPES


class HabitatSim(HabitatActuator):
    """Proxy for HabitatSim - delegates all calls to habitat implementation."""

    def __init__(
        self,
        agents=None,
        scene_id=None,
        seed=42,
        data_path=None,
    ):
        # Map proxy agents to habitat agents
        import tbp.monty.simulators.habitat as _habitat

        habitat_agents = []
        if agents:
            for agent in agents:
                agent_type_name = type(agent).__name__
                habitat_agent_type = getattr(_habitat, agent_type_name)

                # Reconstruct agent with habitat class
                # Copy attributes from proxy agent to create habitat agent
                habitat_agent = habitat_agent_type.__new__(habitat_agent_type)
                habitat_agent.__dict__.update(agent.__dict__)
                habitat_agents.append(habitat_agent)

        # Create delegate with habitat agents
        self._delegate = _habitat_simulator.HabitatSim(
            agents=habitat_agents,
            scene_id=scene_id,
            seed=seed,
            data_path=data_path,
        )

    def initialize_agent(self, agent_id: AgentID, agent_state) -> None:
        return self._delegate.initialize_agent(agent_id, agent_state)

    def remove_all_objects(self) -> None:
        return self._delegate.remove_all_objects()

    def add_object(
        self,
        name: str,
        position: VectorXYZ = (0.0, 0.0, 0.0),
        rotation: QuaternionWXYZ = (1.0, 0.0, 0.0, 0.0),
        scale: VectorXYZ = (1.0, 1.0, 1.0),
        semantic_id: SemanticID | None = None,
        primary_target_object: ObjectID | None = None,
    ) -> ObjectInfo:
        return self._delegate.add_object(
            name, position, rotation, scale, semantic_id, primary_target_object
        )

    def _bounding_corners(self, object_id: ObjectID):
        return self._delegate._bounding_corners(object_id)

    def non_conflicting_vector(self) -> np.ndarray:
        return self._delegate.non_conflicting_vector()

    def check_viewpoint_collision(
        self,
        primary_obj_bb,
        new_obj_bb,
        overlap_threshold=0.75,
    ) -> bool:
        return self._delegate.check_viewpoint_collision(
            primary_obj_bb, new_obj_bb, overlap_threshold
        )

    def find_non_colliding_positions(
        self,
        new_object,
        start_position,
        start_orientation,
        primary_obj_bb,
        max_distance=1,
        step_size=0.00005,
    ):
        return self._delegate.find_non_colliding_positions(
            new_object, start_position, start_orientation, primary_obj_bb,
            max_distance, step_size
        )

    @property
    def num_objects(self):
        return self._delegate.num_objects

    @property
    def action_space(self) -> set[str]:
        return self._delegate.action_space

    def get_agent(self, agent_id: AgentID) -> habitat_sim.Agent:
        return self._delegate.get_agent(agent_id)

    def apply_actions(self, actions: Sequence[Action]) -> dict[str, dict]:
        return self._delegate.apply_actions(actions)

    @property
    def observations(self) -> dict:
        return self._delegate.observations

    def process_observations(self, obs) -> dict:
        return self._delegate.process_observations(obs)

    @property
    def states(self) -> dict:
        return self._delegate.states

    def reset(self):
        return self._delegate.reset()

    def close(self) -> None:
        return self._delegate.close()

    def __enter__(self):
        self._delegate.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._delegate.__exit__(exc_type, exc_val, exc_tb)

    # Actuator methods - delegate to habitat
    def action_name(self, action: Action) -> str:
        return self._delegate.action_name(action)

    def to_habitat(self, action: Action) -> tuple[Agent, ActuationSpec, str]:
        return self._delegate.to_habitat(action)

    def actuate_look_down(self, action: LookDown) -> None:
        return self._delegate.actuate_look_down(action)

    def actuate_look_up(self, action: LookUp) -> None:
        return self._delegate.actuate_look_up(action)

    def actuate_move_forward(self, action: MoveForward) -> None:
        return self._delegate.actuate_move_forward(action)

    def actuate_move_tangentially(self, action: MoveTangentially) -> None:
        return self._delegate.actuate_move_tangentially(action)

    def actuate_orient_horizontal(self, action: OrientHorizontal) -> None:
        return self._delegate.actuate_orient_horizontal(action)

    def actuate_orient_vertical(self, action: OrientVertical) -> None:
        return self._delegate.actuate_orient_vertical(action)

    def actuate_set_agent_pitch(self, action: SetAgentPitch) -> None:
        return self._delegate.actuate_set_agent_pitch(action)

    def actuate_set_agent_pose(self, action: SetAgentPose) -> None:
        return self._delegate.actuate_set_agent_pose(action)

    def actuate_set_sensor_pitch(self, action: SetSensorPitch) -> None:
        return self._delegate.actuate_set_sensor_pitch(action)

    def actuate_set_sensor_pose(self, action: SetSensorPose) -> None:
        return self._delegate.actuate_set_sensor_pose(action)

    def actuate_set_sensor_rotation(self, action: SetSensorRotation) -> None:
        return self._delegate.actuate_set_sensor_rotation(action)

    def actuate_set_yaw(self, action: SetYaw) -> None:
        return self._delegate.actuate_set_yaw(action)

    def actuate_turn_left(self, action: TurnLeft) -> None:
        return self._delegate.actuate_turn_left(action)

    def actuate_turn_right(self, action: TurnRight) -> None:
        return self._delegate.actuate_turn_right(action)

