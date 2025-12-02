# tbp.simulator_habitat

## Generate proto files

python -m grpc_tools.protoc -IPATH/TO/TBP/MONTY/proto --python_out=src --pyi_out=src --grpc_python_out=src PATH/TO/TBP/MONTY/proto/tbp/simulator/protocol/v1/protocol.proto

python -m grpc_tools.protoc -I/Users/tslominski/tbp/prototype.simulator/proto --python_out=src --pyi_out=src --grpc_python_out=src /Users/tslominski/tbp/prototype.simulator/proto/tbp/simulator/protocol/v1/protocol.proto


# grpcurl commands debug

grpcurl -plaintext -d '{"name":"cubeSolid", "position": {"x": 0, "y": 0, "z": 0}, "rotation": {"w":1, "x": 0, "y": 0, "z": 0}, "scale": {"x": 1, "y": 1, "z": 1} }' localhost:50051 tbp.simulator.protocol.v1.SimulatorService/AddObject

grpcurl -plaintext localhost:50051 tbp.simulator.protocol.v1.SimulatorService/Reset
