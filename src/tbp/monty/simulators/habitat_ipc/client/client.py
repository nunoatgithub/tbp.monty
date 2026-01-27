from __future__ import annotations

import logging
import pickle
from typing import Iterable, Sequence, Tuple

import numpy as np
import quaternion as qt

from tbp.monty.frameworks.actions.actions import Action, LookDown, LookUp, MoveForward, TurnLeft, \
    TurnRight, SetYaw, \
    SetSensorRotation, SetAgentPose, SetAgentPitch, OrientVertical, \
    OrientHorizontal, MoveTangentially, SetSensorPitch
from tbp.monty.frameworks.agents import AgentID
from tbp.monty.frameworks.environments.environment import (ObjectInfo, ObjectID,
                                                           SemanticID, \
                                                           VectorXYZ, QuaternionWXYZ)
from tbp.monty.frameworks.models.abstract_monty_classes import Observations, AgentObservations, \
    SensorObservations
from tbp.monty.frameworks.models.motor_system_state import ProprioceptiveState, SensorState, \
    AgentState
from tbp.monty.frameworks.sensors import SensorID
from tbp.monty.simulators.habitat_ipc.transport import Transport
from tbp.monty.simulators.protocol.v1 import protocol_pb2, habitat_pb2, basic_types_pb2
from tbp.monty.simulators.simulator import Simulator

Resolution = Tuple[int, int]

from shm_rpc_bridge import get_logger

# file_handler = logging.FileHandler("habitat_ipc.log")
# file_handler.setFormatter(logging.Formatter("%(asctime)s - %(process)s - %(name)s - %(levelname)s: %(message)s"))
# shm_logger = get_logger()
# shm_logger.setLevel(logging.DEBUG)
# shm_logger.addHandler(file_handler)

