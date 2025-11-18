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
    def __init__(
        self,
        agent_id: AgentID | None,
        position: Vector3 = (0.0, 1.5, 0.0),
        rotation: Quaternion = (1.0, 0.0, 0.0, 0.0),
        height: float = 0.0,
    ):
        pass

    def get_spec(self) -> AgentConfiguration:
        return None

    def initialize(self, simulator):
        pass

    def process_observations(self, agent_obs) -> dict:
        return {}


def action_space(
    action_space_type: ActionSpaceName,
    agent_id: str,
    translation_step: float,
    rotation_step: float,
) -> dict[str, dict]:
    return {}


class MultiSensorAgent(HabitatAgent):
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
        pass

    def get_spec(self):
        return None

    def initialize(self, simulator):
        pass


class SingleSensorAgent(HabitatAgent):
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
        pass

    def get_spec(self):
        return None

    def initialize(self, simulator):
        pass

