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

import os
from dataclasses import dataclass, field
from typing import Callable, Mapping
from tbp.monty.frameworks.agents import AgentID
from tbp.monty.frameworks.config_utils.make_env_interface_configs import (
    FiveLMMountConfig,
    MultiLMMountConfig,
    PatchAndViewFinderMountConfig,
    PatchAndViewFinderMountLowResConfig,
    PatchAndViewFinderMultiObjectMountConfig,
    SurfaceAndViewFinderMountConfig,
    TwoCameraMountConfig,
    TwoLMStackedDistantMountConfig,
    TwoLMStackedSurfaceMountConfig,
    make_multi_sensor_mount_config,
)
from tbp.monty.frameworks.environment_utils.transforms import (
    AddNoiseToRawDepthImage,
    DepthTo3DLocations,
    MissingToMaxDepth,
)
from tbp.monty.simulators.habitat_proxy import MultiSensorAgent, SingleSensorAgent
from tbp.monty.simulators.habitat_proxy.environment import (
    AgentConfig,
    HabitatEnvironment,
    ObjectConfig,
)
from tbp.monty.simulators.habitat import configs as _habitat_configs

__all__ = [
    "EnvInitArgs",
    "EnvInitArgsFiveLMMount",
    "EnvInitArgsMontyWorldPatchViewMount",
    "EnvInitArgsMontyWorldSurfaceViewMount",
    "EnvInitArgsMultiLMMount",
    "EnvInitArgsPatchViewFinderMultiObjectMount",
    "EnvInitArgsPatchViewMount",
    "EnvInitArgsPatchViewMountLowRes",
    "EnvInitArgsShapenetPatchViewMount",
    "EnvInitArgsSimpleMount",
    "EnvInitArgsSinglePTZ",
    "EnvInitArgsSurfaceViewMount",
    "EnvInitArgsTwoLMDistantStackedMount",
    "EnvInitArgsTwoLMSurfaceStackedMount",
    "FiveLMMountHabitatEnvInterfaceConfig",
    "MultiLMMountHabitatEnvInterfaceConfig",
    "NoisyPatchViewFinderMountHabitatEnvInterfaceConfig",
    "NoisySurfaceViewFinderMountHabitatEnvInterfaceConfig",
    "ObjectConfig",
    "PatchViewFinderLowResMountHabitatEnvInterfaceConfig",
    "PatchViewFinderMontyWorldMountHabitatEnvInterfaceConfig",
    "PatchViewFinderMountHabitatEnvInterfaceConfig",
    "PatchViewFinderMultiObjectMountHabitatEnvInterfaceConfig",
    "PatchViewFinderShapenetMountHabitatEnvInterfaceConfig",
    "SimpleMountHabitatEnvInterfaceConfig",
    "SinglePTZHabitatEnvInterfaceConfig",
    "SurfaceViewFinderMontyWorldMountHabitatEnvInterfaceConfig",
    "SurfaceViewFinderMountHabitatEnvInterfaceConfig",
    "TwoLMStackedDistantMountHabitatEnvInterfaceConfig",
    "TwoLMStackedSurfaceMountHabitatEnvInterfaceConfig",
    "make_multi_sensor_habitat_env_interface_config",
]


@dataclass
class EnvInitArgs:
    agents: list = field(default_factory=list)
    objects: list = field(default_factory=list)
    scene_id: int | None = field(default=None)
    seed: int = field(default=42)
    data_path: str = ""


@dataclass
class EnvInitArgsSinglePTZ(EnvInitArgs):
    pass


@dataclass
class EnvInitArgsSimpleMount(EnvInitArgs):
    pass


@dataclass
class EnvInitArgsPatchViewMount(EnvInitArgs):
    pass


@dataclass
class EnvInitArgsSurfaceViewMount(EnvInitArgs):
    pass


@dataclass
class EnvInitArgsMontyWorldPatchViewMount(EnvInitArgsPatchViewMount):
    pass


@dataclass
class EnvInitArgsMontyWorldSurfaceViewMount(EnvInitArgsMontyWorldPatchViewMount):
    pass


