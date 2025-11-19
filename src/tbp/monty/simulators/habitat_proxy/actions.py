# Copyright 2025 Thousand Brains Project
# Copyright 2022-2024 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from tbp.monty.simulators.habitat_impl import actions as _habitat_impl_actions

__all__ = [
    "SetAgentPitch",
    "SetAgentPose",
    "SetSensorPitch",
    "SetSensorPose",
    "SetSensorRotation",
    "SetYaw",
]


class SetYaw:
    def __init__(self, body_action: bool = True) -> None:
        self._delegate = _habitat_impl_actions.SetYaw(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)


class SetSensorPitch:
    def __init__(self, body_action: bool = False) -> None:
        self._delegate = _habitat_impl_actions.SetSensorPitch(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)


class SetAgentPitch:
    def __init__(self, body_action: bool = True) -> None:
        self._delegate = _habitat_impl_actions.SetAgentPitch(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)


class SetSensorPose:
    def __init__(self, body_action: bool = False) -> None:
        self._delegate = _habitat_impl_actions.SetSensorPose(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)


class SetSensorRotation:
    def __init__(self, body_action: bool = False) -> None:
        self._delegate = _habitat_impl_actions.SetSensorRotation(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)


class SetAgentPose:
    def __init__(self, body_action: bool = True) -> None:
        self._delegate = _habitat_impl_actions.SetAgentPose(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)


class MoveForward:
    def __init__(self, body_action: bool = False) -> None:
        self._delegate = _habitat_impl_actions.MoveForward(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)


class MoveTangentially:
    def __init__(self, body_action: bool = False) -> None:
        self._delegate = _habitat_impl_actions.MoveTangentially(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)


class OrientHorizontal:
    def __init__(self, body_action: bool = False) -> None:
        self._delegate = _habitat_impl_actions.OrientHorizontal(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)


class OrientVertical:
    def __init__(self, body_action: bool = False) -> None:
        self._delegate = _habitat_impl_actions.OrientVertical(body_action=body_action)

    def __call__(self, scene_node, actuation_spec):
        return self._delegate(scene_node, actuation_spec)
