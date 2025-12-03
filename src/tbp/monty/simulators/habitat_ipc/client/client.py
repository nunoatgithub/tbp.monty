from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import quaternion as qt

from tbp.monty.frameworks.actions.actions import Action, LookDown, LookUp, MoveForward, TurnLeft, \
    TurnRight, SetYaw, \
    SetSensorRotation, SetAgentPose, SetAgentPitch, OrientVertical, \
    OrientHorizontal
from tbp.monty.frameworks.agents import AgentID
from tbp.monty.frameworks.environments.embodied_environment import (ObjectInfo, ObjectID,
                                                                    SemanticID, \
                                                                    VectorXYZ, QuaternionWXYZ)
from tbp.monty.frameworks.models.abstract_monty_classes import Observations, AgentObservations, \
    SensorObservations
from tbp.monty.frameworks.models.motor_system_state import ProprioceptiveState, SensorState, \
    AgentState
from tbp.monty.frameworks.sensors import SensorID
from tbp.monty.simulators.habitat_ipc.transport import Transport
from tbp.monty.simulators.protocol.v1 import protocol_pb2
from tbp.monty.simulators.simulator import Simulator


class HabitatClient(Simulator):

    def __init__(self, transport: Transport):
        self.transport = transport

    def init(self, config_name: str):
        init_request = protocol_pb2.InitRequest(config_name=config_name)
        request_msg = protocol_pb2.RequestMessage(init_request=init_request)
        self.transport.send_request(request_msg.SerializeToString())
        self.transport.receive_response()


    def remove_all_objects(self) -> None:
        request = protocol_pb2.RemoveAllObjectsRequest()
        request_msg = protocol_pb2.RequestMessage(remove_all_objects_req=request)
        self.transport.send_request(request_msg.SerializeToString())
        self.transport.receive_response()

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

        response_bytes = self.transport.receive_response()
        response_msg = protocol_pb2.ResponseMessage().ParseFromString(response_bytes)
        response: protocol_pb2.AddObjectResponse = response_msg.addObject

        semantic_id = SemanticID(response.semantic_id) if response.semantic_id else None
        return ObjectInfo(ObjectID(response.object_id), semantic_id)

    def apply_actions(self, actions: Sequence[Action]) -> Observations:

        pb_actions = []
        for action in actions:
            pb_action = self._action_to_proto(action)
            pb_actions.append(pb_action)
        request = protocol_pb2.ApplyActionsRequest(actions=pb_actions)
        request_msg = protocol_pb2.RequestMessage(apply_actions_req=request)
        self.transport.send_request(request_msg.SerializeToString())

        response_bytes = self.transport.receive_response()
        response_msg = protocol_pb2.ResponseMessage().ParseFromString(response_bytes)
        response: protocol_pb2.ApplyActionsResponse = response_msg.applyActionsResp
        pb_observations = response.observations
        observations = self._observations_from_proto(pb_observations)
        return observations

    @property
    def states(self) -> ProprioceptiveState:
        request_msg = protocol_pb2.RequestMessage(
            proprioceptive_state_req=protocol_pb2.ProprioceptiveStateRequest())
        self.transport.send_request(request_msg.SerializeToString())

        response_bytes = self.transport.receive_response()
        response_msg = protocol_pb2.ResponseMessage().ParseFromString(response_bytes)
        response: protocol_pb2.ProprioceptiveStateResponse = response_msg.proprioceptiveStateResp
        proprioceptive_state: protocol_pb2.ProprioceptiveState = response.proprioceptive_state
        pb_agent_states: Iterable[
            protocol_pb2.ProprioceptiveState.AgentState] = proprioceptive_state.agent_states

        result = ProprioceptiveState()
        for pb_agent_state in pb_agent_states:
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
            )
            result[AgentID(pb_agent_state.agent_id)] = agent_state

        return result

    def reset(self) -> Observations:
        request_msg = protocol_pb2.RequestMessage(reset_req=protocol_pb2.ResetRequest())
        self.transport.send_request(request_msg.SerializeToString())

        response_bytes = self.transport.receive_response()
        response_msg = protocol_pb2.ResponseMessage().ParseFromString(response_bytes)
        response: protocol_pb2.ResetResponse = response_msg.resetResp
        pb_observations = response.observations
        observations = self._observations_from_proto(pb_observations)
        return observations

    def close(self) -> None:
        request = protocol_pb2.CloseRequest()
        request_msg = protocol_pb2.RequestMessage(close_req=request)
        self.transport.send_request(request_msg.SerializeToString())
        self.transport.receive_response()

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
                    location=protocol_pb2.VectorXYZ(
                        x=action.location[0],
                        y=action.location[1],
                        z=action.location[2],
                    ),
                    rotation=protocol_pb2.QuaternionWXYZ(
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
                    rotation=protocol_pb2.QuaternionWXYZ(
                        w=action.rotation_quat[0],
                        x=action.rotation_quat[1],
                        y=action.rotation_quat[2],
                        z=action.rotation_quat[3],
                    ),
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

        return obs
