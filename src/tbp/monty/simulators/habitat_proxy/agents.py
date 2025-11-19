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

from habitat_sim import ActionSpec
from habitat_sim.agent import AgentConfiguration

from tbp.monty.frameworks.agents import AgentID
from tbp.monty.simulators.habitat_impl import agents as _habitat_impl_agents

__all__ = [
    "HabitatAgent",
    "MultiSensorAgent",
    "SingleSensorAgent",
]

ActionSpaceName = _habitat_impl_agents.ActionSpaceName
Vector3 = _habitat_impl_agents.Vector3
Quaternion = _habitat_impl_agents.Quaternion
Size = _habitat_impl_agents.Size


class HabitatAgent:
    """Proxy for HabitatAgent - delegates to habitat implementation."""

    def __init__(
            self,
            agent_id: AgentID | None,
            position: Vector3 = (0.0, 1.5, 0.0),
            rotation: Quaternion = (1.0, 0.0, 0.0, 0.0),
            height: float = 0.0,
    ):
        self._delegate = _habitat_impl_agents.HabitatAgent(
            agent_id, position, rotation, height
        )

    def __getattr__(self, name):
        return self._delegate.__getattribute__(name)

    @classmethod
    def _from_delegate(cls, delegate_agent: _habitat_impl_agents.HabitatAgent) -> HabitatAgent:
        instance = cls.__new__(cls)
        instance._delegate = delegate_agent
        return instance

    def get_spec(self) -> AgentConfiguration:
        return self._delegate.get_spec()

    def initialize(self, simulator):
        return self._delegate.initialize(simulator)

    def process_observations(self, agent_obs) -> dict:
        return self._delegate.process_observations(agent_obs)


def action_space(
        action_space_type: ActionSpaceName,
        agent_id: str,
        translation_step: float,
        rotation_step: float,
) -> dict[str, ActionSpec]:
    """Proxy for action_space function - delegates to habitat implementation."""
    return _habitat_impl_agents.action_space(
        action_space_type, agent_id, translation_step, rotation_step
    )


class MultiSensorAgent(HabitatAgent):
    """Proxy for MultiSensorAgent - delegates to habitat implementation."""

    def __init__(
            self,
            agent_id: AgentID | None,
            sensor_ids: tuple[str],
            position: Vector3 = (0.0, 1.5, 0.0),
            rotation: Quaternion = (1.0, 0.0, 0.0, 0.0),
            height: float = 0.0,
            rotation_step: float = 0.0,
            translation_step: float = 0.0,
            action_space_type: ActionSpaceName = "distant_agent",
            resolutions: tuple[Size] = ((16, 16),),
            positions: tuple[Vector3] = ((0.0, 0.0, 0.0),),
            rotations: tuple[Quaternion] = ((1.0, 0.0, 0.0, 0.0),),
            zooms: tuple[float] = (1.0,),
            semantics: tuple[bool] = (False,),
    ):
        # Don't call super().__init__ - create delegate directly
        self._delegate = _habitat_impl_agents.MultiSensorAgent(
            agent_id, sensor_ids, position, rotation, height,
            rotation_step, translation_step, action_space_type,
            resolutions, positions, rotations, zooms, semantics
        )


    def get_spec(self):
        return self._delegate.get_spec()

    def initialize(self, simulator):
        return self._delegate.initialize(simulator)


class SingleSensorAgent(HabitatAgent):
    """Proxy for SingleSensorAgent - delegates to habitat implementation."""

    def __init__(
            self,
            agent_id: AgentID | None,
            sensor_id: str,
            agent_position: Vector3 = (0.0, 1.5, 0.0),
            sensor_position: Vector3 = (0.0, 0.0, 0.0),
            rotation: Quaternion = (1.0, 0.0, 0.0, 0.0),
            height: float = 0.0,
            resolution: Size = (16, 16),
            zoom: float = 1.0,
            semantic: bool = False,
            rotation_step: float = 0.0,
            translation_step: float = 0.0,
            action_space_type: ActionSpaceName = "distant_agent",
    ):
        # Don't call super().__init__ - create delegate directly
        self._delegate = _habitat_impl_agents.SingleSensorAgent(
            agent_id, sensor_id, agent_position, sensor_position, rotation,
            height, resolution, zoom, semantic, rotation_step, translation_step,
            action_space_type
        )

    def get_spec(self):
        return self._delegate.get_spec()

    def initialize(self, simulator):
        return self._delegate.initialize(simulator)
