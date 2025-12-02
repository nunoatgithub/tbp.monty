# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
from __future__ import annotations

import inspect
import logging
import os
from concurrent import futures
from dataclasses import asdict, dataclass
from queue import Queue

import grpc
import numpy as np
import quaternion as qt
from grpc_reflection.v1alpha import reflection

import tbp.simulator.protocol.v1.protocol_pb2 as protocol_pb2
import tbp.simulator.protocol.v1.protocol_pb2_grpc as protocol_pb2_grpc
from tbp.monty.frameworks.run_env import setup_env

setup_env()

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
from tbp.simulator_habitat.agents import (
    HabitatAgent,
    MultiSensorAgent,
)
from tbp.simulator_habitat.simulator import HabitatSim

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This is a sanity check that we are using the correct protocol files
logger.info(protocol_pb2.__file__)
logger.info(inspect.getsourcefile(protocol_pb2))

def serialize_obs_and_state(observations, proprioceptive_state):
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
        for sensor_id, sensor_state in agent_state.sensors.items():
            pb_sensor_state = pb_agent_state.sensor_states.add(sensor_id=sensor_id)
            pb_sensor_state.position.x = sensor_state.position.x
            pb_sensor_state.position.y = sensor_state.position.y
            pb_sensor_state.position.z = sensor_state.position.z
            pb_sensor_state.rotation.w = sensor_state.rotation.w
            pb_sensor_state.rotation.x = sensor_state.rotation.x
            pb_sensor_state.rotation.y = sensor_state.rotation.y
            pb_sensor_state.rotation.z = sensor_state.rotation.z
    return pb_obs, pb_state

