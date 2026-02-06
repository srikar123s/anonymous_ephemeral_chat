import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import threading
import queue
from datetime import datetime

from ephemeral_chat import EphemeralChatNode

class GuiChatManager(threading.Thread):
    """
    This class runs the EphemeralChatNode in a separate thread
    and uses queues to communicate with the GUI to prevent freezing.
    """
    def __init__(self, gui_queue, port=0, username=None):
        super().__init__(daemon=True)
        self.gui_queue = gui_queue
        self.command_queue = queue.Queue()
        self.chat_node = EphemeralChatNode(port=port, username=username)

        # --- Monkey-patch the backend to push updates to the GUI queue ---
        self.chat_node.display_received_message = self.handle_received_message
        self.chat_node.perform_key_exchange = self.handle_key_exchange
        
        # Patch connection closed message
        original_handle_peer_connection = self.chat_node.handle_peer_connection
        def patched_handle_peer_connection(conn, addr):
            peer_id = f"{addr[0]}:{addr[1]}"
            original_handle_peer_connection(conn, addr)
            self.gui_queue.put(("SYSTEM", f"Connection closed with {peer_id}. Chat history cleared."))
        self.chat_node.handle_peer_connection = patched_handle_peer_connection
        # --- End Patching ---

    def run(self):
        """The main loop for the backend thread."""
        # Start the listener in its own thread
        listener = threading.Thread(target=self.chat_node.start_listening, daemon=True)
        listener.start()

        # Post startup info to the GUI
        self.gui_queue.put(("SYSTEM", f"Your connection info: localhost:{self.chat_node.port}"))
        self.gui_queue.put(("SYSTEM", f"Your username: {self.chat_node.username}"))

        # Process commands from the GUI
        while self.chat_node.session_active:
            try:
                command, args = self.command_queue.get(timeout=0.1)
                if command == "SEND":
                    self.chat_node.send_message(args)
                    self.gui_queue.put(("SENT", args))
                elif command == "CONNECT":
                    host, port = args
                    # Run connection in its own thread to not block this loop
                    threading.Thread(target=self.chat_node.connect_to_peer, args=(host, port), daemon=True).start()
                elif command == "CLEANUP":
                    self.chat_node.cleanup_session()
                    break
            except queue.Empty:
                continue
    
    def handle_key_exchange(self, conn, peer_id):
        """Wrapper for key exchange to post fingerprint to GUI."""
        # Use the original class method to avoid recursion
        is_success = self.chat_node.__class__.perform_key_exchange(self.chat_node, conn, peer_id)
        if is_success:
            session_key = self.chat_node.session_keys.get(peer_id)
            if session_key:
                fingerprint = self.chat_node.get_session_fingerprint(session_key)
                self.gui_queue.put(("SYSTEM", f"Secure session with {peer_id}"))
                self.gui_queue.put(("FINGERPRINT", f"🔒 VERIFY: {fingerprint}"))
        return is_success

    def handle_received_message(self, message_data, from_peer):
        """Wrapper to post received messages to the GUI queue."""
        self.gui_queue.put(("RECEIVED", message_data))

class ChatGUI:
    def __init__(self, root, args):
        self.root = root
        self.root.title("Anonymous & Ephemeral Chat")
        self.root.geometry("550x450")

        self.gui_queue = queue.Queue()
        self.args = args # Store args

        # --- Menu ---
        self.menu = tk.Menu(root)
        self.root.config(menu=self.menu)
        self.connection_menu = tk.Menu(self.menu, tearoff=0)
# ... (rest of the __init__ method is the same)

        self.menu.add_cascade(label="Connection", menu=self.connection_menu)
        self.connection_menu.add_command(label="Connect to Peer", command=self.prompt_connect_peer)
        self.connection_menu.add_separator()
        self.connection_menu.add_command(label="Exit", command=self.on_closing)

        # --- Chat Display ---
        self.chat_box = scrolledtext.ScrolledText(root, state='disabled', wrap=tk.WORD, bg="#2b2b2b", fg="#dcdcdc", font=("Helvetica", 10), insertbackground="white")
        self.chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.chat_box.tag_config("sent", foreground="#6c95eb")  # Light Blue
        self.chat_box.tag_config("received", foreground="#dcdcdc")  # White/Gray
        self.chat_box.tag_config("system", foreground="#999999", font=("Helvetica", 9, "italic"))
        self.chat_box.tag_config("fingerprint", foreground="#e8a866", font=("Helvetica", 10, "bold"))

        # --- Message Input ---
        self.entry_frame = tk.Frame(root, bg="#2b2b2b")
        self.entry_frame.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.entry_box = tk.Entry(self.entry_frame, font=("Helvetica", 10), bg="#3c3f41", fg="#dcdcdc", insertbackground="white")
        self.entry_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=5)
        self.entry_box.bind("<Return>", self.send_message_event)
        self.send_button = tk.Button(self.entry_frame, text="Send", command=self.send_message_event, bg="#3c3f41", fg="#dcdcdc", activebackground="#4e5254")
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0), ipady=4, ipadx=10)

        # --- Initialize and start Chat Backend ---
        self.chat_manager = GuiChatManager(self.gui_queue, port=self.args.port, username=self.args.username)
        self.chat_manager.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.process_queue()

    def process_queue(self):
        """Process all messages from the backend thread."""
        try:
            while not self.gui_queue.empty():
                msg_type, data = self.gui_queue.get_nowait()
                
                if msg_type == "SYSTEM":
                    self.insert_message(f"--- {data} ---", "system")
                elif msg_type == "FINGERPRINT":
                    self.insert_message(data, "fingerprint")
                elif msg_type == "SENT":
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.insert_message(f"[{timestamp}] You: {data}", "sent")
                elif msg_type == "RECEIVED":
                    timestamp = datetime.fromtimestamp(data['timestamp']).strftime("%H:%M:%S")
                    username = data.get('username', 'Unknown')
                    message = data.get('message', '')
                    self.insert_message(f"[{timestamp}] {username}: {message}", "received")

        finally:
            self.root.after(100, self.process_queue)

    def send_message_event(self, event=None):
        message = self.entry_box.get()
        if message:
            self.chat_manager.command_queue.put(("SEND", message))
            self.entry_box.delete(0, tk.END)

    def prompt_connect_peer(self):
        peer_info = simpledialog.askstring("Connect to Peer", "Enter peer address (host:port):", parent=self.root)
        if peer_info and ':' in peer_info:
            try:
                host, port_str = peer_info.split(':')
                port = int(port_str)
                self.chat_manager.command_queue.put(("CONNECT", (host, port)))
            except ValueError:
                messagebox.showerror("Invalid Input", "Port must be a number.")
            except Exception as e:
                messagebox.showerror("Connection Error", f"An unexpected error occurred: {e}")

    def insert_message(self, message, tag=None):
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, message + "\n", tag)
        self.chat_box.config(state='disabled')
        self.chat_box.see(tk.END)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit? All data will be destroyed."):
            if self.chat_manager.is_alive():
                self.chat_manager.command_queue.put(("CLEANUP", None))
            self.root.destroy()

def main(args=None):
    root = tk.Tk()
    app = ChatGUI(root, args)
    root.mainloop()

if __name__ == "__main__":
    # This part is now primarily for testing the GUI directly
    # The main entry is from ephemeral_chat.py
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=13377)
    parser.add_argument('--username', type=str, default=None)
    cli_args = parser.parse_args()
    main(cli_args)
