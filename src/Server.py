import argparse
from connection.Node import Node, Connection
from lib.Segment import SegmentError, Segment
from lib.MessageInfo import MessageInfo
from collections import deque
import socket
import datetime
import time
import threading

HEARTBEAT_TIMEOUT = 30  # seconds
KILL_PASSWORD = "jarkom"
import random
from datetime import datetime
from lib.Constant import TIMEOUT_LISTEN, MESSAGES_LIMIT
from typing import List

EMOTICONS = {
    ":smile:": "😊",
    ":sad:": "😢",
    ":laugh:": "😂",
    ":grin:": "😁",
    ":cool:": "😎",
    ":cry:": "😭",
    ":sleeping:": "😴",
    ":heart:": "❤️",
    ":wink:": "😉",
    ":angry:": "😠",
    ":surprise:": "😲",
    ":thumbsup:": "👍",
    ":wave:": "👋"
}

class Server(Node):
    def __init__(self, ip: str, port: int,  kill_password: str = KILL_PASSWORD):
        super().__init__("Server", ip, port)
        self.client_buffers = {}                # {(ip, port): {seq_num: segment}}
        self.expected_seq = {}                  # {(ip, port): next_expected_seq}
        self.temp_seqs = {}
        self.kill_password = kill_password
        self.client_usernames = {}

        self.messages = deque()
        
    # Running server and listening to messages
    def run_server(self):
        threading.Thread(target=self.monitor_heartbeats, daemon=True).start()
        listen = True
        while listen:
            try:
                self.listen(TIMEOUT_LISTEN)
            except socket.error:
                continue


    def connect(self, ip, port):
        return
    

    def receive(self, ip_dest: str, port_dest: int, segment: Segment) -> None:
        flag = segment.get_flag()
        
        if flag.is_psh_flag() and not segment.get_data():
            # print(f"[<] Heartbeat received from {ip_dest}:{port_dest}")
    
            conn_key = (ip_dest, port_dest)
            if (len(self.messages) > 0):
                length = self.connections[conn_key].get_current_index()
                for i in range(length, len(self.messages)):
                    self._send_message(self.messages[i], ip_dest, port_dest)
                    self.connections[conn_key].increase_index()
            if conn_key in self.connections:
                self.connections[conn_key].last_heartbeat = datetime.now()
            return
          
        if flag.is_fin_flag() and not flag.is_ack_flag() and not flag.is_psh_flag():
            # print("[<] FIN received")
            if (ip_dest, port_dest) not in self.connections:
                self.send_segment(Segment.fin_ack(), ip_dest, port_dest)
                return
            # print("[>] Sending FIN-ACK")
            # print("[!] Closing connection")
            self.send_segment(Segment.fin_ack(), ip_dest, port_dest)
            self.remove_client(ip_dest, port_dest)
            return

        if flag.is_fin_ack_flag() and not flag.is_psh_flag():
            # print("[<] FIN-ACK received → link closed")
            self.remove_client(ip_dest, port_dest)
            return

        # SYN_FLAG
        if segment.get_flag().is_syn_flag():
            client_seq = segment.get_header()['seqNumber']
            # print("[<] Received SYN")

            # print("[>] Sending SYN-ACK")
            # Send: SYN
            server_seq = random.randint(1000, 50000)

            self.temp_seqs[(ip_dest, port_dest)] = {
                'server_seq': server_seq,
                'client_seq': client_seq
            }

            syn_ack = Segment.syn_ack(
                username = "Server",
                seq_num = server_seq, 
                ack_num = client_seq + 1
            )

            self.send_segment(syn_ack, ip_dest, port_dest)
        
        # ACK_FLAG in handshake
        elif segment.get_flag().is_ack_flag() and not segment.get_flag().is_psh_flag():
            if not hasattr(segment, 'payload') or not segment.payload:
                # print("[<] Received final ACK")
                # print("[!] Handshake complete")
                # print(f"[!] {ip_dest}:{port_dest} Connected!")

                self.client_usernames[(ip_dest, port_dest)] = segment.get_username()
                # Add log to messages
                self.messages.append(MessageInfo(
                    "Server",
                    datetime.now(),
                    f"{segment.get_username()} joined!"
                ))
                
                if (ip_dest, port_dest) not in self.connections:
                    # Add client ke list of Connections
                    client_seq = segment.get_header()['seqNumber']

                    server_seq = self.temp_seqs[(ip_dest, port_dest)]['server_seq']

                    self.connections[(ip_dest, port_dest)] = Connection(
                        self.ip, 
                        self.port, 
                        ip_dest, 
                        port_dest, 
                        server_seq + 1, 
                        client_seq + 1,
                        current_index=len(self.messages) - 1
                    )

                    # Initialize client buffer
                    self.client_buffers[(ip_dest, port_dest)] = {}
                    del self.temp_seqs[(ip_dest, port_dest)]
        
        else: # kasus kirim pesan (ada payload)
            payload_data = segment.get_data()
            if payload_data and len(payload_data) > 0:
                self._handle_data_segment(ip_dest, port_dest, segment)
            else:
                print(f"[DEBUG] Received segment with no payload, ignoring")


    def _handle_data_segment(self, ip_dest: str, port_dest: int, segment: Segment):
        client_key = (ip_dest, port_dest)
        seq_num = segment.header.get('seqNumber', 0)
        payload = segment.get_data().decode()
    
        # print(f"[<] Received segment seq={seq_num} from {ip_dest}:{port_dest}")
    
        if client_key not in self.connections:
            print(f"[!] Received data from unknown client {ip_dest}:{port_dest}, ignoring")
            return
        
        # Initialize buffer for new client
        if client_key not in self.client_buffers:
            self.client_buffers[client_key] = {}
            self.expected_seq[client_key] = 0
    
        # Handle duplicate
        if seq_num in self.client_buffers[client_key]:
            # print(f"[DEBUG] Duplicate segment {seq_num}, resending ACK")
            
            ack_segment = Segment.ack(
                username = "Server",
                ack_num  = seq_num + 1
            )

            self.send_segment(ack_segment, ip_dest, port_dest)
            return
    
        # Buffer the segment
        self.client_buffers[client_key][seq_num] = segment
    
        # Always ACK
        ack_segment = Segment.ack(
            username = "Server",
            ack_num=seq_num + len(payload)
        )
        self.send_segment(ack_segment, ip_dest, port_dest)
        # print(f"[>] Sent ACK for segment {seq_num} (ack={seq_num + 1})")
    
        # If this is the final segment (FIN)
        if segment.get_flag().is_fin_flag():
            # print(f"[!] FIN received from {ip_dest}:{port_dest}")
    
            # Reconstruct full message
            segments = self.client_buffers[client_key]
            full_message = b''.join(
                segments[seq].get_data() for seq in sorted(segments)
            )
    
            # Print final message
            full_message_str = full_message.decode(errors='ignore')
            full_message_str = self.replace_emoticons(full_message_str)
            print(f"[O] Full message from {ip_dest}:{port_dest}: {full_message_str}")

            if self.handle_command(ip_dest, port_dest, segment.get_username(), full_message_str):
                return
            
            self.messages.append(MessageInfo(
                segment.get_username(),
                datetime.now(),
                full_message_str
            ))

            # Clean up
            if client_key in self.client_buffers:
                del self.client_buffers[client_key]


    def handle_command(self, ip_dest: str, port_dest: int, username: str, message: str) -> bool:
        client_key = (ip_dest, port_dest)
        
        if message.startswith('!disconnect'):
            self.remove_client(ip_dest, port_dest)
            return True
            
        elif message.startswith('!kill '):
            password = message[6:].strip()
            
            if password == self.kill_password:
                shutdown_message = MessageInfo(
                    "Server",
                    datetime.now(),
                    f"Server shutting down by {username}"
                )
                
                for client_key in list(self.connections.keys()):
                    try:
                        self._send_message(shutdown_message, client_key[0], client_key[1])
                    except:
                        pass
                for (ip, port) in list(self.connections.keys()):
                    self.close_connection(ip, port)
                print(f"[!] Server shutdown command accepted from {username}")
                exit(0)
                return True
            else:
                print(f"[!] KILL COMMAND REJECTED! Wrong password from {username}")
                # Optionally send error message back to client
                error_message = MessageInfo(
                    "Server",
                    datetime.now(),
                    "Kill command rejected: incorrect password"
                )
                try:
                    self._send_message(error_message, ip_dest, port_dest)
                except:
                    pass
            #TODO: actually kill the server
            return True
            
        elif message.startswith('!change '):
            new_name = message[8:].strip()
            old_name = username
            
            if new_name and new_name != old_name:
                print(f"[CMD] {old_name} ({ip_dest}:{port_dest}) changed name to {new_name}")
                
                self.client_usernames[client_key] = new_name
                
                self.messages.append(MessageInfo(
                    "Server",
                    datetime.now(),
                    f"{old_name} changed name to {new_name}"
                ))
                
                print(f"[!] Username updated: {old_name} → {new_name}")
            else:
                print(f"[!] Invalid name change request from {username}: '{new_name}'")
            
            return True
        return False
    
    def replace_emoticons(self, message: str) -> str:
        for text_emoticon, emoji in EMOTICONS.items():
            message = message.replace(text_emoticon, emoji)
        return message
    
    def broadcast(self, messageInfo: MessageInfo):
        # print(f"[DEBUG] Broadcasting message to {len(self.connections)} clients: '{message}'")
        
        message = messageInfo.get_msg()
        username = messageInfo.get_username()

        for conn_key, conn in self.connections:


            segments: List[Segment] = self._split_message_to_segments(
                username,
                message,
                conn.send_seq,
                conn.recv_seq
            )

            ip, port = conn_key
            # print(f"[>] Broadcasting to {ip}:{port}")
            

    def get_client_status(self):
        print(f"\n[STATUS] Connected clients: {len(self.connections)}")
        for i, (client_key, conn) in enumerate(self.connections.items(), 1):
            ip, port = client_key
            expected_seq = self.expected_seq.get(client_key, 'Unknown')
            buffer_size = len(self.client_buffers.get(client_key, {}))
            print(f"  {i}. {ip}:{port} - Expected seq: {expected_seq}, Buffer: {buffer_size} segments")


    def list_clients(self):
        print(f"\n[CLIENTS] Connected clients ({len(self.connections)}):")
        for i, (client_key, conn) in enumerate(self.connections.items(), 1):
            ip, port = client_key
            print(f"  {i}. {ip}:{port}")
        return list(self.connections.keys())

    # Mornitor heartbeats from all connections
    def monitor_heartbeats(self):
        while True:
            now = datetime.now()
            to_remove = []

            for key, conn in list(self.connections.items()):
                if (now - conn.last_heartbeat).total_seconds() > HEARTBEAT_TIMEOUT:
                    # print(f"[!] Connection {key} timed out (AFK), removing.")
                    to_remove.append(key)

            for key in to_remove:
                self.connections.pop(key, None)

            time.sleep(5)  # periksa tiap 5 detik

            
    def remove_client(self, ip: str, port: int):
        key = (ip, port)
        if key not in self.connections:
            return
        username = self.client_usernames.get(key, "Unknown")
        self.connections.pop(key, None)
        self.client_buffers.pop(key, None)
        self.expected_seq.pop(key, None)
        self.client_usernames.pop(key, None)
        print(f"[!] Client {username} ({ip}:{port}) removed from server.")
        if username != "Unknown":  # Only add if we knew the user
            self.messages.append(MessageInfo(
                "Server",
                datetime.now(),
                f"{username} left the chat"
            ))
# Config argument
def load_args():
    # parsing argument from CLI
    arg = argparse.ArgumentParser()
    arg.add_argument('-i', '--ip', type=str, default='localhost', help='ip server')
    arg.add_argument('-p', '--port', type=int, default=1234, help='port server')
    args = arg.parse_args()
    return args

if __name__ == '__main__':
    args = load_args()
    server = Server(args.ip, args.port)
    
    # Can also be heartbeat
    def status_thread():
        import time
        while True:
            time.sleep(10)
            server.get_client_status()

    status_monitor = threading.Thread(target=status_thread)
    status_monitor.daemon = True
    status_monitor.start()
    
    try:
        server.run_server()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down...")
        for (ip, port) in list(server.connections.keys()):
            server.close_connection(ip, port)
        print("[!] All connections closed. Exiting.")
        exit(0)