@dataclass
class EnvInitArgsPatchViewMountLowRes(EnvInitArgs):
    pass


@dataclass
class SinglePTZHabitatEnvInterfaceConfig:
    env_init_func: Callable | None = None
    env_init_args: dict = field(default_factory=dict)
    transform: Callable | list | None = None


@dataclass
class SimpleMountHabitatEnvInterfaceConfig:
    env_init_func: Callable | None = None
    env_init_args: dict = field(default_factory=dict)
    transform: Callable | list | None = None


@dataclass
class PatchViewFinderMountHabitatEnvInterfaceConfig:
    env_init_func: Callable | None = None
    env_init_args: dict = field(default_factory=dict)
    transform: Callable | list | None = None
    rng: Callable | None = None

    def __post_init__(self):
        pass


@dataclass
class NoisyPatchViewFinderMountHabitatEnvInterfaceConfig:
    env_init_func: Callable | None = None
    env_init_args: dict = field(default_factory=dict)
    transform: Callable | list | None = None

    def __post_init__(self):
        pass


@dataclass
class EnvInitArgsShapenetPatchViewMount(EnvInitArgsPatchViewMount):
    pass


@dataclass
class PatchViewFinderLowResMountHabitatEnvInterfaceConfig(
    PatchViewFinderMountHabitatEnvInterfaceConfig
):
    pass


@dataclass
class PatchViewFinderShapenetMountHabitatEnvInterfaceConfig(
    PatchViewFinderMountHabitatEnvInterfaceConfig
):
    pass


@dataclass
class PatchViewFinderMontyWorldMountHabitatEnvInterfaceConfig(
    PatchViewFinderMountHabitatEnvInterfaceConfig
):
    pass


@dataclass
class SurfaceViewFinderMountHabitatEnvInterfaceConfig(
    PatchViewFinderMountHabitatEnvInterfaceConfig
):
    def __post_init__(self):
        pass


@dataclass
class SurfaceViewFinderMontyWorldMountHabitatEnvInterfaceConfig(
    SurfaceViewFinderMountHabitatEnvInterfaceConfig
):
    pass


@dataclass
class NoisySurfaceViewFinderMountHabitatEnvInterfaceConfig(
    PatchViewFinderMountHabitatEnvInterfaceConfig
):
    def __post_init__(self):
        pass


@dataclass
class EnvInitArgsMultiLMMount(EnvInitArgs):
    pass


@dataclass
class MultiLMMountHabitatEnvInterfaceConfig:
    env_init_func: Callable | None = None
    env_init_args: dict = field(default_factory=dict)
    transform: Callable | list | None = None

    def __post_init__(self):
        pass


@dataclass
class EnvInitArgsTwoLMDistantStackedMount(EnvInitArgs):
    pass


@dataclass
class TwoLMStackedDistantMountHabitatEnvInterfaceConfig(
    MultiLMMountHabitatEnvInterfaceConfig
):
    pass


@dataclass
class EnvInitArgsTwoLMSurfaceStackedMount(EnvInitArgs):
    pass


@dataclass
class TwoLMStackedSurfaceMountHabitatEnvInterfaceConfig(
    MultiLMMountHabitatEnvInterfaceConfig
):
    pass


@dataclass
class EnvInitArgsFiveLMMount(EnvInitArgs):
    pass


@dataclass
class FiveLMMountHabitatEnvInterfaceConfig(MultiLMMountHabitatEnvInterfaceConfig):
    pass


@dataclass
class EnvInitArgsPatchViewFinderMultiObjectMount(EnvInitArgs):
    pass


@dataclass
class PatchViewFinderMultiObjectMountHabitatEnvInterfaceConfig:
    env_init_func: Callable | None = None
    env_init_args: dict = field(default_factory=dict)
    transform: Callable | list | None = None
    rng: Callable | None = None

    def __post_init__(self):
        pass


def make_multi_sensor_habitat_env_interface_config(
    n_sensors: int,
    **mount_kwargs: Mapping,
):
    return None
