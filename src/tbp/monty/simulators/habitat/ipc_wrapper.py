# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""IPC-based wrapper for HabitatSim using multiprocessing.Queue and protobuf.

This module provides an IPC-based communication layer for HabitatSim that uses
multiprocessing.Queue for transport while maintaining the same protobuf schema
and wire format as the original gRPC implementation.
"""

from __future__ import annotations

import logging
import multiprocessing
import os
from dataclasses import asdict, dataclass
from multiprocessing import Process, Queue
from typing import Any

import numpy as np
import quaternion as qt

import tbp.monty.simulators.habitat.protocol.v1.protocol_pb2 as protocol_pb2
from tbp.monty.frameworks.actions.actions import (
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
from tbp.monty.frameworks.config_utils.make_dataset_configs import (
    PatchAndViewFinderMountConfig,
)
from tbp.monty.frameworks.environments.embodied_environment import (
    QuaternionWXYZ,
    VectorXYZ,
)
from tbp.monty.simulators.habitat.agents import (
    HabitatAgent,
    MultiSensorAgent,
)
from tbp.monty.simulators.habitat.simulator import HabitatSim

logger = logging.getLogger(__name__)


def serialize_obs_and_state(observations, proprioceptive_state):
    """Serialize observations and proprioceptive state to protobuf format.
    
    Args:
        observations: Dict of agent observations
        proprioceptive_state: Dict of agent proprioceptive states
        
    Returns:
        Tuple of (protobuf Observations, protobuf ProprioceptiveState)
    """
    pb_obs = protocol_pb2.Observations()
    for agent_id, agent_obs in observations.items():
        pb_agent_obs = pb_obs.agent_observations.add(agent_id=agent_id)
        for sensor_id, sensor_obs in agent_obs.items():
            pb_sensor_obs = pb_agent_obs.sensor_observations.add(sensor_id=sensor_id)
            for modality, data in sensor_obs.items():
                if modality == "raw":
                    pb_sensor_obs.raw = data.tobytes()
                elif modality == "rgba":
                    pb_sensor_obs.rgba = data.tobytes()
                elif modality == "depth":
                    pb_sensor_obs.depth = data.tobytes()
                elif modality == "semantic":
                    pb_sensor_obs.semantic = data.tobytes()
                elif modality == "semantic_3d":
                    pb_sensor_obs.semantic_3d = data.tobytes()
                elif modality == "sensor_frame_data":
                    pb_sensor_obs.sensor_frame_data = data.tobytes()
                elif modality == "world_camera":
                    pb_sensor_obs.world_camera = data.tobytes()
                elif modality == "pixel_loc":
                    pb_sensor_obs.pixel_loc = data.tobytes()

    pb_state = protocol_pb2.ProprioceptiveState()
    for agent_id, agent_state in proprioceptive_state.items():
        pb_agent_state = pb_state.agent_states.add(agent_id=agent_id)
        pb_agent_state.position.x = agent_state.position[0]
        pb_agent_state.position.y = agent_state.position[1]
        pb_agent_state.position.z = agent_state.position[2]
        pb_agent_state.rotation.w = agent_state.rotation.w
        pb_agent_state.rotation.x = agent_state.rotation.x
        pb_agent_state.rotation.y = agent_state.rotation.y
        pb_agent_state.rotation.z = agent_state.rotation.z
        if hasattr(agent_state, "motor_only_step"):
            pb_agent_state.motor_only_step = agent_state.motor_only_step
        
        for sensor_id, sensor_state in agent_state.sensors.items():
            pb_sensor_state = pb_agent_state.sensor_states.add(sensor_id=sensor_id)
            pb_sensor_state.position.x = sensor_state.position[0]
            pb_sensor_state.position.y = sensor_state.position[1]
            pb_sensor_state.position.z = sensor_state.position[2]
            pb_sensor_state.rotation.w = sensor_state.rotation.w
            pb_sensor_state.rotation.x = sensor_state.rotation.x
            pb_sensor_state.rotation.y = sensor_state.rotation.y
            pb_sensor_state.rotation.z = sensor_state.rotation.z
            
    return pb_obs, pb_state


def habitat_sim_process(request_queue: Queue, response_queue: Queue, config: dict):
    """Process function that runs HabitatSim and handles IPC requests.
    
    This function runs in a separate process and communicates with the main
    process via multiprocessing.Queue. It receives protobuf-serialized requests
    and sends back protobuf-serialized responses.
    
    Args:
        request_queue: Queue for receiving requests from main process
        response_queue: Queue for sending responses to main process
        config: Configuration dict for HabitatSim initialization
    """
    logger.info("HabitatSim subprocess starting")
    
    # Initialize HabitatSim with the provided config
    agents = config.get("agents", [])
    data_path = config.get("data_path")
    scene_id = config.get("scene_id")
    seed = config.get("seed", 42)
    
    habitat_sim = HabitatSim(
        agents=agents,
        data_path=data_path,
        scene_id=scene_id,
        seed=seed,
    )
    logger.info("HabitatSim initialized in subprocess")
    
    # Main message handling loop
    while True:
        try:
            request_bytes = request_queue.get()
            
            # Deserialize the request based on message type
            # The message format is (operation_type, serialized_protobuf_message)
            op_type, msg_bytes = request_bytes
            
            if op_type == "remove_all_objects":
                logger.debug("Processing RemoveAllObjects")
                habitat_sim.remove_all_objects()
                response = protocol_pb2.RemoveAllObjectsResponse()
                response_queue.put(("remove_all_objects", response.SerializeToString()))
                
            elif op_type == "add_object":
                logger.debug("Processing AddObject")
                request = protocol_pb2.AddObjectRequest()
                request.ParseFromString(msg_bytes)
                
                position = VectorXYZ((
                    request.position.x,
                    request.position.y,
                    request.position.z,
                ))
                rotation = QuaternionWXYZ((
                    request.rotation.w,
                    request.rotation.x,
                    request.rotation.y,
                    request.rotation.z,
                ))
                scale = VectorXYZ((
                    request.scale.x,
                    request.scale.y,
                    request.scale.z,
                ))
                semantic_id = request.semantic_id if request.HasField("semantic_id") else None
                primary_target_object = (
                    request.primary_target_object
                    if request.HasField("primary_target_object")
                    else None
                )
                
                object_info = habitat_sim.add_object(
                    name=request.name,
                    position=position,
                    rotation=rotation,
                    scale=scale,
                    semantic_id=semantic_id,
                    primary_target_object=primary_target_object,
                )
                
                response = protocol_pb2.AddObjectResponse(
                    object_id=object_info.object_id,
                    semantic_id=object_info.semantic_id,
                )
                response_queue.put(("add_object", response.SerializeToString()))
                
            elif op_type == "step":
                logger.debug("Processing Step")
                request = protocol_pb2.StepRequest()
                request.ParseFromString(msg_bytes)
                
                # Deserialize the action from the protobuf request
                action_type = request.WhichOneof("action")
                action = _deserialize_action(request, action_type)
                
                # Execute the action
                observations, proprioceptive_state = habitat_sim.apply_actions([action])
                
                # Serialize the response
                pb_obs, pb_state = serialize_obs_and_state(
                    observations, proprioceptive_state
                )
                
                response = protocol_pb2.StepResponse(
                    observations=pb_obs,
                    proprioceptive_state=pb_state,
                )
                response_queue.put(("step", response.SerializeToString()))
                
            elif op_type == "reset":
                logger.debug("Processing Reset")
                observations, proprioceptive_state = habitat_sim.reset()
                
                pb_obs, pb_state = serialize_obs_and_state(
                    observations, proprioceptive_state
                )
                
                response = protocol_pb2.ResetResponse(
                    observations=pb_obs,
                    proprioceptive_state=pb_state,
                )
                response_queue.put(("reset", response.SerializeToString()))
                
            elif op_type == "close":
                logger.info("Processing Close - shutting down subprocess")
                habitat_sim.close()
                response = protocol_pb2.CloseResponse()
                response_queue.put(("close", response.SerializeToString()))
                break
                
            else:
                logger.error(f"Unknown operation type: {op_type}")
                
        except Exception as e:
            logger.error(f"Error in habitat_sim_process: {e}", exc_info=True)
            response_queue.put(("error", str(e)))
    
    logger.info("HabitatSim subprocess terminating")


def _deserialize_action(request: protocol_pb2.StepRequest, action_type: str):
    """Deserialize an action from a protobuf StepRequest.
    
    Args:
        request: The protobuf StepRequest
        action_type: The type of action (from WhichOneof)
        
    Returns:
        The deserialized Action object
    """
    if action_type == "look_down":
        look_down = request.look_down
        return LookDown(
            agent_id=look_down.agent_id,
            rotation_degrees=look_down.rotation_degrees,
            constraint_degrees=look_down.constraint_degrees,
        )
    elif action_type == "look_up":
        look_up = request.look_up
        return LookUp(
            agent_id=look_up.agent_id,
            rotation_degrees=look_up.rotation_degrees,
            constraint_degrees=look_up.constraint_degrees,
        )
    elif action_type == "move_forward":
        move_forward = request.move_forward
        return MoveForward(
            agent_id=move_forward.agent_id,
            distance=move_forward.distance,
        )
    elif action_type == "move_tangentially":
        move_tangentially = request.move_tangentially
        return MoveTangentially(
            agent_id=move_tangentially.agent_id,
            distance=move_tangentially.distance,
            direction=VectorXYZ((
                move_tangentially.direction.x,
                move_tangentially.direction.y,
                move_tangentially.direction.z,
            )),
        )
    elif action_type == "orient_horizontal":
        orient_horizontal = request.orient_horizontal
        return OrientHorizontal(
            agent_id=orient_horizontal.agent_id,
            rotation_degrees=orient_horizontal.rotation_degrees,
            left_distance=orient_horizontal.left_distance,
            forward_distance=orient_horizontal.forward_distance,
        )
    elif action_type == "orient_vertical":
        orient_vertical = request.orient_vertical
        return OrientVertical(
            agent_id=orient_vertical.agent_id,
            rotation_degrees=orient_vertical.rotation_degrees,
            down_distance=orient_vertical.down_distance,
            forward_distance=orient_vertical.forward_distance,
        )
    elif action_type == "set_agent_pitch":
        set_agent_pitch = request.set_agent_pitch
        return SetAgentPitch(
            agent_id=set_agent_pitch.agent_id,
            pitch_degrees=set_agent_pitch.pitch_degrees,
        )
    elif action_type == "set_agent_pose":
        set_agent_pose = request.set_agent_pose
        location = VectorXYZ((
            set_agent_pose.location.x,
            set_agent_pose.location.y,
            set_agent_pose.location.z,
        ))
        rotation = qt.quaternion(
            set_agent_pose.rotation.w,
            set_agent_pose.rotation.x,
            set_agent_pose.rotation.y,
            set_agent_pose.rotation.z,
        )
        return SetAgentPose(
            agent_id=set_agent_pose.agent_id,
            location=location,
            rotation_quat=rotation,
        )
    elif action_type == "set_sensor_pitch":
        set_sensor_pitch = request.set_sensor_pitch
        return SetSensorPitch(
            agent_id=set_sensor_pitch.agent_id,
            pitch_degrees=set_sensor_pitch.pitch_degrees,
        )
    elif action_type == "set_sensor_pose":
        set_sensor_pose = request.set_sensor_pose
        location = VectorXYZ((
            set_sensor_pose.location.x,
            set_sensor_pose.location.y,
            set_sensor_pose.location.z,
        ))
        rotation = qt.quaternion(
            set_sensor_pose.rotation.w,
            set_sensor_pose.rotation.x,
            set_sensor_pose.rotation.y,
            set_sensor_pose.rotation.z,
        )
        return SetSensorPose(
            agent_id=set_sensor_pose.agent_id,
            location=location,
            rotation_quat=rotation,
        )
    elif action_type == "set_sensor_rotation":
        set_sensor_rotation = request.set_sensor_rotation
        rotation = qt.quaternion(
            set_sensor_rotation.rotation.w,
            set_sensor_rotation.rotation.x,
            set_sensor_rotation.rotation.y,
            set_sensor_rotation.rotation.z,
        )
        return SetSensorRotation(
            agent_id=set_sensor_rotation.agent_id,
            rotation_quat=rotation,
        )
    elif action_type == "set_yaw":
        set_yaw = request.set_yaw
        return SetYaw(
            agent_id=set_yaw.agent_id,
            rotation_degrees=set_yaw.rotation_degrees,
        )
    elif action_type == "turn_left":
        turn_left = request.turn_left
        return TurnLeft(
            agent_id=turn_left.agent_id,
            rotation_degrees=turn_left.rotation_degrees,
        )
    elif action_type == "turn_right":
        turn_right = request.turn_right
        return TurnRight(
            agent_id=turn_right.agent_id,
            rotation_degrees=turn_right.rotation_degrees,
        )
    else:
        raise ValueError(f"Unknown action type: {action_type}")


@dataclass
class HabitatSimConfig:
    """Configuration for HabitatSim initialization."""
    agents: list[HabitatAgent]
    data_path: str
    scene_id: str | None = None
    seed: int = 42


class HabitatIPCWrapper:
    """Wrapper that manages HabitatSim in a subprocess with IPC communication.
    
    This class spawns HabitatSim in a separate process and communicates with it
    using multiprocessing.Queue and protobuf messages, maintaining the same data
    contract as the original gRPC implementation.
    """
    
    def __init__(self, config: HabitatSimConfig):
        """Initialize the IPC wrapper and spawn the HabitatSim subprocess.
        
        Args:
            config: Configuration for HabitatSim
        """
        self.config = config
        self.request_queue = Queue()
        self.response_queue = Queue()
        
        # Convert config to dict for passing to subprocess
        config_dict = asdict(config)
        
        # Start the subprocess
        self.process = Process(
            target=habitat_sim_process,
            args=(self.request_queue, self.response_queue, config_dict),
        )
        self.process.start()
        logger.info(f"Started HabitatSim subprocess with PID: {self.process.pid}")
    
    def remove_all_objects(self):
        """Remove all objects from the simulator."""
        request = protocol_pb2.RemoveAllObjectsRequest()
        self.request_queue.put(("remove_all_objects", request.SerializeToString()))
        op_type, response_bytes = self.response_queue.get()
        response = protocol_pb2.RemoveAllObjectsResponse()
        response.ParseFromString(response_bytes)
        return response
    
    def add_object(
        self,
        name: str,
        position: VectorXYZ = (0.0, 0.0, 0.0),
        rotation: QuaternionWXYZ = (1.0, 0.0, 0.0, 0.0),
        scale: VectorXYZ = (1.0, 1.0, 1.0),
        semantic_id: int | None = None,
        primary_target_object: int | None = None,
    ):
        """Add an object to the simulator.
        
        Args:
            name: Object name
            position: Object position (x, y, z)
            rotation: Object rotation quaternion (w, x, y, z)
            scale: Object scale (x, y, z)
            semantic_id: Optional semantic ID
            primary_target_object: Optional primary target object ID
            
        Returns:
            AddObjectResponse with object_id and semantic_id
        """
        request = protocol_pb2.AddObjectRequest()
        request.name = name
        request.position.x = position[0]
        request.position.y = position[1]
        request.position.z = position[2]
        request.rotation.w = rotation[0]
        request.rotation.x = rotation[1]
        request.rotation.y = rotation[2]
        request.rotation.z = rotation[3]
        request.scale.x = scale[0]
        request.scale.y = scale[1]
        request.scale.z = scale[2]
        if semantic_id is not None:
            request.semantic_id = semantic_id
        if primary_target_object is not None:
            request.primary_target_object = primary_target_object
        
        self.request_queue.put(("add_object", request.SerializeToString()))
        op_type, response_bytes = self.response_queue.get()
        response = protocol_pb2.AddObjectResponse()
        response.ParseFromString(response_bytes)
        return response
    
    def step(self, action_request: protocol_pb2.StepRequest):
        """Execute a step with the given action.
        
        Args:
            action_request: Protobuf StepRequest with the action to execute
            
        Returns:
            StepResponse with observations and proprioceptive state
        """
        self.request_queue.put(("step", action_request.SerializeToString()))
        op_type, response_bytes = self.response_queue.get()
        response = protocol_pb2.StepResponse()
        response.ParseFromString(response_bytes)
        return response
    
    def reset(self):
        """Reset the simulator.
        
        Returns:
            ResetResponse with initial observations and proprioceptive state
        """
        request = protocol_pb2.ResetRequest()
        self.request_queue.put(("reset", request.SerializeToString()))
        op_type, response_bytes = self.response_queue.get()
        response = protocol_pb2.ResetResponse()
        response.ParseFromString(response_bytes)
        return response
    
    def close(self):
        """Close the simulator and terminate the subprocess."""
        request = protocol_pb2.CloseRequest()
        self.request_queue.put(("close", request.SerializeToString()))
        op_type, response_bytes = self.response_queue.get()
        
        # Wait for the process to terminate
        self.process.join(timeout=5)
        if self.process.is_alive():
            logger.warning("HabitatSim subprocess did not terminate gracefully, forcing...")
            self.process.terminate()
            self.process.join(timeout=2)
            if self.process.is_alive():
                self.process.kill()
                self.process.join()
        
        logger.info("HabitatSim subprocess terminated")
