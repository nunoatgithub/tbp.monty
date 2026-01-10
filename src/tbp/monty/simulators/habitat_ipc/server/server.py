from __future__ import annotations

import logging
import pickle
import traceback
from dataclasses import dataclass, asdict, is_dataclass

from tbp.monty.frameworks.actions.actions import Action, LookDown, LookUp, MoveForward, TurnLeft, \
    TurnRight, SetYaw, \
    SetSensorRotation, SetSensorPose, SetSensorPitch, SetAgentPose, SetAgentPitch, OrientVertical, \
    OrientHorizontal, MoveTangentially
from tbp.monty.frameworks.agents import AgentID
from tbp.monty.frameworks.models.abstract_monty_classes import Observations
from tbp.monty.frameworks.models.motor_system_state import ProprioceptiveState
from tbp.monty.simulators.protocol.v1 import protocol_pb2, habitat_pb2, basic_types_pb2
from tbp.monty.simulators.simulator import Simulator
from .agents import HabitatAgent, SingleSensorAgent, MultiSensorAgent
from .simulator import HabitatSim
from ..transport import Transport

@dataclass
class HabitatSimConfig:
    agents: list[HabitatAgent]
    data_path: str
    scene_id: str | None = None
    seed: int = 42

class HabitatServer(Simulator):

    def __init__(self, transport: Transport):
        self.transport = transport
        self._habitat_sim = None

    def __del__(self):
        if hasattr(self, 'transport') and self.transport is not None:
            self.transport.close()

    def start(self) -> None:

        # from shm_rpc_bridge import get_logger
        # file_handler = logging.FileHandler("habitat_ipc.log")
        # file_handler.setFormatter(logging.Formatter("%(asctime)s - %(process)s - %(name)s - %(levelname)s: %(message)s"))
        # shm_logger = get_logger()
        # shm_logger.setLevel(logging.DEBUG)
        # shm_logger.addHandler(file_handler)

        self.transport.start()
        while True:
            try:
                request_msg_bytes = self.transport.receive_request()
                request_msg = protocol_pb2.RequestMessage()
                request_msg.ParseFromString(request_msg_bytes)

                request = request_msg.WhichOneof("request")
                if request == "init_request":
                    response_msg = self._init(request_msg.init_request)
                elif request == "remove_all_objects_req":
                    response_msg = self._remove_all_objects()
                elif request == "add_object_req":
                    response_msg = self._add_objects(request_msg.add_object_req)
                elif request == "step_req":
                    response_msg = self._step(request_msg.step_req)
                elif request == "reset_req":
                    response_msg = self._reset()
                elif request == "close_req":
                    response_msg = self._close()
                else:
                    raise NotImplementedError(str(request))

            except Exception as e:
                print(traceback.format_exc()) # TODO push as part of the error response
                response = protocol_pb2.ErrorResponse(msg=str(e))
                response_msg = protocol_pb2.ResponseMessage(error_resp=response)

            self.transport.send_response(response_msg.SerializeToString())

    def _init(self, request: protocol_pb2.InitRequest) -> protocol_pb2.ResponseMessage:

        habitat_cfg = request.habitat

        agent_cfg = self._agent_cfg_from_proto(habitat_cfg.agent_cfg)
        agent_type = agent_cfg["agent_type"]
        args = agent_cfg["agent_args"]
        if is_dataclass(args):
            args = asdict(args)
        agent = agent_type(**args)

        _data_path = habitat_cfg.data_path if habitat_cfg.data_path else None
        _scene_id = habitat_cfg.scene_id if habitat_cfg.scene_id else None

        self._habitat_sim = HabitatSim(
            agents=[agent],
            scene_id=_scene_id,
            seed=habitat_cfg.seed,
            data_path=_data_path
        )

        object_cfgs = pickle.loads(habitat_cfg.pickle_object_cfgs)
        if object_cfgs is not None:
            for obj_dict in object_cfgs:
                self._habitat_sim.add_object(**obj_dict)

        response_msg = protocol_pb2.ResponseMessage(init_resp=protocol_pb2.InitResponse())
        return response_msg

    def _remove_all_objects(self) -> protocol_pb2.ResponseMessage:
        self._habitat_sim.remove_all_objects()
        response_msg = protocol_pb2.ResponseMessage(
            remove_all_objects_resp=protocol_pb2.RemoveAllObjectsResponse())
        return response_msg

    def _add_objects(self, request: protocol_pb2.AddObjectRequest) -> protocol_pb2.ResponseMessage:

        position = (request.position.x, request.position.y, request.position.z)
        rotation = (
                request.rotation.w,
                request.rotation.x,
                request.rotation.y,
                request.rotation.z,
        )
        scale = (request.scale.x, request.scale.y, request.scale.z)
        semantic_id = request.semantic_id if request.HasField("semantic_id") else None
        primary_target_object = (
            request.primary_target_object
            if request.HasField("primary_target_object")
            else None
        )

        object_info = self._habitat_sim.add_object(
            name=request.name,
            position=position,
            rotation=rotation,
            scale=scale,
            semantic_id=semantic_id,
            primary_target_object=primary_target_object,
        )

        response = protocol_pb2.AddObjectResponse(object_id=object_info.object_id)
        if object_info.semantic_id is not None:
            response.semantic_id = object_info.semantic_id
        return protocol_pb2.ResponseMessage(add_object_resp=response)

    def _step(self, request: protocol_pb2.StepRequest):

        actions: list[Action] = []
        pb_actions = request.actions
        for pb_action in pb_actions:
            action = self._action_from_proto(pb_action)
            actions.append(action)
        observations, state = self._habitat_sim.step(actions)
        pb_obs = self._observations_to_proto(observations)
        pb_state = self._state_to_proto(state)
        response = protocol_pb2.StepResponse(observations=pb_obs, proprioceptive_state=pb_state)
        response_msg = protocol_pb2.ResponseMessage(step_resp=response)
        return response_msg

    def _reset(self) -> protocol_pb2.ResponseMessage:

        observations, state = self._habitat_sim.reset()
        pb_obs = self._observations_to_proto(observations)
        pb_state = self._state_to_proto(state)
        response = protocol_pb2.ResetResponse(observations=pb_obs, proprioceptive_state=pb_state)
        response_msg = protocol_pb2.ResponseMessage(reset_resp=response)
        return response_msg

    def _close(self) -> protocol_pb2.ResponseMessage:

        self._habitat_sim.close()
        response_msg = protocol_pb2.ResponseMessage(close_resp=protocol_pb2.CloseResponse())
        return response_msg

    @staticmethod
    def _action_from_proto(pb_action: protocol_pb2.Action):

        action_type = pb_action.WhichOneof("action")
        if action_type == "look_down":
            look_down = pb_action.look_down
            return LookDown(
                agent_id=AgentID(look_down.agent_id),
                rotation_degrees=look_down.rotation_degrees,
                constraint_degrees=look_down.constraint_degrees,
            )
        elif action_type == "look_up":

            look_up = pb_action.look_up
            return LookUp(
                agent_id=AgentID(look_up.agent_id),
                rotation_degrees=look_up.rotation_degrees,
                constraint_degrees=look_up.constraint_degrees,
            )
        elif action_type == "move_forward":

            move_forward = pb_action.move_forward
            return MoveForward(
                agent_id=AgentID(move_forward.agent_id),
                distance=move_forward.distance,
            )
        elif action_type == "move_tangentially":

            move_tangentially = pb_action.move_tangentially
            distance = move_tangentially.distance
            direction = (
                move_tangentially.direction.x,
                move_tangentially.direction.y,
                move_tangentially.direction.z
            )
            return MoveTangentially(
                agent_id=AgentID(move_tangentially.agent_id),
                distance=distance,
                direction=direction,
            )
        elif action_type == "orient_horizontal":

            orient_horizontal = pb_action.orient_horizontal
            return OrientHorizontal(
                agent_id=AgentID(orient_horizontal.agent_id),
                rotation_degrees=orient_horizontal.rotation_degrees,
                left_distance=orient_horizontal.left_distance,
                forward_distance=orient_horizontal.forward_distance,
            )
        elif action_type == "orient_vertical":

            orient_vertical = pb_action.orient_vertical
            return OrientVertical(
                agent_id=AgentID(orient_vertical.agent_id),
                rotation_degrees=orient_vertical.rotation_degrees,
                down_distance=orient_vertical.down_distance,
                forward_distance=orient_vertical.forward_distance,
            )
        elif action_type == "set_agent_pitch":

            set_agent_pitch = pb_action.set_agent_pitch
            return SetAgentPitch(
                agent_id=AgentID(set_agent_pitch.agent_id),
                pitch_degrees=set_agent_pitch.pitch_degrees,
            )
        elif action_type == "set_agent_pose":

            set_agent_pose = pb_action.set_agent_pose
            location = (
                set_agent_pose.location.x,
                set_agent_pose.location.y,
                set_agent_pose.location.z,
            )
            rotation = (
                set_agent_pose.rotation.w,
                set_agent_pose.rotation.x,
                set_agent_pose.rotation.y,
                set_agent_pose.rotation.z,
            )
            return SetAgentPose(
                agent_id=AgentID(set_agent_pose.agent_id),
                location=location,
                rotation_quat=rotation,
            )
        elif action_type == "set_sensor_pitch":

            set_sensor_pitch = pb_action.set_sensor_pitch
            return SetSensorPitch(
                agent_id=AgentID(set_sensor_pitch.agent_id),
                pitch_degrees=set_sensor_pitch.pitch_degrees,
            )
        elif action_type == "set_sensor_pose":

            set_sensor_pose = pb_action.set_sensor_pose
            location = (
                set_sensor_pose.location.x,
                set_sensor_pose.location.y,
                set_sensor_pose.location.z,
            )
            rotation = (
                set_sensor_pose.rotation.w,
                set_sensor_pose.rotation.x,
                set_sensor_pose.rotation.y,
                set_sensor_pose.rotation.z,
            )
            return SetSensorPose(
                agent_id=AgentID(set_sensor_pose.agent_id),
                location=location,
                rotation_quat=rotation,
            )
        elif action_type == "set_sensor_rotation":

            set_sensor_rotation = pb_action.set_sensor_rotation
            rotation = (
                set_sensor_rotation.rotation.w,
                set_sensor_rotation.rotation.x,
                set_sensor_rotation.rotation.y,
                set_sensor_rotation.rotation.z,
            )
            return SetSensorRotation(
                agent_id=AgentID(set_sensor_rotation.agent_id),
                rotation_quat=rotation,
            )
        elif action_type == "set_yaw":

            set_yaw = pb_action.set_yaw
            return SetYaw(
                agent_id=AgentID(set_yaw.agent_id),
                rotation_degrees=set_yaw.rotation_degrees,
            )
        elif action_type == "turn_left":

            turn_left = pb_action.turn_left
            return TurnLeft(
                agent_id=AgentID(turn_left.agent_id),
                rotation_degrees=turn_left.rotation_degrees,
            )
        else:  # action_type == "turn_right":

            turn_right = pb_action.turn_right
            return TurnRight(
                agent_id=AgentID(turn_right.agent_id),
                rotation_degrees=turn_right.rotation_degrees,
            )

    @staticmethod
    def _agent_cfg_from_proto(pb_agent_cfg: habitat_pb2.HabitatAgentConfig) -> dict:
        pb_config_type = pb_agent_cfg.WhichOneof("config")

        if pb_config_type == "single_sensor_cfg":
            single_cfg = pb_agent_cfg.single_sensor_cfg
            agent_args = {
                "agent_id": AgentID(single_cfg.agent_id),
                "sensor_id": single_cfg.sensor_id,
            }
            if single_cfg.HasField("resolution"):
                agent_args["resolution"] = (single_cfg.resolution.height, single_cfg.resolution.width)
            if single_cfg.HasField("action_space_type"):
                agent_args["action_space_type"] = single_cfg.action_space_type

            return {
                "agent_type": SingleSensorAgent,
                "agent_args": agent_args,
            }
        else:  # config type  == "multi_sensor_cfg"
            multi_cfg = pb_agent_cfg.multi_sensor_cfg
            agent_args: dict = {
                "agent_id": AgentID(multi_cfg.agent_id),
                "sensor_ids": tuple(multi_cfg.sensor_ids),
                "height": multi_cfg.height,
            }

            # Add position if present
            if multi_cfg.HasField("position"):
                agent_args["position"] = (
                    multi_cfg.position.x,
                    multi_cfg.position.y,
                    multi_cfg.position.z,
                )

            # Add resolutions if present
            if multi_cfg.resolutions:
                agent_args["resolutions"] = tuple(
                    (res.height, res.width) for res in multi_cfg.resolutions
                )

            # Add sensor positions if present
            if multi_cfg.positions:
                agent_args["positions"] = tuple(
                    (pos.x, pos.y, pos.z) for pos in multi_cfg.positions
                )

            # Add sensor rotations if present
            if multi_cfg.rotations:
                agent_args["rotations"] = tuple(
                    (rot.w, rot.x, rot.y, rot.z) for rot in multi_cfg.rotations
                )

            # Add semantics if present
            if multi_cfg.semantics:
                agent_args["semantics"] = tuple(multi_cfg.semantics)

            # Add zooms if present
            if multi_cfg.zooms:
                agent_args["zooms"] = tuple(multi_cfg.zooms)

            # Add action_space_type if present
            if multi_cfg.HasField("action_space_type"):
                agent_args["action_space_type"] = multi_cfg.action_space_type

            return {
                "agent_type": MultiSensorAgent,
                "agent_args": agent_args,
            }

    @staticmethod
    def _observations_to_proto(observations: Observations) -> protocol_pb2.Observations:

        # Helper function to serialize NumpyArray message
        def _serialize_numpy_array(np_array, pb_array):
            pb_array.data = np_array.tobytes()
            pb_array.dtype = str(np_array.dtype)
            pb_array.shape.extend(np_array.shape)
            
        pb_obs = protocol_pb2.Observations()
        for agent_id, agent_obs in observations.items():
            pb_agent_obs = pb_obs.agent_observations.add(agent_id=agent_id)
            for sensor_id, sensor_obs in agent_obs.items():
                pb_sensor_obs = pb_agent_obs.sensor_observations.add(sensor_id=sensor_id)
                for modality, data in sensor_obs.items():
                    if modality == "raw":
                        pb_sensor_obs.raw = data.tobytes()
                    elif modality == "rgba":
                        _serialize_numpy_array(data, pb_sensor_obs.rgba)
                    elif modality == "depth":
                        _serialize_numpy_array(data, pb_sensor_obs.depth)
                    elif modality == "semantic":
                        _serialize_numpy_array(data, pb_sensor_obs.semantic)
                    elif modality == "semantic_3d":
                        _serialize_numpy_array(data, pb_sensor_obs.semantic_3d)
                    elif modality == "sensor_frame_data":
                        _serialize_numpy_array(data, pb_sensor_obs.sensor_frame_data)
                    elif modality == "world_camera":
                        _serialize_numpy_array(data, pb_sensor_obs.world_camera)
                    elif modality == "pixel_loc":
                        _serialize_numpy_array(data, pb_sensor_obs.pixel_loc)
        return pb_obs

    @staticmethod
    def _state_to_proto(state: ProprioceptiveState):

        a_states = []
        for agent_id, a_state in state.items():
            a_pos = a_state.position
            a_rot = a_state.rotation
            a_sensors = a_state.sensors
            sensor_states = []
            for sensor_id, sensor_state in a_sensors.items():
                s_pos = sensor_state.position
                s_rot = sensor_state.rotation
                s_state = protocol_pb2.ProprioceptiveState.AgentState.SensorState(
                    sensor_id=sensor_id,
                    position=basic_types_pb2.VectorXYZ(x=s_pos.x, y=s_pos.y, z=s_pos.z),
                    rotation=basic_types_pb2.QuaternionWXYZ(w=s_rot.w, x=s_rot.x, y=s_rot.y, z=s_rot.z),
                )
                sensor_states.append(s_state)
            a_state = protocol_pb2.ProprioceptiveState.AgentState(
                agent_id=agent_id,
                position=basic_types_pb2.VectorXYZ(x=a_pos.x, y=a_pos.y, z=a_pos.z),
                rotation=basic_types_pb2.QuaternionWXYZ(w=a_rot.w, x=a_rot.x, y=a_rot.y, z=a_rot.z),
                sensor_states=sensor_states,
            )
            a_states.append(a_state)

        pb_state = protocol_pb2.ProprioceptiveState(agent_states=a_states)

        return pb_state
