from __future__ import annotations

from multiprocessing import Queue
from typing import Protocol


class Transport(Protocol):

    def send_request(self, data: bytes):
        ...

    def receive_request(self) -> bytes:
        ...

    def send_response(self, data: bytes):
        ...

    def receive_response(self) -> bytes:
        ...


class QueueBasedTransport(Transport):

    def __init__(self):
        self.to_habitat = Queue()
        self.from_habitat = Queue()

    def send_request(self, data: bytes):
        self.to_habitat.put(data)

    def receive_request(self) -> bytes:
        return self.to_habitat.get()

    def send_response(self, data: bytes):
        self.from_habitat.put(data)

    def receive_response(self) -> bytes:
        return self.from_habitat.get()

