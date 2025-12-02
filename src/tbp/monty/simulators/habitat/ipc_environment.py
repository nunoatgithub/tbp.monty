# Copyright 2025 Thousand Brains Project
# Copyright 2022-2024 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Habitat environment using IPC for communication with HabitatSim subprocess."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, is_dataclass
from typing import Sequence

import numpy as np
import quaternion as qt

import tbp.monty.simulators.habitat.protocol.v1.protocol_pb2 as protocol_pb2
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
from tbp.monty.frameworks.environments.embodied_environment import (
    EmbodiedEnvironment,
    ObjectID,
    QuaternionWXYZ,
    SemanticID,
    VectorXYZ,
)
from tbp.monty.frameworks.models.abstract_monty_classes import (
    AgentID,
    AgentObservations,
    Observations,
    SensorID,
    SensorObservations,
)
from tbp.monty.frameworks.models.motor_system_state import (
    AgentState,
    ProprioceptiveState,
    SensorState,
)
from tbp.monty.frameworks.utils.dataclass_utils import create_dataclass_args
from tbp.monty.simulators.habitat import HabitatAgent
from tbp.monty.simulators.habitat.ipc_wrapper import (
    HabitatIPCWrapper,
    HabitatSimConfig,
)

logger = logging.getLogger(__name__)

__all__ = [
    "AgentConfig",
    "HabitatIPCEnvironment",
    "ObjectConfig",
]


# Create helper dataclasses
class HabitatAgentArgs:
    pass


@dataclass
class AgentConfig:
    """Agent configuration used by :class:`HabitatIPCEnvironment`."""

    agent_type: type[HabitatAgent]
    agent_args: dict | type[HabitatAgentArgs]


def deserialize_obs_and_state(
    observations: protocol_pb2.Observations,
    proprioceptive_state: protocol_pb2.ProprioceptiveState,
) -> tuple[Observations, ProprioceptiveState]:
    """Deserialize protobuf observations and state to Monty data structures.
    
    Args:
        observations: Protobuf Observations message
        proprioceptive_state: Protobuf ProprioceptiveState message
        
    Returns:
        Tuple of (Observations dict, ProprioceptiveState dict)
    """
    obs = Observations()
    for pb_agent_obs in observations.agent_observations:
        agent_obs = AgentObservations()
        for pb_sensor_obs in pb_agent_obs.sensor_observations:
            sensor_obs = SensorObservations()
            if pb_sensor_obs.HasField("raw"):
                sensor_obs.raw = np.frombuffer(pb_sensor_obs.raw)
            if pb_sensor_obs.HasField("rgba"):
                # NOTE: Resolution is hardcoded to (64, 64) to match default sensor config
                # TODO: Make resolution dynamic based on actual sensor configuration
                sensor_obs.rgba = np.frombuffer(
                    pb_sensor_obs.rgba, dtype=np.uint8
                ).reshape((64, 64, 4))
            if pb_sensor_obs.HasField("depth"):
                # NOTE: Resolution is hardcoded to (64, 64) to match default sensor config
                # TODO: Make resolution dynamic based on actual sensor configuration
                sensor_obs.depth = np.frombuffer(
                    pb_sensor_obs.depth, dtype=np.float32
                ).reshape((64, 64))
            if pb_sensor_obs.HasField("semantic"):
                sensor_obs.semantic = np.frombuffer(pb_sensor_obs.semantic)
            if pb_sensor_obs.HasField("semantic_3d"):
                sensor_obs.semantic_3d = np.frombuffer(pb_sensor_obs.semantic_3d)
            if pb_sensor_obs.HasField("sensor_frame_data"):
                sensor_obs.sensor_frame_data = np.frombuffer(
                    pb_sensor_obs.sensor_frame_data
                )
            if pb_sensor_obs.HasField("world_camera"):
                sensor_obs.world_camera = np.frombuffer(pb_sensor_obs.world_camera)
            if pb_sensor_obs.HasField("pixel_loc"):
                sensor_obs.pixel_loc = np.frombuffer(pb_sensor_obs.pixel_loc)
            agent_obs[SensorID(pb_sensor_obs.sensor_id)] = sensor_obs
        obs[AgentID(pb_agent_obs.agent_id)] = agent_obs

    state = ProprioceptiveState()
    for pb_agent_state in proprioceptive_state.agent_states:
        position = np.array(
            [
                pb_agent_state.position.x,
                pb_agent_state.position.y,
                pb_agent_state.position.z,
            ]
        )
        rotation = qt.quaternion(
            pb_agent_state.rotation.w,
            pb_agent_state.rotation.x,
            pb_agent_state.rotation.y,
            pb_agent_state.rotation.z,
        )
        motor_only_step = (
            pb_agent_state.motor_only_step
            if pb_agent_state.HasField("motor_only_step")
            else False
        )
        sensors = {}
        for pb_sensor_state in pb_agent_state.sensor_states:
            sensor_position = np.array(
                [
                    pb_sensor_state.position.x,
                    pb_sensor_state.position.y,
                    pb_sensor_state.position.z,
                ]
            )
            sensor_rotation = qt.quaternion(
                pb_sensor_state.rotation.w,
                pb_sensor_state.rotation.x,
                pb_sensor_state.rotation.y,
                pb_sensor_state.rotation.z,
            )
            sensors[SensorID(pb_sensor_state.sensor_id)] = SensorState(
                position=sensor_position,
                rotation=sensor_rotation,
            )

        agent_state = AgentState(
            sensors=sensors,
            position=position,
            rotation=rotation,
            motor_only_step=motor_only_step,
        )
        state[AgentID(pb_agent_state.agent_id)] = agent_state

    return obs, state


