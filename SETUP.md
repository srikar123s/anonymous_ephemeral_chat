# Setup Instructions for Anonymous & Ephemeral Chat Application

## Quick Setup (Recommended)

1. **Extract the project:**
   ```bash
   unzip anonymous_ephemeral_chat.zip
   cd anonymous_ephemeral_chat
   ```

2. **Run the quick start script:**
   ```bash
   python quick_start.py
   ```

   This will automatically:
   - Check and install dependencies
   - Run basic tests
   - Start the interactive chat interface

## Manual Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection for dependency installation

### Step-by-Step Installation

1. **Extract and navigate to project:**
   ```bash
   unzip anonymous_ephemeral_chat.zip
   cd anonymous_ephemeral_chat
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv ephemeral_chat_env

   # On Windows:
   ephemeral_chat_env\Scripts\activate

   # On macOS/Linux:
   source ephemeral_chat_env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests to verify installation:**
   ```bash
   python examples/network_test.py
   ```

5. **Start the application:**
   ```bash
   python src/ephemeral_chat.py
   ```

## Testing the Installation

### Automated Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python tests/test_crypto.py
python tests/test_network.py
python tests/test_security.py
```

### Manual Testing
```bash
# Test network connectivity
python examples/network_test.py

# Run demonstration
python examples/demo_session.py
```

## First Use

### Starting Your First Chat Session

1. **Terminal 1 - Start first node:**
   ```bash
   python src/ephemeral_chat.py --port 8000 --username alice
   ```

2. **Terminal 2 - Start second node:**
   ```bash
   python src/ephemeral_chat.py --port 8001 --username bob
   ```

3. **In Terminal 2, connect to first node:**
   ```
   bob> /connect localhost 8000
   ```

4. **Send messages in either terminal:**
   ```
   alice> Hello Bob! This message is encrypted.
   bob> Hi Alice! No traces will remain after we exit.
   ```

5. **Exit when done:**
   ```
   alice> /quit
   bob> /quit
   ```

## Troubleshooting

### Common Issues

**"Module not found" error:**
```bash
# Make sure you're in the project directory
cd anonymous_ephemeral_chat

# Check Python path
python -c "import sys; print(sys.path)"

# Try adding current directory to path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**"Permission denied" on port:**
```bash
# Use different port numbers
python src/ephemeral_chat.py --port 8080
```

**"Connection refused":**
- Make sure the listening node is started first
- Check firewall settings
- Verify the correct IP and port

**Cryptography installation fails:**
```bash
# On some systems, try:
pip install --upgrade pip setuptools wheel
pip install cryptography --no-use-pep517

# Or use system package manager:
# Ubuntu/Debian:
sudo apt-get install python3-cryptography

# macOS:
brew install python-cryptography
```

### Getting Help

1. **Check the documentation:**
   - README.md - Overview and basic usage
   - docs/API.md - API documentation
   - docs/ARCHITECTURE.md - Technical details
   - docs/SECURITY.md - Security analysis

2. **Run diagnostic tests:**
   ```bash
   python examples/network_test.py
   ```

3. **Verify installation:**
   ```bash
   python -c "from src.ephemeral_chat import EphemeralChatNode; print('OK')"
   ```

## Next Steps

Once you have the basic setup working:

1. **Read the documentation** in the `docs/` folder
2. **Experiment with the examples** in `examples/`
3. **Run security tests** to understand the security model
4. **Try the interactive demo** for hands-on experience

## Development Setup

If you want to modify or extend the code:

1. **Install development dependencies:**
   ```bash
   pip install pytest pytest-cov black flake8
   ```

2. **Run development tools:**
   ```bash
   # Format code
   black src/ tests/ examples/

   # Lint code  
   flake8 src/ tests/ examples/

   # Run tests with coverage
   pytest tests/ --cov=src --cov-report=html
   ```

3. **Use the Makefile for common tasks:**
   ```bash
   make help      # Show available commands
   make install   # Install dependencies
   make test      # Run tests
   make demo      # Run demo
   make lint      # Check code style
   make format    # Format code
   ```

Remember: This is a proof-of-concept for educational purposes. All communication data is stored only in memory and is automatically destroyed when the application exits.
