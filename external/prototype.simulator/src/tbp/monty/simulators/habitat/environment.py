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

import logging
from dataclasses import asdict, dataclass
from typing import Type

import grpc
import numpy as np
import quaternion as qt

import tbp.simulator.protocol.v1.protocol_pb2 as protocol_pb2
import tbp.simulator.protocol.v1.protocol_pb2_grpc as protocol_pb2_grpc
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
from tbp.monty.frameworks.config_utils.make_dataset_configs import ObjectParams
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
from tbp.monty.frameworks.utils.dataclass_utils import (
    create_dataclass_args,
    is_dataclass_instance,
)

logger = logging.getLogger(__name__)

__all__ = [
    "AgentConfig",
    "HabitatEnvironment",
    "MultiSensorAgentArgs",
    "ObjectConfig",
    "SingleSensorAgentArgs",
]

# Create agent and object configuration helper dataclasses
class HabitatAgentArgs:
    pass


@dataclass
class AgentConfig:
    """Agent configuration used by :class:`HabitatEnvironment`."""

    agent_type: Type[HabitatAgent]
    agent_args: dict | Type[HabitatAgentArgs]


def deserialize_obs_and_state(
    observations: protocol_pb2.Observations,
    proprioceptive_state: protocol_pb2.ProprioceptiveState,
) -> tuple[Observations, ProprioceptiveState]:
    obs = Observations()
    for pb_agent_obs in observations.agent_observations:
        agent_obs = AgentObservations()
        for pb_sensor_obs in pb_agent_obs.sensor_observations:
            sensor_obs = SensorObservations()
            if pb_sensor_obs.HasField("raw"):
                sensor_obs.raw = np.frombuffer(pb_sensor_obs.raw)
            if pb_sensor_obs.HasField("rgba"):
                sensor_obs.rgba = np.frombuffer(
                    pb_sensor_obs.rgba, dtype=np.uint8
                ).reshape((64, 64, 4))
            if pb_sensor_obs.HasField("depth"):
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
            position = np.array(
                [
                    pb_sensor_state.position.x,
                    pb_sensor_state.position.y,
                    pb_sensor_state.position.z,
                ]
            )
            rotation = qt.quaternion(
                pb_sensor_state.rotation.w,
                pb_sensor_state.rotation.x,
                pb_sensor_state.rotation.y,
                pb_sensor_state.rotation.z,
            )
            sensors[SensorID(pb_sensor_state.sensor_id)] = SensorState(
                position=position,
                rotation=rotation,
            )

        agent_state = AgentState(
            sensors=sensors,
            position=position,
            rotation=rotation,
            motor_only_step=motor_only_step,
        )
        state[AgentID(pb_agent_state.agent_id)] = agent_state

    return obs, state


