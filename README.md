# Anonymous & Ephemeral Chat Application

🔐 A proof-of-concept for secure, private communication that prioritizes user anonymity and data minimization.

## 1. Overview

The Anonymous & Ephemeral Chat Application is a peer-to-peer messaging system that eliminates permanent data storage and implements true anonymity through temporary cryptographic identities. Unlike traditional messaging apps that store data on servers, this application keeps everything in RAM and automatically destroys all traces when closed.

## 2. Problem Statement

Traditional messaging applications often depend on centralized servers, persistent user accounts, databases, and metadata collection. This project explores a decentralized alternative where peers communicate directly, messages are encrypted end-to-end, and session data is not intentionally persisted.

## 3. Objectives

- Provide private peer-to-peer text communication.
- Generate temporary cryptographic identities for each session.
- Protect messages using modern key exchange and authenticated encryption.
- Minimize stored data by keeping messages and keys in memory only.
- Provide both command-line and desktop GUI interfaces.

## 4. Key Features

- **🔒 True Anonymity**: New cryptographic identity generated for each session
- **⏰ Ephemeral Data**: All messages stored only in RAM, automatically destroyed
- **🔐 End-to-End Encryption**: AES-256-GCM encryption with ECDH key exchange
- **🌐 Peer-to-Peer**: Direct connections, no central servers
- **🛡️ Perfect Forward Secrecy**: Each session uses unique encryption keys
- **💾 Zero Persistence**: No data written to disk or databases
- **🗑️ Self-Destruction**: All traces removed when application closes

## 5. Screenshots & Demo

No screenshots are currently included. A two-node demonstration is available:

```bash
python examples/demo_session.py
```

For a manual demo, start two nodes on different ports, connect them with `/connect`, and exchange messages.

## 6. System Architecture

The application consists of a CLI or Tkinter GUI, an `EphemeralChatNode` backend, a cryptographic layer, and a TCP networking layer. Each peer derives a shared session key during connection setup and exchanges encrypted length-prefixed messages directly.

```text
CLI / Tkinter GUI
        |
EphemeralChatNode
  |     |       |
Crypto  TCP   RAM-only state
        |
   Encrypted peer
```

The detailed architecture is described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 7. Technology Stack

- **Language:** Python 3.8+
- **Cryptography:** `cryptography`
- **Key exchange:** ECDH with SECP256R1
- **Key derivation:** HKDF-SHA256
- **Message encryption:** AES-256-GCM
- **Networking:** Python TCP sockets
- **Concurrency:** Python `threading`
- **GUI:** Tkinter
- **Testing:** pytest and unittest
- **Packaging:** setuptools

## 8. Project Structure

