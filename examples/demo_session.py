#!/usr/bin/env python3
"""
Demo script for Anonymous & Ephemeral Chat Application
Demonstrates basic usage and automated testing scenarios.
"""

import sys
import os
import time
import threading
import subprocess

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from ephemeral_chat import EphemeralChatNode
except ImportError:
    print("❌ Could not import EphemeralChatNode. Make sure you're in the project directory.")
    sys.exit(1)


def demo_two_nodes():
    """Demonstrate communication between two nodes."""
    print("🎭 Demo: Two Node Communication")
    print("=" * 40)

    # Create two nodes
    print("Creating Alice's node...")
    alice = EphemeralChatNode(port=0, username="Alice")

    print("Creating Bob's node...")
    bob = EphemeralChatNode(port=0, username="Bob")

    # Start Alice's listener
    alice_thread = threading.Thread(target=alice.start_listening, daemon=True)
    alice_thread.start()

    # Bob connects to Alice
    print(f"\nBob connecting to Alice on port {alice.port}...")
    time.sleep(1)  # Give Alice time to start listening

    if bob.connect_to_peer("localhost", alice.port):
        print("✅ Connection established!")

        # Send some messages
        time.sleep(1)
        print("\n📤 Bob sends message to Alice...")
        bob.send_message("Hello Alice! This is an encrypted ephemeral message.")

        time.sleep(1)
        print("\n📤 Alice sends reply to Bob...")
        alice.send_message("Hi Bob! Great to see the encryption working!")

        time.sleep(2)

        # Show message history
        print("\n📜 Alice's message history:")
        alice.show_message_history()

        print("\n📜 Bob's message history:")
        bob.show_message_history()

    else:
        print("❌ Connection failed!")

    # Cleanup
    print("\n🧹 Cleaning up...")
    alice.cleanup_session()
    bob.cleanup_session()

    print("✅ Demo complete - all data destroyed!")


def demo_security_features():
    """Demonstrate security features."""
    print("\n🔐 Demo: Security Features")
    print("=" * 40)

    node = EphemeralChatNode(username="SecurityDemo")

    print(f"🔑 Generated temporary identity: {node.username}")
    print(f"🔧 Public key fingerprint: {node.get_public_key_string()[:64]}...")

    # Show key generation
    print("\n🎲 Generating session key with dummy peer...")
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.backends import default_backend

    # Create dummy peer key for demonstration
    dummy_private = ec.generate_private_key(ec.SECP256R1(), default_backend())
    dummy_public = dummy_private.public_key()

    session_key = node.generate_session_key(dummy_public)
    if session_key:
        print(f"✅ Session key generated: {session_key[:16].hex()}... (first 16 bytes)")

    # Demonstrate message encryption
    print("\n🔒 Encrypting test message...")
    test_message = "This is a secret message that will be encrypted!"
    encrypted = node.encrypt_message(test_message, session_key)

    if encrypted:
        print(f"✅ Message encrypted: {len(encrypted)} bytes")
        print(f"🔧 Encrypted data (first 32 bytes): {encrypted[:32].hex()}")

        # Decrypt the message
        decrypted = node.decrypt_message(encrypted, session_key)
        if decrypted and decrypted.get('message') == test_message:
            print("✅ Message successfully decrypted and verified!")
        else:
            print("❌ Decryption failed!")

    # Show memory usage
    print("\n💾 Memory usage demonstration:")
    import psutil
    import os

    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"📊 Current memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
    print("📝 All chat data is stored in this memory - no disk storage!")

    # Cleanup
    node.cleanup_session()
    print("\n✅ All cryptographic data destroyed!")


def main():
    """Run all demos."""
    print("🚀 Anonymous & Ephemeral Chat - Demo Suite")
    print("=" * 50)
    print("This demo showcases the key features of the application.")
    print("All data remains in memory and is destroyed at the end.\n")

    try:
        # Demo 1: Basic communication
        demo_two_nodes()

        # Demo 2: Security features
        demo_security_features()

        print("\n🎉 All demos completed successfully!")
        print("🔐 Remember: In a real session, this data would be destroyed when you exit.")

    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")

    print("\n💡 Try running the interactive mode with:")
    print("   python src/ephemeral_chat.py --port 8000")


if __name__ == "__main__":
    main()