class HabitatEnvironment(EmbodiedEnvironment):
    """habitat-sim environment compatible with Monty.

    Attributes:
        agents: List of :class:`AgentConfig` to place in the scene.
        objects: Optional list of :class:`ObjectParams` to place in the scene.
        scene_id: Scene to use or None for empty environment.
        seed: Simulator seed to use
        data_path: Path to the dataset.
    """

    def __init__(
        self,
        agents: list,
        objects: list[ObjectParams] | None = None,
        scene_id: str | None = None,
        seed: int = 42,
        data_path: str | None = None,
        address: str | None = None,
    ):
        super().__init__()
        # self._agents = []
        # for config in agents:
        #     cfg_dict = asdict(config) if is_dataclass(config) else config
        #     agent_type = cfg_dict["agent_type"]
        #     args = cfg_dict["agent_args"]
        #     if is_dataclass(args):
        #         args = asdict(args)
        #     agent = agent_type(**args)
        #     self._agents.append(agent)

        # channel = grpc.insecure_channel("localhost:50051")
        channel = grpc.insecure_channel(address)
        self._env: protocol_pb2_grpc.SimulatorServiceStub = (
            protocol_pb2_grpc.SimulatorServiceStub(channel)
        )
        # self._env: Simulator = HabitatSim(
        #     agents=self._agents,
        #     scene_id=scene_id,
        #     seed=seed,
        #     data_path=data_path,
        # )

        if objects is not None:
            for obj in objects:
                obj_dict = asdict(obj) if is_dataclass_instance(obj) else obj
                pb_add_object_request = protocol_pb2.AddObjectRequest()
                if hasattr(obj_dict, "position"):
                    position = obj_dict["position"]
                    pb_add_object_request.position.x = position[0]
                    pb_add_object_request.position.y = position[1]
                    pb_add_object_request.position.z = position[2]
                if hasattr(obj_dict, "rotation"):
                    rotation = obj_dict["rotation"]
                    pb_add_object_request.rotation.w = rotation[0]
                    pb_add_object_request.rotation.x = rotation[1]
                    pb_add_object_request.rotation.y = rotation[2]
                    pb_add_object_request.rotation.z = rotation[3]
                if hasattr(obj_dict, "scale"):
                    scale = obj_dict["scale"]
                    pb_add_object_request.scale.x = scale[0]
                    pb_add_object_request.scale.y = scale[1]
                    pb_add_object_request.scale.z = scale[2]
                if hasattr(obj_dict, "semantic_id"):
                    semantic_id = obj_dict["semantic_id"]
                    pb_add_object_request.semantic_id = semantic_id
                if hasattr(obj_dict, "primary_target_object"):
                    primary_target_object = obj_dict["primary_target_object"]
                    pb_add_object_request.primary_target_object = primary_target_object

                self._env.AddObject(pb_add_object_request)

    def add_object(
        self,
        name: str,
        position: VectorXYZ | None = None,
        rotation: QuaternionWXYZ | None = None,
        scale: VectorXYZ | None = None,
        semantic_id: SemanticID | None = None,
        primary_target_object: ObjectID | None = None,
    ) -> ObjectID:
        position = position or VectorXYZ((0.0, 0.0, 0.0))
        rotation = rotation or QuaternionWXYZ((1.0, 0.0, 0.0, 0.0))
        scale = scale or VectorXYZ((1.0, 1.0, 1.0))

        pb_add_object_request = protocol_pb2.AddObjectRequest()
        pb_add_object_request.name = name
        pb_add_object_request.position.x = position[0]
        pb_add_object_request.position.y = position[1]
        pb_add_object_request.position.z = position[2]
        pb_add_object_request.rotation.w = rotation[0]
        pb_add_object_request.rotation.x = rotation[1]
        pb_add_object_request.rotation.y = rotation[2]
        pb_add_object_request.rotation.z = rotation[3]
        pb_add_object_request.scale.x = scale[0]
        pb_add_object_request.scale.y = scale[1]
        pb_add_object_request.scale.z = scale[2]
        if semantic_id is not None:
            pb_add_object_request.semantic_id = semantic_id
        if primary_target_object is not None:
            pb_add_object_request.primary_target_object = primary_target_object
        pb_add_object_response = self._env.AddObject(pb_add_object_request)
        return pb_add_object_response.object_id

        # object_id, _ = self._env.add_object(
        #     name,
        #     position,
        #     rotation,
        #     scale,
        #     semantic_id,
        #     primary_target_object,
        # )
        # return object_id

    def step(self, action: Action) -> tuple[Observations, ProprioceptiveState]:
        # TODO: This is for the purpose of type checking, but would be better handled
        #       using the action space check above, once those are integrated into the
        #       type system.
        if not isinstance(
            action,
            (
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
            ),
        ):
            raise TypeError(f"Invalid action type: {type(action)}")

        action.act(self)

        return self.observations, self.state

    def remove_all_objects(self):
        request = protocol_pb2.RemoveAllObjectsRequest()
        return self._env.RemoveAllObjects(request)

    def reset(self) -> tuple[Observations, ProprioceptiveState]:
        request = protocol_pb2.ResetRequest()
        response = self._env.Reset(request)
        return deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def close(self):
        logger.info("NOPE!")

    def actuate_look_down(self, action: LookDown) -> None:
        request = protocol_pb2.StepRequest(
            look_down=protocol_pb2.LookDownAction(
                agent_id=action.agent_id,
                rotation_degrees=action.rotation_degrees,
                constraint_degrees=action.constraint_degrees,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_look_up(self, action: LookUp) -> None:
        request = protocol_pb2.StepRequest(
            look_up=protocol_pb2.LookUpAction(
                agent_id=action.agent_id,
                rotation_degrees=action.rotation_degrees,
                constraint_degrees=action.constraint_degrees,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_move_forward(self, action: MoveForward) -> None:
        request = protocol_pb2.StepRequest(
            move_forward=protocol_pb2.MoveForwardAction(
                agent_id=action.agent_id,
                distance=action.distance,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_move_tangentially(self, action: MoveTangentially) -> None:
        request = protocol_pb2.StepRequest(
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
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_orient_horizontal(self, action: OrientHorizontal) -> None:
        request = protocol_pb2.StepRequest(
            orient_horizontal=protocol_pb2.OrientHorizontalAction(
                agent_id=action.agent_id,
                rotation_degrees=action.rotation_degrees,
                left_distance=action.left_distance,
                forward_distance=action.forward_distance,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_orient_vertical(self, action: OrientVertical) -> None:
        request = protocol_pb2.StepRequest(
            orient_vertical=protocol_pb2.OrientVerticalAction(
                agent_id=action.agent_id,
                rotation_degrees=action.rotation_degrees,
                down_distance=action.down_distance,
                forward_distance=action.forward_distance,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_set_agent_pitch(self, action: SetAgentPitch) -> None:
        request = protocol_pb2.StepRequest(
            set_agent_pitch=protocol_pb2.SetAgentPitchAction(
                agent_id=action.agent_id,
                pitch_degrees=action.pitch_degrees,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_set_agent_pose(self, action: SetAgentPose) -> None:
        request = protocol_pb2.StepRequest(
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
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_set_sensor_pitch(self, action: SetSensorPitch) -> None:
        request = protocol_pb2.StepRequest(
            set_sensor_pitch=protocol_pb2.SetSensorPitchAction(
                agent_id=action.agent_id,
                pitch_degrees=action.pitch_degrees,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_set_sensor_pose(self, action: SetSensorPose) -> None:
        request = protocol_pb2.StepRequest(
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
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_set_sensor_rotation(self, action: SetSensorRotation) -> None:
        request = protocol_pb2.StepRequest(
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
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_set_yaw(self, action: SetYaw) -> None:
        request = protocol_pb2.StepRequest(
            set_yaw=protocol_pb2.SetYawAction(
                agent_id=action.agent_id,
                rotation_degrees=action.rotation_degrees,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_turn_left(self, action: TurnLeft) -> None:
        request = protocol_pb2.StepRequest(
            turn_left=protocol_pb2.TurnLeftAction(
                agent_id=action.agent_id,
                rotation_degrees=action.rotation_degrees,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )

    def actuate_turn_right(self, action: TurnRight) -> None:
        request = protocol_pb2.StepRequest(
            turn_right=protocol_pb2.TurnRightAction(
                agent_id=action.agent_id,
                rotation_degrees=action.rotation_degrees,
            )
        )
        response = self._env.Step(request)
        self.observations, self.state = deserialize_obs_and_state(
            response.observations, response.proprioceptive_state
        )
