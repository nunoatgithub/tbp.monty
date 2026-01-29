from __future__ import annotations

import time
from multiprocessing import Queue
from typing import Protocol

import zmq


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

class ZmqTransport(Transport):
    """ZeroMQ-based transport for inter-process communication.
    
    Uses a REQ-REP pattern where:
    - Server binds to a TCP port and receives requests
    - Client connects to the server and sends requests
    """

    def __init__(self, port: int = 5555, host: str = "127.0.0.1"):
        self.context: zmq.Context | None = None
        self.socket: zmq.Socket | None = None
        self._port = port
        self._host = host
        self._is_server = False

    def start(self) -> None:
        """Start as server: bind to port and wait for connections."""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{self._host}:{self._port}")
        self._is_server = True

    def connect(self) -> ZmqTransport:
        """Connect as client: connect to server."""
        transport = ZmqTransport(self._port, self._host)
        transport.context = zmq.Context()
        transport.socket = transport.context.socket(zmq.REQ)
        
        # Try to connect with retries for server startup
        max_retries = 120
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                transport.socket.connect(f"tcp://{self._host}:{self._port}")
                # Test connection by setting a timeout
                transport.socket.setsockopt(zmq.RCVTIMEO, 300000)  # 300 second timeout
                transport.socket.setsockopt(zmq.SNDTIMEO, 300000)  # 300 second timeout
                transport._is_server = False
                return transport
            except zmq.ZMQError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
        
        return transport

    def send_request(self, data: bytes) -> None:
        """Send request (client -> server)."""
        if self.socket is None:
            raise RuntimeError("Socket not initialized")
        self.socket.send(data)

    def receive_request(self) -> bytes:
        """Receive request (server from client)."""
        if self.socket is None:
            raise RuntimeError("Socket not initialized")
        return self.socket.recv()

    def send_response(self, data: bytes) -> None:
        """Send response (server -> client)."""
        if self.socket is None:
            raise RuntimeError("Socket not initialized")
        self.socket.send(data)

    def receive_response(self) -> bytes:
        """Receive response (client from server)."""
        if self.socket is None:
            raise RuntimeError("Socket not initialized")
        return self.socket.recv()

    def close(self) -> None:
        """Close the socket and context."""
        if self.socket is not None:
            self.socket.close()
            self.socket = None
        if self.context is not None:
            self.context.term()
            self.context = None


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
