# Copyright 2025 Thousand Brains Project
# Copyright 2022-2024 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
from __future__ import annotations

import unittest
import time
import threading

from tbp.monty.simulators.habitat_ipc.transport import ZmqTransport


class TestZmqTransport(unittest.TestCase):
    """Test ZeroMQ transport implementation."""

    def test_zmq_transport_basic_communication(self):
        """Test basic request-response communication."""
        port = 15555  # Use a specific test port
        test_message = b"test message"
        response_message = b"response message"

        # Create server in a separate thread
        server_transport = ZmqTransport(port=port)
        
        def server_thread():
            server_transport.start()
            # Receive request
            received = server_transport.receive_request()
            self.assertEqual(received, test_message)
            # Send response
            server_transport.send_response(response_message)
            # Clean up
            server_transport.close()

        server = threading.Thread(target=server_thread)
        server.start()
        
        # Give server time to start
        time.sleep(1)

        # Create client and connect
        client_transport = ZmqTransport(port=port)
        client = client_transport.connect()
        
        try:
            # Send request
            client.send_request(test_message)
            # Receive response
            response = client.receive_response()
            self.assertEqual(response, response_message)
        finally:
            client.close()
            server.join(timeout=5)

    def test_zmq_transport_multiple_messages(self):
        """Test multiple request-response cycles."""
        port = 15556  # Use a different port for this test
        num_messages = 3

        server_transport = ZmqTransport(port=port)
        
        def server_thread():
            server_transport.start()
            for i in range(num_messages):
                # Receive request
                received = server_transport.receive_request()
                # Send response with the same number
                server_transport.send_response(received)
            server_transport.close()

        server = threading.Thread(target=server_thread)
        server.start()
        
        # Give server time to start
        time.sleep(1)

        # Create client and connect
        client_transport = ZmqTransport(port=port)
        client = client_transport.connect()
        
        try:
            for i in range(num_messages):
                message = f"message {i}".encode()
                client.send_request(message)
                response = client.receive_response()
                self.assertEqual(response, message)
        finally:
            client.close()
            server.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
