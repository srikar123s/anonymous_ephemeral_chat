#!/usr/bin/env python3
"""
Security-focused tests for the Anonymous & Ephemeral Chat Application.
"""

import unittest
import tempfile
import os
import sys
import time
import threading
import subprocess
import psutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from ephemeral_chat import EphemeralChatNode
except ImportError:
    print("Warning: Could not import EphemeralChatNode for testing")
    EphemeralChatNode = None


class TestSecurityFeatures(unittest.TestCase):
    """Test security-related features."""

    def setUp(self):
        """Set up test fixtures."""
        if EphemeralChatNode is None:
            self.skipTest("EphemeralChatNode not available")

    def test_no_disk_writes(self):
        """Test that no data is written to disk during operation."""
        # Get initial directory contents
        temp_dir = tempfile.mkdtemp()
        initial_files = set(os.listdir(temp_dir))

        # Change to temp directory and run node
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            node = EphemeralChatNode(username="DiskTest")

            # Perform some operations
            test_message = "Secret message that should not be saved"
            session_key = b"0" * 32  # Dummy key for testing
            encrypted = node.encrypt_message(test_message, session_key)

            # Add to message buffer
            node.message_buffer.append({
                'type': 'test',
                'message': test_message,
                'timestamp': time.time()
            })

            # Cleanup
            node.cleanup_session()

            # Check that no new files were created
            final_files = set(os.listdir(temp_dir))
            new_files = final_files - initial_files

            self.assertEqual(len(new_files), 0, 
                           f"Unexpected files created: {new_files}")

        finally:
            os.chdir(original_cwd)
            # Clean up temp directory
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)

    def test_memory_only_storage(self):
        """Test that all data is stored in memory only."""
        node = EphemeralChatNode(username="MemoryTest")

        # Add test data to in-memory structures
        test_data = {
            'type': 'memory_test',
            'message': 'This should only exist in RAM',
            'timestamp': time.time()
        }

        node.message_buffer.append(test_data)

        # Verify data exists in memory
        self.assertEqual(len(node.message_buffer), 1)
        self.assertEqual(node.message_buffer[0]['message'], test_data['message'])

        # Cleanup should clear all data
        node.cleanup_session()
        self.assertEqual(len(node.message_buffer), 0)

    def test_key_uniqueness(self):
        """Test that each node generates unique keys."""
        nodes = [EphemeralChatNode(username=f"Node{i}") for i in range(5)]

        # Collect all public keys
        public_keys = [node.get_public_key_string() for node in nodes]

        # All keys should be unique
        self.assertEqual(len(public_keys), len(set(public_keys)))

        # All usernames should be unique (since keys are unique)
        usernames = [node.username for node in nodes]
        self.assertEqual(len(usernames), len(set(usernames)))

        # Cleanup
        for node in nodes:
            node.cleanup_session()

    def test_session_key_uniqueness(self):
        """Test that session keys are unique between different pairs."""
        # Create three nodes
        node1 = EphemeralChatNode(username="Node1")
        node2 = EphemeralChatNode(username="Node2")
        node3 = EphemeralChatNode(username="Node3")

        # Generate session keys between different pairs
        key_12_from_1 = node1.generate_session_key(node2.public_key)
        key_12_from_2 = node2.generate_session_key(node1.public_key)
        key_13_from_1 = node1.generate_session_key(node3.public_key)
        key_23_from_2 = node2.generate_session_key(node3.public_key)

        # Same pair should generate same key
        self.assertEqual(key_12_from_1, key_12_from_2)

        # Different pairs should generate different keys
        self.assertNotEqual(key_12_from_1, key_13_from_1)
        self.assertNotEqual(key_12_from_1, key_23_from_2)
        self.assertNotEqual(key_13_from_1, key_23_from_2)

        # Cleanup
        for node in [node1, node2, node3]:
            node.cleanup_session()

    def test_message_integrity(self):
        """Test that tampered messages are rejected."""
        node1 = EphemeralChatNode(username="Sender")
        node2 = EphemeralChatNode(username="Receiver")

        # Generate session key
        session_key = node1.generate_session_key(node2.public_key)

        # Encrypt a message
        original_message = "Original secure message"
        encrypted = node1.encrypt_message(original_message, session_key)

        # Tamper with the encrypted message
        tampered = bytearray(encrypted)
        tampered[-1] = (tampered[-1] + 1) % 256  # Flip last byte

        # Attempt to decrypt tampered message
        decrypted = node2.decrypt_message(bytes(tampered), session_key)

        # Should fail to decrypt or produce garbage
        self.assertIsNone(decrypted)

        # Original message should still decrypt correctly
        original_decrypted = node2.decrypt_message(encrypted, session_key)
        self.assertIsNotNone(original_decrypted)
        self.assertEqual(original_decrypted['message'], original_message)

        # Cleanup
        node1.cleanup_session()
        node2.cleanup_session()

    def test_forward_secrecy(self):
        """Test perfect forward secrecy properties."""
        node1 = EphemeralChatNode(username="Alice")
        node2 = EphemeralChatNode(username="Bob")

        # First session
        session_key1 = node1.generate_session_key(node2.public_key)
        message1 = "First session message"
        encrypted1 = node1.encrypt_message(message1, session_key1)

        # Simulate key compromise by creating new nodes (new session)
        node1_new = EphemeralChatNode(username="Alice2")
        node2_new = EphemeralChatNode(username="Bob2")

        # Second session with different keys
        session_key2 = node1_new.generate_session_key(node2_new.public_key)

        # Keys should be different
        self.assertNotEqual(session_key1, session_key2)

        # Old encrypted message should not decrypt with new key
        decrypted_wrong = node2_new.decrypt_message(encrypted1, session_key2)
        self.assertIsNone(decrypted_wrong)

        # Cleanup
        for node in [node1, node2, node1_new, node2_new]:
            node.cleanup_session()

    def test_anonymous_usernames(self):
        """Test that usernames are properly anonymized."""
        # Create nodes without specifying username
        nodes = [EphemeralChatNode() for _ in range(3)]

        # All should have anonymous usernames
        for node in nodes:
            self.assertTrue(node.username.startswith("anon_"))
            # Username should be reasonably short hash
            self.assertLessEqual(len(node.username), 13)  # "anon_" + 8 chars

        # All usernames should be unique
        usernames = [node.username for node in nodes]
        self.assertEqual(len(usernames), len(set(usernames)))

        # Cleanup
        for node in nodes:
            node.cleanup_session()

    def test_cleanup_thoroughness(self):
        """Test that cleanup thoroughly removes all data."""
        node = EphemeralChatNode(username="CleanupTest")

        # Add data to all in-memory structures
        dummy_socket = None  # Placeholder for testing
        node.active_sessions["test_peer"] = dummy_socket
        node.message_buffer.append({"test": "data"})
        node.peer_keys["test_peer"] = node.public_key
        node.session_keys["test_peer"] = b"test_key"

        # Verify data exists
        self.assertEqual(len(node.active_sessions), 1)
        self.assertEqual(len(node.message_buffer), 1)
        self.assertEqual(len(node.peer_keys), 1)
        self.assertEqual(len(node.session_keys), 1)

        # Cleanup
        node.cleanup_session()

        # Verify all data is cleared
        self.assertEqual(len(node.active_sessions), 0)
        self.assertEqual(len(node.message_buffer), 0)
        self.assertEqual(len(node.peer_keys), 0)
        self.assertEqual(len(node.session_keys), 0)
        self.assertFalse(node.session_active)