class HabitatIPCEnvironment(EmbodiedEnvironment):
    """Habitat-sim environment using IPC communication with subprocess.
    
    This environment spawns HabitatSim in a separate process and communicates
    with it using multiprocessing.Queue and protobuf messages, maintaining the
    same data contract as the original implementation.

    Attributes:
        agents: List of :class:`AgentConfig` to place in the scene.
        objects: Optional list of object configurations to place in the scene.
        scene_id: Scene to use or None for empty environment.
        seed: Simulator seed to use
        data_path: Path to the dataset.
    """

    def __init__(
        self,
        agents: dict | AgentConfig,
        objects: list[dict] | None = None,
        scene_id: str | None = None,
        seed: int = 42,
        data_path: str | None = None,
    ):
        super().__init__()
        
        # TODO: Change the configuration to configure multiple agents
        agents = [agents]
        self._agents = []
        for config in agents:
            cfg_dict = asdict(config) if is_dataclass(config) else config
            agent_type = cfg_dict["agent_type"]
            args = cfg_dict["agent_args"]
            if is_dataclass(args):
                args = asdict(args)
            agent = agent_type(**args)
            self._agents.append(agent)

        # Create config for the IPC wrapper
        config = HabitatSimConfig(
            agents=self._agents,
            scene_id=scene_id,
            seed=seed,
            data_path=data_path,
        )
        
        # Initialize the IPC wrapper which spawns the subprocess
        self._ipc_wrapper = HabitatIPCWrapper(config)
        logger.info("HabitatIPCEnvironment initialized with subprocess")

        # Add initial objects if provided
        if objects is not None:
            for obj in objects:
                obj_dict = asdict(obj) if is_dataclass(obj) else obj
                self.add_object(**obj_dict)

    def add_object(
        self,
        name: str,
        position: VectorXYZ = (0.0, 0.0, 0.0),
        rotation: QuaternionWXYZ = (1.0, 0.0, 0.0, 0.0),
        scale: VectorXYZ = (1.0, 1.0, 1.0),
        semantic_id: SemanticID | None = None,
        primary_target_object: ObjectID | None = None,
    ) -> ObjectID:
        """Add an object to the environment.
        
        Args:
            name: Object name
            position: Object position
            rotation: Object rotation quaternion
            scale: Object scale
            semantic_id: Optional semantic ID override
            primary_target_object: Optional primary target object ID
            
        Returns:
            The ID of the added object
        """
        response = self._ipc_wrapper.add_object(
            name=name,
            position=position,
            rotation=rotation,
            scale=scale,
            semantic_id=semantic_id,
            primary_target_object=primary_target_object,
        )
        return ObjectID(response.object_id)

    def step(self, actions: Sequence[Action]) -> dict[str, dict]:
        """Execute actions in the environment.
        
        Args:
            actions: Sequence of actions to execute
            
        Returns:
            Dictionary of observations
        """
        # For now, assume single action (matching current implementation)
        if len(actions) != 1:
            raise ValueError(f"Expected 1 action, got {len(actions)}")
        
        action = actions[0]
        
        # Convert action to protobuf StepRequest
        step_request = self._action_to_protobuf(action)
        
        # Send request and get response
        response = self._ipc_wrapper.step(step_request)
        
        # Deserialize response
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )
        
        return self.observations

    def _action_to_protobuf(self, action: Action) -> protocol_pb2.StepRequest:
        """Convert an Action to a protobuf StepRequest.
        
        Args:
            action: The action to convert
            
        Returns:
            Protobuf StepRequest message
        """
        if isinstance(action, LookDown):
            return protocol_pb2.StepRequest(
                look_down=protocol_pb2.LookDownAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                    constraint_degrees=action.constraint_degrees,
                )
            )
        elif isinstance(action, LookUp):
            return protocol_pb2.StepRequest(
                look_up=protocol_pb2.LookUpAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                    constraint_degrees=action.constraint_degrees,
                )
            )
        elif isinstance(action, MoveForward):
            return protocol_pb2.StepRequest(
                move_forward=protocol_pb2.MoveForwardAction(
                    agent_id=action.agent_id,
                    distance=action.distance,
                )
            )
        elif isinstance(action, MoveTangentially):
            return protocol_pb2.StepRequest(
                move_tangentially=protocol_pb2.MoveTangentiallyAction(
                    agent_id=action.agent_id,
                    distance=action.distance,
                    direction=protocol_pb2.VectorXYZ(
                        x=action.direction[0],
                        y=action.direction[1],
                        z=action.direction[2],
                    ),
                )
            )
        elif isinstance(action, OrientHorizontal):
            return protocol_pb2.StepRequest(
                orient_horizontal=protocol_pb2.OrientHorizontalAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                    left_distance=action.left_distance,
                    forward_distance=action.forward_distance,
                )
            )
        elif isinstance(action, OrientVertical):
            return protocol_pb2.StepRequest(
                orient_vertical=protocol_pb2.OrientVerticalAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                    down_distance=action.down_distance,
                    forward_distance=action.forward_distance,
                )
            )
        elif isinstance(action, SetAgentPitch):
            return protocol_pb2.StepRequest(
                set_agent_pitch=protocol_pb2.SetAgentPitchAction(
                    agent_id=action.agent_id,
                    pitch_degrees=action.pitch_degrees,
                )
            )
        elif isinstance(action, SetAgentPose):
            return protocol_pb2.StepRequest(
                set_agent_pose=protocol_pb2.SetAgentPoseAction(
                    agent_id=action.agent_id,
                    location=protocol_pb2.VectorXYZ(
                        x=action.location[0],
                        y=action.location[1],
                        z=action.location[2],
                    ),
                    rotation=protocol_pb2.QuaternionWXYZ(
                        w=action.rotation_quat.w,
                        x=action.rotation_quat.x,
                        y=action.rotation_quat.y,
                        z=action.rotation_quat.z,
                    ),
                )
            )
        elif isinstance(action, SetSensorPitch):
            return protocol_pb2.StepRequest(
                set_sensor_pitch=protocol_pb2.SetSensorPitchAction(
                    agent_id=action.agent_id,
                    pitch_degrees=action.pitch_degrees,
                )
            )
        elif isinstance(action, SetSensorPose):
            return protocol_pb2.StepRequest(
                set_sensor_pose=protocol_pb2.SetSensorPoseAction(
                    agent_id=action.agent_id,
                    location=protocol_pb2.VectorXYZ(
                        x=action.location[0],
                        y=action.location[1],
                        z=action.location[2],
                    ),
                    rotation=protocol_pb2.QuaternionWXYZ(
                        w=action.rotation_quat.w,
                        x=action.rotation_quat.x,
                        y=action.rotation_quat.y,
                        z=action.rotation_quat.z,
                    ),
                )
            )
        elif isinstance(action, SetSensorRotation):
            return protocol_pb2.StepRequest(
                set_sensor_rotation=protocol_pb2.SetSensorRotationAction(
                    agent_id=action.agent_id,
                    rotation=protocol_pb2.QuaternionWXYZ(
                        w=action.rotation_quat.w,
                        x=action.rotation_quat.x,
                        y=action.rotation_quat.y,
                        z=action.rotation_quat.z,
                    ),
                )
            )
        elif isinstance(action, SetYaw):
            return protocol_pb2.StepRequest(
                set_yaw=protocol_pb2.SetYawAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                )
            )
        elif isinstance(action, TurnLeft):
            return protocol_pb2.StepRequest(
                turn_left=protocol_pb2.TurnLeftAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                )
            )
        elif isinstance(action, TurnRight):
            return protocol_pb2.StepRequest(
                turn_right=protocol_pb2.TurnRightAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                )
            )
        else:
            raise TypeError(f"Unsupported action type: {type(action)}")

    def remove_all_objects(self) -> None:
        """Remove all objects from the environment."""
        self._ipc_wrapper.remove_all_objects()

    def reset(self):
        """Reset the environment.
        
        Returns:
            Tuple of (observations, proprioceptive_state)
        """
        response = self._ipc_wrapper.reset()
        observations, state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )
        self.observations = observations
        self.state = state
        return observations, state

    def close(self) -> None:
        """Close the environment and terminate the subprocess."""
        wrapper = getattr(self, "_ipc_wrapper", None)
        if wrapper is not None:
            wrapper.close()
            self._ipc_wrapper = None
        logger.info("HabitatIPCEnvironment closed")

    def get_state(self):
        """Get the current proprioceptive state."""
        return getattr(self, "state", None)
