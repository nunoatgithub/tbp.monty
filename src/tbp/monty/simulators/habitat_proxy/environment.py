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
        # Translate proxy AgentConfig to habitat AgentConfig
        import tbp.monty.simulators.habitat as _habitat
        from dataclasses import asdict, is_dataclass

        habitat_agents = []
        for config in agents:
            cfg_dict = asdict(config) if is_dataclass(config) else config
            agent_type = cfg_dict["agent_type"]
            args = cfg_dict["agent_args"]
            if is_dataclass(args):
                args = asdict(args)

            # Map proxy agent class to habitat agent class
            agent_type_name = agent_type.__name__
            habitat_agent_type = getattr(_habitat, agent_type_name)

            habitat_agent_config = _habitat.environment.AgentConfig(
                agent_type=habitat_agent_type,
                agent_args=args
            )
            habitat_agents.append(habitat_agent_config)

        # Create delegate
        self._delegate = _habitat_environment.HabitatEnvironment(
            agents=habitat_agents,
            objects=objects,
            scene_id=scene_id,
            seed=seed,
            data_path=data_path,
        )

    def add_object(
        self,
        name: str,
        position: VectorXYZ = (0.0, 0.0, 0.0),
        rotation: QuaternionWXYZ = (1.0, 0.0, 0.0, 0.0),
        scale: VectorXYZ = (1.0, 1.0, 1.0),
        semantic_id: SemanticID | None = None,
        primary_target_object: ObjectID | None = None,
    ) -> ObjectID:
        return self._delegate.add_object(
            name, position, rotation, scale, semantic_id, primary_target_object
        )

    def step(self, actions: Sequence[Action]) -> dict[str, dict]:
        return self._delegate.step(actions)

    def remove_all_objects(self) -> None:
        return self._delegate.remove_all_objects()

    def reset(self):
        return self._delegate.reset()

    def close(self) -> None:
        return self._delegate.close()

    def get_state(self):
        return self._delegate.get_state()

