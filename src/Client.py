import argparse
import threading
import time
import random
from datetime import datetime
from collections import deque
from connection.Node import Node, Connection
from lib.MessageInfo import MessageInfo
from lib.Segment import Segment
import threading
import os
import time
from lib.Constant import TIMEOUT_TIME, WINDOW_SIZE, MESSAGES_LIMIT, HEARTBEAT_INTERVAL, MAX_WIDTH

class Client(Node):
    def __init__(self, username: str, client_ip: str, client_port: int,
                 server_ip: str, server_port: int) -> None:
        super().__init__(username, client_ip, client_port)

        # Server address
        self.server_ip = server_ip
        self.server_port = server_port

        # Sliding window state
        self.window_base: int = 0
        self.next_seq_num: int = 0
        self.window_buffer: dict[int, Segment] = {}  # {seq_num: segment}
        self.ack_received: set[int] = set()          # ACKed sequence numbers
        self.send_times: dict[int, float] = {}       # {seq_num: time sent}

        # Receiving state
        self.receive_buffer: dict[int, Segment] = {} # {seq_num: segment}
        self.expected_receive_seq: int = 1000        # Expected seq from server

        self.messages = deque(maxlen=MESSAGES_LIMIT)

        # Connect to Server
        self.connect(server_ip, server_port)
        
        # Start listening for incoming messages
        self._start_message_listener()

    # Three-way Handshake in Client
    def connect(self, ip: str, port: int) -> None:

        # [Step 1] Send SYN_FLAG
        initial_seq = random.randint(1000, 50000)
        syn_segment = Segment.syn(
            username = self.username,
            seq_num  = initial_seq
        )

        self.send_segment(syn_segment, ip, port)
        print("[>] Sent SYN")

        # [Step 2] Wait for SYN_FLAG and ACK_FLAG
        while True:
            try:
                segment, _, checksum_valid = self._Node__listen_recv(timeout=5)

                # TODO: checksum validation
                if segment.get_flag().is_syn_ack_flag():
                    server_seq = segment.get_header()['seqNumber']
                    server_ack = segment.get_header()['ackNumber']
                    print("[<] Received SYN-ACK")
                    break
            except Exception as e:
                print(f"[!] Error waiting for SYN-ACK: {e}")
                continue

        #[Step 3] Send ACK
        ack_segment = Segment.ack(
            username = self.username,
            seq_num  = initial_seq + 1,
            ack_num  = server_seq + 1
        )

        self.send_segment(ack_segment, ip, port)
        print("[>] Sent ACK")
        print("[!] Handshake complete")

        # store connection
        self.connections[(ip, port)] = Connection(
            self.ip, 
            self.port, 
            ip, 
            port, 
            initial_seq + 1, 
            server_seq + 1
        )

        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat, args=(ip, port), daemon=True)
        heartbeat_thread.start()

    def _start_message_listener(self):
        def clear_terminal():
            if os.name == 'nt':
                os.system('cls')
            else:
                os.system('clear')

        # TODO [low]: change to receive method in Node
        def listen_for_messages():
            while True:
                try:
                    segment, addr, checksum_valid = self._Node__listen_recv(timeout=1)
                    payload = segment.get_data()
                    # Skip jika ini adalah ACK untuk pesan yang kita kirim
                    if segment.get_flag().is_ack_flag():
                        continue

                    # send fin-ack to close connections
                    if segment.get_flag().is_fin_flag() and not payload:
                        self.send_segment(Segment.fin_ack(), self.server_ip, self.server_port)
                        os._exit(0)

                    # Handle pesan data yang masuk
                    if payload and len(payload) > 0:
                        seq_num = segment.header.get('seqNumber', 0)
                        
                        print(f"[<] Received message segment {seq_num}")

                        self.receive_buffer[seq_num] = segment
                        ack_segment = Segment.ack(
                            self.username,
                            ack_num=seq_num + len(payload.decode())
                        )

                        self.send_segment(
                            ack_segment,
                            self.server_ip,
                            self.server_port
                        )
                        print(f"[>] Sent ACK for message segment {seq_num}")


                        if segment.get_flag().is_fin_flag():
                            print(f"[!] FIN received from {self.server_ip}:{self.server_port}")
    
                            # Reconstruct full message
                            segments = self.receive_buffer
                            full_message = b''.join(
                                segments[seq].get_data() for seq in sorted(segments)
                            )

                            # Print final message
                            # print(f"[O] Full message from {self.server_ip}:{self.server_port}: {full_message.decode(errors='ignore')}")
                            self.messages.append(MessageInfo(
                                segment.get_username(),
                                datetime.now(),
                                f"{full_message.decode(errors='ignore')}"
                            ))

                            clear_terminal()
                            print("┌" + "─" * (MAX_WIDTH - 2) + "┐")
                            print(f"│{'CHAT ROOM'.center(MAX_WIDTH - 2)}│")
                            print("├" + "─" * (MAX_WIDTH - 2) + "┤")
                            for i, msg in enumerate(self.messages):
                                print(msg)
                                if i < len(self.messages) - 1:
                                    print("│" + " " * (MAX_WIDTH - 2) + "│") 
                            print("└" + "─" * (MAX_WIDTH - 2) + "┘")

                            self.receive_buffer.clear()

                            if (segment.get_username() == "Server" and 
                                full_message.decode(errors='ignore').startswith("Server shutting down")):
                                self.connections.pop((self.server_ip, self.server_port), None)

                except Exception as e:
                    continue
        
        listener_thread = threading.Thread(target=listen_for_messages)
        listener_thread.daemon = True
        listener_thread.start()


    def send_private_message(self, target_port: int, message: str):
        formatted_message = f"@{target_port}:{message}"
        # print(f"[DEBUG] Sending private message to port {target_port}: '{message}'")
        messageInfo = MessageInfo(self.username, datetime.now(), message)
        self._send_message(messageInfo, self.server_ip, self.server_port)


    def send_broadcast_message(self, message: str):
        # print(f"[DEBUG] Broadcasting message: '{message}'")
        messageInfo = MessageInfo(self.username, datetime.now(), message)
        self._send_message(messageInfo, self.server_ip, self.server_port)


    def receive(self, ip_dest: str, port_dest: str, segment: Segment):
        flag = segment.get_flag()

        # FIN Flag for close connection
        if flag.is_fin_flag() and not flag.is_ack_flag():
            # print("[<] FIN received")
            self.send_segment(Segment.fin_ack(), ip_dest, port_dest)
            self.connections.pop((ip_dest, port_dest), None)
            return
        
        # ACK for close connection
        elif flag.is_fin_ack_flag():
            # print("[<] FIN-ACK received → link closed")
            self.connections.pop((ip_dest, port_dest), None)
            return

    
    def heartbeat(self, server_ip, server_port):
        while True:
            try:
                if (server_ip, server_port) not in self.connections:
                    print("[DEBUG] Connection lost, stopping heartbeat")
                    break
                conn = self.connections[(server_ip, server_port)]
                segment = Segment.psh(
                    self.username,
                    seq_num=conn.send_seq,
                    ack_num=conn.recv_seq
                )

                self.send_segment(segment, server_ip, server_port)
            except:
                print("Failed to send heartbeat.")
                break
            time.sleep(HEARTBEAT_INTERVAL)


    def send_command(self, text: str):
        mi = MessageInfo(self.username, datetime.now(), text)
        self._send_message(mi, self.server_ip, self.server_port)

    def pop_connection(self):
        self.connections.pop((self.server_ip, self.server_port), None)
        return


