https://github.com/grpc/grpc/blob/v1.74.0/examples/python/route_guide/route_guide_server.py

https://github.com/grpc/grpc/blob/master/examples/python/helloworld/greeter_server_with_reflection.py

```
buf curl --protocol grpc --http2-prior-knowledge http://localhost:50051/tbp.simulator.protocol.v1.SimulatorService/RemoveAllObjects -v
```

## Generate proto files

python -m grpc_tools.protoc -Iproto --python_out=src --pyi_out=src --grpc_python_out=src proto/tbp/simulator/protocol/v1/protocol.proto