class HabitatClient(Simulator):

    def __init__(self, transport: Transport):
        self.transport = transport.connect()
        self._sensor_resolution_map: dict[SensorID, Resolution] = {}

    def __del__(self):
        if hasattr(self, 'transport') and self.transport is not None:
            self.transport.close()

    def init(self, agent_cfg: dict, object_cfgs: list[dict] | None, scene_id: str | None, seed: int,
             data_path: str | None):

        pb_agent_cfg = self._agent_cfg_to_proto(agent_cfg)
        pickle_object_cfgs = pickle.dumps(object_cfgs, protocol=5) # python 3.8 compatible
        habitat_cfg = habitat_pb2.HabitatConfig(
            agent_cfg=pb_agent_cfg,
            pickle_object_cfgs=pickle_object_cfgs,
            scene_id=scene_id,
            seed=seed,
            data_path=data_path
        )
        init_request = protocol_pb2.InitRequest(habitat=habitat_cfg)
        request_msg = protocol_pb2.RequestMessage(init_request=init_request)
        self.transport.send_request(request_msg.SerializeToString())
        self._receive_response()

    def remove_all_objects(self) -> None:
        request = protocol_pb2.RemoveAllObjectsRequest()
        request_msg = protocol_pb2.RequestMessage(remove_all_objects_req=request)
        self.transport.send_request(request_msg.SerializeToString())
        self._receive_response()

    def add_object(
            self,
            name: str,
            position: VectorXYZ = (0.0, 0.0, 0.0),
            rotation: QuaternionWXYZ = (1.0, 0.0, 0.0, 0.0),
            scale: VectorXYZ = (1.0, 1.0, 1.0),
            semantic_id: SemanticID | None = None,
            primary_target_object: ObjectID | None = None,
    ) -> ObjectInfo:

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

        request_msg = protocol_pb2.RequestMessage(add_object_req=request)
        self.transport.send_request(request_msg.SerializeToString())

        response_msg = self._receive_response()
        response: protocol_pb2.AddObjectResponse = response_msg.add_object_resp

        semantic_id = SemanticID(response.semantic_id) if response.semantic_id else None
        return ObjectInfo(ObjectID(response.object_id), semantic_id)

    def step(self, actions: Sequence[Action]) -> tuple[Observations, ProprioceptiveState]:

        pb_actions = []
        for action in actions:
            pb_action = self._action_to_proto(action)
            pb_actions.append(pb_action)
        request = protocol_pb2.StepRequest(actions=pb_actions)
        request_msg = protocol_pb2.RequestMessage(step_req=request)
        self.transport.send_request(request_msg.SerializeToString())

        response_msg = self._receive_response()
        response: protocol_pb2.StepResponse = response_msg.step_resp
        pb_observations = response.observations
        observations = self._observations_from_proto(pb_observations)
        pb_state = response.proprioceptive_state
        state = self._state_from_proto(pb_state)
        return observations, state

    def reset(self) -> tuple[Observations, ProprioceptiveState]:
        request_msg = protocol_pb2.RequestMessage(reset_req=protocol_pb2.ResetRequest())
        self.transport.send_request(request_msg.SerializeToString())

        response_msg = self._receive_response()
        response: protocol_pb2.ResetResponse = response_msg.reset_resp
        pb_observations = response.observations
        observations = self._observations_from_proto(pb_observations)
        pb_state = response.proprioceptive_state
        state = self._state_from_proto(pb_state)
        return observations, state

    def close(self) -> None:
        request = protocol_pb2.CloseRequest()
        request_msg = protocol_pb2.RequestMessage(close_req=request)
        self.transport.send_request(request_msg.SerializeToString())
        self._receive_response()

    @staticmethod
    def _agent_cfg_to_proto(agent_cfg) -> habitat_pb2.HabitatAgentConfig:
        """Convert agent config (dict or dataclass) to protobuf."""
        import dataclasses

        # Convert dataclass to dict if needed
        if dataclasses.is_dataclass(agent_cfg):
            agent_cfg = dataclasses.asdict(agent_cfg)

        agent_args = agent_cfg["agent_args"]

        # Check if it's a single sensor config (has sensor_id) or multi sensor (has sensor_ids)
        if "sensor_id" in agent_args:
            # Single sensor configuration
            single_sensor_cfg = habitat_pb2.HabitatAgentConfig.SingleSensorConfig(
                agent_id=agent_args["agent_id"],
                sensor_id=agent_args["sensor_id"],
            )
            if "resolution" in agent_args:
                resolution = agent_args["resolution"]
                single_sensor_cfg.resolution.height = resolution[0]
                single_sensor_cfg.resolution.width = resolution[1]
            if "action_space_type" in agent_args:
                single_sensor_cfg.action_space_type = agent_args["action_space_type"]

            return habitat_pb2.HabitatAgentConfig(single_sensor_cfg=single_sensor_cfg)
        else:
            # Multi sensor configuration
            pb_multi_sensor_cfg = habitat_pb2.HabitatAgentConfig.MultiSensorConfig(
                agent_id=agent_args["agent_id"],
                sensor_ids=agent_args["sensor_ids"],
                height=agent_args.get("height"),
            )

            if "position" in agent_args:
                position = agent_args["position"]
                pb_multi_sensor_cfg.position.x = position[0]
                pb_multi_sensor_cfg.position.y = position[1]
                pb_multi_sensor_cfg.position.z = position[2]

            if "resolutions" in agent_args:
                for res in agent_args["resolutions"]:
                    resolution = basic_types_pb2.Resolution(height=res[0], width=res[1])
                    pb_multi_sensor_cfg.resolutions.append(resolution)

            if "positions" in agent_args:
                for pos in agent_args["positions"]:
                    position = basic_types_pb2.VectorXYZ(x=pos[0], y=pos[1], z=pos[2])
                    pb_multi_sensor_cfg.positions.append(position)

            if "rotations" in agent_args:
                for rot in agent_args["rotations"]:
                    rotation = basic_types_pb2.QuaternionWXYZ(w=rot[0], x=rot[1], y=rot[2], z=rot[3])
                    pb_multi_sensor_cfg.rotations.append(rotation)

            if "semantics" in agent_args:
                pb_multi_sensor_cfg.semantics.extend(agent_args["semantics"])

            if "zooms" in agent_args:
                pb_multi_sensor_cfg.zooms.extend(agent_args["zooms"])

            if "action_space_type" in agent_args:
                pb_multi_sensor_cfg.action_space_type = agent_args["action_space_type"]

            return habitat_pb2.HabitatAgentConfig(multi_sensor_cfg=pb_multi_sensor_cfg)

    def _receive_response(self):
        response_bytes = self.transport.receive_response()
        response_msg = protocol_pb2.ResponseMessage()
        response_msg.ParseFromString(response_bytes)

        if response_msg.HasField("error_resp"):
            error_resp = response_msg.error_resp
            raise Exception(error_resp.msg)
        else:
            return response_msg

    @staticmethod
    def _action_to_proto(action: Action) -> protocol_pb2.Action:
        if isinstance(action, LookDown):
            return protocol_pb2.Action(
                look_down=protocol_pb2.LookDownAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                    constraint_degrees=action.constraint_degrees,
                )
            )
        elif isinstance(action, LookUp):
            return protocol_pb2.Action(
                look_up=protocol_pb2.LookUpAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                    constraint_degrees=action.constraint_degrees,
                )
            )
        elif isinstance(action, MoveForward):
            return protocol_pb2.Action(
                move_forward=protocol_pb2.MoveForwardAction(
                    agent_id=action.agent_id,
                    distance=action.distance,
                )
            )
        elif isinstance(action, MoveTangentially):
            return protocol_pb2.Action(
                move_tangentially=protocol_pb2.MoveTangentiallyAction(
                    agent_id=action.agent_id,
                    distance=action.distance,
                    direction=basic_types_pb2.VectorXYZ(
                        x=action.direction[0],
                        y=action.direction[1],
                        z=action.direction[2],
                    ),
                )
            )
        elif isinstance(action, OrientHorizontal):
            return protocol_pb2.Action(
                orient_horizontal=protocol_pb2.OrientHorizontalAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                    left_distance=action.left_distance,
                    forward_distance=action.forward_distance,
                )
            )
        elif isinstance(action, OrientVertical):
            return protocol_pb2.Action(
                orient_vertical=protocol_pb2.OrientVerticalAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                    down_distance=action.down_distance,
                    forward_distance=action.forward_distance,
                )
            )
        elif isinstance(action, SetAgentPitch):
            return protocol_pb2.Action(
                set_agent_pitch=protocol_pb2.SetAgentPitchAction(
                    agent_id=action.agent_id,
                    pitch_degrees=action.pitch_degrees,
                )
            )
        elif isinstance(action, SetAgentPose):
            return protocol_pb2.Action(
                set_agent_pose=protocol_pb2.SetAgentPoseAction(
                    agent_id=action.agent_id,
                    location=basic_types_pb2.VectorXYZ(
                        x=action.location[0],
                        y=action.location[1],
                        z=action.location[2],
                    ),
                    rotation=basic_types_pb2.QuaternionWXYZ(
                        w=action.rotation_quat[0],
                        x=action.rotation_quat[1],
                        y=action.rotation_quat[2],
                        z=action.rotation_quat[3],
                    ),
                )
            )
        elif isinstance(action, SetSensorRotation):
            return protocol_pb2.Action(
                set_sensor_rotation=protocol_pb2.SetSensorRotationAction(
                    agent_id=action.agent_id,
                    rotation=basic_types_pb2.QuaternionWXYZ(
                        w=action.rotation_quat[0],
                        x=action.rotation_quat[1],
                        y=action.rotation_quat[2],
                        z=action.rotation_quat[3],
                    ),
                )
            )
        elif isinstance(action, SetSensorPitch):
            return protocol_pb2.Action(
                set_sensor_pitch=protocol_pb2.SetSensorPitchAction(
                    agent_id=action.agent_id,
                    pitch_degrees=action.pitch_degrees,
                )
            )
        elif isinstance(action, SetYaw):
            return protocol_pb2.Action(
                set_yaw=protocol_pb2.SetYawAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                )
            )
        elif isinstance(action, TurnLeft):
            return protocol_pb2.Action(
                turn_left=protocol_pb2.TurnLeftAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                )
            )
        elif isinstance(action, TurnRight):
            return protocol_pb2.Action(
                turn_right=protocol_pb2.TurnRightAction(
                    agent_id=action.agent_id,
                    rotation_degrees=action.rotation_degrees,
                )
            )
        else:
            return None

    @staticmethod
    def _observations_from_proto(pb_observations: protocol_pb2.Observations) -> Observations:

        obs = Observations()
        for pb_agent_obs in pb_observations.agent_observations:
            agent_obs = AgentObservations()
            for pb_sensor_obs in pb_agent_obs.sensor_observations:
                sensor_obs = SensorObservations()

                # Helper function to deserialize NumpyArray message
                def deserialize_numpy_array(pb_array):
                    dtype = np.dtype(pb_array.dtype)
                    shape = tuple(pb_array.shape)
                    data = np.frombuffer(pb_array.data, dtype=dtype)
                    return data.reshape(shape).copy() if shape else data.copy()

                if pb_sensor_obs.HasField("rgba"):
                    sensor_obs["rgba"] = deserialize_numpy_array(pb_sensor_obs.rgba)
                if pb_sensor_obs.HasField("depth"):
                    sensor_obs["depth"] = deserialize_numpy_array(pb_sensor_obs.depth).copy()
                if pb_sensor_obs.HasField("semantic"):
                    sensor_obs["semantic"] = deserialize_numpy_array(pb_sensor_obs.semantic)
                if pb_sensor_obs.HasField("semantic_3d"):
                    sensor_obs["semantic_3d"] = deserialize_numpy_array(pb_sensor_obs.semantic_3d)
                if pb_sensor_obs.HasField("sensor_frame_data"):
                    sensor_obs["sensor_frame_data"] = deserialize_numpy_array(
                        pb_sensor_obs.sensor_frame_data)
                if pb_sensor_obs.HasField("world_camera"):
                    sensor_obs["world_camera"] = deserialize_numpy_array(pb_sensor_obs.world_camera)
                if pb_sensor_obs.HasField("pixel_loc"):
                    sensor_obs["pixel_loc"] = deserialize_numpy_array(pb_sensor_obs.pixel_loc)
                if pb_sensor_obs.HasField("raw"):
                    sensor_obs["raw"] = np.frombuffer(pb_sensor_obs.raw)

                agent_obs[SensorID(pb_sensor_obs.sensor_id)] = sensor_obs
            obs[AgentID(pb_agent_obs.agent_id)] = agent_obs

        return obs

    @staticmethod
    def _state_from_proto(pb_state: protocol_pb2.ProprioceptiveState) -> ProprioceptiveState:
        pb_agent_states: Iterable[
            protocol_pb2.ProprioceptiveState.AgentState] = pb_state.agent_states

        result = ProprioceptiveState()
        for pb_agent_state in pb_agent_states:
            agent_position = np.array(
                [
                    pb_agent_state.position.x,
                    pb_agent_state.position.y,
                    pb_agent_state.position.z,
                ]
            )

            agent_rotation = qt.quaternion(
                pb_agent_state.rotation.w,
                pb_agent_state.rotation.x,
                pb_agent_state.rotation.y,
                pb_agent_state.rotation.z,
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
                position=agent_position,
                rotation=agent_rotation,
            )

            result[AgentID(pb_agent_state.agent_id)] = agent_state

        return result