class SimulatorServiceServicer(protocol_pb2_grpc.SimulatorServiceServicer):
    def __init__(self, to_habitat: Queue, from_habitat: Queue):
        logger.info("SimulatorServiceServicer initialized")
        self.to_habitat = to_habitat
        self.from_habitat = from_habitat

    def RemoveAllObjects(self, request, context):  # noqa: N802
        logger.info("remove_all_objects: removing all objects")
        self.to_habitat.put({"op": "remove_all_objects"})
        self.from_habitat.get()
        logger.debug("remove_all_objects: serializing")
        return protocol_pb2.RemoveAllObjectsResponse()

    def AddObject(self, request, context):  # noqa: N802
        logger.info("add_object: adding object")
        logger.debug(request)
        position = VectorXYZ(
            (request.position.x, request.position.y, request.position.z)
        )
        rotation = QuaternionWXYZ(
            (
                request.rotation.w,
                request.rotation.x,
                request.rotation.y,
                request.rotation.z,
            )
        )
        scale = VectorXYZ((request.scale.x, request.scale.y, request.scale.z))
        semantic_id = request.semantic_id if request.HasField("semantic_id") else None
        primary_target_object = (
            request.primary_target_object
            if request.HasField("primary_target_object")
            else None
        )
        self.to_habitat.put(
            {
                "op": "add_object",
                "name": request.name,
                "position": position,
                "rotation": rotation,
                "scale": scale,
                "semantic_id": semantic_id,
                "primary_target_object": primary_target_object,
            }
        )

        response = self.from_habitat.get()

        logger.debug("add_object: serializing")
        return protocol_pb2.AddObjectResponse(
            object_id=response["object_id"],
            semantic_id=response["semantic_id"],
        )

    def Step(self, request, context):  # noqa: N802
        logger.debug("step: stepping")
        logger.debug(request)
        action_type = request.WhichOneof("action")
        if action_type == "look_down":
            logger.info("step: looking down")
            look_down = request.look_down
            action = LookDown(
                agent_id=look_down.agent_id,
                rotation_degrees=look_down.rotation_degrees,
                constraint_degrees=look_down.constraint_degrees,
            )
        elif action_type == "look_up":
            logger.info("step: looking up")
            look_up = request.look_up
            action = LookUp(
                agent_id=look_up.agent_id,
                rotation_degrees=look_up.rotation_degrees,
                constraint_degrees=look_up.constraint_degrees,
            )
        elif action_type == "move_forward":
            logger.info("step: moving forward")
            move_forward = request.move_forward
            action = MoveForward(
                agent_id=move_forward.agent_id,
                distance=move_forward.distance,
            )
        elif action_type == "move_tangentially":
            logger.info("step: moving tangentially")
            move_tangentially = request.move_tangentially
            action = MoveTangentially(
                agent_id=move_tangentially.agent_id,
                distance=move_tangentially.distance,
                direction=move_tangentially.direction,
            )
        elif action_type == "orient_horizontal":
            logger.info("step: orienting horizontally")
            orient_horizontal = request.orient_horizontal
            action = OrientHorizontal(
                agent_id=orient_horizontal.agent_id,
                rotation_degrees=orient_horizontal.rotation_degrees,
                left_distance=orient_horizontal.left_distance,
                forward_distance=orient_horizontal.forward_distance,
            )
        elif action_type == "orient_vertical":
            logger.info("step: orienting vertically")
            orient_vertical = request.orient_vertical
            action = OrientVertical(
                agent_id=orient_vertical.agent_id,
                rotation_degrees=orient_vertical.rotation_degrees,
                down_distance=orient_vertical.down_distance,
                forward_distance=orient_vertical.forward_distance,
            )
        elif action_type == "set_agent_pitch":
            logger.info("step: setting agent pitch")
            set_agent_pitch = request.set_agent_pitch
            action = SetAgentPitch(
                agent_id=set_agent_pitch.agent_id,
                pitch_degrees=set_agent_pitch.pitch_degrees,
            )
        elif action_type == "set_agent_pose":
            logger.info("step: setting agent pose")
            set_agent_pose = request.set_agent_pose
            location = VectorXYZ(
                (
                    set_agent_pose.location.x,
                    set_agent_pose.location.y,
                    set_agent_pose.location.z,
                )
            )
            rotation = np.quaternion(
                set_agent_pose.rotation.w,
                set_agent_pose.rotation.x,
                set_agent_pose.rotation.y,
                set_agent_pose.rotation.z,
            )
            action = SetAgentPose(
                agent_id=set_agent_pose.agent_id,
                location=location,
                rotation_quat=rotation,
            )
        elif action_type == "set_sensor_pitch":
            logger.info("step: setting sensor pitch")
            set_sensor_pitch = request.set_sensor_pitch
            action = SetSensorPitch(
                agent_id=set_sensor_pitch.agent_id,
                pitch_degrees=set_sensor_pitch.pitch_degrees,
            )
        elif action_type == "set_sensor_pose":
            logger.info("step: setting sensor pose")
            set_sensor_pose = request.set_sensor_pose
            location = VectorXYZ(
                (
                    set_sensor_pose.location.x,
                    set_sensor_pose.location.y,
                    set_sensor_pose.location.z,
                )
            )
            rotation = np.quaternion(
                set_sensor_pose.rotation.w,
                set_sensor_pose.rotation.x,
                set_sensor_pose.rotation.y,
                set_sensor_pose.rotation.z,
            )
            action = SetSensorPose(
                agent_id=set_sensor_pose.agent_id,
                location=location,
                rotation_quat=rotation,
            )
        elif action_type == "set_sensor_rotation":
            logger.info("step: setting sensor rotation")
            set_sensor_rotation = request.set_sensor_rotation
            rotation = np.quaternion(
                set_sensor_rotation.rotation.w,
                set_sensor_rotation.rotation.x,
                set_sensor_rotation.rotation.y,
                set_sensor_rotation.rotation.z,
            )
            action = SetSensorRotation(
                agent_id=set_sensor_rotation.agent_id,
                rotation_quat=rotation,
            )
        elif action_type == "set_yaw":
            logger.info("step: setting yaw")
            set_yaw = request.set_yaw
            action = SetYaw(
                agent_id=set_yaw.agent_id,
                rotation_degrees=set_yaw.rotation_degrees,
            )
        elif action_type == "turn_left":
            logger.info("step: turning left")
            turn_left = request.turn_left
            action = TurnLeft(
                agent_id=turn_left.agent_id,
                rotation_degrees=turn_left.rotation_degrees,
            )
        elif action_type == "turn_right":
            logger.info("step: turning right")
            turn_right = request.turn_right
            action = TurnRight(
                agent_id=turn_right.agent_id,
                rotation_degrees=turn_right.rotation_degrees,
            )
        else:
            logger.error(f"step: unknown action: {action_type}")
            return protocol_pb2.StepResponse()
        self.to_habitat.put({"op": "step", "action": action})

        response = self.from_habitat.get()
        observations = response["observations"]
        proprioceptive_state = response["proprioceptive_state"]
        logger.debug("step: serializing")

        pb_obs, pb_state = serialize_obs_and_state(observations, proprioceptive_state)

        return protocol_pb2.StepResponse(
            observations=pb_obs,
            proprioceptive_state=pb_state,
        )

    def Reset(self, request, context):  # noqa: N802
        logger.info("reset: resetting")
        self.to_habitat.put({"op": "reset"})

        response = self.from_habitat.get()
        observations = response["observations"]
        proprioceptive_state = response["proprioceptive_state"]
        logger.debug("reset: serializing")

        pb_obs, pb_state = serialize_obs_and_state(observations, proprioceptive_state)

        return protocol_pb2.ResetResponse(
            observations=pb_obs,
            proprioceptive_state=pb_state,
        )

    def Close(self, request, context):  # noqa: N802
        logger.info("close: I'm afraid I can't do that, Dave.")
        return protocol_pb2.CloseResponse()