# Config Argument
def load_args():
    # parsing argument from CLI
    arg = argparse.ArgumentParser()
    arg.add_argument('-ci', '--client_ip', type=str, default='localhost', help='ip the client is on')
    arg.add_argument('-cp', '--client_port', type=int, default=None, help='port the client is on')
    arg.add_argument('-si', '--server_ip', type=str, required=True, help='ip to listen on')
    arg.add_argument('-sp', '--server_port', type=int, required=True, help='port to listen on')
    arg.add_argument('-un', '--username', type=str, default='User', help='username of the client')
    args = arg.parse_args()
    return args

if __name__ == '__main__':
    args = load_args()
    # TODO: add username params
    if args.username.lower() == "server":
        exit()
        
    client = Client(username=args.username,
                    client_ip=args.client_ip,
                    client_port=None,
                    server_ip=args.server_ip,
                    server_port=args.server_port)

    print(f"Connected to {client.server_ip} {client.server_port} chat room ()" )
    
    while True:
        try:
            cmd = input(f"{client.username} > ").strip()
            
            if cmd == '!disconnect':
                client.send_command('!disconnect')
                client.close_connection(args.server_ip, args.server_port)
                break
            elif cmd.startswith('!kill '):
                password = cmd[6:].strip()
                client.send_command(f'!kill {password}')
            elif cmd.startswith('!change '):
                new_name = cmd[8:].strip()
                if new_name:
                    client.send_command(f'!change {new_name}')
                    client.change_username(new_name)
            elif cmd.startswith('!private '):
                parts = cmd[9:].split(' ', 1)           # Remove 'private '
                if len(parts) == 2:
                    target_port = int(parts[0])
                    message = parts[1]
                    client.send_private_message(target_port, message)
                else:
                    print("Usage: private <target_port> <message>")
            else:
                message = cmd[0:]                      # Remove 'broadcast '
                client.send_broadcast_message(message)
                
        except KeyboardInterrupt:
            client.close_connection(args.server_ip, args.server_port)
            print("\nClient interrupted. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Client shutting down...")
    # client.close_connection(args.server_ip, args.server_port)
