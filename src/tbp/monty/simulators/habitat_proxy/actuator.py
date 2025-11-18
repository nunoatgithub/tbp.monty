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

from typing_extensions import Protocol

from habitat_sim import Agent, ActuationSpec

from tbp.monty.frameworks.actions.actions import (
    Action,
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
from tbp.monty.frameworks.agents import AgentID
from tbp.monty.simulators.habitat import actuator as _habitat_actuator

__all__ = [
    "HabitatActuator",
    "HabitatActuatorRequirements",
]


class HabitatActuatorRequirements(Protocol):
    def get_agent(self, agent_id: AgentID) -> Agent | None: ...


class HabitatActuator(HabitatActuatorRequirements):
    def action_name(self, action: Action) -> str:
        return ""

    def to_habitat(self, action: Action) -> tuple[Agent, ActuationSpec, str]:
        raise NotImplementedError

    def actuate_look_down(self, action: LookDown) -> None:
        pass

    def actuate_look_up(self, action: LookUp) -> None:
        pass

    def actuate_move_forward(self, action: MoveForward) -> None:
        pass

    def actuate_move_tangentially(self, action: MoveTangentially) -> None:
        pass

    def actuate_orient_horizontal(self, action: OrientHorizontal) -> None:
        pass

    def actuate_orient_vertical(self, action: OrientVertical) -> None:
        pass

    def actuate_set_agent_pitch(self, action: SetAgentPitch) -> None:
        pass

    def actuate_set_agent_pose(self, action: SetAgentPose) -> None:
        pass

    def actuate_set_sensor_pitch(self, action: SetSensorPitch) -> None:
        pass

    def actuate_set_sensor_pose(self, action: SetSensorPose) -> None:
        pass

    def actuate_set_sensor_rotation(self, action: SetSensorRotation) -> None:
        pass

    def actuate_set_yaw(self, action: SetYaw) -> None:
        pass

    def actuate_turn_left(self, action: TurnLeft) -> None:
        pass

    def actuate_turn_right(self, action: TurnRight) -> None:
        pass