class TestCryptographicSecurity(unittest.TestCase):
    """Test cryptographic security properties."""

    def test_key_strength(self):
        """Test that generated keys meet security requirements."""
        if EphemeralChatNode is None:
            self.skipTest("EphemeralChatNode not available")

        node = EphemeralChatNode(username="SecurityTest")

        # Test key size (SECP256R1 should provide 256-bit keys)
        session_key = node.generate_session_key(node.public_key)
        self.assertEqual(len(session_key), 32)  # 256 bits

        # Test key randomness (keys should not be all zeros or all ones)
        self.assertNotEqual(session_key, b' ' * 32)
        self.assertNotEqual(session_key, b'ÿ' * 32)

        node.cleanup_session()

    def test_iv_randomness(self):
        """Test that IVs are properly randomized."""
        if EphemeralChatNode is None:
            self.skipTest("EphemeralChatNode not available")

        node = EphemeralChatNode(username="IVTest")
        session_key = b"test_key_32_bytes_long_for_aes256"

        # Encrypt the same message multiple times
        message = "Test message for IV randomness"
        encryptions = []

        for _ in range(10):
            encrypted = node.encrypt_message(message, session_key)
            encryptions.append(encrypted[:16])  # First 16 bytes are IV

        # All IVs should be different
        self.assertEqual(len(encryptions), len(set(encryptions)))

        node.cleanup_session()


if __name__ == '__main__':
    # Run with verbose output for security tests
    unittest.main(verbosity=2)
