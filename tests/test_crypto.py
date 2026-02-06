#!/usr/bin/env python3
"""
Unit tests for cryptographic functions in the Anonymous & Ephemeral Chat Application.
"""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from ephemeral_chat import EphemeralChatNode
except ImportError:
    print("Warning: Could not import EphemeralChatNode for testing")
    EphemeralChatNode = None

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend


class TestCryptographicFunctions(unittest.TestCase):
    """Test cryptographic functions."""

    def setUp(self):
        """Set up test fixtures."""
        if EphemeralChatNode is None:
            self.skipTest("EphemeralChatNode not available")
        self.node1 = EphemeralChatNode(username="TestNode1")
        self.node2 = EphemeralChatNode(username="TestNode2")

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'node1'):
            self.node1.cleanup_session()
        if hasattr(self, 'node2'):
            self.node2.cleanup_session()

    def test_key_generation(self):
        """Test cryptographic key generation."""
        # Test that keys are generated
        self.assertIsNotNone(self.node1.private_key)
        self.assertIsNotNone(self.node1.public_key)

        # Test that keys are different for different nodes
        self.assertNotEqual(
            self.node1.get_public_key_string(),
            self.node2.get_public_key_string()
        )

    def test_key_serialization(self):
        """Test public key serialization and deserialization."""
        # Get public key as string
        key_string = self.node1.get_public_key_string()
        self.assertIsInstance(key_string, str)
        self.assertIn("BEGIN PUBLIC KEY", key_string)
        self.assertIn("END PUBLIC KEY", key_string)

        # Load key back from string
        loaded_key = self.node1.load_public_key_from_string(key_string)
        self.assertIsNotNone(loaded_key)

    def test_session_key_generation(self):
        """Test ECDH session key generation."""
        # Generate session key between two nodes
        session_key1 = self.node1.generate_session_key(self.node2.public_key)
        session_key2 = self.node2.generate_session_key(self.node1.public_key)

        # Both nodes should derive the same session key
        self.assertEqual(session_key1, session_key2)
        self.assertEqual(len(session_key1), 32)  # 256 bits

    def test_message_encryption_decryption(self):
        """Test message encryption and decryption."""
        # Generate shared session key
        session_key = self.node1.generate_session_key(self.node2.public_key)

        # Test message
        test_message = "This is a secret test message!"

        # Encrypt message
        encrypted = self.node1.encrypt_message(test_message, session_key)
        self.assertIsNotNone(encrypted)
        self.assertIsInstance(encrypted, bytes)
        self.assertGreater(len(encrypted), len(test_message))

        # Decrypt message
        decrypted = self.node2.decrypt_message(encrypted, session_key)
        self.assertIsNotNone(decrypted)
        self.assertEqual(decrypted['message'], test_message)
        self.assertEqual(decrypted['username'], self.node1.username)

    def test_encryption_randomness(self):
        """Test that encryption produces different ciphertext for same message."""
        session_key = self.node1.generate_session_key(self.node2.public_key)
        test_message = "Same message"

        # Encrypt the same message twice
        encrypted1 = self.node1.encrypt_message(test_message, session_key)
        encrypted2 = self.node1.encrypt_message(test_message, session_key)

        # Ciphertext should be different (due to random IV)
        self.assertNotEqual(encrypted1, encrypted2)

        # But both should decrypt to the same message
        decrypted1 = self.node2.decrypt_message(encrypted1, session_key)
        decrypted2 = self.node2.decrypt_message(encrypted2, session_key)

        self.assertEqual(decrypted1['message'], decrypted2['message'])

    def test_wrong_key_decryption(self):
        """Test that wrong key fails to decrypt."""
        # Generate two different session keys
        session_key1 = self.node1.generate_session_key(self.node2.public_key)

        # Create a third node with different key
        node3 = EphemeralChatNode(username="TestNode3")
        session_key2 = self.node1.generate_session_key(node3.public_key)

        # Encrypt with first key
        test_message = "Secret message"
        encrypted = self.node1.encrypt_message(test_message, session_key1)

        # Try to decrypt with wrong key
        decrypted_wrong = self.node2.decrypt_message(encrypted, session_key2)

        # Should fail to decrypt properly
        self.assertIsNone(decrypted_wrong)

        node3.cleanup_session()

    def test_empty_message_encryption(self):
        """Test encryption of empty message."""
        session_key = self.node1.generate_session_key(self.node2.public_key)

        # Test empty message
        encrypted = self.node1.encrypt_message("", session_key)
        self.assertIsNotNone(encrypted)

        decrypted = self.node2.decrypt_message(encrypted, session_key)
        self.assertIsNotNone(decrypted)
        self.assertEqual(decrypted['message'], "")

    def test_large_message_encryption(self):
        """Test encryption of large message."""
        session_key = self.node1.generate_session_key(self.node2.public_key)

        # Create a large message (10KB)
        large_message = "A" * 10240

        encrypted = self.node1.encrypt_message(large_message, session_key)
        self.assertIsNotNone(encrypted)

        decrypted = self.node2.decrypt_message(encrypted, session_key)
        self.assertIsNotNone(decrypted)
        self.assertEqual(decrypted['message'], large_message)


if __name__ == '__main__':
    unittest.main()
