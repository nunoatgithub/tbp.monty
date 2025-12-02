from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RemoveAllObjectsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RemoveAllObjectsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class VectorXYZ(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class QuaternionWXYZ(_message.Message):
    __slots__ = ("w", "x", "y", "z")
    W_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    w: float
    x: float
    y: float
    z: float
    def __init__(self, w: _Optional[float] = ..., x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class AddObjectRequest(_message.Message):
    __slots__ = ("name", "position", "rotation", "scale", "semantic_id", "primary_target_object")
    NAME_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    SEMANTIC_ID_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_TARGET_OBJECT_FIELD_NUMBER: _ClassVar[int]
    name: str
    position: VectorXYZ
    rotation: QuaternionWXYZ
    scale: VectorXYZ
    semantic_id: int
    primary_target_object: int
    def __init__(self, name: _Optional[str] = ..., position: _Optional[_Union[VectorXYZ, _Mapping]] = ..., rotation: _Optional[_Union[QuaternionWXYZ, _Mapping]] = ..., scale: _Optional[_Union[VectorXYZ, _Mapping]] = ..., semantic_id: _Optional[int] = ..., primary_target_object: _Optional[int] = ...) -> None: ...

class AddObjectResponse(_message.Message):
    __slots__ = ("object_id", "semantic_id")
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    SEMANTIC_ID_FIELD_NUMBER: _ClassVar[int]
    object_id: int
    semantic_id: int
    def __init__(self, object_id: _Optional[int] = ..., semantic_id: _Optional[int] = ...) -> None: ...

class LookDownAction(_message.Message):
    __slots__ = ("agent_id", "rotation_degrees", "constraint_degrees")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ROTATION_DEGREES_FIELD_NUMBER: _ClassVar[int]
    CONSTRAINT_DEGREES_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    rotation_degrees: float
    constraint_degrees: float
    def __init__(self, agent_id: _Optional[str] = ..., rotation_degrees: _Optional[float] = ..., constraint_degrees: _Optional[float] = ...) -> None: ...

class LookUpAction(_message.Message):
    __slots__ = ("agent_id", "rotation_degrees", "constraint_degrees")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ROTATION_DEGREES_FIELD_NUMBER: _ClassVar[int]
    CONSTRAINT_DEGREES_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    rotation_degrees: float
    constraint_degrees: float
    def __init__(self, agent_id: _Optional[str] = ..., rotation_degrees: _Optional[float] = ..., constraint_degrees: _Optional[float] = ...) -> None: ...

class MoveForwardAction(_message.Message):
    __slots__ = ("agent_id", "distance")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    distance: float
    def __init__(self, agent_id: _Optional[str] = ..., distance: _Optional[float] = ...) -> None: ...

class MoveTangentiallyAction(_message.Message):
    __slots__ = ("agent_id", "distance", "direction")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    distance: float
    direction: VectorXYZ
    def __init__(self, agent_id: _Optional[str] = ..., distance: _Optional[float] = ..., direction: _Optional[_Union[VectorXYZ, _Mapping]] = ...) -> None: ...

class OrientHorizontalAction(_message.Message):
    __slots__ = ("agent_id", "rotation_degrees", "left_distance", "forward_distance")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ROTATION_DEGREES_FIELD_NUMBER: _ClassVar[int]
    LEFT_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    FORWARD_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    rotation_degrees: float
    left_distance: float
    forward_distance: float
    def __init__(self, agent_id: _Optional[str] = ..., rotation_degrees: _Optional[float] = ..., left_distance: _Optional[float] = ..., forward_distance: _Optional[float] = ...) -> None: ...

class OrientVerticalAction(_message.Message):
    __slots__ = ("agent_id", "rotation_degrees", "down_distance", "forward_distance")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ROTATION_DEGREES_FIELD_NUMBER: _ClassVar[int]
    DOWN_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    FORWARD_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    rotation_degrees: float
    down_distance: float
    forward_distance: float
    def __init__(self, agent_id: _Optional[str] = ..., rotation_degrees: _Optional[float] = ..., down_distance: _Optional[float] = ..., forward_distance: _Optional[float] = ...) -> None: ...

class SetAgentPitchAction(_message.Message):
    __slots__ = ("agent_id", "pitch_degrees")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    PITCH_DEGREES_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    pitch_degrees: float
    def __init__(self, agent_id: _Optional[str] = ..., pitch_degrees: _Optional[float] = ...) -> None: ...

class SetAgentPoseAction(_message.Message):
    __slots__ = ("agent_id", "location", "rotation")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    location: VectorXYZ
    rotation: QuaternionWXYZ
    def __init__(self, agent_id: _Optional[str] = ..., location: _Optional[_Union[VectorXYZ, _Mapping]] = ..., rotation: _Optional[_Union[QuaternionWXYZ, _Mapping]] = ...) -> None: ...

class SetSensorPitchAction(_message.Message):
    __slots__ = ("agent_id", "pitch_degrees")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    PITCH_DEGREES_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    pitch_degrees: float
    def __init__(self, agent_id: _Optional[str] = ..., pitch_degrees: _Optional[float] = ...) -> None: ...

class SetSensorPoseAction(_message.Message):
    __slots__ = ("agent_id", "location", "rotation")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    location: VectorXYZ
    rotation: QuaternionWXYZ
    def __init__(self, agent_id: _Optional[str] = ..., location: _Optional[_Union[VectorXYZ, _Mapping]] = ..., rotation: _Optional[_Union[QuaternionWXYZ, _Mapping]] = ...) -> None: ...

class SetSensorRotationAction(_message.Message):
    __slots__ = ("agent_id", "rotation")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    rotation: QuaternionWXYZ
    def __init__(self, agent_id: _Optional[str] = ..., rotation: _Optional[_Union[QuaternionWXYZ, _Mapping]] = ...) -> None: ...

class SetYawAction(_message.Message):
    __slots__ = ("agent_id", "rotation_degrees")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ROTATION_DEGREES_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    rotation_degrees: float
    def __init__(self, agent_id: _Optional[str] = ..., rotation_degrees: _Optional[float] = ...) -> None: ...

class TurnLeftAction(_message.Message):
    __slots__ = ("agent_id", "rotation_degrees")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ROTATION_DEGREES_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    rotation_degrees: float
    def __init__(self, agent_id: _Optional[str] = ..., rotation_degrees: _Optional[float] = ...) -> None: ...

class TurnRightAction(_message.Message):
    __slots__ = ("agent_id", "rotation_degrees")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ROTATION_DEGREES_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    rotation_degrees: float
    def __init__(self, agent_id: _Optional[str] = ..., rotation_degrees: _Optional[float] = ...) -> None: ...

class StepRequest(_message.Message):
    __slots__ = ("look_down", "look_up", "move_forward", "move_tangentially", "orient_horizontal", "orient_vertical", "set_agent_pitch", "set_agent_pose", "set_sensor_pitch", "set_sensor_pose", "set_sensor_rotation", "set_yaw", "turn_left", "turn_right")
    LOOK_DOWN_FIELD_NUMBER: _ClassVar[int]
    LOOK_UP_FIELD_NUMBER: _ClassVar[int]
    MOVE_FORWARD_FIELD_NUMBER: _ClassVar[int]
    MOVE_TANGENTIALLY_FIELD_NUMBER: _ClassVar[int]
    ORIENT_HORIZONTAL_FIELD_NUMBER: _ClassVar[int]
    ORIENT_VERTICAL_FIELD_NUMBER: _ClassVar[int]
    SET_AGENT_PITCH_FIELD_NUMBER: _ClassVar[int]
    SET_AGENT_POSE_FIELD_NUMBER: _ClassVar[int]
    SET_SENSOR_PITCH_FIELD_NUMBER: _ClassVar[int]
    SET_SENSOR_POSE_FIELD_NUMBER: _ClassVar[int]
    SET_SENSOR_ROTATION_FIELD_NUMBER: _ClassVar[int]
    SET_YAW_FIELD_NUMBER: _ClassVar[int]
    TURN_LEFT_FIELD_NUMBER: _ClassVar[int]
    TURN_RIGHT_FIELD_NUMBER: _ClassVar[int]
    look_down: LookDownAction
    look_up: LookUpAction
    move_forward: MoveForwardAction
    move_tangentially: MoveTangentiallyAction
    orient_horizontal: OrientHorizontalAction
    orient_vertical: OrientVerticalAction
    set_agent_pitch: SetAgentPitchAction
    set_agent_pose: SetAgentPoseAction
    set_sensor_pitch: SetSensorPitchAction
    set_sensor_pose: SetSensorPoseAction
    set_sensor_rotation: SetSensorRotationAction
    set_yaw: SetYawAction
    turn_left: TurnLeftAction
    turn_right: TurnRightAction
    def __init__(self, look_down: _Optional[_Union[LookDownAction, _Mapping]] = ..., look_up: _Optional[_Union[LookUpAction, _Mapping]] = ..., move_forward: _Optional[_Union[MoveForwardAction, _Mapping]] = ..., move_tangentially: _Optional[_Union[MoveTangentiallyAction, _Mapping]] = ..., orient_horizontal: _Optional[_Union[OrientHorizontalAction, _Mapping]] = ..., orient_vertical: _Optional[_Union[OrientVerticalAction, _Mapping]] = ..., set_agent_pitch: _Optional[_Union[SetAgentPitchAction, _Mapping]] = ..., set_agent_pose: _Optional[_Union[SetAgentPoseAction, _Mapping]] = ..., set_sensor_pitch: _Optional[_Union[SetSensorPitchAction, _Mapping]] = ..., set_sensor_pose: _Optional[_Union[SetSensorPoseAction, _Mapping]] = ..., set_sensor_rotation: _Optional[_Union[SetSensorRotationAction, _Mapping]] = ..., set_yaw: _Optional[_Union[SetYawAction, _Mapping]] = ..., turn_left: _Optional[_Union[TurnLeftAction, _Mapping]] = ..., turn_right: _Optional[_Union[TurnRightAction, _Mapping]] = ...) -> None: ...

class Observations(_message.Message):
    __slots__ = ("agent_observations",)
    class AgentObservation(_message.Message):
        __slots__ = ("agent_id", "sensor_observations")
        class SensorObservation(_message.Message):
            __slots__ = ("sensor_id", "raw", "rgba", "depth", "semantic", "semantic_3d", "sensor_frame_data", "world_camera", "pixel_loc")
            SENSOR_ID_FIELD_NUMBER: _ClassVar[int]
            RAW_FIELD_NUMBER: _ClassVar[int]
            RGBA_FIELD_NUMBER: _ClassVar[int]
            DEPTH_FIELD_NUMBER: _ClassVar[int]
            SEMANTIC_FIELD_NUMBER: _ClassVar[int]
            SEMANTIC_3D_FIELD_NUMBER: _ClassVar[int]
            SENSOR_FRAME_DATA_FIELD_NUMBER: _ClassVar[int]
            WORLD_CAMERA_FIELD_NUMBER: _ClassVar[int]
            PIXEL_LOC_FIELD_NUMBER: _ClassVar[int]
            sensor_id: str
            raw: bytes
            rgba: bytes
            depth: bytes
            semantic: bytes
            semantic_3d: bytes
            sensor_frame_data: bytes
            world_camera: bytes
            pixel_loc: bytes
            def __init__(self, sensor_id: _Optional[str] = ..., raw: _Optional[bytes] = ..., rgba: _Optional[bytes] = ..., depth: _Optional[bytes] = ..., semantic: _Optional[bytes] = ..., semantic_3d: _Optional[bytes] = ..., sensor_frame_data: _Optional[bytes] = ..., world_camera: _Optional[bytes] = ..., pixel_loc: _Optional[bytes] = ...) -> None: ...
        AGENT_ID_FIELD_NUMBER: _ClassVar[int]
        SENSOR_OBSERVATIONS_FIELD_NUMBER: _ClassVar[int]
        agent_id: str
        sensor_observations: _containers.RepeatedCompositeFieldContainer[Observations.AgentObservation.SensorObservation]
        def __init__(self, agent_id: _Optional[str] = ..., sensor_observations: _Optional[_Iterable[_Union[Observations.AgentObservation.SensorObservation, _Mapping]]] = ...) -> None: ...
    AGENT_OBSERVATIONS_FIELD_NUMBER: _ClassVar[int]
    agent_observations: _containers.RepeatedCompositeFieldContainer[Observations.AgentObservation]
    def __init__(self, agent_observations: _Optional[_Iterable[_Union[Observations.AgentObservation, _Mapping]]] = ...) -> None: ...

class ProprioceptiveState(_message.Message):
    __slots__ = ("agent_states",)
    class AgentState(_message.Message):
        __slots__ = ("agent_id", "position", "rotation", "motor_only_step", "sensor_states")
        class SensorState(_message.Message):
            __slots__ = ("sensor_id", "position", "rotation")
            SENSOR_ID_FIELD_NUMBER: _ClassVar[int]
            POSITION_FIELD_NUMBER: _ClassVar[int]
            ROTATION_FIELD_NUMBER: _ClassVar[int]
            sensor_id: str
            position: VectorXYZ
            rotation: QuaternionWXYZ
            def __init__(self, sensor_id: _Optional[str] = ..., position: _Optional[_Union[VectorXYZ, _Mapping]] = ..., rotation: _Optional[_Union[QuaternionWXYZ, _Mapping]] = ...) -> None: ...
        AGENT_ID_FIELD_NUMBER: _ClassVar[int]
        POSITION_FIELD_NUMBER: _ClassVar[int]
        ROTATION_FIELD_NUMBER: _ClassVar[int]
        MOTOR_ONLY_STEP_FIELD_NUMBER: _ClassVar[int]
        SENSOR_STATES_FIELD_NUMBER: _ClassVar[int]
        agent_id: str
        position: VectorXYZ
        rotation: QuaternionWXYZ
        motor_only_step: bool
        sensor_states: _containers.RepeatedCompositeFieldContainer[ProprioceptiveState.AgentState.SensorState]
        def __init__(self, agent_id: _Optional[str] = ..., position: _Optional[_Union[VectorXYZ, _Mapping]] = ..., rotation: _Optional[_Union[QuaternionWXYZ, _Mapping]] = ..., motor_only_step: bool = ..., sensor_states: _Optional[_Iterable[_Union[ProprioceptiveState.AgentState.SensorState, _Mapping]]] = ...) -> None: ...
    AGENT_STATES_FIELD_NUMBER: _ClassVar[int]
    agent_states: _containers.RepeatedCompositeFieldContainer[ProprioceptiveState.AgentState]
    def __init__(self, agent_states: _Optional[_Iterable[_Union[ProprioceptiveState.AgentState, _Mapping]]] = ...) -> None: ...

class StepResponse(_message.Message):
    __slots__ = ("observations", "proprioceptive_state")
    OBSERVATIONS_FIELD_NUMBER: _ClassVar[int]
    PROPRIOCEPTIVE_STATE_FIELD_NUMBER: _ClassVar[int]
    observations: Observations
    proprioceptive_state: ProprioceptiveState
    def __init__(self, observations: _Optional[_Union[Observations, _Mapping]] = ..., proprioceptive_state: _Optional[_Union[ProprioceptiveState, _Mapping]] = ...) -> None: ...

class ResetRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResetResponse(_message.Message):
    __slots__ = ("observations", "proprioceptive_state")
    OBSERVATIONS_FIELD_NUMBER: _ClassVar[int]
    PROPRIOCEPTIVE_STATE_FIELD_NUMBER: _ClassVar[int]
    observations: Observations
    proprioceptive_state: ProprioceptiveState
    def __init__(self, observations: _Optional[_Union[Observations, _Mapping]] = ..., proprioceptive_state: _Optional[_Union[ProprioceptiveState, _Mapping]] = ...) -> None: ...

class CloseRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CloseResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
