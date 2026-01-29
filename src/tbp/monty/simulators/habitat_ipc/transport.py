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
    
    Uses IPC (Unix domain sockets) with REQ-REP pattern where:
    - Each client-server pair has a unique channel identified by channel_name
    - Server binds to the IPC endpoint and receives requests
    - Client connects to the same IPC endpoint and sends requests
    - Multiple client-server pairs can coexist independently
    """

    def __init__(self, channel_name: str):
        self.context: zmq.Context | None = None
        self.socket: zmq.Socket | None = None
        self._channel_name = channel_name
        # Use /tmp for IPC socket to ensure it's accessible
        self._ipc_path = f"ipc:///tmp/habitat_ipc_{channel_name}.sock"

    def start(self) -> None:
        """Start as server: bind to IPC endpoint and wait for connections."""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self._ipc_path)

    def connect(self) -> ZmqTransport:
        """Connect as client: connect to server IPC endpoint."""
        transport = ZmqTransport(self._channel_name)
        transport.context = zmq.Context()
        transport.socket = transport.context.socket(zmq.REQ)
        
        # Try to connect with retries for server startup
        max_retries = 120
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                transport.socket.connect(transport._ipc_path)
                # Set timeouts for send and receive operations
                transport.socket.setsockopt(zmq.RCVTIMEO, 300000)  # 300 second timeout
                transport.socket.setsockopt(zmq.SNDTIMEO, 300000)  # 300 second timeout
                # Small delay to ensure connection is established
                time.sleep(0.1)
                return transport
            except zmq.ZMQError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

    def send_request(self, data: bytes) -> None:
        """Send request (client -> server)."""
        if self.socket is None:
            msg = "Socket not initialized. Call connect() for client first."
            raise RuntimeError(msg)
        self.socket.send(data)

    def receive_request(self) -> bytes:
        """Receive request (server from client)."""
        if self.socket is None:
            msg = "Socket not initialized. Call start() for server first."
            raise RuntimeError(msg)
        return self.socket.recv()

    def send_response(self, data: bytes) -> None:
        """Send response (server -> client)."""
        if self.socket is None:
            msg = "Socket not initialized. Call start() for server first."
            raise RuntimeError(msg)
        self.socket.send(data)

    def receive_response(self) -> bytes:
        """Receive response (client from server)."""
        if self.socket is None:
            msg = "Socket not initialized. Call connect() for client first."
            raise RuntimeError(msg)
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
