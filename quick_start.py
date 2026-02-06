#!/usr/bin/env python3
"""
Quick Start Script for Anonymous & Ephemeral Chat Application

This script helps you get started quickly with the chat application.
It will run basic tests and then start the interactive chat interface.
"""

import sys
import os
import subprocess

def check_dependencies():
    """Check if all dependencies are installed."""
    print("🔍 Checking dependencies...")

    try:
        import cryptography
        print("✅ cryptography library found")
        return True
    except ImportError:
        print("❌ cryptography library not found")
        print("📦 Installing cryptography...")

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
            print("✅ cryptography installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install cryptography")
            print("💡 Try running: pip install cryptography")
            return False

def run_tests():
    """Run basic network tests."""
    print("\n🧪 Running network tests...")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "examples"))
        from network_test import test_port_availability, test_crypto_dependencies

        # Test port availability
        available_ports = test_port_availability((8000, 8010))
        if not available_ports:
            print("⚠️  No available ports found in range 8000-8010")
            print("💡 You may need to use different port numbers")

        # Test crypto dependencies
        if test_crypto_dependencies():
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed")
            return False

    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def start_chat():
    """Start the interactive chat application."""
    print("\n🚀 Starting Anonymous & Ephemeral Chat...")
    print("💡 In another terminal, run:")
    print("   python quick_start.py --port 8001")
    print("   Then use: /connect localhost 8000")
    print()

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
        from ephemeral_chat import EphemeralChatNode

        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description="Quick start for ephemeral chat")
        parser.add_argument("--port", type=int, default=8000, help="Port to use")
        parser.add_argument("--username", type=str, default=None, help="Username")
        parser.add_argument("--skip-tests", action="store_true", help="Skip tests")

        args = parser.parse_args()

        if not args.skip_tests:
            if not run_tests():
                print("⚠️  Tests failed, but continuing anyway...")

        # Create and start chat node
        node = EphemeralChatNode(port=args.port, username=args.username)
        node.run_interactive_mode()

    except KeyboardInterrupt:
        print("\n👋 Chat terminated by user")
    except Exception as e:
        print(f"❌ Error starting chat: {e}")
        print("💡 Try running: python src/ephemeral_chat.py")

def main():
    """Main function."""
    print("🔐 Anonymous & Ephemeral Chat - Quick Start")
    print("=" * 50)

    # Check dependencies first
    if not check_dependencies():
        return

    # Start the chat application
    start_chat()

if __name__ == "__main__":
    main()
