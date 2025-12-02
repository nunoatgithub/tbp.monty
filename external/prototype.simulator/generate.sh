#!/bin/zsh

python -m grpc_tools.protoc -Iproto --python_out=src --pyi_out=src --grpc_python_out=src proto/tbp/simulator/protocol/v1/protocol.proto