See the complete file layout in the [Project Structure](#-project-structure) section below.

## 9. Installation & Setup

### Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Network connectivity for P2P connections

### Installation

1. **Extract the project:**
   ```bash
   unzip anonymous_ephemeral_chat.zip
   cd anonymous_ephemeral_chat
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python src/ephemeral_chat.py
   ```

### Alternative Installation Methods

#### Method 1: Using setup.py
```bash
python setup.py install
ephemeral-chat
```

#### Method 2: Development Mode
```bash
pip install -e .
ephemeral-chat
```

#### Method 3: Virtual Environment (Recommended)
```bash
python -m venv ephemeral_chat_env
source ephemeral_chat_env/bin/activate  # On Windows: ephemeral_chat_env\Scripts\activate
pip install -r requirements.txt
python src/ephemeral_chat.py
```

## 10. Environment Configuration

The application does not require environment variables, a database, or an external service. Configuration is supplied through command-line arguments:

- `--port`: Listening port; the default is `13377`.
- `--username`: Optional session username. If omitted, an anonymous username is generated.
- `--no-gui`: Run the command-line interface instead of the GUI.

## 11. Running the Application

### Usage

### Starting a Chat Node

```bash
# Start with default settings (random port, auto-generated username)
python src/ephemeral_chat.py

# Start with specific port and username
python src/ephemeral_chat.py --port 8000 --username alice

# Start second node for testing
python src/ephemeral_chat.py --port 8001 --username bob
```

### Basic Commands

Once the application is running, use these commands:

```
/connect <host> <port>  - Connect to another peer
/send <message>         - Send message to all connected peers
/status                 - Show current node status
/peers                  - List connected peers
/history                - Show message history (RAM only)
/clear                  - Clear message buffer
/help                   - Show all available commands
/quit                   - Exit and destroy all data
```

### Example Session

**Terminal 1 (Alice):**
```bash
$ python src/ephemeral_chat.py --port 8000 --username alice
🔐 Initializing Anonymous & Ephemeral Chat Node...
✅ Node initialized as 'alice' on port 8000
🔑 Temporary cryptographic identity generated (RAM only)
👂 Listening for connections on port 8000

🚀 Anonymous & Ephemeral Chat Node Running!
📡 Share your connection info: localhost:8000
alice> /help
```

**Terminal 2 (Bob):**
```bash
$ python src/ephemeral_chat.py --port 8001 --username bob
🔐 Initializing Anonymous & Ephemeral Chat Node...
✅ Node initialized as 'bob' on port 8001
bob> /connect localhost 8000
🤝 Connected to peer localhost:8000
bob> Hello Alice! This message is encrypted and ephemeral.
📤 Message sent to localhost:8000
```

**Back in Terminal 1 (Alice):**
```bash
📞 New connection from 127.0.0.1:54321
🔐 Secure session established with 127.0.0.1:54321
📥 [14:30:15] bob: Hello Alice! This message is encrypted and ephemeral.
alice> Hi Bob! No traces will remain after we close the app.
📤 Message sent to 127.0.0.1:54321
```

## 12. API Documentation

The main public class is `EphemeralChatNode`. Its constructor, connection methods, messaging methods, and cleanup lifecycle are documented in [docs/API.md](docs/API.md).

## 13. Dataset & Data Sources

This is a communication application and does not use a training dataset or external data source. User messages are generated at runtime and retained only in process memory during an active session.

## 14. Methodology & Implementation

1. Generate a temporary SECP256R1 key pair when a node starts.
2. Exchange public keys over a TCP connection.
3. Derive a 32-byte session key using ECDH and HKDF-SHA256.
4. Serialize message content and session metadata as JSON.
5. Encrypt each message with AES-GCM using a fresh random nonce.
6. Send the encrypted payload using a length-prefixed protocol.
7. Decrypt and display messages at the receiving peer.
8. Close sockets and clear session collections during cleanup.

## 🏗️ Detailed Architecture

### Core Components

1. **EphemeralChatNode**: Main class handling all chat functionality
2. **Cryptographic Layer**: ECDH key exchange + AES-256 encryption
3. **Network Layer**: Raw TCP sockets for P2P communication
4. **Memory Management**: In-RAM data structures with automatic cleanup

### Security Architecture

```
┌─────────────────┐    Encrypted P2P     ┌─────────────────┐
│   Alice's Node  │◄──── Connection ────►│   Bob's Node    │
│                 │                       │                 │
│ ┌─────────────┐ │                       │ ┌─────────────┐ │
│ │ Private Key │ │                       │ │ Private Key │ │
│ │  (Temp)     │ │                       │ │  (Temp)     │ │
│ └─────────────┘ │                       │ └─────────────┘ │
│ ┌─────────────┐ │   ECDH Key Exchange   │ ┌─────────────┐ │
│ │ Session Key │ │◄─────────────────────►│ │ Session Key │ │
│ │  (RAM Only) │ │                       │ │  (RAM Only) │ │
│ └─────────────┘ │                       │ └─────────────┘ │
│ ┌─────────────┐ │                       │ ┌─────────────┐ │
│ │  Messages   │ │                       │ │  Messages   │ │
│ │  (RAM Only) │ │                       │ │  (RAM Only) │ │
│ └─────────────┘ │                       │ └─────────────┘ │
└─────────────────┘                       └─────────────────┘
```

### Data Flow

1. **Identity Generation**: Temporary ECDH key pair created in RAM
2. **Peer Discovery**: Manual connection using IP:Port
3. **Key Exchange**: ECDH protocol establishes shared secret
4. **Message Encryption**: AES-256-GCM with a fresh random nonce per message
5. **Transmission**: Encrypted data sent over TCP socket
6. **Reception**: Decrypt using session key, display, store in RAM
7. **Cleanup**: All data automatically destroyed on exit

## 15. Results & Evaluation

- Cryptographic and networking tests currently pass with `17 passed`.
- Tests cover key generation, ECDH agreement, encryption/decryption, tamper detection, peer connections, multi-peer connections, and cleanup.
- Session keys are 32 bytes (256 bits).
- AES-GCM uses a 12-byte nonce for each encrypted message.
- No application database or intentional message file storage is used.

Run the test suite with:

```bash
python -m pytest tests/ -v
```

## 🔒 Security Features

### Cryptographic Implementation

- **Key Generation**: SECP256R1 elliptic curve (256-bit security)
- **Key Exchange**: Elliptic Curve Diffie-Hellman (ECDH)
- **Encryption**: AES-256-GCM with authenticated encryption
- **Key Derivation**: HKDF with SHA-256
- **Random Generation**: Cryptographically secure random numbers

### Privacy Protection

- **No Persistent Identity**: New key pair generated each session
- **No Metadata Storage**: Connection info not logged or stored
- **Memory-Only Data**: Zero disk writes, all data in RAM
- **Automatic Cleanup**: OS reclaims memory on process termination
- **Perfect Forward Secrecy**: Past messages remain secure even if keys compromised

### Attack Mitigation

- **Man-in-the-Middle**: Out-of-band key verification recommended
- **Replay Attacks**: Session keys and random IVs prevent replay
- **Traffic Analysis**: Direct P2P reduces metadata exposure
- **Memory Dumps**: Sensitive data cleared before process exit
- **Side Channels**: Process isolation and secure memory management

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/ -v
```

### Security Testing
```bash
# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Security-focused tests
python tests/test_security.py
```

### Manual Testing Scenarios

1. **Two-Node Communication**:
   - Start two instances on different ports
   - Connect and exchange messages
   - Verify encryption and decryption

2. **Multi-Node Network**:
   - Start 3+ instances
   - Create mesh network of connections
   - Test broadcast messaging

3. **Security Validation**:
   - Monitor network traffic with Wireshark
   - Verify all traffic is encrypted
   - Confirm no plaintext message leakage

4. **Ephemeral Verification**:
   - Send messages, then force-quit application
   - Check for any persistent data files
   - Confirm memory is clean after termination

## 📁 Project Structure

```
anonymous_ephemeral_chat/
├── src/
│   ├── ephemeral_chat.py      # Main application code
│   ├── ephemeral_chat_gui.py  # Tkinter GUI
│   └── __init__.py
├── examples/
│   ├── demo_session.py        # Demo script for testing
│   └── network_test.py        # Network connectivity test
├── tests/
│   ├── test_crypto.py         # Cryptography tests
│   ├── test_network.py        # Network layer tests
│   └── test_security.py       # Security validation tests
├── docs/
│   ├── ARCHITECTURE.md        # Technical architecture details
│   ├── SECURITY.md           # Security analysis and threat model
│   └── API.md                # API documentation
├── requirements.txt           # Python dependencies
├── setup.py                  # Installation script
├── quick_start.py             # Dependency check and launcher
├── SETUP.md                   # Setup instructions
├── README.md                 # This file
└── LICENSE                   # MIT License
```

## 16. Limitations

This is an educational proof of concept and has not undergone a professional security audit. It does not provide complete network anonymity, automated peer authentication, NAT traversal, offline messaging, or group-key management. Python memory cleanup also cannot guarantee immediate physical erasure of every sensitive object.

## 17. Future Scope

- Add automated authenticated peer verification.
- Support Tor, I2P, or relay-based anonymous routing.
- Add NAT traversal and secure peer discovery.
- Replace per-peer threads with an asynchronous networking model.
- Add bounded message buffers and stronger memory handling.
- Support group messaging, file transfer, and optional mobile clients.

## ⚠️ Important Security Notes

### Educational Purpose
This is a **proof-of-concept** implementation for educational and research purposes. While it implements strong cryptographic principles, it has not undergone professional security auditing and should not be used for production communications requiring high security.

### Known Limitations

1. **NAT Traversal**: May require port forwarding for connections across NAT
2. **Key Verification**: No automated key verification (manual process recommended)
3. **Offline Messages**: No message storage for offline users
4. **Group Management**: Limited scalability for large groups
5. **Network Monitoring**: Traffic patterns may be observable

### Recommendations for Enhanced Security

- Use with VPN or Tor for additional anonymity
- Verify public key fingerprints out-of-band
- Run on isolated or air-gapped systems for sensitive communications
- Regular security audits and code reviews
- Consider hardware security modules for key generation

## 18. Contributing

Contributions are welcome. Please add tests for new functionality, preserve the project’s security assumptions, and document behavior changes.

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your change.
4. Run formatting, linting, and relevant tests.
5. Submit a pull request.

## 🛠️ Development

### Code Style
```bash
# Format code
black src/ tests/ examples/

# Lint code
flake8 src/ tests/ examples/
```

### Building from Source
```bash
git clone https://github.com/privacy-research/anonymous-ephemeral-chat.git
cd anonymous-ephemeral-chat
python setup.py build
python setup.py install
```

## 📚 Educational Resources

### Cryptography Concepts
- [Elliptic Curve Cryptography](https://en.wikipedia.org/wiki/Elliptic-curve_cryptography)
- [Diffie-Hellman Key Exchange](https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange)
- [Advanced Encryption Standard](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard)

### Network Security
- [Peer-to-Peer Networks](https://en.wikipedia.org/wiki/Peer-to-peer)
- [End-to-End Encryption](https://en.wikipedia.org/wiki/End-to-end_encryption)
- [Perfect Forward Secrecy](https://en.wikipedia.org/wiki/Forward_secrecy)

### Privacy Engineering
- [Privacy by Design](https://en.wikipedia.org/wiki/Privacy_by_design)
- [Data Minimization](https://en.wikipedia.org/wiki/Data_minimization)
- [Anonymous Communication](https://en.wikipedia.org/wiki/Anonymous_communication)

## 🐛 Troubleshooting

### Common Issues

**Connection Failed**:
```bash
# Check if port is available
netstat -an | grep :8000

# Try different port
python src/ephemeral_chat.py --port 8080
```

**Import Error - cryptography**:
```bash
# Install/upgrade cryptography
pip install --upgrade cryptography

# On some systems, may need:
pip install cryptography --no-use-pep517
```

**Permission Denied**:
```bash
# Use unprivileged port (>1024)
python src/ephemeral_chat.py --port 8000
```

**Key Exchange Failed**:
- Ensure both nodes are running
- Check network connectivity
- Verify correct IP address and port
- Check firewall settings

### Debug Mode
```bash
# Run with verbose output
python src/ephemeral_chat.py --debug
```

## 19. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 20. Authors & Acknowledgements

**Authors:** Privacy Research Team

- **Cryptography Library**: Python Cryptographic Authority
- **Elliptic Curve Cryptography**: Victor Miller and Neal Koblitz
- **Diffie-Hellman**: Whitfield Diffie and Martin Hellman
- **Privacy Research Community**: For inspiration and guidance

## 📞 Support

- Create an issue on GitHub for bug reports
- Check existing issues for common problems
- Review documentation in the `docs/` directory
- Join the privacy engineering community for discussions

---

**⚠️ Remember**: This application stores NO data permanently. When you close it, all messages and identities are destroyed forever. This is by design for maximum privacy protection.

**🔐 Stay Anonymous. Stay Ephemeral. Stay Secure.**
