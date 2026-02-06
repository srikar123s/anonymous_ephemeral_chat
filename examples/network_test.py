#!/usr/bin/env python3
"""
Network connectivity test for Anonymous & Ephemeral Chat Application
Tests basic network functionality and port availability.
"""

import socket
import threading
import time
import sys


def test_port_availability(port_range=(8000, 8010)):
    """Test which ports are available for use."""
    print("🔍 Testing port availability...")
    available_ports = []

    for port in range(*port_range):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            available_ports.append(port)
            print(f"✅ Port {port} available")
        except OSError:
            print(f"❌ Port {port} in use")

    return available_ports


def test_socket_communication():
    """Test basic socket communication."""
    print("\n🔌 Testing socket communication...")

    # Simple echo server for testing
    def echo_server(port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', port))
        server_socket.listen(1)

        print(f"📡 Test server listening on port {port}")

        try:
            conn, addr = server_socket.accept()
            data = conn.recv(1024)
            conn.send(b"Echo: " + data)
            conn.close()
            print(f"✅ Server echoed data from {addr}")
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            server_socket.close()

    # Find available port
    available_ports = test_port_availability((9000, 9010))
    if not available_ports:
        print("❌ No available ports for testing")
        return False

    test_port = available_ports[0]

    # Start server in background
    server_thread = threading.Thread(target=echo_server, args=(test_port,), daemon=True)
    server_thread.start()

    # Give server time to start
    time.sleep(0.5)

    # Test client connection
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', test_port))

        test_message = b"Hello from client!"
        client_socket.send(test_message)

        response = client_socket.recv(1024)
        client_socket.close()

        if response == b"Echo: " + test_message:
            print("✅ Socket communication test passed")
            return True
        else:
            print(f"❌ Unexpected response: {response}")
            return False

    except Exception as e:
        print(f"❌ Client connection error: {e}")
        return False


def test_firewall_and_nat():
    """Test for common firewall and NAT issues."""
    print("\n🛡️ Testing firewall and NAT configuration...")

    # Test localhost binding
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        local_port = sock.getsockname()[1]
        sock.close()
        print(f"✅ Can bind to localhost (127.0.0.1:{local_port})")
    except Exception as e:
        print(f"❌ Cannot bind to localhost: {e}")

    # Test external interface binding (if available)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', 0))
        external_port = sock.getsockname()[1]
        sock.close()
        print(f"✅ Can bind to all interfaces (0.0.0.0:{external_port})")
        print("⚠️  Note: Binding to 0.0.0.0 allows external connections")
    except Exception as e:
        print(f"❌ Cannot bind to external interfaces: {e}")
        print("ℹ️  This may limit P2P connectivity across networks")

    # Get local IP address
    try:
        # Connect to a remote address to find local IP
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_sock.connect(("8.8.8.8", 80))
        local_ip = temp_sock.getsockname()[0]
        temp_sock.close()
        print(f"🌐 Local IP address: {local_ip}")

        if local_ip.startswith(('192.168.', '10.', '172.')):
            print("⚠️  Behind NAT - may need port forwarding for external connections")
        else:
            print("✅ Public IP - direct P2P connections should work")

    except Exception as e:
        print(f"❌ Could not determine local IP: {e}")


def test_crypto_dependencies():
    """Test cryptography library functionality."""
    print("\n🔐 Testing cryptography dependencies...")

    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        print("✅ Cryptography library imported successfully")

        # Test key generation
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        public_key = private_key.public_key()
        print("✅ Elliptic curve key generation working")

        # Test ECDH
        private_key2 = ec.generate_private_key(ec.SECP256R1(), default_backend())
        public_key2 = private_key2.public_key()
        shared_key1 = private_key.exchange(ec.ECDH(), public_key2)
        shared_key2 = private_key2.exchange(ec.ECDH(), public_key)

        if shared_key1 == shared_key2:
            print("✅ ECDH key exchange working")
        else:
            print("❌ ECDH key exchange failed")
            return False

        # Test AES encryption
        import secrets
        key = secrets.token_bytes(32)
        iv = secrets.token_bytes(16)

        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(b"test message") + encryptor.finalize()

        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        if plaintext == b"test message":
            print("✅ AES encryption/decryption working")
            return True
        else:
            print("❌ AES encryption/decryption failed")
            return False

    except ImportError as e:
        print(f"❌ Cryptography import failed: {e}")
        print("💡 Install with: pip install cryptography")
        return False
    except Exception as e:
        print(f"❌ Cryptography test failed: {e}")
        return False


def main():
    """Run all network tests."""
    print("🧪 Anonymous & Ephemeral Chat - Network Test Suite")
    print("=" * 55)
    print("Testing network connectivity and dependencies...\n")

    tests_passed = 0
    total_tests = 4

    # Test 1: Port availability
    available_ports = test_port_availability()
    if available_ports:
        tests_passed += 1
        print(f"✅ Port test passed - {len(available_ports)} ports available")
    else:
        print("❌ Port test failed - no available ports")

    # Test 2: Socket communication
    if test_socket_communication():
        tests_passed += 1

    # Test 3: Network configuration
    test_firewall_and_nat()
    tests_passed += 1  # This test is informational

    # Test 4: Crypto dependencies
    if test_crypto_dependencies():
        tests_passed += 1

    # Summary
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! Your system is ready for ephemeral chat.")
        print("\n💡 You can now run:")
        print("   python src/ephemeral_chat.py --port 8000")
        print("   python src/ephemeral_chat.py --port 8001")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

        if available_ports:
            print(f"\n✨ Available ports for testing: {available_ports}")

        print("\n🔧 Troubleshooting tips:")
        print("   - Install cryptography: pip install cryptography")
        print("   - Check firewall settings for local connections")
        print("   - Ensure Python 3.8+ is installed")


if __name__ == "__main__":
    main()
