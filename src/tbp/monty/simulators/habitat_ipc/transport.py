from __future__ import annotations

from multiprocessing import Queue
from typing import Protocol

from shm_rpc_bridge.transport.transport_chooser import SharedMemoryTransport


class Transport(Protocol):

    def start(self) -> None:
        ...

    def connect(self) -> Transport:
        ...

    def send_request(self, data: bytes) -> None:
        ...

    def receive_request(self) -> bytes:
        ...

    def send_response(self, data: bytes) -> None:
        ...

    def receive_response(self) -> bytes:
        ...

    def close(self) -> None:
        ...

class ShmRpcTransport(Transport):

    def __init__(self, name : str):
        self.shm_transport: SharedMemoryTransport | None = None
        self._name = name
        self._buffer_size = 750_000
        self._timeout = 300.0

    def start(self) -> None:
        self.shm_transport = SharedMemoryTransport.create(
            self._name,
            self._buffer_size,
            self._timeout
        )

    def connect(self) -> ShmRpcTransport:
        transport = ShmRpcTransport(self._name)
        transport.shm_transport = SharedMemoryTransport.open(
            self._name,
            self._buffer_size,
            self._timeout,
            wait_for_creation=120.0
        )
        return transport

    def send_request(self, data: bytes):
        self.shm_transport.send_request(data)

    def receive_request(self) -> bytes:
        return self.shm_transport.receive_request()

    def send_response(self, data: bytes):
        self.shm_transport.send_response(data)

    def receive_response(self) -> bytes:
        return self.shm_transport.receive_response()

    def close(self):
        if self.shm_transport is not None:
            self.shm_transport.close()


class QueueBasedTransport(Transport):

    def __init__(self):
        self.to_habitat = Queue()
        self.from_habitat = Queue()

    def start(self):
        pass

    def connect(self):
        return self

    def send_request(self, data: bytes):
        self.to_habitat.put(data)

    def receive_request(self) -> bytes:
        return self.to_habitat.get()

    def send_response(self, data: bytes):
        self.from_habitat.put(data)

    def receive_response(self) -> bytes:
        return self.from_habitat.get()

    def close(self):
        if self.to_habitat is not None:
            self.to_habitat.close()
        if self.from_habitat is not None:
            self.from_habitat.close()