def serve(to_habitat: Queue, from_habitat: Queue):
    # The threadpool max_workers cannot be 1, somehow we get into deadlock if it is.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    protocol_pb2_grpc.add_SimulatorServiceServicer_to_server(
        SimulatorServiceServicer(to_habitat, from_habitat), server
    )
    service_names = (
        protocol_pb2.DESCRIPTOR.services_by_name["SimulatorService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)
    server.add_insecure_port("[::]:50051")
    server.start()
    return server

@dataclass
class HabitatSimConfig:
    agents: list[HabitatAgent]
    data_path: str
    scene_id: str | None = None
    seed: int = 42


def base_config_10distinctobj_dist_agent() -> HabitatSimConfig:
    return HabitatSimConfig(
        agents=[MultiSensorAgent(**PatchAndViewFinderMountConfig().__dict__)],
        data_path=os.path.join(os.environ["MONTY_DATA"], "habitat/objects/ycb"),
    )

def create_habitat_sim(to_habitat: Queue, from_habitat: Queue) -> HabitatSim:
    logger.info("Creating habitat sim")
    habitat_sim_config = base_config_10distinctobj_dist_agent()
    habitat_sim = HabitatSim(**asdict(habitat_sim_config))
    logger.info("Habitat sim created")
    while True:
        logger.debug("Waiting for message")
        msg = to_habitat.get()
        if msg["op"] == "remove_all_objects":
            habitat_sim.remove_all_objects()
            from_habitat.put({})
        elif msg["op"] == "add_object":
            object_id, semantic_id = habitat_sim.add_object(
                name=msg["name"],
                position=msg["position"],
                rotation=msg["rotation"],
                scale=msg["scale"],
                semantic_id=msg["semantic_id"],
                primary_target_object=msg["primary_target_object"],
            )
            from_habitat.put(
                {
                    "object_id": object_id,
                    "semantic_id": semantic_id,
                }
            )
        elif msg["op"] == "step":
            observations, proprioceptive_state = habitat_sim.step(msg["action"])
            from_habitat.put(
                {
                    "observations": observations,
                    "proprioceptive_state": proprioceptive_state,
                }
            )
        elif msg["op"] == "reset":
            observations, proprioceptive_state = habitat_sim.reset()
            from_habitat.put(
                {
                    "observations": observations,
                    "proprioceptive_state": proprioceptive_state,
                }
            )
        else:
            logger.error(f"Unknown operation: {msg['op']}")
            from_habitat.put({})

if __name__ == "__main__":
    logger.info("Starting server")
    # Using queues to communicate with HabitatSim because
    # attempting to use the HabitatSim reference from a thread in
    # the threadpool of the GRPC server causes HabitatSim
    # to go into uninterruptible sleep requiring machine restart.
    # SIGKILL, SIGTERM, et. al. cannot kill the process.
    to_habitat: Queue = Queue()
    from_habitat: Queue = Queue()
    server = serve(to_habitat, from_habitat)
    create_habitat_sim(to_habitat, from_habitat)
    server.wait_for_termination()
