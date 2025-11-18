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

from tbp.monty.simulators.habitat import actions as _habitat_actions

__all__ = [
    "SetAgentPitch",
    "SetAgentPose",
    "SetSensorPitch",
    "SetSensorPose",
    "SetSensorRotation",
    "SetYaw",
]


class SetYaw:
    def __init__(self, body_action: bool = False) -> None:
        pass

    def __call__(self, scene_node, actuation_spec):
        return None


class SetSensorPitch:
    def __init__(self, body_action: bool = False) -> None:
        pass

    def __call__(self, scene_node, actuation_spec):
        return None


class SetAgentPitch:
    def __init__(self, body_action: bool = False) -> None:
        pass

    def __call__(self, scene_node, actuation_spec):
        return None


class SetSensorPose:
    def __init__(self, body_action: bool = False) -> None:
        pass

    def __call__(self, scene_node, actuation_spec):
        return None


class SetSensorRotation:
    def __init__(self, body_action: bool = False) -> None:
        pass

    def __call__(self, scene_node, actuation_spec):
        return None


class SetAgentPose:
    def __init__(self, body_action: bool = False) -> None:
        pass

    def __call__(self, scene_node, actuation_spec):
        return None

