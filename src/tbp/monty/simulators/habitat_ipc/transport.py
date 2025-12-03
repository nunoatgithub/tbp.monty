from __future__ import annotations

from multiprocessing import Queue
from typing import Protocol


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


