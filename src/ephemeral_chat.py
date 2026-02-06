# corrected_ephemeral_chat.py
import socket
import threading
import secrets
import time
import json
import sys
import hashlib
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


def int_to_bytes(n):
    length = (n.bit_length() + 7) // 8 or 1
    return n.to_bytes(length, 'big')


def bytes_to_int(b):
    return int.from_bytes(b, 'big')


def recv_exact(conn, n):
    """Read exactly n bytes from conn, or return None if connection closes early."""
    data = b''
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


class EphemeralChatNode:
    def __init__(self, port=0, username=None):
        self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        self.public_key = self.private_key.public_key()

        if username:
            self.username = username
        else:
            public_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            username_hash = hashlib.sha256(public_bytes).hexdigest()[:8]
            self.username = f"anon_{username_hash}"

        self.active_sessions = {}   # peer_id -> socket
        self.message_buffer = []
        self.peer_keys = {}         # peer_id -> peer public key object
        self.session_keys = {}      # peer_id -> session AES key (bytes)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('localhost', port))
        self.port = self.socket.getsockname()[1]

        self.session_active = True
        self.listener_thread = None

    def get_public_key_string(self):
        public_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_bytes.decode('utf-8')

    def load_public_key_from_string(self, key_string):
        key_bytes = key_string.encode('utf-8')
        return serialization.load_pem_public_key(key_bytes, backend=default_backend())

    def generate_session_key(self, peer_public_key):
        shared_key = self.private_key.exchange(ec.ECDH(), peer_public_key)
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'ephemeral_chat_session',
            backend=default_backend()
        ).derive(shared_key)
        return derived_key

    def encrypt_message(self, message, session_key):
        """
        Encrypt a message with AES-GCM.
        Returns: nonce + ciphertext + tag
        """
        try:
            aesgcm = AESGCM(session_key)
            nonce = secrets.token_bytes(12)  # recommended size for GCM
            full_message = {
                'username': self.username,
                'message': message,
                'timestamp': time.time()
            }
            message_json = json.dumps(full_message).encode('utf-8')
            encrypted_data = aesgcm.encrypt(nonce, message_json, None)
            return nonce + encrypted_data   # nonce | ciphertext | tag
        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            return None

    def decrypt_message(self, encrypted_data, session_key):
        """
        Decrypt a message with AES-GCM.
        Input: nonce + ciphertext + tag
        """
        try:
            if len(encrypted_data) < 12:
                raise ValueError("Encrypted payload too short")

            nonce = encrypted_data[:12]
            ciphertext_tag = encrypted_data[12:]

            aesgcm = AESGCM(session_key)
            decrypted_data = aesgcm.decrypt(nonce, ciphertext_tag, None)
            message_data = json.loads(decrypted_data.decode('utf-8'))
            return message_data
        except Exception as e:
            print(f"❌ Error decrypting message: {e}")
            return None

    def start_listening(self):
        self.socket.listen(5)
        print(f"🟡 Listening for connections on port {self.port}")

        while self.session_active:
            try:
                conn, addr = self.socket.accept()
                peer_thread = threading.Thread(
                    target=self.handle_peer_connection,
                    args=(conn, addr),
                    daemon=True
                )
                peer_thread.start()
            except Exception as e:
                if self.session_active:
                    print(f"❌ Error accepting connection: {e}")

    def handle_peer_connection(self, conn, addr):
        peer_id = f"{addr[0]}:{addr[1]}"
        try:
            if peer_id not in self.session_keys:
                ok = self.perform_key_exchange(conn, peer_id)
                if not ok:
                    print(f"❌ Key exchange failed for {peer_id}; closing connection")
                    conn.close()
                    return
                else:
                    print(f"🔐 Secure session established with {peer_id}")
            else:
                print(f"🔐 Session already established with {peer_id} (skipping key exchange)")

            self.active_sessions[peer_id] = conn

            while self.session_active:
                try:
                    length_size_byte = conn.recv(1)
                    if not length_size_byte:
                        break
                    length_size = int.from_bytes(length_size_byte, 'big')

                    length_bytes = recv_exact(conn, length_size)
                    if length_bytes is None:
                        break

                    message_length = bytes_to_int(length_bytes)
                    if message_length <= 0:
                        print(f"❌ Received invalid message length {message_length} from {peer_id}")
                        break

                    encrypted_data = recv_exact(conn, message_length)
                    if encrypted_data is None:
                        break

                    session_key = self.session_keys.get(peer_id)
                    if session_key:
                        message_data = self.decrypt_message(encrypted_data, session_key)
                        if message_data:
                            self.display_received_message(message_data, peer_id)

                            self.message_buffer.append({
                                'type': 'received',
                                'from': peer_id,
                                'data': message_data,
                                'timestamp': time.time()
                            })

                            # 👁 Show encrypted + decrypted
                            print(f"   🔒 Encrypted (hex): {encrypted_data.hex()[:80]}... ({len(encrypted_data)} bytes)")
                            print(f"   🔑 Decrypted: {message_data['message']}")
                        else:
                            print(f"❌ Error decrypting message from {peer_id}")
                    else:
                        print(f"❌ No session key for {peer_id} while receiving message")
                except Exception as e:
                    print(f"❌ Error in peer connection: {e}")
                    break
        except Exception as e:
            print(f"❌ Error in key exchange: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            self.active_sessions.pop(peer_id, None)
            self.session_keys.pop(peer_id, None)
            self.peer_keys.pop(peer_id, None)
            self.message_buffer.clear()
            print(f"🟣 Connection with {peer_id} closed, message buffer cleared.")

    def perform_key_exchange(self, conn, peer_id):
        try:
            our_public_key = self.get_public_key_string()
            key_bytes = our_public_key.encode('utf-8')

            conn.sendall(len(key_bytes).to_bytes(4, byteorder='big'))
            conn.sendall(key_bytes)

            peer_key_length_bytes = recv_exact(conn, 4)
            if not peer_key_length_bytes:
                print(f"❌ Failed to receive key length from {peer_id}")
                return False
            peer_key_length = int.from_bytes(peer_key_length_bytes, byteorder='big')

            if peer_key_length <= 0 or peer_key_length > 10_000_000:
                print(f"❌ Received unreasonable peer key length: {peer_key_length}")
                return False

            peer_key_bytes = recv_exact(conn, peer_key_length)
            if peer_key_bytes is None:
                print(f"❌ Connection lost while receiving key from {peer_id}")
                return False

            peer_key_string = peer_key_bytes.decode('utf-8')
            peer_public_key = self.load_public_key_from_string(peer_key_string)
            self.peer_keys[peer_id] = peer_public_key

            session_key = self.generate_session_key(peer_public_key)
            if session_key:
                self.session_keys[peer_id] = session_key
                fingerprint = self.get_session_fingerprint(session_key)
                print(f"✅ Session key established with {peer_id}")
                print(f"🔒 Verify this fingerprint with your peer: {fingerprint}")
                return True
            else:
                print(f"❌ Failed to generate session key with {peer_id}")
                return False
        except Exception as e:
            print(f"❌ Key exchange failed with {peer_id}: {e}")
            return False

    def connect_to_peer(self, peer_host, peer_port):
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_host, peer_port))

            peer_id = f"{peer_host}:{peer_port}"
            if self.perform_key_exchange(peer_socket, peer_id):
                print(f"🤝 Connected to peer {peer_id}")
                self.active_sessions[peer_id] = peer_socket

                peer_thread = threading.Thread(
                    target=self.handle_peer_connection,
                    args=(peer_socket, (peer_host, peer_port)),
                    daemon=True
                )
                peer_thread.start()
                return True
            else:
                peer_socket.close()
                return False
        except Exception as e:
            print(f"❌ Failed to connect to peer {peer_host}:{peer_port} - {e}")
            return False

    def send_message(self, message, peer_id=None):
        if not self.active_sessions:
            print("❌ No active connections. Connect to peers first.")
            return

        targets = [peer_id] if peer_id else list(self.active_sessions.keys())

        for target in targets:
            if target in self.active_sessions and target in self.session_keys:
                try:
                    session_key = self.session_keys[target]
                    encrypted_msg = self.encrypt_message(message, session_key)
                    if not encrypted_msg:
                        continue
                    peer_socket = self.active_sessions[target]

                    length_bytes = int_to_bytes(len(encrypted_msg))
                    length_prefix = len(length_bytes).to_bytes(1, 'big') + length_bytes

                    peer_socket.sendall(length_prefix)
                    peer_socket.sendall(encrypted_msg)

                    self.message_buffer.append({
                        'type': 'sent',
                        'to': target,
                        'message': message,
                        'timestamp': time.time()
                    })

                    # 👁 Show encrypted + plaintext
                    print(f"📤 Message sent to {target}")
                    print(f"   🔒 Encrypted (hex): {encrypted_msg.hex()[:80]}... ({len(encrypted_msg)} bytes)")
                    print(f"   🔑 Plaintext: {message}")

                except Exception as e:
                    print(f"❌ Error sending message to {target}: {e}")

    def display_received_message(self, message_data, from_peer):
        timestamp = datetime.fromtimestamp(message_data['timestamp'])
        time_str = timestamp.strftime("%H:%M:%S")
        print(f"[{time_str}] {message_data['username']}: {message_data['message']}")

    def show_status(self):
        print(f"📊 Node Status:")
        print(f"   Username: {self.username}")
        print(f"   Port: {self.port}")
        print(f"   Active sessions: {len(self.active_sessions)}")
        print(f"   Messages in buffer: {len(self.message_buffer)}")
        if self.active_sessions:
            print(f"   Connected peers:")
            for peer_id in self.active_sessions.keys():
                print(f"     • {peer_id}")
        print()

    def show_help(self):
        help_text = """
/connect <host> <port>  - Connect to a peer
/send <message>         - Send message to all peers
/status                 - Show node status
/peers                  - List connected peers
/history                - Show message history (RAM only)
/clear                  - Clear message buffer
/help                   - Show this help
/quit                   - Exit application (destroys all data)
"""
        print(help_text)

    def show_message_history(self):
        print(f"📜 Message History (RAM only - {len(self.message_buffer)} messages):")
        if not self.message_buffer:
            print("   No messages in buffer")
            return

        for msg in self.message_buffer[-10:]:
            timestamp = datetime.fromtimestamp(msg['timestamp'])
            time_str = timestamp.strftime("%H:%M:%S")
            if msg['type'] == 'sent':
                print(f"   📤 [{time_str}] You: {msg['message']}")
            else:
                username = msg['data'].get('username', 'Unknown')
                message = msg['data'].get('message', '')
                print(f"   📥 [{time_str}] {username}: {message}")
        print()

    def cleanup_session(self):
        print("🧹 Cleaning up session...")
        self.session_active = False
        for peer_id, peer_socket in list(self.active_sessions.items()):
            try:
                peer_socket.close()
            except:
                pass
        try:
            self.socket.close()
        except:
            pass
        self.message_buffer.clear()
        self.active_sessions.clear()
        self.peer_keys.clear()
        self.session_keys.clear()
        print("✅ Session cleaned up - all data ephemeral, no traces left")

    def run_interactive_mode(self):
        self.listener_thread = threading.Thread(target=self.start_listening, daemon=True)
        self.listener_thread.start()
        print(f"🚀 Anonymous & Ephemeral Chat Node Running!")
        print(f"📡 Share your connection info: localhost:{self.port}")
        print(f"🔑 Your public key fingerprint: {self.username}")
        self.show_help()
        try:
            while self.session_active:
                try:
                    command = input(f"{self.username}> ").strip()
                    if not command:
                        continue
                    if command.startswith('/'):
                        self.handle_command(command)
                    else:
                        self.send_message(command)
                except KeyboardInterrupt:
                    print("👋 Goodbye! All ephemeral data will be destroyed.")
                    break
                except EOFError:
                    break
        finally:
            self.cleanup_session()

    def handle_command(self, command):
        parts = command.split()
        cmd = parts[0].lower()
        if cmd == '/connect':
            if len(parts) == 3:
                host, port = parts[1], int(parts[2])
                self.connect_to_peer(host, port)
            else:
                print("Usage: /connect <host> <port>")
        elif cmd == '/send':
            if len(parts) > 1:
                message = ' '.join(parts[1:])
                self.send_message(message)
            else:
                print("Usage: /send <message>")
        elif cmd == '/status':
            self.show_status()
        elif cmd == '/peers':
            if self.active_sessions:
                print("Connected peers:")
                for peer_id in self.active_sessions.keys():
                    print(f"  • {peer_id}")
            else:
                print("No connected peers")
        elif cmd == '/history':
            self.show_message_history()
        elif cmd == '/clear':
            self.message_buffer.clear()
            print("📝 Message buffer cleared")
        elif cmd == '/help':
            self.show_help()
        elif cmd == '/quit':
            print("👋 Exiting... All ephemeral data will be destroyed.")
            self.session_active = False
        else:
            print(f"Unknown command: {cmd}. Type /help for available commands.")

    def get_session_fingerprint(self, session_key):
        """Generates a human-readable fingerprint for a session key."""
        return hashlib.sha256(session_key).hexdigest()[:16]


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Anonymous & Ephemeral Chat Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--port', type=int, default=13377, help='Port to listen on. Default is 13377 (0 for random).')
    parser.add_argument('--username', type=str, default=None, help='Username for this session (auto-generated if not provided)')
    parser.add_argument('--no-gui', action='store_true', help='Run in command-line mode only')
    args = parser.parse_args()

    if not args.no_gui:
        try:
            from ephemeral_chat_gui import main as run_gui
            # Pass the parsed arguments to the GUI's main function
            run_gui(args)
        except ImportError:
            print("❌ GUI component not found. Running in command-line mode.")
            print("   To run the GUI, make sure 'ephemeral_chat_gui.py' is in the same directory.")
            run_cli(args)
        except Exception as e:
            print(f"❌ Failed to start GUI: {e}. Falling back to command-line mode.")
            run_cli(args)
        finally:
            # This message prints to the terminal after the GUI window is closed.
            print("\n🔐 GUI Closed. All ephemeral data destroyed - no traces remain.")
    else:
        run_cli(args)

def run_cli(args):
    try:
        node = EphemeralChatNode(port=args.port, username=args.username)
        node.run_interactive_mode()
    except KeyboardInterrupt:
        print("👋 Application terminated by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        print("🔐 All ephemeral data destroyed - no traces remain")


if __name__ == "__main__":
    main()
