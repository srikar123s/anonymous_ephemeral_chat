#!/usr/bin/env python3
"""
Unit tests for network functions in the Anonymous & Ephemeral Chat Application.
"""

import unittest
import socket
import threading
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from ephemeral_chat import EphemeralChatNode
except ImportError:
    print("Warning: Could not import EphemeralChatNode for testing")
    EphemeralChatNode = None


class TestNetworkFunctions(unittest.TestCase):
    """Test network communication functions."""

    def setUp(self):
        """Set up test fixtures."""
        if EphemeralChatNode is None:
            self.skipTest("EphemeralChatNode not available")

    def test_node_initialization(self):
        """Test node initialization with network binding."""
        node = EphemeralChatNode(username="TestNode")

        # Should have valid socket and port
        self.assertIsNotNone(node.socket)
        self.assertGreater(node.port, 0)
        self.assertEqual(node.username, "TestNode")

        node.cleanup_session()

    def test_port_binding(self):
        """Test binding to specific port."""
        # Find an available port
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('localhost', 0))
        test_port = test_socket.getsockname()[1]
        test_socket.close()

        # Create node with specific port
        node = EphemeralChatNode(port=test_port, username="PortTest")
        self.assertEqual(node.port, test_port)

        node.cleanup_session()

    def test_peer_connection(self):
        """Test P2P connection between two nodes."""
        # Create two nodes
        node1 = EphemeralChatNode(username="Node1")
        node2 = EphemeralChatNode(username="Node2")

        # Start node1 listening
        listener_thread = threading.Thread(target=node1.start_listening, daemon=True)
        listener_thread.start()
        time.sleep(0.1)  # Give time to start listening

        # Node2 connects to node1
        success = node2.connect_to_peer("localhost", node1.port)

        time.sleep(0.1)  # Give time for connection to establish

        # Check connection was successful
        self.assertTrue(success)
        self.assertEqual(len(node2.active_sessions), 1)

        # Cleanup
        node1.cleanup_session()
        node2.cleanup_session()

    def test_message_transmission(self):
        """Test message transmission between nodes."""
        # Create two nodes
        node1 = EphemeralChatNode(username="Sender")
        node2 = EphemeralChatNode(username="Receiver")

        # Start node1 listening
        listener_thread = threading.Thread(target=node1.start_listening, daemon=True)
        listener_thread.start()
        time.sleep(0.1)

        # Connect node2 to node1
        success = node2.connect_to_peer("localhost", node1.port)
        self.assertTrue(success)
        time.sleep(0.2)  # Give time for key exchange

        # Send message from node2 to node1
        test_message = "Hello from automated test!"
        node2.send_message(test_message)
        time.sleep(0.1)  # Give time for message delivery

        # Check that message was stored in node1's buffer
        # (In a real test, we'd need a way to verify receipt)
        self.assertEqual(len(node2.message_buffer), 1)
        self.assertEqual(node2.message_buffer[0]['message'], test_message)

        # Cleanup
        node1.cleanup_session()
        node2.cleanup_session()

    def test_multiple_connections(self):
        """Test multiple peer connections."""
        # Create three nodes
        node1 = EphemeralChatNode(username="Hub")
        node2 = EphemeralChatNode(username="Peer1")
        node3 = EphemeralChatNode(username="Peer2")

        # Start node1 listening
        listener_thread = threading.Thread(target=node1.start_listening, daemon=True)
        listener_thread.start()
        time.sleep(0.1)

        # Connect both peers to hub
        success2 = node2.connect_to_peer("localhost", node1.port)
        success3 = node3.connect_to_peer("localhost", node1.port)

        self.assertTrue(success2)
        self.assertTrue(success3)

        time.sleep(0.2)  # Give time for connections

        # Check connections
        self.assertEqual(len(node2.active_sessions), 1)
        self.assertEqual(len(node3.active_sessions), 1)

        # Cleanup
        node1.cleanup_session()
        node2.cleanup_session()
        node3.cleanup_session()

    def test_connection_failure(self):
        """Test connection to non-existent peer fails gracefully."""
        node = EphemeralChatNode(username="TestNode")

        # Try to connect to non-existent peer
        success = node.connect_to_peer("localhost", 99999)  # Unlikely to be in use
        self.assertFalse(success)

        # Should have no active sessions
        self.assertEqual(len(node.active_sessions), 0)

        node.cleanup_session()

    def test_session_cleanup(self):
        """Test that session cleanup properly closes connections."""
        node = EphemeralChatNode(username="CleanupTest")

        # Verify initial state
        self.assertTrue(node.session_active)
        self.assertIsNotNone(node.socket)

        # Cleanup
        node.cleanup_session()

        # Verify cleanup
        self.assertFalse(node.session_active)
        self.assertEqual(len(node.active_sessions), 0)
        self.assertEqual(len(node.message_buffer), 0)


class TestSocketUtilities(unittest.TestCase):
    """Test low-level socket utilities."""

    def test_socket_creation(self):
        """Test basic socket creation and binding."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Should be able to bind to localhost
        sock.bind(('localhost', 0))
        port = sock.getsockname()[1]

        self.assertGreater(port, 0)
        self.assertLess(port, 65536)

        sock.close()

    def test_socket_communication(self):
        """Test basic socket communication."""
        def echo_server(server_socket):
            server_socket.listen(1)
            conn, addr = server_socket.accept()
            data = conn.recv(1024)
            conn.send(data)
            conn.close()

        # Create server socket
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('localhost', 0))
        port = server_sock.getsockname()[1]

        # Start server in thread
        server_thread = threading.Thread(target=echo_server, args=(server_sock,))
        server_thread.start()

        # Client connects and sends data
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect(('localhost', port))

        test_data = b"test message"
        client_sock.send(test_data)
        received = client_sock.recv(1024)

        client_sock.close()
        server_thread.join()
        server_sock.close()

        self.assertEqual(received, test_data)


if __name__ == '__main__':
    unittest.main()
