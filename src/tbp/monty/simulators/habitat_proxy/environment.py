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

from dataclasses import asdict, dataclass, is_dataclass
from typing import Sequence

from tbp.monty.frameworks.actions.actions import Action
from tbp.monty.frameworks.environments.embodied_environment import (
    EmbodiedEnvironment,
    ObjectID,
    QuaternionWXYZ,
    SemanticID,
    VectorXYZ,
)
from tbp.monty.frameworks.utils.dataclass_utils import create_dataclass_args
from tbp.monty.simulators.habitat import environment as _habitat_environment
from tbp.monty.simulators.habitat_proxy.agents import (
    HabitatAgent,
    MultiSensorAgent,
    SingleSensorAgent,
)
from tbp.monty.simulators.habitat_proxy.simulator import HabitatSim
from tbp.monty.simulators.simulator import Simulator

__all__ = [
    "AgentConfig",
    "HabitatEnvironment",
    "MultiSensorAgentArgs",
    "ObjectConfig",
    "SingleSensorAgentArgs",
]


class HabitatAgentArgs:
    pass


# SingleSensorAgentArgs dataclass based on constructor args
SingleSensorAgentArgs = create_dataclass_args(
    "SingleSensorAgentArgs", SingleSensorAgent.__init__, HabitatAgentArgs
)
SingleSensorAgentArgs.__module__ = __name__

# MultiSensorAgentArgs dataclass based on constructor args
MultiSensorAgentArgs = create_dataclass_args(
    "MultiSensorAgentArgs", MultiSensorAgent.__init__, HabitatAgentArgs
)
MultiSensorAgentArgs.__module__ = __name__

# ObjectConfig dataclass based on the arguments of `HabitatSim.add_object` method
ObjectConfig = create_dataclass_args("ObjectConfig", HabitatSim.add_object)
ObjectConfig.__module__ = __name__


@dataclass
class AgentConfig:
    agent_type: type[HabitatAgent]
    agent_args: dict | type[HabitatAgentArgs]


class HabitatEnvironment:
    def __init__(
        self,
        agents: list[dict | AgentConfig],
        objects: list[dict | ObjectConfig] | None = None,
        scene_id: str | None = None,
        seed: int = 42,
        data_path: str | None = None,
    ):
        pass

    def add_object(
        self,
        name: str,
        position=(0.0, 0.0, 0.0),
        rotation=(1.0, 0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        semantic_id=None,
        primary_target_object=None,
    ):
        return None

    def step(self, actions: Sequence):
        return {}

    def remove_all_objects(self):
        pass

    def reset(self):
        return {}

    def close(self):
        pass

    def get_state(self):
        return {}

