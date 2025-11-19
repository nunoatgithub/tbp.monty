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
from tbp.monty.simulators.habitat_impl import actuator as _habitat_impl_actuator

__all__ = [
    "HabitatActuator",
    "HabitatActuatorRequirements",
]


class HabitatActuatorRequirements(Protocol):
    def get_agent(self, agent_id: AgentID) -> Agent | None: ...


class HabitatActuator(HabitatActuatorRequirements):
    """Proxy for habitat actuator - delegates to habitat_impl.HabitatActuator."""
    def __init__(self, *args, **kwargs):
        self._delegate = _habitat_impl_actuator.HabitatActuator(*args, **kwargs)

    def __getattr__(self, name):
        return self._delegate.__getattribute__(name)

    def action_name(self, action: Action) -> str:
        return self._delegate.action_name(action)

    def to_habitat(self, action: Action) -> tuple[Agent, ActuationSpec, str]:
        try:
            return self._delegate.to_habitat(action)
        except _habitat_impl_actuator.InvalidActionName as e:
            raise InvalidActionName(str(e)) from e
        except _habitat_impl_actuator.NoActionParameters as e:
            raise NoActionParameters(str(e)) from e

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


class InvalidActionName(Exception):
    """Proxy for InvalidActionName exception from habitat_impl.actuator."""
    def __init__(self, action_name: str):
        super().__init__(action_name)

class NoActionParameters(Exception):
    """Proxy for NoActionParameters exception from habitat_impl.actuator."""
    def __init__(self, action_name: str):
        super().__init__(action_name)
