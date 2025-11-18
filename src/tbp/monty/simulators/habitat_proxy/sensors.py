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

import uuid
from dataclasses import dataclass, field
from typing import Tuple

from habitat_sim.sensor import SensorSpec

from tbp.monty.simulators.habitat import sensors as _habitat_sensors

__all__ = [
    "RGBDSensorConfig",
    "SemanticSensorConfig",
    "SensorConfig",
]

Vector3 = Tuple[float, float, float]
Quaternion = Tuple[float, float, float, float]
Size = Tuple[int, int]


@dataclass(frozen=True)
class SensorConfig:
    """Proxy for SensorConfig - uses habitat implementation."""
    sensor_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    position: Vector3 = (0.0, 0.0, 0.0)
    rotation: Quaternion = (1.0, 0.0, 0.0, 0.0)

    def get_specs(self) -> list[SensorSpec]:
        # Create habitat sensor config and delegate
        habitat_sensor = _habitat_sensors.SensorConfig(
            sensor_id=self.sensor_id,
            position=self.position,
            rotation=self.rotation
        )
        return habitat_sensor.get_specs()

    def process_observations(self, sensor_obs) -> dict:
        # Create habitat sensor config and delegate
        habitat_sensor = _habitat_sensors.SensorConfig(
            sensor_id=self.sensor_id,
            position=self.position,
            rotation=self.rotation
        )
        return habitat_sensor.process_observations(sensor_obs)


@dataclass(frozen=True)
class RGBDSensorConfig(SensorConfig):
    """Proxy for RGBDSensorConfig - uses habitat implementation."""
    resolution: Size = (64, 64)
    zoom: float = 1.0

    def get_specs(self) -> list[SensorSpec]:
        # Create habitat sensor config and delegate
        habitat_sensor = _habitat_sensors.RGBDSensorConfig(
            sensor_id=self.sensor_id,
            position=self.position,
            rotation=self.rotation,
            resolution=self.resolution,
            zoom=self.zoom
        )
        return habitat_sensor.get_specs()


@dataclass(frozen=True)
class SemanticSensorConfig(SensorConfig):
    """Proxy for SemanticSensorConfig - uses habitat implementation."""
    resolution: Size = (64, 64)
    zoom: float = 1.0

    def get_specs(self) -> list[SensorSpec]:
        # Create habitat sensor config and delegate
        habitat_sensor = _habitat_sensors.SemanticSensorConfig(
            sensor_id=self.sensor_id,
            position=self.position,
            rotation=self.rotation,
            resolution=self.resolution,
            zoom=self.zoom
        )
        return habitat_sensor.get_specs()

