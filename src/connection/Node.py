from __future__ import annotations

from lib.Segment import Segment
from lib.Constant import PAYLOAD_SIZE, WINDOW_SIZE
from connection.Connection import Connection
from lib.MessageInfo import MessageInfo
from abc import ABC, abstractmethod
import socket
from typing import Dict, List
import time

class Node(ABC):
    def __init__(self, username: str, ip: str, port: int) -> None:
        self.username = username
        self.ip = ip
        self.port = port
        self.connections: Dict[(str, int), Connection] = {}
        self.__socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if port is None:
            self.__socket.bind(('', 0))  # 0 = auto-assign
            self.port = self.__socket.getsockname()[1]
        else:
            self.__socket.bind((ip, port))
            self.port = port

    @abstractmethod
    def connect(self, ip: str, port: int) -> None:  #implement di anaknya
        raise NotImplementedError

    @abstractmethod
    def receive(self, ip_dest: str, port_dest: int, segment: Segment):
        raise NotImplementedError

    def _split_message_to_segments(self, username, message: str, seq_num: int = 0, ack_num: int = 0) -> List[Segment]:
        segments = []

        for i in range(0, len(message), PAYLOAD_SIZE):
            chunk = message[i:i + PAYLOAD_SIZE]

            # PSH + FIN
            if i + PAYLOAD_SIZE >= len(message):
                segment = Segment(username, [True, False, True, False], seq_num, ack_num, chunk.encode(), 0)    
            else: # PSH
                segment = Segment(username, [False, False, True, False], seq_num, ack_num, chunk.encode(), 0)
            
            segments.append(segment)
            seq_num += len(chunk)

        return segments

    def listen(self, timeout):
        try:
            segment, address, checksum_valid = self.__listen_recv(timeout)
            if checksum_valid:
                self.receive(address[0], address[1], segment=segment)
            else:   # invalid checksum
                print(f"[!] Dropped corrupted segment from {address} (checksum invalid)")
            
        except ErrHandshake as e:
            print(e)


    def __listen_recv(self, timeout=None):
        self.__socket.settimeout(timeout)
        data, address = self.__socket.recvfrom(128)
        segment, checksum_valid = Segment.from_bytes(data)
        return  (segment, address, checksum_valid)

    def send_segment(self, seg: Segment, ip:str, port:int) -> None:
        seg.update_checksum()
        if (ip, port) in self.connections.keys():
            self.__socket.sendto(seg.get_bytes(), (ip, port))
        else:
            # self.connect(ip, port)
            self.__socket.sendto(seg.get_bytes(), (ip, port))

    # sending segment to ip and port destination
    def _send_message(self, message: MessageInfo, server_ip: str, server_port: int):
        conn = self.connections[(server_ip, server_port)]
        seq = conn.send_seq  
        ack = conn.recv_seq  
        username = message.get_username()
        payload = message.get_msg()

        segments = self._split_message_to_segments(
            username,
            payload,
            seq,
            ack
        )

        # print(f"[DEBUG] Split message into {len(segments)} segments.")

        # Sliding window
        self.window_buffer = {}  # seq_num -> Segment
        self.send_times = {}     # seq_num -> time
        self.ack_received = set()
        self.window_base = 0
        self.next_seq_num = 0

        while self.window_base < len(segments):
            # Send segments within the window
            while (self.next_seq_num < self.window_base + WINDOW_SIZE and
                   self.next_seq_num < len(segments)):
                segment = segments[self.next_seq_num]
                seq_num = segment.get_header()['seqNumber']

                # print(f"[>] Sending segment {self.next_seq_num} (seq={seq_num})")
                self.send_segment(segment, server_ip, server_port)

                self.window_buffer[seq_num] = segment
                self.send_times[seq_num] = time.time()
                self.next_seq_num += 1

            
            try: # Wait for ACK
                segment, addr, checksum_valid = self.__listen_recv(timeout=2)

                if segment.get_flag().is_ack_flag():
                    ack_num = segment.get_header()['ackNumber']
                    # print(f"[<] ACK received for seq < {ack_num}")
                    self.ack_received.add(ack_num)

                    # Slide window: remove all segments fully acked
                    while self.window_base < len(segments):
                        seg = segments[self.window_base]
                        seq_num = seg.get_header()['seqNumber']
                        seg_end = seq_num + len(seg.get_data().decode())

                        if seg_end <= ack_num:
                            del self.window_buffer[seq_num]
                            del self.send_times[seq_num]
                            self.window_base += 1
                        else:
                            break

            except Exception:
                pass  # timeout, check for resend

            # Retransmit timed-out segments
            current_time = time.time()
            for seq_num, seg in self.window_buffer.items():
                if seq_num not in self.ack_received:
                    if current_time - self.send_times[seq_num] > 2.5:
                        # print(f"[!] Timeout: Resending segment seq={seq_num}")
                        self.send_segment(seg, server_ip, server_port)
                        self.send_times[seq_num] = current_time

        # Update connection state
        conn.send_seq = seq
        # print("[!] All segments sent and acknowledged successfully.")


    # closes connection
    def close_connection(self, ip:str, port:int) -> None:
        connection = self.connections.get((ip, port))
        # if there's no connections
        if connection is None:
            return
        
        # send FIN_FLAG
        self.send_segment(Segment.fin(), ip, port)
        while self.connections.get((ip, port)) is not None:
            try:
                segment, address, checksum_valid = self.__listen_recv(timeout=2)
                if not checksum_valid:
                    continue
                flag = segment.get_flag()

                if flag.is_fin_ack_flag():
                    # print(f"[<] Received FIN-ACK from {ip}:{port}")
                    self.connections.pop((ip, port), None)
                    # print(f"[!] {ip}:{port} closed cleanly")
                    break
            except socket.timeout:
                # try sending
                self.send_segment(Segment.fin(), ip, port)
    def change_username(self, new_name: str, origin_addr: tuple[str, int] | None = None):
        if origin_addr is None:
            self.username = new_name
        else:
            pass

# Exception Handling
class ErrHandshake(Exception):
    def __init__(self):
        super().__init__("[ Error ]: Handshake")