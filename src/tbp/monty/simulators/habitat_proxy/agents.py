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

from typing import Tuple
from typing_extensions import Literal

from habitat_sim.agent import AgentConfiguration

from tbp.monty.frameworks.agents import AgentID
from tbp.monty.simulators.habitat import agents as _habitat_agents

__all__ = [
    "HabitatAgent",
    "MultiSensorAgent",
    "SingleSensorAgent",
]

ActionSpaceName = Literal["absolute_only", "distant_agent", "surface_agent"]
Vector3 = Tuple[float, float, float]
Quaternion = Tuple[float, float, float, float]
Size = Tuple[int, int]


class HabitatAgent:
    """Proxy for HabitatAgent - delegates to habitat implementation."""

    def __init__(
        self,
        agent_id: AgentID | None,
        position: Vector3 = (0.0, 1.5, 0.0),
        rotation: Quaternion = (1.0, 0.0, 0.0, 0.0),
        height: float = 0.0,
    ):
        self._delegate = _habitat_agents.HabitatAgent(
            agent_id, position, rotation, height
        )
        # Copy delegate attributes to self for transparent access
        self.agent_id = self._delegate.agent_id
        self.position = self._delegate.position
        self.rotation = self._delegate.rotation
        self.height = self._delegate.height
        self.sensors = self._delegate.sensors

    def get_spec(self) -> AgentConfiguration:
        return self._delegate.get_spec()

    def initialize(self, simulator):
        return self._delegate.initialize(simulator)

    def process_observations(self, agent_obs) -> dict:
        return self._delegate.process_observations(agent_obs)


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
        self._delegate = _habitat_agents.MultiSensorAgent(
            agent_id, sensor_ids, position, rotation, height,
            rotation_step, translation_step, action_space_type,
            resolutions, positions, rotations, zooms, semantics
        )
        # Copy delegate attributes
        self.agent_id = self._delegate.agent_id
        self.position = self._delegate.position
        self.rotation = self._delegate.rotation
        self.height = self._delegate.height
        self.sensors = self._delegate.sensors
        self.sensor_ids = self._delegate.sensor_ids
        self.rotation_step = self._delegate.rotation_step
        self.translation_step = self._delegate.translation_step
        self.action_space_type = self._delegate.action_space_type
        self.resolutions = self._delegate.resolutions
        self.positions = self._delegate.positions
        self.rotations = self._delegate.rotations
        self.zooms = self._delegate.zooms
        self.semantics = self._delegate.semantics

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
        self._delegate = _habitat_agents.SingleSensorAgent(
            agent_id, sensor_id, agent_position, sensor_position, rotation,
            height, resolution, zoom, semantic, rotation_step, translation_step,
            action_space_type
        )
        # Copy delegate attributes
        self.agent_id = self._delegate.agent_id
        self.position = self._delegate.position
        self.rotation = self._delegate.rotation
        self.height = self._delegate.height
        self.sensors = self._delegate.sensors

    def get_spec(self):
        return self._delegate.get_spec()

    def initialize(self, simulator):
        return self._delegate.initialize(simulator)

