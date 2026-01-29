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

import secrets
import threading
import time
import unittest

from tbp.monty.simulators.habitat_ipc.transport import ZmqTransport


class TestZmqTransport(unittest.TestCase):
    """Test ZeroMQ transport implementation.
    
    Each test creates a unique channel to ensure isolation between tests
    and demonstrate the one-to-one client-server relationship.
    """

    def test_zmq_transport_basic_communication(self):
        """Test basic request-response communication with unique channel."""
        # Each test gets a unique channel name
        channel_name = f"test_{secrets.token_hex(5)}"
        test_message = b"test message"
        response_message = b"response message"

        # Create server in a separate thread
        server_transport = ZmqTransport(channel_name=channel_name)
        
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
        
        # Give server time to start and bind
        time.sleep(1)

        # Create client and connect
        client_transport = ZmqTransport(channel_name=channel_name)
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
        """Test multiple request-response cycles with unique channel."""
        # Each test gets a unique channel name
        channel_name = f"test_{secrets.token_hex(5)}"
        num_messages = 3

        server_transport = ZmqTransport(channel_name=channel_name)
        
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
        
        # Give server time to start and bind
        time.sleep(1)

        # Create client and connect
        client_transport = ZmqTransport(channel_name=channel_name)
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

    def test_zmq_transport_multiple_independent_channels(self):
        """Test that multiple client-server pairs can operate independently.
        
        This demonstrates the one-to-one relationship and ability to run
        multiple channels simultaneously without interference.
        """
        # Create two independent channels
        channel1 = f"test_{secrets.token_hex(5)}"
        channel2 = f"test_{secrets.token_hex(5)}"
        
        results = {"channel1": None, "channel2": None}
        
        def server_thread(channel_name, expected_msg, response_msg, result_key):
            transport = ZmqTransport(channel_name=channel_name)
            transport.start()
            received = transport.receive_request()
            results[result_key] = (received == expected_msg)
            transport.send_response(response_msg)
            transport.close()
        
        # Start two independent servers
        msg1 = b"message for channel 1"
        msg2 = b"message for channel 2"
        resp1 = b"response from channel 1"
        resp2 = b"response from channel 2"
        
        server1 = threading.Thread(target=server_thread, args=(channel1, msg1, resp1, "channel1"))
        server2 = threading.Thread(target=server_thread, args=(channel2, msg2, resp2, "channel2"))
        
        server1.start()
        server2.start()
        
        # Give servers time to start
        time.sleep(1)
        
        # Connect clients to their respective servers
        client1 = ZmqTransport(channel_name=channel1).connect()
        client2 = ZmqTransport(channel_name=channel2).connect()
        
        try:
            # Each client communicates with its own server
            client1.send_request(msg1)
            response1 = client1.receive_response()
            
            client2.send_request(msg2)
            response2 = client2.receive_response()
            
            # Verify each got the correct response
            self.assertEqual(response1, resp1)
            self.assertEqual(response2, resp2)
            
            # Verify servers received correct messages
            self.assertTrue(results["channel1"])
            self.assertTrue(results["channel2"])
        finally:
            client1.close()
            client2.close()
            server1.join(timeout=5)
            server2.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
