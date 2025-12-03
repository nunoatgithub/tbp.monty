from __future__ import annotations

from dataclasses import dataclass, asdict
from importlib import import_module

import hydra
from omegaconf import OmegaConf

from tbp.monty.frameworks.actions.actions import Action, LookDown, LookUp, MoveForward, TurnLeft, \
    TurnRight, SetYaw, \
    SetSensorRotation, SetSensorPose, SetSensorPitch, SetAgentPose, SetAgentPitch, OrientVertical, \
    OrientHorizontal, MoveTangentially
from tbp.monty.frameworks.agents import AgentID
from tbp.monty.frameworks.environments.embodied_environment import (ObjectID,
                                                                    SemanticID, \
                                                                    VectorXYZ, QuaternionWXYZ)
from tbp.monty.frameworks.models.abstract_monty_classes import Observations
from tbp.monty.frameworks.models.motor_system_state import ProprioceptiveState
from tbp.monty.simulators.protocol.v1 import protocol_pb2
from tbp.monty.simulators.simulator import Simulator
from .agents import HabitatAgent
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

    def start(self) -> None:

        while True:
            request_msg_bytes = self.transport.receive_request()
            request_msg = protocol_pb2.RequestMessage().ParseFromString(request_msg_bytes)

            request = request_msg.WhichOneof("request")
            if request == "removeAllObjectsReq":
                response_msg = self._remove_all_objects()
            elif request == "addObjectReq":
                response_msg = self._add_objects(request_msg.addObjectReq)
            elif request == "applyActionsReq":
                response_msg = self._apply_actions(request_msg.applyActionsReq)
            elif request == "proprioceptiveStateReq":
                response_msg = self._proprioceptive_state()
            elif request == "resetReq":
                response_msg = self._reset()
            else:
                response_msg = self._close()

            self.transport.send_response(response_msg.SerializeToString())

    def init(self, request: protocol_pb2.InitRequest) -> protocol_pb2.ResponseMessage:

        habitat_sim_config_name = request.config_name
        habitat_sim_config = self._load_config(habitat_sim_config_name)
        self._habitat_sim = HabitatSim(**asdict(habitat_sim_config))
        response_msg = protocol_pb2.ResponseMessage(init_resp=protocol_pb2.InitResponse())
        return response_msg

    @staticmethod
    def _load_config(config_name:str) -> HabitatSimConfig:

        def _load_class(path: str):
            module_name, class_name = path.rsplit(".", 1)
            module = import_module(module_name)
            return getattr(module, class_name)

        # Compose the Hydra config located under `../../conf`.
        # `config_name` can be a path-like string (e.g. `experiment/config/monty/motor_system/defaults`).
        with hydra.initialize(config_path="../../conf", version_base=None):
            cfg = hydra.compose(config_name=config_name)

        cfg_dict = OmegaConf.to_container(cfg, resolve=True)

        agents_cfg = cfg_dict.get("agents", [])
        agents: list[HabitatAgent] = []
        for a in agents_cfg:
            if isinstance(a, dict) and "agent_type" in a:
                agent_type = a["agent_type"]
                agent_args = a.get("agent_args", {}) or {}
                cls = _load_class(agent_type) if isinstance(agent_type, str) else agent_type
                agents.append(cls(**agent_args))
            else:
                agents.append(a)

        return HabitatSimConfig(
            agents=agents,
            data_path=cfg_dict.get("data_path"),
            scene_id=cfg_dict.get("scene_id"),
            seed=cfg_dict.get("seed", 42),
        )

    def _remove_all_objects(self) -> protocol_pb2.ResponseMessage:
        self._habitat_sim.remove_all_objects()
        response_msg = protocol_pb2.ResponseMessage(
            remove_all_objects_resp=protocol_pb2.RemoveAllObjectsResponse())
        return response_msg

    def _add_objects(self, request: protocol_pb2.AddObjectRequest) -> protocol_pb2.ResponseMessage:

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

        object_id, semantic_id = self._habitat_sim.add_object(
            name=request.name,
            position=position,
            rotation=rotation,
            scale=scale,
            semantic_id=semantic_id,
            primary_target_object=primary_target_object,
        )

        response = protocol_pb2.AddObjectResponse(SemanticID(semantic_id),
                                                  ObjectID(object_id) if object_id else None)
        return protocol_pb2.ResponseMessage(add_object_resp=response)

    def _apply_actions(self, request: protocol_pb2.ApplyActionsRequest):

        actions: list[Action] = []
        pb_actions = request.actions
        for pb_action in pb_actions:
            action = self._action_from_proto(pb_action)
            actions.append(action)
        observations: Observations = self._habitat_sim.apply_actions(actions)
        pb_obs = self._observations_to_proto(observations)
        response = protocol_pb2.ApplyActionsResponse(observations=pb_obs)
        response_msg = protocol_pb2.ResponseMessage(apply_actions_resp=response)
        return response_msg

    def _proprioceptive_state(self):

        states: ProprioceptiveState = self._habitat_sim.states

        a_states = []
        for agent_id, a_state in states.items():
            a_pos = a_state["position"]
            a_rot = a_state["rotation"]
            a_sensors = a_state["sensors"]
            sensor_states = []
            for sensor_id, sensor_state in a_sensors.items():
                s_pos = sensor_state["position"]
                s_rot = sensor_state["rotation"]
                s_state = protocol_pb2.ProprioceptiveState.AgentState.SensorState(
                    sensor_id=sensor_id,
                    position=protocol_pb2.VectorXYZ(s_pos.x, s_pos.y, s_pos.z),
                    rotation=protocol_pb2.QuaternionWXYZ(s_rot.w, s_rot.x, s_rot.y, s_rot.z),
                )
                sensor_states.append(s_state)
            a_state = protocol_pb2.ProprioceptiveState.AgentState(
                agent_id=agent_id,
                position=protocol_pb2.VectorXYZ(a_pos.x, a_pos.y, a_pos.z),
                rotation=protocol_pb2.QuaternionWXYZ(a_rot.w, a_rot.x, a_rot.y, a_rot.z),
                sensor_states=sensor_states,
            )
            a_states.append(a_state)

        proprioceptive_state = protocol_pb2.ProprioceptiveState(a_states)
        response = protocol_pb2.ProprioceptiveStateResponse(
            proprioceptive_state=proprioceptive_state
        )
        return protocol_pb2.ResponseMessage(proprioceptive_state_resp=response)

    def _reset(self) -> protocol_pb2.ResponseMessage:

        observations: Observations = self._habitat_sim.reset()
        pb_obs = self._observations_to_proto(observations)
        response = protocol_pb2.ResetResponse(observations=pb_obs)
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
            direction = VectorXYZ(
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
            location = VectorXYZ(
                (
                    set_agent_pose.location.x,
                    set_agent_pose.location.y,
                    set_agent_pose.location.z,
                )
            )
            rotation = QuaternionWXYZ(
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
            location = VectorXYZ(
                (
                    set_sensor_pose.location.x,
                    set_sensor_pose.location.y,
                    set_sensor_pose.location.z,
                )
            )
            rotation = QuaternionWXYZ(
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
            rotation = QuaternionWXYZ(
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
    def _observations_to_proto(observations: Observations) -> protocol_pb2.Observations:

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
        return pb_obs
